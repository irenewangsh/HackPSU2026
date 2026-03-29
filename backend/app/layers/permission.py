"""Layer 4 — Permission Manager: map risk + envelope to decisions + scopes."""

from app.models.schemas import (
    ActionType,
    DecisionType,
    PermissionDecision,
    TransformKind,
)


class PermissionManager:
    def decide(
        self,
        *,
        composite_risk: float,
        envelope: float,
        action: ActionType,
    ) -> tuple[DecisionType, bool, bool, bool]:
        """
        Returns decision, need_mask, need_isolate, time_limit
        """
        effective = composite_risk * (1.15 - envelope)
        need_mask = composite_risk >= 0.35 or action in (
            ActionType.PAYMENT,
            ActionType.LOGIN,
        )
        need_isolate = action in (ActionType.SHELL, ActionType.UPLOAD, ActionType.WRITE_FILE)
        time_limit = action in (ActionType.OPEN_URL, ActionType.SHELL)

        if action in (ActionType.PAYMENT, ActionType.LOGIN):
            return DecisionType.PROMPT_USER, True, True, True

        if effective < 0.28:
            return DecisionType.ALLOW, need_mask, need_isolate, time_limit
        if effective < 0.55:
            return DecisionType.TRANSFORM, True, need_isolate, time_limit
        if effective < 0.78:
            return DecisionType.PROMPT_USER, True, True, time_limit
        return DecisionType.DENY, True, True, True

    def build_scope(
        self,
        action: ActionType,
        decision: DecisionType,
    ) -> dict:
        scope: dict = {"read_only": action == ActionType.READ_FILE}
        if decision == DecisionType.TRANSFORM:
            scope["write_mode"] = "sandbox_copy_only"
            scope["network"] = "restricted"
        elif decision == DecisionType.ALLOW:
            scope["network"] = "allow_same_origin"
        else:
            scope["network"] = "deny"
        return scope
