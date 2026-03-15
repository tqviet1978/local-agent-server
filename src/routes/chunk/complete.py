"""
/chunk/complete - Finalize chunked upload

Merges all received chunks into the target file.
Optionally runs a post-upload command (like unzip, restart, etc.)
"""

from flask import request
from auth import require_auth
from logger import log_request
from utils.path_utils import get_safe_path
from utils.response_utils import success_response, error_response
from utils.chunk_session import get_session, get_progress, merge_chunks
from utils.post_command_helper import execute_post_command
from config import get_repo_manager


def register(app):
    @app.route("/chunk/complete", methods=["POST"])
    @require_auth
    @log_request
    def chunk_complete():
        """
        Finalize a chunked upload.

        Body parameters:
            - session_id: str (required)
            - post_cmd: str (optional) - bash command to run after merge

        Returns:
            - path: str
            - size: int - final file size
            - post_cmd: object (if provided)
        """
        try:
            data = request.get_json()
            session_id = data["session_id"]
            post_cmd = data.get("post_cmd")

            # Check session exists
            session = get_session(session_id)
            if session is None:
                return error_response("Session not found or expired")

            # Check all chunks received
            progress = get_progress(session_id)
            if not progress["complete"]:
                return error_response(
                    f"Upload incomplete: {progress['received_chunks']}/{progress['total_chunks']} chunks. "
                    f"Missing: {progress['missing_chunks']}"
                )

            # Merge chunks
            success, err, file_size = merge_chunks(session_id)
            if not success:
                return error_response(f"Merge failed: {err}")

            response_data = {
                "session_id": session_id,
                "path": session["filename"],
                "repository": session["repo_code"],
                "size": file_size,
                "total_chunks": session["total_chunks"],
            }

            # Execute post command if provided
            if post_cmd:
                try:
                    repo_manager = get_repo_manager()
                    repo_path = get_safe_path(repo_manager, session["repo_code"], "")
                    post_result = execute_post_command(post_cmd, repo_path)
                    response_data["post_cmd"] = post_result
                except Exception as e:
                    response_data["post_cmd"] = {"error": str(e)}

            return success_response(response_data)

        except KeyError as e:
            return error_response(f"Missing required field: {e}")
        except Exception as e:
            return error_response(str(e))
