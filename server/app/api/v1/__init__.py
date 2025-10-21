"""API v1 package."""
from fastapi import APIRouter
from .endpoints import file_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(file_router)

__all__ = ["api_router"]
