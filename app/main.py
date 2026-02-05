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
    """Root endpoint with HTML documentation"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Honeypot Scam Detector API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; }
            .status { display: inline-block; padding: 5px 15px; background: #27ae60; color: white; border-radius: 5px; font-size: 14px; }
            .endpoint { background: #ecf0f1; padding: 15px; margin: 15px 0; border-left: 4px solid #3498db; border-radius: 4px; }
            code { background: #2c3e50; color: #ecf0f1; padding: 2px 6px; border-radius: 3px; font-size: 14px; }
            .example { background: #34495e; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; margin: 10px 0; }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; border-radius: 5px; margin: 10px 5px 10px 0; }
            .btn:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍯 Honeypot Scam Detector API</h1>
            <p><span class="status">✓ OPERATIONAL</span></p>
            
            <h2>📖 Quick Start</h2>
            <p>This API detects scam messages and extracts intelligence using heuristic pattern matching.</p>
            
            <a href="/honeypot/test" class="btn">🧪 Try Interactive Test Page</a>
            <a href="/docs" class="btn">📚 API Documentation</a>
            <a href="/health" class="btn">💚 Health Check</a>
            
            <h2>🔑 API Endpoint</h2>
            <div class="endpoint">
                <strong>POST</strong> <code>/honeypot/message</code>
                <p><strong>Headers:</strong> <code>x-api-key: test-api-key-123</code></p>
            </div>
            
            <h3>Example Request:</h3>
            <div class="example">
curl -X POST https://honeypot-scam-detector-h82t.onrender.com/honeypot/message \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: test-api-key-123" \\
  -d '{"conversation_id": "test-123", "message": "Your KYC is pending. Share OTP now!"}'
            </div>
            
            <h3>Example Response:</h3>
            <div class="example">
{
  "scam_detected": true,
  "engagement_metrics": { "turns": 2, "duration_seconds": 0 },
  "intelligence": {
    "upi_ids": [],
    "bank_accounts": [],
    "urls": [],
    "phones": []
  },
  "reply": "I see. Can you tell me more about this?"
}
            </div>
            
            <h2>🔐 Authentication</h2>
            <p>Use API key: <code>test-api-key-123</code> in the <code>x-api-key</code> header.</p>
            
            <h2>📊 Features</h2>
            <ul>
                <li>✓ Heuristic-based scam detection</li>
                <li>✓ Autonomous agent responses</li>
                <li>✓ Intelligence extraction (UPI, bank accounts, URLs, phones)</li>
                <li>✓ Conversation memory with Redis</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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
