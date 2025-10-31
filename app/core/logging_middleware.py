"""
Structured logging middleware with correlation IDs for request tracing.

This module provides middleware for adding correlation IDs to every request
and implementing structured JSON logging for better observability.
"""

import json
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to all requests for distributed tracing.
    
    The correlation ID is:
    1. Extracted from X-Correlation-ID header if present
    2. Generated if not present
    3. Added to response headers
    4. Added to all logs for the request
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Get or generate correlation ID
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4())
        )
        
        # Store in request state for access in route handlers
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        self._log_request_start(request, correlation_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request completion
            self._log_request_end(
                request, 
                response, 
                correlation_id, 
                duration
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_request_error(request, correlation_id, duration, e)
            raise

    def _log_request_start(self, request: Request, correlation_id: str):
        """Log structured request start information."""
        log_data = {
            "event": "request_start",
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        logger.info(json.dumps(log_data))

    def _log_request_end(
        self,
        request: Request,
        response: Response,
        correlation_id: str,
        duration: float
    ):
        """Log structured request completion information."""
        log_data = {
            "event": "request_complete",
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": request.client.host if request.client else None,
        }
        logger.info(json.dumps(log_data))

    def _log_request_error(
        self,
        request: Request,
        correlation_id: str,
        duration: float,
        error: Exception
    ):
        """Log structured request error information."""
        log_data = {
            "event": "request_error",
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "duration_ms": round(duration * 1000, 2),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "client_ip": request.client.host if request.client else None,
        }
        logger.error(json.dumps(log_data))


def get_correlation_id(request: Request) -> str:
    """
    Get the correlation ID for the current request.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The correlation ID string
    """
    return getattr(request.state, "correlation_id", "unknown")
