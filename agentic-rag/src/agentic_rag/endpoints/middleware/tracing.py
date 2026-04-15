# tracing.py
"""Request tracing middleware."""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class TracingMiddleware(BaseHTTPMiddleware):
    """Add tracing to all requests."""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Add to request state
        request.state.request_id = request_id
        request.state.start_time = start_time

        # Process request
        response = await call_next(request)

        # Add headers
        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Duration-MS"] = str(round(duration_ms, 2))

        return response
