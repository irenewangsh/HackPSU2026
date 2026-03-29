from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    READ_FILE = "read_file"
    CLASSIFY_FILE = "classify_file"
    MOVE_FILE = "move_file"
    RENAME_FILE = "rename_file"
    UPLOAD_FILE = "upload_file"
    RUN_SHELL = "run_shell"
    OPEN_WEBSITE = "open_website"
    LOGIN = "login"
    PASTE_CONTENT = "paste_content"
    SUBMIT_FORM = "submit_form"
    MAKE_PAYMENT = "make_payment"
    DELETE_FILE = "delete_file"
    SHARE_DATA = "share_data"


class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionType(str, Enum):
    ALLOW = "allow"
    LIMITED = "limited"
    CONFIRM = "confirm"
    DENY = "deny"


class TransformKind(str, Enum):
    ALLOW = "allow"
    ALLOW_LIMITED_SCOPE = "allow_limited_scope"
    PREVIEW_FIRST = "preview_first"
    MASK_SENSITIVE_FIELDS = "mask_sensitive_fields"
    SANDBOX_COPY = "sandbox_copy"
    REQUIRE_CONFIRMATION = "require_confirmation"
    READ_ONLY_MODE = "read_only_mode"
    STRICT_ISOLATION = "strict_isolation"
    REQUIRE_EXPLICIT_CONFIRMATION = "require_explicit_confirmation"


class DomainTrust(str, Enum):
    TRUSTED = "trusted"
    FINANCIAL = "financial"
    UNTRUSTED = "untrusted"


class TaskType(str, Enum):
    GENERAL = "general"
    COURSEWORK_ORGANIZER = "coursework_organizer"
    FINANCIAL_ASSISTANT = "financial_assistant"


class AgentActionRequest(BaseModel):
    """What the OS agent wants to do — must pass through the mediator."""

    action_type: ActionType
    task_type: TaskType = TaskType.GENERAL
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
    domain_trust: DomainTrust = DomainTrust.UNTRUSTED
    categories: list[str]
    signals: list[str]


class RiskReport(BaseModel):
    action_risk: float = Field(ge=0, le=100)
    data_risk: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    composite_score: float = Field(ge=0, le=1)
    reasons: list[str]


class PermissionState(BaseModel):
    file_read_write: str
    execution: str
    network: str
    review_required: bool
    limited_mode_only: bool


class PermissionDecision(BaseModel):
    decision: DecisionType
    permissions: PermissionState
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
    masked_preview: str | None = None
    transformed_payload_hint: str | None = None
    audit_note: str
    preference_memory: dict[str, Any] = Field(default_factory=dict)
    capability_token: str | None = None
    policy_digest: str | None = None
    capability_scopes: list[str] = []
    native: dict[str, Any] | None = None


class UserFeedback(BaseModel):
    request_id: str
    accepted: bool | None = None
    outcome: str | None = None  # allow | ask | deny
    task_type: TaskType = TaskType.GENERAL
    action_type: ActionType = ActionType.READ_FILE
    sensitivity: SensitivityLevel = SensitivityLevel.LOW
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
