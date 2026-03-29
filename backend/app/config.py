from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_path: str = "sentinelos.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    trust_decay_half_life_hours: float = 168.0  # 1 week
    max_memory_entries: int = 500
    # HMAC for capability tokens — set SENTINEL_TOKEN_SECRET in production
    token_secret: str = "sentinelos-dev-cap-secret-change-me"
    # Real file/exec hooks stay under this directory (see native path checks)
    sandbox_root: str = str(
        Path(__file__).resolve().parent.parent.parent / "sandbox_workspace"
    )
    exec_timeout_sec: int = 8
    enable_namespace_exec: bool = False
    enable_container_exec: bool = True
    container_image: str = "alpine:3.20"
    forgetting_lambda_per_hour: float = 0.015

    class Config:
        env_prefix = "SENTINEL_"


settings = Settings()
