--

# 🚀 Project Overview: “Kimmi V2 – Autonomous Agent Platform”

### 🧩 Project Goal

Create a **local or self-hosted AI agent environment** that:

* Uses **OpenRouter** for LLM calls (e.g. Kimi-K2, Mixtral, Claude, GPT-4-Turbo, etc.)
* Exposes **your own MCP servers** for tools (e.g. Notion sync, TikTok data, image generation, SEO scraping, etc.)
* Offers a **web-based UI** (built in Cursor using Next.js) where you can chat with your agent, inspect structured JSON output, and manage sessions.
* Can later be extended into a **multi-agent SaaS product** like CronPost or LegalLeaflet.

---

## 🧱 1. System Architecture Overview

```
kimmi-v2/
├── agent_core/
│   ├── orchestrator.py            # Manages agent reasoning loops
│   ├── memory.py                  # Handles short/long-term context
│   ├── registry.py                # Loads/communicates with MCP servers
│   ├── tools/
│   │   ├── notion_mcp/
│   │   ├── tiktok_mcp/
│   │   ├── ideogram_mcp/
│   │   └── custom_mcp_example/
│   └── schemas/                   # JSON schemas for agent outputs
│
├── api/
│   └── openrouter_api.py          # Wrapper for model calls
│
├── web/                           # Frontend (Cursor / Next.js)
│   ├── pages/
│   │   ├── index.tsx              # Chat UI
│   │   └── api/
│   │       └── agent.ts           # Calls orchestrator via HTTP
│   ├── components/
│   │   ├── ChatWindow.tsx
│   │   ├── JsonViewer.tsx
│   │   └── MemoryPanel.tsx
│   ├── styles/
│   └── tailwind.config.js
│
├── data/
│   ├── sessions/
│   ├── logs/
│   └── memory_store.json
│
├── .env
├── requirements.txt
└── README.md
```

---

## ⚙️ 2. Core Components Explained

### 🧠 **A. Agent Core (Backend Brain)**

This layer orchestrates reasoning and tool-use.

**Key files:**

* `orchestrator.py` → Routes user queries to the main model via OpenRouter, determines which MCP tool (if any) to call, handles loops and reasoning chains.
* `memory.py` → Stores conversation summaries, extracted facts, and references to external context (e.g. active campaign, product data, Notion doc links).
* `registry.py` → Discovers and connects to your MCP servers via standard protocol (usually WebSocket or HTTP).

Example pseudocode:

```python
from mcp_sdk import MCPRegistry
from openrouter_api import query_model

registry = MCPRegistry.load("config/mcp_servers.json")

def run_agent(prompt):
    context = load_memory()
    model_reply = query_model(prompt, context)
    if "tool_call" in model_reply:
        result = registry.call(model_reply["tool"], model_reply["args"])
        save_memory(result)
    return model_reply
```

---

### 🌐 **B. MCP Servers (Tool Layer)**

Each MCP server is a mini-service providing *one capability* to the agent.
Think of them as “plug-in brains”:

| MCP Server          | Purpose                        | Example Tasks                         |
| ------------------- | ------------------------------ | ------------------------------------- |
| **Notion MCP**      | Read/write to Notion databases | Sync content queues, pull blog drafts |
| **TikTok MCP**      | Fetch TikTok trend data        | Track hashtags, performance metrics   |
| **Ideogram MCP**    | Generate brand images          | Create social post graphics           |
| **SEO MCP**         | Analyze search trends          | Rank keywords, export reports         |
| **LocalMemory MCP** | Store custom data              | Notes, embeddings, metrics            |

Each server just exposes endpoints or sockets conforming to the **Model Context Protocol (MCP)**:

```json
{
  "tools": [
    {
      "name": "get_tiktok_trends",
      "description": "Fetch trending hashtags and sound IDs from TikTok",
      "input_schema": {"type": "object", "properties": {"category": {"type": "string"}}},
      "output_schema": {"type": "object", "properties": {"trend_list": {"type": "array"}}}
    }
  ]
}
```

✅ **No SDK strictly required** — but it helps.

You can:

* Write your own lightweight SDK for convenience (Python or JS)
* Or import **OpenAI’s official MCP SDKs** (`@modelcontextprotocol/sdk` in Node, `mcp` Python package)

These SDKs make it easier to register tools and maintain schemas, but aren’t mandatory — the protocol is just JSON + HTTP/WebSocket messages.

---

### 💬 **C. OpenRouter API Wrapper**

This module abstracts LLM calls so you can swap models easily.

