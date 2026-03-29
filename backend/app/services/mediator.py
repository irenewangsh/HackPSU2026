"""Orchestrates all six layers for a single agent action."""

from __future__ import annotations

import re
import uuid

from app.capability_tokens import issue_capability
from app.layers.hook import validate_hooked_action
from app.layers.memory import PreferenceMemory
from app.layers.permission import PermissionManager
from app.layers.risk import RiskEngine
from app.layers.safety_transform import SafetyTransformLayer
from app.layers.sensitivity import SensitivityAnalyzer
from app.layers.trust_envelope import ProgressiveTrustEnvelope
from app.models.schemas import (
    AgentActionRequest,
    DecisionType,
    MediationResult,
    PermissionDecision,
    SensitivityLevel,
    TransformKind,
)
from app.native_policy import native_status, policy_digest


def _mask_preview(text: str | None) -> str | None:
    if not text:
        return None
    out = text
    out = re.sub(
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "[CARD_REDACTED]",
        out,
    )
    out = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]", out)
    out = re.sub(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "[EMAIL_REDACTED]",
        out,
        flags=re.I,
    )
    out = re.sub(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_REDACTED]", out)
    out = re.sub(r"\b(?:sk_live|Bearer)\s+\S+", "[TOKEN_REDACTED]", out, flags=re.I)
    return out


def _primary_category(sens_categories: list[str]) -> str:
    if not sens_categories:
        return "general"
    priority = (
        "secret_material",
        "financial_surface",
        "identity_or_finance",
        "authentication",
        "sensitive_form",
        "structured_id",
        "monetary",
        "coursework",
    )
    for p in priority:
        if p in sens_categories:
            return p
    return sens_categories[0]


class MediatorService:
    def __init__(self, memory: PreferenceMemory | None = None) -> None:
        self.memory = memory or PreferenceMemory()
        self.sensitivity = SensitivityAnalyzer()
        self.risk = RiskEngine()
        self.permission = PermissionManager()
        self.transforms = SafetyTransformLayer()
        self.envelope = ProgressiveTrustEnvelope()

    async def mediate(self, req: AgentActionRequest) -> MediationResult:
        await self.memory.apply_forgetting_if_due()
        req_id = str(uuid.uuid4())
        block = validate_hooked_action(req)
        if block:
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail={"hook_reject": block})

        sens = self.sensitivity.analyze(
            path=req.target_path,
            url=req.target_url,
            mime=req.mime_type,
            text=req.payload_preview,
            form_fields=req.form_field_names,
        )
        cat = _primary_category(sens.categories)
        trust_bias = await self.memory.trust_bias(cat)
        scenario_bias = await self.memory.scenario_bias(
            task_type=req.task_type.value,
            action_type=req.action_type.value,
            sensitivity=sens.level.value,
        )
        combined_bias = max(-1.0, min(1.0, 0.6 * trust_bias + 0.4 * scenario_bias))

        risk = self.risk.score(req, sens.level, sens.domain_trust, combined_bias)
        mem_trust = max(0.0, min(1.0, (combined_bias + 1) / 2))
        trust_state = self.envelope.compute(req, sens.level, mem_trust)

        dec, perm_state = self.permission.decide(
            composite_risk=risk.composite_score,
            envelope=trust_state.value,
            action=req.action_type,
        )
        scope = self.permission.build_scope(req.action_type, dec)

        kinds = self.transforms.propose(
            decision=dec,
            sensitivity=sens.level,
        )
        expires = 300 if dec in (DecisionType.LIMITED, DecisionType.CONFIRM) else None
        user_msg = _user_message(dec, sens.level, risk.composite_score, trust_state)

        permission = PermissionDecision(
            decision=dec,
            permissions=perm_state,
            transforms=kinds,
            effective_scope=scope,
            user_message=user_msg,
            expires_in_seconds=expires,
        )

        transformed = _mask_preview(req.payload_preview)

        summary = f"{req.action_type.value} risk={risk.composite_score:.2f} -> {dec.value}"
        digest = policy_digest(
            [
                req.action_type.value,
                req.target_path or "",
                req.target_url or "",
                sens.level.value,
                dec.value,
            ]
        )
        scopes = [
            f"action:{req.action_type.value}",
            f"sensitivity:{sens.level.value}",
        ]
        if dec in (DecisionType.ALLOW, DecisionType.LIMITED):
            scopes.append("hook:execute")
        if dec == DecisionType.CONFIRM:
            scopes.append("approval:pending")
        ttl = expires or 300
        cap_token = None
        if dec in (DecisionType.ALLOW, DecisionType.LIMITED, DecisionType.CONFIRM):
            cap_token = issue_capability(
                request_id=req_id,
                scopes=scopes,
                policy_digest=digest,
                ttl_seconds=ttl,
            )

        scenario_profile = await self.memory.scenario_profile(
            task_type=req.task_type.value,
            action_type=req.action_type.value,
            sensitivity=sens.level.value,
        )

        await self.memory.append_audit(
            action_type=req.action_type.value,
            decision=dec.value,
            composite_risk=risk.composite_score,
            summary=summary,
        )
        await self.memory.append_authority_event(
            request_id=req_id,
            action_type=req.action_type.value,
            decision=dec.value,
            composite_risk=risk.composite_score,
            envelope=trust_state.value,
            summary=summary,
        )

        return MediationResult(
            request_id=req_id,
            sensitivity=sens,
            risk=risk,
            trust_envelope=trust_state,
            decision=permission,
            masked_preview=transformed,
            transformed_payload_hint=transformed,
            audit_note=summary,
            preference_memory=scenario_profile,
            capability_token=cap_token,
            policy_digest=digest,
            capability_scopes=scopes,
            native=native_status(),
        )


def _user_message(
    dec: DecisionType,
    sens: SensitivityLevel,
    composite: float,
    trust,
) -> str:
    parts = [
        f"Composite risk {composite:.2f}; data sensitivity {sens.value}.",
        f"Progressive Trust Envelope at {trust.value:.2f}.",
    ]
    if dec == DecisionType.DENY:
        parts.append("Blocked: default deny for high-risk composition.")
    elif dec == DecisionType.CONFIRM:
        parts.append("User confirmation required before proceeding.")
    elif dec == DecisionType.LIMITED:
        parts.append("Proceeding in limited mode with constrained transforms.")
    else:
        parts.append("Within policy: allowed with ongoing monitoring.")
    return " ".join(parts)
