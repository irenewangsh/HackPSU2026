"""Layer 5 — Safety Transform: intermediate states beyond allow/deny."""

from app.models.schemas import ActionType, DecisionType, PermissionDecision, TransformKind


class SafetyTransformLayer:
    def propose(
        self,
        *,
        action: ActionType,
        decision: DecisionType,
        need_mask: bool,
        need_isolate: bool,
        time_limit: bool,
    ) -> list[TransformKind]:
        kinds: list[TransformKind] = []
        if decision == DecisionType.DENY:
            return [TransformKind.NONE]
        if need_mask:
            kinds.append(TransformKind.MASK_PII)
        if action in (ActionType.READ_FILE, ActionType.OPEN_URL) and need_mask:
            kinds.append(TransformKind.SUMMARY_ONLY)
        if action == ActionType.WRITE_FILE and need_isolate:
            kinds.append(TransformKind.SANDBOX_COPY)
        if action in (ActionType.FORM_SUBMIT, ActionType.PAYMENT):
            kinds.append(TransformKind.SIMULATE_ONLY)
        if action == ActionType.OPEN_URL:
            kinds.append(TransformKind.DOMAIN_WHITELIST)
        if time_limit:
            kinds.append(TransformKind.TIME_LIMITED)
        if not kinds:
            kinds.append(TransformKind.NONE)
        return kinds

    def describe(self, kinds: list[TransformKind]) -> str:
        if kinds == [TransformKind.NONE] or not kinds:
            return "No transform applied."
        return "Apply: " + ", ".join(k.value for k in kinds)
