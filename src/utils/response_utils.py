"""
Enhanced response format utilities with BACKWARD COMPATIBILITY
"""

from flask import jsonify, g
from datetime import datetime
import time


def success_response(data=None, message=None):
    """
    Return standardized success response (BACKWARD COMPATIBLE)
    
    Args:
        data: Response data (dict or any serializable type)
        message: Optional success message
    
    Returns:
        Flask JSON response
    
    Behavior:
        - If data is dict: spreads keys into root (backward compatible)
        - If data is non-dict: wraps in {"result": value}
        - Adds metadata if available
    """
    response = {"success": True}
    
    # BACKWARD COMPATIBLE: Spread dict into root
    if data is not None:
        if isinstance(data, dict):
            response.update(data)  # Spread into root (OLD BEHAVIOR)
        else:
            response["result"] = data  # Non-dict values
    
    if message:
        response["message"] = message
    
    # Add metadata if available (set by middleware)
    if hasattr(g, 'request_metadata'):
        response["metadata"] = g.request_metadata
    
    return jsonify(response)


def success_response_wrapped(data=None, message=None):
    """
    Return success response with data wrapped (NEW STYLE)
    
    Use this for new APIs that want structured responses
    """
    response = {"success": True}
    
    if data is not None:
        response["data"] = data
    
    if message:
        response["message"] = message
    
    if hasattr(g, 'request_metadata'):
        response["metadata"] = g.request_metadata
    
    return jsonify(response)


def error_response(error, status_code=400):
    """
    Return standardized error response
    
    Args:
        error: Error object (ErrorResponse, ErrorCode, Exception, or string)
        status_code: HTTP status code (default: 400)
    
    Returns:
        Flask JSON response with error and status code
    """
    from utils.error_codes import ErrorResponse, ErrorCode
    
    response = {"success": False}
    
    # Handle different error types
    if isinstance(error, ErrorResponse):
        # Structured error response
        response["error"] = error.to_dict()
    elif isinstance(error, ErrorCode):
        # ErrorCode enum
        response["error"] = {
            "code": error.code,
            "type": error.name,
            "message": error.message
        }
    elif isinstance(error, dict):
        # Already a dict
        response["error"] = error
    else:
        # String or exception - keep it simple for backward compat
        response["error"] = str(error)
    
    # Add metadata if available
    if hasattr(g, 'request_metadata'):
        response["metadata"] = g.request_metadata
    
    return jsonify(response), status_code


def paginated_response(items, page=1, per_page=50, total=None):
    """
    Return paginated response
    
    Args:
        items: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items (if known)
    
    Returns:
        Flask JSON response with pagination info
    """
    if total is None:
        total = len(items)
    
    total_pages = (total + per_page - 1) // per_page
    
    data = {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
    
    return success_response(data)


def dry_run_response(changes_preview, message=None):
    """
    Return dry-run preview response
    
    Args:
        changes_preview: Dictionary describing what would change
        message: Optional message
    
    Returns:
        Flask JSON response
    """
    response = {
        "success": True,
        "dry_run": True,
        "preview": changes_preview
    }
    
    if message:
        response["message"] = message
    
    if hasattr(g, 'request_metadata'):
        response["metadata"] = g.request_metadata
    
    return jsonify(response)


def streaming_response(generator, mimetype='text/event-stream'):
    """
    Return streaming response for Server-Sent Events
    
    Args:
        generator: Generator function yielding data
        mimetype: MIME type (default: text/event-stream)
    
    Returns:
        Flask streaming response
    """
    from flask import Response
    
    def generate():
        """Wrapper to add SSE formatting"""
        for data in generator:
            if isinstance(data, dict):
                import json
                yield f"data: {json.dumps(data)}\n\n"
            else:
                yield f"data: {data}\n\n"
    
    return Response(generate(), mimetype=mimetype)


# Helper functions for common response patterns
def created_response(resource_data, resource_name="Resource"):
    """Response for successful resource creation"""
    return success_response(
        data=resource_data,
        message=f"{resource_name} created successfully"
    )


def updated_response(resource_data, resource_name="Resource"):
    """Response for successful resource update"""
    return success_response(
        data=resource_data,
        message=f"{resource_name} updated successfully"
    )


def deleted_response(resource_id=None, resource_name="Resource"):
    """Response for successful resource deletion"""
    data = {"deleted": True}
    if resource_id:
        data["id"] = resource_id
    
    return success_response(
        data=data,
        message=f"{resource_name} deleted successfully"
    )


def no_content_response():
    """Response for successful operation with no content"""
    from flask import make_response
    response = make_response('', 204)
    return response
