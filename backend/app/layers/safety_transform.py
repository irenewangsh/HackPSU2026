"""Layer 5 — Safety Transform: suggest safer execution strategy."""

from app.models.schemas import DecisionType, SensitivityLevel, TransformKind


class SafetyTransformLayer:
    def propose(
        self,
        *,
        decision: DecisionType,
        sensitivity: SensitivityLevel,
    ) -> list[TransformKind]:
        by_level: dict[SensitivityLevel, list[TransformKind]] = {
            SensitivityLevel.LOW: [TransformKind.ALLOW],
            SensitivityLevel.MEDIUM: [
                TransformKind.ALLOW_LIMITED_SCOPE,
                TransformKind.PREVIEW_FIRST,
            ],
            SensitivityLevel.HIGH: [
                TransformKind.MASK_SENSITIVE_FIELDS,
                TransformKind.SANDBOX_COPY,
                TransformKind.REQUIRE_CONFIRMATION,
            ],
            SensitivityLevel.CRITICAL: [
                TransformKind.READ_ONLY_MODE,
                TransformKind.STRICT_ISOLATION,
                TransformKind.REQUIRE_EXPLICIT_CONFIRMATION,
            ],
        }
        kinds = by_level[sensitivity][:]
        if decision == DecisionType.ALLOW:
            return [TransformKind.ALLOW]
        if decision == DecisionType.LIMITED:
            return [k for k in kinds if k != TransformKind.REQUIRE_EXPLICIT_CONFIRMATION]
        if decision == DecisionType.CONFIRM:
            if TransformKind.REQUIRE_CONFIRMATION not in kinds:
                kinds.append(TransformKind.REQUIRE_CONFIRMATION)
            return kinds
        return [TransformKind.READ_ONLY_MODE, TransformKind.STRICT_ISOLATION]

    def describe(self, kinds: list[TransformKind]) -> str:
        if not kinds:
            return "No transform applied."
        return "Apply: " + ", ".join(k.value for k in kinds)
