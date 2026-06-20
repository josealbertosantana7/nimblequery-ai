# NimbleQueryAI — AI Assistant for Student Pilots ✈️

A **multi-agent generative-AI assistant** for student pilots and aviation learners, built on
AWS Bedrock. A LangGraph **supervisor** routes each question to a domain **specialist agent**
— regulations, weather, live traffic, airports, or aerospace engineering — and each agent
gets its tools through a standard **MCP** (Model Context Protocol) tool layer. Domain
expertise comes from **RAG + domain prompts + tools** (no fine-tuning).

> ⚠️ **Safety:** This project is for **training and study only — not for operational use.**
> It is not an official weather briefer, dispatcher, or source of NOTAMs. Always verify with
> an FAA-authorized preflight briefing (1-800-WX-BRIEF), current charts, the aircraft POH, and
> your CFI. Every answer carries this disclaimer.

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11+-blue.svg">
  <img alt="FastAPI" src="https://img.shields.io/badge/api-FastAPI-009688.svg">
  <img alt="LangGraph" src="https://img.shields.io/badge/agents-LangGraph%20supervisor-1c3c3c.svg">
  <img alt="MCP" src="https://img.shields.io/badge/tools-MCP-7b3ff2.svg">
  <img alt="AWS Bedrock" src="https://img.shields.io/badge/LLM-AWS%20Bedrock-ff9900.svg">
</p>

---

## 🧠 Architecture

```
Streamlit UI ──HTTP──▶ FastAPI ──▶ Supervisor (router)
                                      │ classify → 1 specialist → answer + disclaimer
        ┌───────────────┬────────────┼─────────────┬───────────────┐
        ▼               ▼            ▼              ▼               ▼
      Regs           Weather      Tracking       Airport          Aero
   (FAR/AIM/KB)   (METAR/TAF)    (ADS-B)      (info/NOTAM)   (perf calculators)
        └───────────────┴──────┬─────┴──────────────┘ │
                               ▼                       ▼
                      MCP aviation-tools server   local calculators + RAG (aviation_kb)
```

- **Supervisor** (`app/agents/supervisor.py`) — an LLM router (structured output) picks the
  single best specialist (single-hop), which answers; a safety disclaimer is appended.
- **Specialists** (`app/agents/specialists/`) — each a LangGraph ReAct agent with a domain
  prompt + tools; individually toggleable via config.
- **MCP tool layer** (`app/mcp/server.py`) — the aviation data tools are exposed as an MCP
  server and consumed by the agents via `langchain-mcp-adapters`, with automatic fallback to
  in-process tools if the server is down.
- **Knowledge base** — FAA PDFs embedded once into a persistent Chroma `aviation_kb`
  collection; the Regs and Aero agents retrieve from it.

## 🛰️ Specialist agents & data sources

