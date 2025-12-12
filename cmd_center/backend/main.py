"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .api import api_router
from .integrations import get_config
from .db import init_db
from .services.sync_scheduler import lifespan_manager

# Create FastAPI app
app = FastAPI(
    title="Command Center API",
    description="Sales & Project Management Command Center",
    version="1.0.0",
    lifespan=lifespan_manager,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


def main():
    """Run the FastAPI server."""
    config = get_config()
    uvicorn.run(
        "cmd_center.backend.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
