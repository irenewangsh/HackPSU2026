"""Layer 4 — Permission Manager: map risk + envelope to decisions + scopes."""

from app.models.schemas import (
    ActionType,
    DecisionType,
    PermissionState,
)


class PermissionManager:
    def decide(
        self,
        *,
        composite_risk: float,
        envelope: float,
        action: ActionType,
    ) -> tuple[DecisionType, PermissionState]:
        """
        Returns top-level decision and permission matrix.
        """
        effective = composite_risk * (1.15 - envelope)
        if action in (ActionType.MAKE_PAYMENT, ActionType.LOGIN, ActionType.SUBMIT_FORM):
            if effective < 0.72:
                return DecisionType.CONFIRM, _permission_matrix(DecisionType.CONFIRM)
            return DecisionType.DENY, _permission_matrix(DecisionType.DENY)

        if effective < 0.35:
            decision = DecisionType.ALLOW
        elif effective < 0.7:
            decision = DecisionType.LIMITED
        elif effective < 0.9:
            decision = DecisionType.CONFIRM
        else:
            decision = DecisionType.DENY
        return decision, _permission_matrix(decision)

    def build_scope(
        self,
        action: ActionType,
        decision: DecisionType,
    ) -> dict:
        scope: dict = {"read_only": action == ActionType.READ_FILE}
        if decision == DecisionType.LIMITED:
            scope["write_mode"] = "sandbox_copy_only"
            scope["network"] = "restricted"
        elif decision == DecisionType.ALLOW:
            scope["network"] = "allow_same_origin"
        elif decision == DecisionType.CONFIRM:
            scope["network"] = "confirm_first"
        else:
            scope["network"] = "deny"
        return scope


def _permission_matrix(decision: DecisionType) -> PermissionState:
    if decision == DecisionType.ALLOW:
        return PermissionState(
            file_read_write="full",
            execution="allowed",
            network="allowed",
            review_required=False,
            limited_mode_only=False,
        )
    if decision == DecisionType.LIMITED:
        return PermissionState(
            file_read_write="limited",
            execution="restricted",
            network="restricted",
            review_required=False,
            limited_mode_only=True,
        )
    if decision == DecisionType.CONFIRM:
        return PermissionState(
            file_read_write="preview_only",
            execution="blocked_until_confirm",
            network="blocked_until_confirm",
            review_required=True,
            limited_mode_only=True,
        )
    return PermissionState(
        file_read_write="blocked",
        execution="blocked",
        network="blocked",
        review_required=True,
        limited_mode_only=True,
    )
