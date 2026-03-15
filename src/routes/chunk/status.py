"""
/chunk/status - Check upload progress or cancel a session

Useful for resuming interrupted uploads — the client can
check which chunks were already received and only resend
the missing ones.
"""

from flask import request
from auth import require_auth
from logger import log_request
from utils.response_utils import success_response, error_response
from utils.chunk_session import get_session, get_progress, cancel_session


def register(app):
    @app.route("/chunk/status", methods=["POST"])
    @require_auth
    @log_request
    def chunk_status():
        """
        Check upload session status or cancel it.

        Body parameters:
            - session_id: str (required)
            - action: str (optional) - "cancel" to abort the session

        Returns progress info or cancellation confirmation.
        """
        try:
            data = request.get_json()
            session_id = data["session_id"]
            action = data.get("action")

            if action == "cancel":
                cancel_session(session_id)
                return success_response({
                    "session_id": session_id,
                    "cancelled": True,
                })

            session = get_session(session_id)
            if session is None:
                return error_response("Session not found or expired")

            progress = get_progress(session_id)

            return success_response({
                "session_id": session_id,
                "filename": session["filename"],
                "repository": session["repo_code"],
                "total_size": session["total_size"],
                "total_chunks": progress["total_chunks"],
                "received_chunks": progress["received_chunks"],
                "missing_chunks": progress["missing_chunks"],
                "percent": progress["percent"],
                "complete": progress["complete"],
            })

        except KeyError as e:
            return error_response(f"Missing required field: {e}")
        except Exception as e:
            return error_response(str(e))
