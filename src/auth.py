"""Authentication decorator"""

from functools import wraps
from flask import request, jsonify
import json

# Load auth token from config
with open("config.json", "r") as f:
    CONFIG = json.load(f)
    AUTH_TOKEN = CONFIG["auth_token"]


def require_auth(f):
    """Require Bearer token authentication"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token or token != f"Bearer {AUTH_TOKEN}":
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return decorated_function
