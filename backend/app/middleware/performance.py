"""
Performance Tracking Middleware
Week 3 Day 3: Request/response timing and performance monitoring
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API request/response performance
    Logs request duration and adds performance headers
    """

    def __init__(self, app: ASGIApp, log_slow_requests: bool = True, slow_threshold: float = 1.0):
        """
        Initialize performance middleware

        Args:
            app: FastAPI application
            log_slow_requests: Whether to log slow requests
            slow_threshold: Threshold in seconds for slow request warnings
        """
        super().__init__(app)
        self.log_slow_requests = log_slow_requests
        self.slow_threshold = slow_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and measure performance
        """
        # Record start time
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error and re-raise
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[{duration:.3f}s] - Error: {str(e)}"
            )
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Add performance headers
        response.headers["X-Process-Time"] = f"{duration:.3f}s"
        response.headers["X-Timestamp"] = str(int(start_time))

        # Log request
        log_message = (
            f"{request.method} {request.url.path} "
            f"[{response.status_code}] "
            f"[{duration:.3f}s]"
        )

        # Log slow requests with warning level
        if self.log_slow_requests and duration > self.slow_threshold:
            logger.warning(f"⚠️ SLOW REQUEST: {log_message}")
        else:
            logger.info(log_message)

        # Log additional details for slow requests
        if duration > self.slow_threshold:
            logger.debug(
                f"Slow request details - "
                f"Client: {request.client.host if request.client else 'unknown'}, "
                f"User-Agent: {request.headers.get('user-agent', 'unknown')}, "
                f"Query: {dict(request.query_params)}"
            )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log detailed request information
    """

    def __init__(self, app: ASGIApp, log_body: bool = False):
        """
        Initialize request logging middleware

        Args:
            app: FastAPI application
            log_body: Whether to log request body (careful with sensitive data!)
        """
        super().__init__(app)
        self.log_body = log_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request details
        """
        # Log request
        logger.info(
            f"📥 Incoming: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Log headers (excluding sensitive ones)
        sensitive_headers = {'authorization', 'cookie', 'x-api-key'}
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in sensitive_headers
        }
        logger.debug(f"Headers: {headers}")

        # Log query parameters
        if request.query_params:
            logger.debug(f"Query params: {dict(request.query_params)}")

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            f"📤 Response: {request.method} {request.url.path} "
            f"[{response.status_code}]"
        )

        return response


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and categorize errors
    """

    # Track error counts by type
    _error_counts = {
        "4xx": 0,
        "5xx": 0,
        "total": 0
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Track errors and categorize them
        """
        try:
            response = await call_next(request)

            # Track error responses
            if response.status_code >= 400:
                self._error_counts["total"] += 1

                if 400 <= response.status_code < 500:
                    self._error_counts["4xx"] += 1
                    logger.warning(
                        f"❌ Client error: {request.method} {request.url.path} "
                        f"[{response.status_code}]"
                    )
                elif response.status_code >= 500:
                    self._error_counts["5xx"] += 1
                    logger.error(
                        f"💥 Server error: {request.method} {request.url.path} "
                        f"[{response.status_code}]"
                    )

            return response

        except Exception as e:
            # Track unhandled exceptions
            self._error_counts["5xx"] += 1
            self._error_counts["total"] += 1
            logger.exception(
                f"💥 Unhandled exception: {request.method} {request.url.path} - {str(e)}"
            )
            raise

    @classmethod
    def get_error_stats(cls):
        """Get error statistics"""
        return cls._error_counts.copy()

    @classmethod
    def reset_error_stats(cls):
        """Reset error statistics"""
        cls._error_counts = {
            "4xx": 0,
            "5xx": 0,
            "total": 0
        }
