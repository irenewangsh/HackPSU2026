from pydantic import BaseModel

from fastapi import APIRouter

from app.layers.memory import PreferenceMemory

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])

_memory: PreferenceMemory | None = None


def bind_memory(m: PreferenceMemory) -> None:
    global _memory
    _memory = m


class ProfileUpdate(BaseModel):
    risk_aversion: float | None = None
    forgetting_lambda_per_hour: float | None = None


@router.get("")
async def get_profile():
    assert _memory is not None
    ra = await _memory.profile_value("risk_aversion", 0.45)
    fl = await _memory.profile_value(
        "forgetting_lambda_per_hour", 0.015
    )
    lf = await _memory.profile_value("last_forget_wallclock", 0.0)
    return {
        "risk_aversion": ra,
        "forgetting_lambda_per_hour": fl,
        "last_forget_wallclock": lf,
    }


@router.patch("")
async def patch_profile(body: ProfileUpdate):
    assert _memory is not None
    if body.risk_aversion is not None:
        await _memory.set_profile_value("risk_aversion", body.risk_aversion)
    if body.forgetting_lambda_per_hour is not None:
        await _memory.set_profile_value(
            "forgetting_lambda_per_hour", body.forgetting_lambda_per_hour
        )
    return await get_profile()


@router.post("/forget-now")
async def forget_now():
    """Force one forgetting pass (decay preference weights)."""
    assert _memory is not None
    await _memory.set_profile_value("last_forget_wallclock", 0.0)
    await _memory.apply_forgetting_if_due()
    return {"ok": True}
