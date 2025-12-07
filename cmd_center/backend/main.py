"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .api import api_router
from .integrations import get_config
from .db import init_db

# Create FastAPI app
app = FastAPI(
    title="Command Center API",
    description="Sales & Project Management Command Center",
    version="1.0.0",
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


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    config = get_config()
    init_db()
    print(f"Command Center API starting on {config.api_host}:{config.api_port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("Command Center API shutting down")


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