| Agent | Answers | Data source (attribution) |
|-------|---------|---------------------------|
| **Regs & Knowledge** | FARs, AIM, airman knowledge | [eCFR API](https://www.ecfr.gov) (Title 14) + FAA handbooks (RAG) |
| **Weather** | METAR / TAF / winds | [aviationweather.gov](https://aviationweather.gov) (NOAA AWC), [Windy](https://api.windy.com) |
| **Flight Tracking** | live ADS-B traffic | [OpenSky Network](https://opensky-network.org) |
| **Airport & Planning** | airport info, NOTAMs | [OurAirports](https://ourairports.com), [FAA NOTAM API](https://api.faa.gov) |
| **Aerospace Engineering** | aerodynamics, performance, W&B | local calculators + KB |

> **Note:** FlightRadar24 is intentionally *not* used — it has no free/open developer API and
> scraping violates its ToS. OpenSky provides equivalent ADS-B data under usable terms.

## 🧰 Tech stack
FastAPI · Streamlit · LangGraph + LangChain · AWS Bedrock (Claude + Titan) · Chroma ·
MCP (`mcp`, `langchain-mcp-adapters`) · httpx · pydantic-settings.

## 📁 Project structure
```
app/
├── agents/
│   ├── supervisor.py          # router graph + run_supervisor
│   ├── prompts.py             # domain prompts + SAFETY preamble
│   ├── common.py, state.py
│   └── specialists/           # regs, weather, tracking, airport, aero_eng
├── tools/
│   ├── general_tools.py       # safe calculator + web search
│   ├── mcp_loader.py          # load aviation tools via MCP (local fallback)
│   └── aviation/              # weather, tracking, airports, faa, calculators
├── mcp/server.py              # aviation-tools MCP server (FastMCP)
├── services/rag_engine/       # loader, embedder, vector_store, retriever, rag_llm
├── core/config.py             # central pydantic-settings
└── api/endpoints.py
frontend/streamlit_app.py
scripts/ingest_aviation_docs.py
tests/                         # calculators, tools (mocked), routing, mcp loader
hyperLime/                     # separate Bedrock AgentCore + MCP agent
```

## 🚀 Getting started

### 1. Install
```bash
git clone https://github.com/josealbertosantana7/nimblequery-ai.git
cd nimblequery-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # add -r requirements-dev.txt for tests
```

### 2. Configure
```bash
cp .env.example .env        # then add your AWS + (optional) Windy / FAA NOTAM keys
```
You need AWS **Bedrock** access (Claude + Titan). aviationweather.gov, OpenSky, eCFR and
OurAirports need **no key**; Windy and FAA NOTAMs are optional (those tools self-disable
gracefully without keys).

### 3. Run (three processes)
```bash
# 1) MCP tool server
python -m app.mcp.server                       # http://localhost:9000/mcp

# 2) API
uvicorn app.main:app --reload --port 8000      # http://localhost:8000/docs

# 3) UI  (PYTHONPATH so `app` is importable)
PYTHONPATH=. streamlit run frontend/streamlit_app.py
```
Set `USE_MCP_TOOLS=false` to skip step 1 and run the tools in-process.

### 4. Load the aviation knowledge base (optional but recommended)
```bash
# Drop public-domain FAA PDFs (PHAK, Airplane Flying Handbook, AIM) into data/aviation_docs/
python -m scripts.ingest_aviation_docs
```

### 5. Test
```bash
pip install -r requirements-dev.txt
pytest tests/            # 19 tests; no AWS/network needed (HTTP is mocked)
```

## 🔧 Key configuration (`app/core/config.py` / `.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `AWS_REGION`, `BEDROCK_MODEL_ID` | us-east-1, Claude 3 Haiku | Bedrock |
| `USE_MCP_TOOLS` | `true` | serve aviation tools via MCP (else local) |
| `MCP_AVIATION_URL` | http://localhost:9000/mcp | MCP server endpoint |
| `ENABLE_*_AGENT` | `true` | toggle individual specialists |
| `WINDY_API_KEY`, `FAA_NOTAM_CLIENT_ID/SECRET` | — | optional data sources |
| `VECTOR_STORE` | `chroma` | `chroma` → `pgvector` (future) |

## 📡 API
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agent` | Ask the aviation assistant (routes to a specialist) |
| `POST` | `/rag/upload` · `/rag/ask` | Upload a PDF and ask grounded questions |
| `POST` | `/generate-audio` · `/generate-video` | Media generation |

## 🗺️ Roadmap
- [ ] Full thin client + async job queue + S3 storage (in progress on the infra track).
- [ ] `pgvector`/OpenSearch vector store; containerize (docker-compose) and deploy (ECS).
- [ ] Optional: multi-expert (Mixture-of-Agents) orchestration; expose the assistant over MCP.

## 🩹 Troubleshooting
- **`langchain-mcp-adapters`**: pinned to `~=0.1.0` — 0.2.x needs a newer `langchain-core` than
  the 0.3 line.
- **fastapi/starlette pip warning**: `mcp` pulls a newer starlette than FastAPI's metadata
  bound; it still imports and runs. For clean production images, run the API and the MCP server
  as separate services with separate dependency sets.

## 🌩️ `hyperLime/`
A separate Amazon Bedrock AgentCore + LangChain 1.0 + MCP agent scaffold (IAM-role auth). See
[`hyperLime/README.md`](hyperLime/README.md).

## 📝 License
To be determined — add a `LICENSE` file (e.g. MIT) before open-sourcing.

---
> ⚠️ Portfolio / learning project. For training and study only — not for real flight operations.
