"""Layer 1 — Agent Hook: all agent capabilities must be declared and routed here."""

from app.models.schemas import ActionType, AgentActionRequest

_BLOCKED_COMBOS: set[tuple[ActionType, str | None]] = set()


def validate_hooked_action(req: AgentActionRequest) -> list[str]:
    """Return blocking reasons, empty if the hook accepts the request shape."""
    reasons: list[str] = []
    if req.action_type in (
        ActionType.READ_FILE,
        ActionType.WRITE_FILE,
        ActionType.MOVE_FILE,
    ) and not req.target_path:
        reasons.append("file actions require target_path")
    if req.action_type == ActionType.OPEN_URL and not req.target_url:
        reasons.append("open_url requires target_url")
    if req.action_type in (ActionType.FORM_SUBMIT, ActionType.LOGIN, ActionType.PAYMENT):
        if not req.target_url and not req.payload_preview:
            reasons.append("high-impact actions need url or payload context")
    return reasons
