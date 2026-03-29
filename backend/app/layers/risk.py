"""Layer 3 — Risk Engine: combine action, data, domain, task, and memory."""

from app.models.schemas import (
    ActionType,
    AgentActionRequest,
    DomainTrust,
    RiskReport,
    SensitivityLevel,
    TaskType,
)


class RiskEngine:
    def score(
        self,
        req: AgentActionRequest,
        sensitivity_level: SensitivityLevel,
        domain_trust: DomainTrust,
        user_trust_bias: float,
    ) -> RiskReport:
        reasons: list[str] = []
        base_action = _action_base_risk(req.action_type, req.overwrite, reasons)
        data_map = {
            SensitivityLevel.LOW: 0.12,
            SensitivityLevel.MEDIUM: 0.38,
            SensitivityLevel.HIGH: 0.72,
            SensitivityLevel.CRITICAL: 0.92,
        }
        data_risk = data_map[sensitivity_level]

        domain_delta = 0.0
        if domain_trust == DomainTrust.UNTRUSTED:
            domain_delta = 0.1
            reasons.append("untrusted domain bump")
        elif domain_trust == DomainTrust.FINANCIAL:
            domain_delta = 0.16
            reasons.append("financial domain bump")
        else:
            domain_delta = -0.06
            reasons.append("trusted domain reduction")

        if req.environment_hint and "public" in req.environment_hint.lower():
            base_action = min(1.0, base_action + 0.15)
            reasons.append("public/untrusted environment bump")

        adjusted = 0.5 * base_action + 0.4 * data_risk + domain_delta
        composite = min(1.0, max(0.0, adjusted - 0.1 * user_trust_bias))

        if req.task_type == TaskType.FINANCIAL_ASSISTANT:
            composite = min(1.0, composite + 0.08)
            reasons.append("financial_assistant strict mode bump")

        if req.action_type in (
            ActionType.MAKE_PAYMENT,
            ActionType.LOGIN,
            ActionType.SUBMIT_FORM,
            ActionType.DELETE_FILE,
            ActionType.SHARE_DATA,
        ):
            composite = max(composite, 0.75)
            reasons.append("high-impact action floor")

        risk_100 = round(composite * 100, 1)
        return RiskReport(
            action_risk=round(base_action * 100, 1),
            data_risk=round(data_risk * 100, 1),
            risk_score=risk_100,
            composite_score=round(composite, 3),
            reasons=reasons,
        )


def _action_base_risk(
    action: ActionType, overwrite: bool, reasons: list[str]
) -> float:
    table: dict[ActionType, float] = {
        ActionType.READ_FILE: 0.15,
        ActionType.CLASSIFY_FILE: 0.2,
        ActionType.MOVE_FILE: 0.35,
        ActionType.RENAME_FILE: 0.38,
        ActionType.UPLOAD_FILE: 0.68,
        ActionType.RUN_SHELL: 0.85,
        ActionType.OPEN_WEBSITE: 0.28,
        ActionType.LOGIN: 0.8,
        ActionType.PASTE_CONTENT: 0.62,
        ActionType.SUBMIT_FORM: 0.76,
        ActionType.MAKE_PAYMENT: 0.95,
        ActionType.DELETE_FILE: 0.83,
        ActionType.SHARE_DATA: 0.8,
    }
    r = table.get(action, 0.5)
    if overwrite and action in (ActionType.MOVE_FILE, ActionType.RENAME_FILE):
        r = min(1.0, r + 0.2)
        reasons.append("destructive/overwrite potential")
    return r
