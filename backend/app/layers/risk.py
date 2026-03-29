"""Layer 3 — Risk Engine: combine action, data, environment, and learned prefs."""

from app.models.schemas import ActionType, AgentActionRequest, RiskReport, SensitivityLevel


class RiskEngine:
    def score(
        self,
        req: AgentActionRequest,
        sensitivity_level: SensitivityLevel,
        user_trust_bias: float,
    ) -> RiskReport:
        reasons: list[str] = []
        base_action = _action_base_risk(req.action_type, req.overwrite, reasons)
        data_map = {
            SensitivityLevel.LOW: 0.1,
            SensitivityLevel.MEDIUM: 0.35,
            SensitivityLevel.HIGH: 0.65,
            SensitivityLevel.CRITICAL: 0.9,
        }
        data_risk = data_map[sensitivity_level]

        if req.environment_hint and "public" in req.environment_hint.lower():
            base_action = min(1.0, base_action + 0.15)
            reasons.append("public/untrusted environment bump")

        # User history: slight pull toward their comfort zone without overriding safety
        adjusted = 0.55 * base_action + 0.45 * data_risk
        composite = min(1.0, max(0.0, adjusted - 0.08 * user_trust_bias))

        if req.action_type in (ActionType.PAYMENT, ActionType.LOGIN):
            composite = max(composite, 0.75)
            reasons.append("high-impact action floor")

        return RiskReport(
            action_risk=round(base_action, 3),
            data_risk=round(data_risk, 3),
            composite_score=round(composite, 3),
            reasons=reasons,
        )


def _action_base_risk(
    action: ActionType, overwrite: bool, reasons: list[str]
) -> float:
    table: dict[ActionType, float] = {
        ActionType.READ_FILE: 0.15,
        ActionType.WRITE_FILE: 0.45,
        ActionType.MOVE_FILE: 0.35,
        ActionType.OPEN_URL: 0.25,
        ActionType.PASTE: 0.3,
        ActionType.SHELL: 0.85,
        ActionType.UPLOAD: 0.7,
        ActionType.FORM_SUBMIT: 0.65,
        ActionType.LOGIN: 0.8,
        ActionType.PAYMENT: 0.95,
    }
    r = table.get(action, 0.5)
    if overwrite and action in (ActionType.WRITE_FILE, ActionType.MOVE_FILE):
        r = min(1.0, r + 0.2)
        reasons.append("destructive/overwrite potential")
    return r
