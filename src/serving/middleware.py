import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.common.logging_config import request_id_var

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID for correlation
        request_id = str(uuid.uuid4())
        
        # Set the context variable, which our RequestIdFilter uses
        token = request_id_var.set(request_id)
        
        try:
            response = await call_next(request)
            # Add the request ID to the HTTP response headers for the client
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Reset context var
            request_id_var.reset(token)
