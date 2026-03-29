from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.capability_tokens import verify_capability
from app.config import settings
from app.layers.memory import PreferenceMemory
from app.models.schemas import (
    AgentActionRequest,
    HealthResponse,
    MediationResult,
    PreferenceReset,
    UserFeedback,
)
from app.routers import analytics, hooks, operations, profile
from app.services.mediator import MediatorService


memory = PreferenceMemory()
mediator = MediatorService(memory=memory)

analytics.bind_memory(memory)
operations.bind_memory(memory)
profile.bind_memory(memory)
hooks.bind_mediator(mediator)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await memory.init()
    yield


app = FastAPI(
    title="SentinelOS API",
    description="Supervisory control plane for OS agents — mediation, risk, transforms, memory.",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(analytics.router)
app.include_router(operations.router)
app.include_router(profile.router)
app.include_router(hooks.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        service="SentinelOS",
        version="0.2.0",
        layers=[
            "agent_hook",
            "sensitivity_analyzer",
            "risk_engine",
            "permission_manager",
            "safety_transform",
            "preference_memory",
            "c_native_policy",
            "capability_tokens",
            "sandbox_hooks",
        ],
    )


@app.post("/api/v1/mediate", response_model=MediationResult)
async def mediate(body: AgentActionRequest):
    return await mediator.mediate(body)


@app.post("/api/v1/feedback")
async def feedback(body: UserFeedback):
    outcome = body.outcome
    if outcome is None:
        if body.accepted is True:
            outcome = "allow"
        elif body.accepted is False:
            outcome = "deny"
        else:
            outcome = "ask"
    high = body.scenario_category in (
        "financial_surface",
        "identity_or_finance",
        "secret_material",
        "make_payment",
    )
    await memory.record_feedback(
        category=body.scenario_category,
        accepted=outcome == "allow",
        high_risk=high,
    )
    await memory.record_scenario_feedback(
        task_type=body.task_type.value,
        action_type=body.action_type.value,
        sensitivity=body.sensitivity.value,
        outcome=outcome,
    )
    return {"ok": True, "recorded_under": body.scenario_category, "outcome": outcome}


@app.post("/api/v1/preferences/reset")
async def reset_prefs(body: PreferenceReset):
    await memory.reset(body.category)
    return {"ok": True, "cleared": body.category or "ALL"}


@app.get("/api/v1/trust/{category}")
async def trust_for_category(category: str):
    bias = await memory.trust_bias(category)
    return {"category": category, "bias": bias}


@app.get("/api/v1/audit")
async def audit(limit: int = 50):
    rows = await memory.list_audit(limit=limit)
    return {"items": rows}


class CapabilityVerifyBody(BaseModel):
    token: str


@app.post("/api/v1/capability/verify")
async def verify_capability_token(body: CapabilityVerifyBody):
    payload = verify_capability(body.token)
    return {"valid": payload is not None, "payload": payload}


@app.get("/")
async def root():
    return {
        "name": "SentinelOS",
        "docs": "/docs",
        "mediate": "POST /api/v1/mediate",
    }