```python
def query_model(prompt, context=None, model="moonshotai/kimi-dev-72b:free"):
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {"model": model, "messages": [
        {"role": "system", "content": "You are Kimmi V2, an autonomous marketing strategist."},
        {"role": "user", "content": prompt}
    ]}
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    return r.json()["choices"][0]["message"]["content"]
```

---

### 🖥️ **D. Frontend (Next.js / Cursor UI)**

This is where you interact with your agent — clean, lightweight, local-first.

**Key features:**

* Chat interface (user → Kimmi responses)
* JSON output viewer (for reports, plans, code)
* “Memory” sidebar showing what the agent currently knows
* Logs & progress bar for tool calls

You can start from a simple template:

```bash
npx create-next-app kimmi-ui
npm install tailwindcss react-json-view
```

Then in `/api/agent.ts`:

```ts
export default async function handler(req, res) {
  const { prompt } = req.body;
  const response = await fetch("http://localhost:8000/run_agent", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({prompt}),
  });
  const result = await response.json();
  res.status(200).json(result);
}
```

---

## 🔌 3. Integration Flow

1. **User enters prompt in the web UI.**
2. **Next.js API route** sends prompt to `orchestrator.py` backend.
3. **Backend queries OpenRouter**, receives reasoning output.
4. If the model requests a tool call → **MCP Registry** executes it.
5. Results returned → formatted → sent back to UI as JSON + Markdown.
6. Optional: memory updates saved to `memory_store.json` or Supabase.

---

## 🔐 4. Environment Setup

| Component    | Tech                                       | Purpose                     |
| ------------ | ------------------------------------------ | --------------------------- |
| Core Runtime | **Python 3.11+**                           | Backend agent orchestration |
| Frontend     | **Next.js 14 (TypeScript)**                | Chat UI                     |
| LLM Access   | **OpenRouter API**                         | Model gateway               |
| Tools        | **MCP servers (HTTP or WS)**               | Agent skills                |
| DB           | **Supabase / SQLite / JSON**               | Memory + Logs               |
| Hosting      | **Render / DigitalOcean / Vercel / Local** | Deployment                  |

---

## 🧰 5. Recommended SDKs / Libraries

| Function       | SDK / Library                                        |
| -------------- | ---------------------------------------------------- |
| OpenRouter API | `requests` (Python) / `axios` (JS)                   |
| MCP Support    | `mcp` (Python) or `@modelcontextprotocol/sdk` (Node) |
| Embeddings     | `sentence-transformers` / `text-embedding-3-large`   |
| Memory         | `chromadb` or `sqlite3`                              |
| Frontend       | `Next.js`, `Tailwind`, `react-json-view`             |
| Hosting        | `Docker`, `Vercel`, `Railway`, or `DO App Platform`  |

---

## 🧠 6. Agent Example Flow (Kimmi-style)

```
Phil: "Create a 48-hour TikTok launch plan for Stellar Edge Nutrition."

Kimmi V2:
 ├── calls ResearchAgent → uses TikTok MCP → gathers trend data
 ├── passes to CreativeAgent → generates 3 ad video ideas
 ├── BudgetAgent → estimates spend and ROAS
 ├── AnalyticsAgent → simulates metrics
 └── returns structured JSON + narrative summary
```

---

## 💵 7. Profit-First Upgrade Path

| Phase         | Focus                                    | Outcome                        |
| ------------- | ---------------------------------------- | ------------------------------ |
| **MVP (Now)** | Single-agent, JSON output via OpenRouter | Fully local Kimmi V2           |
| **Phase 2**   | Add Notion MCP + Supabase memory         | Persistent business assistant  |
| **Phase 3**   | Add auth, billing, and sharing           | Marketable SaaS platform       |
| **Phase 4**   | Deploy to Vercel + DigitalOcean          | “Ok Computer” personal console |

---

## ✅ 8. Immediate Action Plan

1. 🧱 Create a GitHub repo `kimmi-v2-openrouter`
2. ⚙️ Set up `.env` with `OPENROUTER_API_KEY`
3. 💬 Test your first call via `openrouter_api.py`
4. 🧠 Build simple `orchestrator.py` with memory + MCP placeholder
5. 💻 Scaffold the Next.js UI in Cursor
6. 🔌 Add one test MCP server (e.g., Notion read/write)
7. 🚀 Test end-to-end: prompt → model → MCP → JSON → UI
8. 🧾 Document each run (turn your tests into content for MoneyMaven.blog!)

---