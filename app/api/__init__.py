# app/api/__init__.py

from fastapi import APIRouter
from .endpoints import router as media_router

router = APIRouter()
router.include_router(media_router)
