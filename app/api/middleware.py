"""
API Key Middleware for request authentication
"""

import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key in requests"""
    
    # Paths that don't require authentication
    EXCLUDED_PATHS = ["/", "/health", "/docs", "/openapi.json", "/redoc", "/honeypot/test"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("x-api-key")
        
        if not api_key:
            logger.warning(f"Missing API key for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API key. Provide x-api-key header."}
            )
        
        # Validate API key
        settings = get_settings()
        valid_keys = settings.api_keys_list
        
        # If no keys configured, allow all (development mode)
        if not valid_keys:
            logger.warning("No API keys configured - allowing all requests")
            return await call_next(request)
        
        if api_key not in valid_keys:
            logger.warning(f"Invalid API key attempt for {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key"}
            )
        
        # Valid key - proceed
        return await call_next(request)
