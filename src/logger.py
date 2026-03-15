"""Enhanced request logger with file output and detailed tracking"""

import logging
import time
import json
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from logging.handlers import RotatingFileHandler
from flask import request


# Create logs directory if not exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Setup main logger
logger = logging.getLogger("local_agent_server")
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler with rotation (max 10MB, keep 5 backup files)
file_handler = RotatingFileHandler(
    LOGS_DIR / "access.log", maxBytes=10 * 1024 * 1024, backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Error file handler
error_handler = RotatingFileHandler(
    LOGS_DIR / "error.log", maxBytes=10 * 1024 * 1024, backupCount=5
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)


def sanitize_payload(data):
    """Remove sensitive information from payload"""
    if not isinstance(data, dict):
        return data

    sanitized = data.copy()

    # List of sensitive keys to mask
    sensitive_keys = ["password", "token", "auth_token", "secret", "api_key"]

    for key in sensitive_keys:
        if key in sanitized:
            sanitized[key] = "***HIDDEN***"

    return sanitized


def log_request(f):
    """Log API requests with detailed information"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        method = request.method
        endpoint = request.path
        ip = request.remote_addr

        # Get repository and payload from request body
        repo = "N/A"
        payload = None
        try:
            if request.is_json:
                data = request.get_json()
                repo = data.get("repository", "N/A")
                payload = sanitize_payload(data)
        except:
            pass

        # Execute request
        try:
            response = f(*args, **kwargs)
            error = None
        except Exception as e:
            # Log exception
            error = e
            response = ({"success": False, "error": str(e)}, 500)
            logger.error(
                f"{method} {endpoint} | repo={repo} | EXCEPTION: {str(e)}\n{traceback.format_exc()}"
            )

        # Calculate execution time
        duration_ms = int((time.time() - start_time) * 1000)

        # Get status code
        if isinstance(response, tuple):
            status = response[1]
        else:
            status = 200

        # Prepare log message
        payload_str = ""
        if payload:
            # Truncate long payloads
            payload_json = json.dumps(payload, ensure_ascii=False)
            if len(payload_json) > 200:
                payload_json = payload_json[:200] + "..."
            payload_str = f" | payload={payload_json}"

        log_message = (
            f"{method} {endpoint} | repo={repo} | status={status} | "
            f"{duration_ms}ms | ip={ip}{payload_str}"
        )

        # Log with appropriate level
        if status >= 500:
            logger.error(log_message)
        elif status >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # If there was an error, re-raise it
        if error:
            raise error

        return response

    return decorated_function
