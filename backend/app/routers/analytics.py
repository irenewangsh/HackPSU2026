from fastapi import APIRouter

from app.layers.memory import PreferenceMemory

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

_memory: PreferenceMemory | None = None


def bind_memory(m: PreferenceMemory) -> None:
    global _memory
    _memory = m


@router.get("/heatmap")
async def risk_heatmap():
    assert _memory is not None
    cells = await _memory.heatmap_buckets()
    return {"cells": cells}


@router.get("/authority-timeline")
async def authority_timeline(limit: int = 100):
    assert _memory is not None
    rows = await _memory.list_authority_timeline(limit=limit)
    return {"items": rows}


@router.get("/preference-memory")
async def preference_memory(limit: int = 80):
    assert _memory is not None
    rows = await _memory.list_scenario_profiles(limit=limit)
    return {"items": rows}
