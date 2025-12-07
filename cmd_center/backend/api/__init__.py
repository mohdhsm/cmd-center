"""FastAPI route handlers."""

from fastapi import APIRouter
from . import health, dashboard, aramco, commercial, owners, deals, emails

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(aramco.router, prefix="/aramco", tags=["aramco"])
api_router.include_router(commercial.router, prefix="/commercial", tags=["commercial"])
api_router.include_router(owners.router, prefix="/owners", tags=["owners"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])

__all__ = ["api_router"]