"""
/chunk/init - Initialize a chunked upload session

Creates a session that tracks incoming chunks and merges
them into the final file when complete.
"""

from flask import request
from auth import require_auth
from logger import log_request
from utils.path_utils import get_safe_path
from utils.response_utils import success_response, error_response
from utils.chunk_session import create_session, DEFAULT_CHUNK_SIZE
from config import get_repo_manager


def register(app):
    @app.route("/chunk/init", methods=["POST"])
    @require_auth
    @log_request
    def chunk_init():
        """
        Initialize a chunked upload session.

        Body parameters:
            - repository: str (required)
            - path: str (required) - target file path in repository
            - total_size: int (required) - total file size in bytes
            - chunk_size: int (optional, default 5MB) - size per chunk
            - filename: str (optional) - original filename for reference

        Returns:
            - session_id: str - use this in subsequent chunk/upload calls
            - total_chunks: int - how many chunks the client should send
            - chunk_size: int - agreed chunk size
        """
        try:
            data = request.get_json()
            repo_code = data["repository"]
            path = data["path"]
            total_size = data["total_size"]
            chunk_size = data.get("chunk_size", DEFAULT_CHUNK_SIZE)
            filename = data.get("filename", path.split("/")[-1])

            if total_size <= 0:
                return error_response("total_size must be positive")
            if chunk_size <= 0:
                return error_response("chunk_size must be positive")

            # Calculate total chunks (ceiling division)
            total_chunks = (total_size + chunk_size - 1) // chunk_size

            # Validate target path
            repo_manager = get_repo_manager()
            target_path = get_safe_path(repo_manager, repo_code, path)

            session_id = create_session(
                filename=filename,
                total_size=total_size,
                total_chunks=total_chunks,
                target_path=target_path,
                repo_code=repo_code,
            )

            return success_response({
                "session_id": session_id,
                "total_chunks": total_chunks,
                "chunk_size": chunk_size,
                "total_size": total_size,
                "path": path,
                "repository": repo_code,
            })

        except KeyError as e:
            return error_response(f"Missing required field: {e}")
        except Exception as e:
            return error_response(str(e))
