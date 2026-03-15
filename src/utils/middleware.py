"""
Middleware to add metadata to all API responses
"""

from flask import g, request
from datetime import datetime
import time
import uuid


class MetadataMiddleware:
    """
    Middleware to add execution metadata to all API responses
    
    Adds:
    - Request ID for tracking
    - Execution time
    - Timestamp
    - Server version
    - Request method and path
    """
    
    def __init__(self, app, version="2.0.0"):
        self.app = app
        self.version = version
        
        # Register before/after request handlers
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Called before each request - start timing"""
        g.request_start_time = time.time()
        g.request_id = str(uuid.uuid4())[:8]  # Short request ID
        
        # Store initial metadata
        g.request_metadata = {
            "request_id": g.request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def after_request(self, response):
        """Called after each request - add metadata"""
        # Skip if no start time (shouldn't happen but be safe)
        if not hasattr(g, 'request_start_time'):
            return response
        
        # Calculate execution time
        execution_time = time.time() - g.request_start_time
        execution_time_ms = int(execution_time * 1000)
        
        # Update metadata
        if hasattr(g, 'request_metadata'):
            g.request_metadata.update({
                "execution_time_ms": execution_time_ms,
                "server_version": self.version
            })
            
            # Add request info for debugging (optional, can be disabled)
            if self.app.debug:
                g.request_metadata.update({
                    "request_method": request.method,
                    "request_path": request.path
                })
        
        # Add custom headers
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Execution-Time-Ms'] = str(execution_time_ms)
        
        return response


def init_metadata_middleware(app, version="2.0.0"):
    """
    Initialize metadata middleware
    
    Args:
        app: Flask application instance
        version: Server version string
    
    Returns:
        MetadataMiddleware instance
    """
    return MetadataMiddleware(app, version)


# Rate limiting placeholder (future implementation)
class RateLimitMiddleware:
    """
    Placeholder for rate limiting middleware
    
    Future implementation will add:
    - X-RateLimit-Limit
    - X-RateLimit-Remaining
    - X-RateLimit-Reset headers
    """
    
    def __init__(self, app, limit=100, per=3600):
        """
        Args:
            app: Flask application
            limit: Number of requests allowed
            per: Time window in seconds
        """
        self.app = app
        self.limit = limit
        self.per = per
        # TODO: Implement actual rate limiting logic
    
    def check_rate_limit(self, identifier):
        """Check if request should be rate limited"""
        # Placeholder - always allow for now
        return True


def init_middleware(app, version="2.0.0"):
    """
    Initialize all middleware
    
    Args:
        app: Flask application instance
        version: Server version string
    
    Returns:
        Dictionary of initialized middleware
    """
    middleware = {
        'metadata': init_metadata_middleware(app, version)
    }
    
    return middleware
