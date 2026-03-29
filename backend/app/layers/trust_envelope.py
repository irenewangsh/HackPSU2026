"""Progressive Trust Envelope — dynamic autonomy boundary."""

from app.models.schemas import ActionType, AgentActionRequest, SensitivityLevel, TrustEnvelopeState


class ProgressiveTrustEnvelope:
    """
    Starts tight; expands when data is low-risk, action is reversible, context is calm.
    Shrinks on money, identity, shell, unknown sensitive surfaces.
    """

    def compute(
        self,
        req: AgentActionRequest,
        sensitivity: SensitivityLevel,
        memory_trust: float,
    ) -> TrustEnvelopeState:
        v = 0.35 + 0.4 * memory_trust
        factors: list[str] = ["baseline user-specific trust prior"]
        shrunk: list[str] = []

        if sensitivity == SensitivityLevel.CRITICAL:
            v -= 0.45
            shrunk.append("critical data sensitivity")
        elif sensitivity == SensitivityLevel.HIGH:
            v -= 0.25
            shrunk.append("high data sensitivity")

        if req.action_type in (ActionType.SHELL, ActionType.PAYMENT, ActionType.LOGIN):
            v -= 0.35
            shrunk.append("high-privilege or irreversible action class")

        if req.environment_hint and "public" in (req.environment_hint or "").lower():
            v -= 0.12
            shrunk.append("untrusted environment")

        if req.action_type in (ActionType.READ_FILE, ActionType.MOVE_FILE):
            v += 0.05
            factors.append("reversible read/move tends to widen envelope slightly")

        v = max(0.05, min(0.95, v))
        return TrustEnvelopeState(value=round(v, 3), factors=factors, shrunk_for=shrunk)
