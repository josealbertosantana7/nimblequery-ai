# NimbleQueryAI — Scalable GenAI Service

A modular, **agentic generative-AI service** built around AWS Bedrock. It exposes a
tool-using chat agent, retrieval-augmented Q&A over your own PDFs, and media generation
(image / text-to-speech / video) behind a clean **FastAPI** backend, with a **Streamlit**
front end.

The project is deliberately structured so that every heavy or stateful component
(vector store, object storage, image backend, job queue) is **swappable by configuration** —
the same code runs on a laptop with local defaults and scales out to managed AWS services in
production.

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11-blue.svg">
  <img alt="FastAPI" src="https://img.shields.io/badge/api-FastAPI-009688.svg">
  <img alt="LangChain" src="https://img.shields.io/badge/agents-LangGraph-1c3c3c.svg">
  <img alt="AWS Bedrock" src="https://img.shields.io/badge/LLM-AWS%20Bedrock-ff9900.svg">
  <img alt="Status" src="https://img.shields.io/badge/status-active%20development-yellow.svg">
</p>

---

## ✨ Features

- **🤖 Tool-using agent** — a LangGraph ReAct agent (Claude on Bedrock) with web search
  (Serper), a safe arithmetic evaluator, and a reasoning tool.
- **📄 RAG over PDFs** — upload a PDF once; it is chunked, embedded (Bedrock Titan) and
  persisted in a vector store. Ask many questions without re-embedding.
- **🎨 Image generation** — text-to-image (Stable Diffusion locally; Bedrock image models in
  production).
- **🔊 Audio & video** — text-to-speech (gTTS) and simple captioned video generation.
- **⚙️ Config-driven backends** — pick your vector store, image backend, storage and job
  store via environment variables; no code changes to scale.

## 🏗️ Architecture

```
Streamlit front end  ──HTTP/JSON──▶  FastAPI service
                                     ├─ /agent           chat + tools
                                     ├─ /generate        plain LLM completion
                                     ├─ /rag/upload       chunk + embed (once)  ─┐
                                     ├─ /rag/ask          retrieve + answer      │
                                     ├─ /generate-audio                          │
                                     └─ /generate-video                          │
                                          │              │                       ▼
                                          ▼              ▼              ┌───────────────────┐
                                   AWS Bedrock     Object storage       │  Vector store     │
                                   (Claude/Titan)  (local → S3)         │  Chroma → pgvector │
                                                                        └───────────────────┘
```

**Design principles**

1. **Swappable backends via one config layer** (`app/core/config.py`) —
   `VECTOR_STORE`, `IMAGE_BACKEND`, `STORAGE_BACKEND`, `JOB_STORE`.
2. **Stateless API** — state lives in external stores (vector DB / object storage), so the
   service can scale horizontally behind a load balancer.
3. **Runs locally today, production-ready by config** — local defaults need no cloud
   resources; managed AWS services are a configuration swap (see the [roadmap](#-roadmap)).

## 🧰 Tech stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI, Uvicorn, Pydantic |
| Agents | LangGraph, LangChain, `langchain-aws` |
| LLM / embeddings | AWS Bedrock (Claude, Titan) |
| RAG vector store | Chroma (dev) → pgvector / OpenSearch (prod) |
| Front end | Streamlit |
| Media | gTTS, MoviePy, Stable Diffusion (`diffusers`) |
| Config | `pydantic-settings` |

## 📁 Project structure

```
scalable_genai_service/
├── app/
│   ├── main.py                 # FastAPI app + middleware
│   ├── api/endpoints.py        # HTTP routes
│   ├── core/config.py          # central pydantic-settings config
│   ├── agents/langgraph_agent.py
│   ├── services/
│   │   ├── llm_services.py      # Bedrock chat interface
│   │   ├── image_gen.py
│   │   └── rag_engine/          # loader, embedder, vector_store, retriever, rag_llm
│   ├── tools/media_tools.py     # TTS + video
│   └── utils/logging.py
├── frontend/streamlit_app.py    # UI client
├── hyperLime/                   # Bedrock AgentCore + MCP agent (see below)
├── tests/
├── requirements.txt
└── .env.example
```

## 🚀 Getting started

### Prerequisites
- Python 3.11+
- An AWS account with **Amazon Bedrock** model access (Claude + Titan embeddings/image)
- A [Serper](https://serper.dev) API key (for the agent's web-search tool)

### 1. Install
```bash
git clone https://github.com/josealbertosantana7/nimblequery-ai.git
cd nimblequery-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# then edit .env with your credentials
```
> 🔐 **Never commit `.env`.** It is git-ignored. Prefer an IAM role / `aws configure` profile
> over long-lived access keys where possible.

### 3. Run (two processes)
```bash
# Terminal 1 — API
uvicorn app.main:app --reload --port 8000

# Terminal 2 — UI  (run from the project root so `app` is importable)
PYTHONPATH=. streamlit run frontend/streamlit_app.py
```
The UI is at http://localhost:8501 and the API docs at http://localhost:8000/docs.

## 🔧 Configuration

All settings live in `app/core/config.py` and are read from the environment / `.env`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `AWS_REGION` | `us-east-1` | Bedrock region |
| `BEDROCK_MODEL_ID` | Claude 3 Haiku | Chat / agent model |
| `BEDROCK_EMBED_MODEL_ID` | Titan v2 | Embeddings model |
| `SERPER_API_KEY` | — | Web-search tool |
| `VECTOR_STORE` | `chroma` | `chroma` \| `pgvector` |
| `IMAGE_BACKEND` | `bedrock` | `bedrock` \| `local` |
| `STORAGE_BACKEND` | `local` | `local` \| `s3` |
| `JOB_STORE` | `memory` | `memory` \| `redis` |

## 📡 API reference

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `POST` | `/agent` | `{prompt}` | Run the tool-using agent |
| `POST` | `/generate` | `{prompt}` | Plain LLM completion |
| `POST` | `/rag/upload` | PDF (multipart) | Chunk + embed; returns `doc_id` |
| `POST` | `/rag/ask` | `{doc_id, question}` | Grounded answer from the document |
| `POST` | `/generate-audio` | `{text}` | Text-to-speech |
| `POST` | `/generate-video` | `{text}` | Captioned video |

## 🗺️ Roadmap

This service is under active development toward a production-grade, horizontally-scalable
deployment. Planned / in-progress:

- [ ] **Thin client** — route chat & image generation entirely through the API.
- [ ] **Async job queue** — offload slow media/image work (`job_id` + `/jobs/{id}`),
      backed by Redis locally and SQS + workers in production.
- [ ] **Object storage** — generated media to S3 with presigned URLs.
- [ ] **Bedrock image generation** — GPU-free image models for scale.
- [ ] **pgvector / OpenSearch** vector store for high concurrency.
- [ ] **Containerization & deploy** — `docker-compose` for local; ECS Fargate behind an ALB,
      with autoscaling, auth and rate limiting, in production.

## 🌩️ `hyperLime/` — Bedrock AgentCore sub-project

A separate, more modern agent scaffold built with **Amazon Bedrock AgentCore**, the
**LangChain 1.0** `create_agent` API, and **MCP** tool integration (uses IAM-role auth rather
than static keys). It is deployed independently via the `agentcore` CLI — see
[`hyperLime/README.md`](hyperLime/README.md).

## 📝 License

To be determined — add a `LICENSE` file (e.g. MIT) before open-sourcing.

---

> ⚠️ Portfolio / learning project. APIs and structure are evolving; see the roadmap for
> what is implemented vs planned.
