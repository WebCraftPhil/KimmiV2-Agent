# Kimmi V2 – Autonomous Agent Platform

End-to-end scaffold for a locally hosted, OpenRouter-powered marketing agent. The repository includes:

- **Agent core** (`agent_core/`): orchestrator, memory, MCP registry, and the four-step content ideation chain documented in `AGENTS.md` & `CURSOR_RULES.md`.
- **API layer** (`api/`): FastAPI service exposing `/run_agent`, logging each turn under `data/logs/` and forwarding requests to OpenRouter.
- **MCP tooling** (`config/mcp_servers.json` + `agent_core/tools/`): stubbed servers and a working `custom_mcp_example` tool for local validation.
- **Web console** (`web/`): Next.js dashboard with chat UI, JSON viewers, and an API proxy for the backend.

Use this foundation to iterate toward a multi-agent SaaS workflow (think CronPost/LegalLeaflet style) while keeping everything JSON-typed and TikTok-native.

---

## 1. Prerequisites

- Python **3.11.x or 3.12.x**
- Node.js **18+** (Next.js 14 requirement)
- OpenRouter API key with access to `moonshotai/kimi-dev-72b:free` (or an alternate model)
- Optional: Docker / Docker Compose for containerized runs

---

## 2. Environment Configuration

1. Copy the backend env template and set secrets:

   ```bash
   cp config/openrouter.env.example .env
   ```

   | Variable | Description |
   | --- | --- |
   | `OPENROUTER_API_KEY` | **Required.** OpenRouter token used by the orchestrator. |
   | `OPENROUTER_BASE_URL` | Defaults to the v1 chat completions endpoint. |
   | `OPENROUTER_DEFAULT_MODEL` | Defaults to `moonshotai/kimi-dev-72b:free`. |
   | `OPENROUTER_REQUEST_TIMEOUT` | HTTP timeout in seconds (default `60`). |

2. (Frontend) Create `web/.env.local` if you need to override the backend URL:

   ```bash
   echo "AGENT_BASE_URL=http://localhost:8000" > web/.env.local
   ```

3. Optional overrides:
   - `LOG_LEVEL` to adjust API logging verbosity
   - Custom MCP servers via `config/mcp_servers.json`

> `.env`, `.env.*`, and runtime artifacts are gitignored. Templates remain tracked for reproducibility.

---

## 3. Backend Setup (FastAPI + Orchestrator)

```bash
python3.11 -m venv .venv  # or python3.12
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

- `app:app` exposes the FastAPI service defined in `api/server.py`.
- `/health` → `{ "status": "ok" }`.
- `/run_agent` accepts `{ "prompt": "Plan three TikTok ideas..." }` and returns structured JSON.
- Every turn is persisted to `data/logs/turn-*.json`; conversation history lives in `data/memory_store.json`.

### Structured content chain

Send a JSON payload that matches the Cursor chain contract to trigger the full summarize → ideas → hooks → performance pipeline implemented in `agent_core/chains/content_ideation.py`:

```bash
curl -X POST http://localhost:8000/run_agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "{\"niche\": \"Luxury skincare\", \"trendSource\": \"GlowTok\", \"notes\": \"Highlight enzyme masks\", \"style\": \"AIDA\", \"platform\": \"TikTok\"}"
  }'
```

The orchestrator validates JSON, retries failures, and records MCP tool calls.

---

## 4. Frontend Setup (Next.js Console)

```bash
cd web
npm install
npm run dev
```

- Dev server runs at `http://localhost:3000`.
- `/pages/api/agent.ts` proxies requests to the backend; adjust `AGENT_BASE_URL` if needed.
- `/pages/index.tsx` provides a split-view chat UI with JSON inspectors powered by `@textea/json-viewer`.
- Global styles live in `web/styles/globals.css`; swap with Tailwind or custom design systems as desired.

---

## 5. MCP Tooling

- `config/mcp_servers.json` enumerates available tools.
- `agent_core/tools/custom_mcp_example/server.py` implements `custom_example_status` for smoke testing.
- Stub directories `notion_mcp`, `tiktok_mcp`, and `ideogram_mcp` include README placeholders—drop real MCP servers here and update the registry.

> When you promote a tool from stub to production, log it in `WORKLOG.md` and document the contract in `AGENTS.md` per the playbook.

---

## 6. Observability & Data

- `data/logs/` retains JSON transcripts of each turn (ignored in Git except for `.gitkeep`).
- `data/sessions/` reserved for future per-session persistence.
- `agent_core/logging.py` centralizes log serialization—extend it to push to Supabase, Notion, Analytics, etc.

---

## 7. Docker & Compose

```bash
docker compose up --build
# Debug variant with debugpy attached to :5678
docker compose -f compose.debug.yaml up --build
```

Images run `gunicorn` against `app:app` with the same environment variables described above.

---

## 8. Scripts & Utilities

- `scripts/test_openrouter.py` – prompt a model, optionally override system prompt/model flags.
- `scripts/openrouter_smoke.py` – lightweight CLI harness for manual checks.
- `agent_core/chains/content_ideation.py` – Cursor rule-compliant content pipeline ready for reuse in other services/tests.

---

## 9. Project Layout

```
kimmi-v2/
├── agent_core/           # orchestrator, memory, registry, chains, MCP stubs
├── api/                  # FastAPI server + OpenRouter client
├── config/               # MCP registry + env templates
├── data/                 # persisted memory + logs (runtime artifacts gitignored)
├── scripts/              # CLI utilities for model smoke tests
├── web/                  # Next.js console
├── AGENTS.md             # Agent roles, prompt rules, chaining order
├── CURSOR_RULES.md       # Cursor-specific prompting guidelines
├── PROJECTOVERVIEW.md    # Architecture blueprint & roadmap
├── WORKLOG.md            # Change log with decisions and open issues
└── requirements.txt
```

---

## 10. Next Steps

- Flesh out real MCP adapters (Notion, TikTok, Ideogram) and register them.
- Add automated schema tests to guarantee JSON contracts per `CURSOR_RULES.md`.
- Expand the orchestrator for multi-agent workflows or streaming responses.
- Deploy to Render/Vercel/DO and integrate authentication + billing for SaaS progression.

Document every significant change in `WORKLOG.md` and keep prompts aligned with `AGENTS.md`. Happy building!
