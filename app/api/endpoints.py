import asyncio
import os
import tempfile
import uuid

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from app.services.llm_services import generate_text_async
from app.models.schemas import GenerateRequest, GenerateResponse
from app.tools.media_tools import speak_text, create_video_with_audio
from app.agents.supervisor import run_supervisor
from app.services.rag_engine.loader import load_and_split
from app.services.rag_engine.retriever import add_documents
from app.services.rag_engine.rag_llm import run_rag_agent

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(payload: GenerateRequest):
    result = await generate_text_async(payload.prompt)
    return {"output": result}

# app/api/endpoints.py


class MediaRequest(BaseModel):
    text: str

@router.post("/generate-audio")
def generate_audio(request: MediaRequest):
    audio_path = speak_text(request.text)
    return {"audio_path": audio_path}

@router.post("/generate-video")
def generate_video(request: MediaRequest):
    audio_path = speak_text(request.text)
    video_path = create_video_with_audio(request.text, audio_path)
    return {"video_path": video_path}

@router.post("/agent", response_model=GenerateResponse)
async def agent_endpoint(payload: GenerateRequest):
    # The supervisor graph is synchronous (LangGraph .invoke); run it off the event loop.
    result = await asyncio.to_thread(run_supervisor, payload.prompt)
    return {"output": result}


# --- Retrieval-Augmented Generation over an uploaded PDF ---

class RagAskRequest(BaseModel):
    doc_id: str
    question: str


@router.post("/rag/upload")
async def rag_upload(file: UploadFile = File(...)):
    """Chunk + embed a PDF once; return a doc_id to ask questions against."""
    doc_id = uuid.uuid4().hex
    data = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        chunks = await asyncio.to_thread(load_and_split, tmp_path)
        n_chunks = await asyncio.to_thread(add_documents, doc_id, chunks)
    finally:
        os.remove(tmp_path)
    return {"doc_id": doc_id, "n_chunks": n_chunks}


@router.post("/rag/ask")
async def rag_ask(payload: RagAskRequest):
    answer = await asyncio.to_thread(run_rag_agent, payload.doc_id, payload.question)
    return {"answer": answer}

