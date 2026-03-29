from fastapi import APIRouter, HTTPException

from app.layers.memory import PreferenceMemory

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])

_memory: PreferenceMemory | None = None


def bind_memory(m: PreferenceMemory) -> None:
    global _memory
    _memory = m


@router.get("")
async def list_ops(limit: int = 50):
    assert _memory is not None
    return {"items": await _memory.list_reversible_ops(limit)}


@router.post("/{op_id}/rollback")
async def rollback(op_id: int):
    assert _memory is not None
    res = await _memory.rollback_operation(op_id)
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res)
    return res
