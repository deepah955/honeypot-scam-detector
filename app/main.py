"""
FastAPI Application Entry Point
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import router, APIKeyMiddleware
from app.memory import get_memory_store

# Configure logging
def setup_logging():
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting Honeypot AI application...")
    
    # Initialize memory store on startup
    memory = await get_memory_store()
    if await memory.health_check():
        logger.info("Memory store initialized successfully")
    else:
        logger.warning("Memory store health check failed")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Honeypot AI application...")
    await memory.close()


# Create FastAPI application
app = FastAPI(
    title="Agentic Honey-Pot API",
    description="Scam Detection & Intelligence Extraction System",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(APIKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Agentic Honey-Pot API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    memory = await get_memory_store()
    memory_healthy = await memory.health_check()
    
    return {
        "status": "healthy" if memory_healthy else "degraded",
        "memory_store": "connected" if memory_healthy else "fallback"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
