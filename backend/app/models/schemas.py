from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    MOVE_FILE = "move_file"
    OPEN_URL = "open_url"
    PASTE = "paste"
    SHELL = "shell"
    UPLOAD = "upload"
    FORM_SUBMIT = "form_submit"
    LOGIN = "login"
    PAYMENT = "payment"


class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionType(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    PROMPT_USER = "prompt_user"
    TRANSFORM = "transform"


class TransformKind(str, Enum):
    NONE = "none"
    MASK_PII = "mask_pii"
    SUMMARY_ONLY = "summary_only"
    READ_ONLY_VIEW = "read_only_view"
    SANDBOX_COPY = "sandbox_copy"
    SIMULATE_ONLY = "simulate_only"
    DOMAIN_WHITELIST = "domain_whitelist"
    TIME_LIMITED = "time_limited"


class AgentActionRequest(BaseModel):
    """What the OS agent wants to do — must pass through the mediator."""

    action_type: ActionType
    target_path: str | None = None
    target_url: str | None = None
    mime_type: str | None = None
    payload_preview: str | None = Field(
        default=None,
        description="Short text snippet for sensitivity scan (not full secrets).",
    )
    form_field_names: list[str] | None = None
    overwrite: bool = False
    session_id: str = "default"
    environment_hint: str | None = Field(
        default=None,
        description="e.g. classroom, home, public_wifi",
    )


class SensitivityReport(BaseModel):
    level: SensitivityLevel
    categories: list[str]
    signals: list[str]


class RiskReport(BaseModel):
    action_risk: float = Field(ge=0, le=1)
    data_risk: float = Field(ge=0, le=1)
    composite_score: float = Field(ge=0, le=1)
    reasons: list[str]


class PermissionDecision(BaseModel):
    decision: DecisionType
    transforms: list[TransformKind] = []
    effective_scope: dict[str, Any] = Field(default_factory=dict)
    user_message: str
    expires_in_seconds: int | None = None


class TrustEnvelopeState(BaseModel):
    """Progressive Trust Envelope — how much autonomy is granted right now."""

    value: float = Field(ge=0, le=1, description="0=tight, 1=expanded")
    factors: list[str]
    shrunk_for: list[str] = []


class MediationResult(BaseModel):
    request_id: str
    sensitivity: SensitivityReport
    risk: RiskReport
    trust_envelope: TrustEnvelopeState
    decision: PermissionDecision
    transformed_payload_hint: str | None = None
    audit_note: str
    capability_token: str | None = None
    policy_digest: str | None = None
    capability_scopes: list[str] = []
    native: dict[str, Any] | None = None


class UserFeedback(BaseModel):
    request_id: str
    accepted: bool
    scenario_category: str = "general"
    notes: str | None = None


class PreferenceReset(BaseModel):
    category: str | None = None  # None = full reset


class AuditEntry(BaseModel):
    id: int
    ts: datetime
    action_type: str
    decision: str
    composite_risk: float
    summary: str


class HealthResponse(BaseModel):
    service: str
    version: str
    layers: list[str]
