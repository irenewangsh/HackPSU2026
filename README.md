# SentinelOS

*HackPSU 2026 submission.*

**Tagline:** *Between intention and impact, a quiet layer of care.*

**SentinelOS** is a FastAPI supervisory control plane that mediates OS-facing agent actions (files under a sandbox workspace, browser URLs, process launches) before anything hits the real filesystem or shell. For each action it computes sensitivity and risk, suggests transforms, and returns a policy decision with permission scope. SQLite stores preference memory with decay, an append-only audit trail, authority timeline events, and reversible operation records. **Capability tokens** are HMAC scoped to policy digests so agents carry short-lived, verifiable permissions. A **native C shared library** (loaded via `ctypes`) handles path mediation, filesystem probes, hashing, capability guards, and sandboxed process primitives; Python paths remain as resilience fallback when native loading is unavailable. The React console exposes mediation, hooks, risk heatmap, timeline, audit, rollback, profile, and demo helpers against the same APIs.

---

## Features

- **Mediation API** — classify and constrain agent actions; progressive “trust envelope” signal.
- **SQLite persistence** — preferences with decay, audit log, authority timeline, reversible ops, user profile.
- **Hooks** — file (sandbox-relative), browser URL checks, and exec mediation; native code preferred, Python fallback.
- **Analytics** — heatmap-style risk buckets, native bridge health, timeline endpoints.
- **React console** — overview, mediation, hooks, heatmap, authority timeline, audit, rollback, profile, demo notes, Devpost copy.
- **Postman** — collection under `postman/SentinelOS.postman_collection.json`.

---

## Stack

| Layer | Technology |
|--------|------------|
| API | Python 3.11+, FastAPI, Pydantic |
| DB | SQLite (`aiosqlite`), file default `sentinelos.db` next to the backend working directory |
| Native | C11 (`sentinel_policy.c`, `sentinel_fs.c`, `sentinel_exec.c`) → `libsentinel.dylib` / `libsentinel.so` |
| UI | React 18, TypeScript, Vite, Tailwind CSS, Framer Motion |

---

## Repository layout

```
sentinelos/
├── backend/           # FastAPI app (`app/main.py`)
├── frontend/          # Vite + React SPA
├── native/            # Makefile builds shared library for ctypes
├── postman/           # HTTP collection
├── sandbox_workspace/ # Demo paths for file/exec hooks (keep payloads here)
└── README.md
```

---

## Prerequisites

- **Python 3.11+** (virtual environment recommended)
- **Node.js 18+** and npm
- **C compiler** (`cc`) if you build the native library (macOS or Linux)
- Optional: **Postman** or any HTTP client

---

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Interactive docs: **http://127.0.0.1:8000/docs**
- Health: **GET** `http://127.0.0.1:8000/health`

On first run, SQLite tables are created automatically (default DB name: `sentinelos.db`).  
To use a custom path:

```bash
export SENTINEL_DATABASE_PATH=/path/to/sentinelos.db
```

### 2. Native library (optional, recommended)

```bash
cd native
make
```

The backend loads the library via `ctypes` when present; otherwise hooks fall back to Python implementations.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open **http://127.0.0.1:5173/** for the opening scroll page; the console lives under **/dashboard** and related routes.  
API calls are proxied to **http://127.0.0.1:8000** (see `frontend/vite.config.ts`).

---

## Configuration (environment)

Optional overrides use the **`SENTINEL_`** prefix (see `backend/app/config.py`):

| Variable | Purpose |
|----------|---------|
| `SENTINEL_DATABASE_PATH` | SQLite file path (default `sentinelos.db`) |
| `SENTINEL_CORS_ORIGINS` | Allowed origins (list; format depends on your pydantic-settings / env parser) |
| `SENTINEL_TOKEN_SECRET` | HMAC secret for capability tokens (**change in production**) |
| `SENTINEL_SANDBOX_ROOT` | Root directory for mediated file/exec hooks |
| `SENTINEL_EXEC_TIMEOUT_SEC` | Exec hook timeout (seconds) |
| `SENTINEL_ENABLE_CONTAINER_EXEC` | Prefer Docker-isolated exec hook path when available |
| `SENTINEL_ENABLE_NAMESPACE_EXEC` | Enable Linux namespace exec path (`unshare`) |
| `SENTINEL_TRUST_DECAY_HALF_LIFE_HOURS` | Preference decay half-life |
| `SENTINEL_MAX_MEMORY_ENTRIES` | Cap on stored memory rows |
| `SENTINEL_FORGETTING_LAMBDA_PER_HOUR` | Profile forgetting rate (per hour) |

---

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service and layer checklist |
| POST | `/api/v1/mediate` | Main mediation |
| POST | `/api/v1/feedback` | Record user feedback / category weight |
| POST | `/api/v1/preferences/reset` | Reset preference memory |
| GET | `/api/v1/trust/{category}` | Trust bias for a category |
| GET | `/api/v1/audit` | Recent audit entries |
| POST | `/api/v1/capability/verify` | Verify a capability token |

Additional routes: **analytics**, **hooks**, **operations** (rollback), **profile** — see `backend/app/routers/` and `/docs`.

---

## Development notes

- **CORS** is preconfigured for the Vite dev server (`localhost` / `127.0.0.1` on port 5173).
- **Sandbox**: keep demo files under `sandbox_workspace/` so path policy hooks behave as expected.
- **Git**: `backend/*.db` and `backend/.venv/` are ignored; each developer keeps a local database.

---

## License

[MIT](LICENSE)
