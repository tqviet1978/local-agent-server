"""
/chunk/download - Download a specific chunk of a file

Reads a slice of the file at the given offset and returns
it as base64-encoded data. Each request is small and fast,
working well through cloudflared tunnels.
"""

from flask import request
from auth import require_auth
from logger import log_request
from utils.path_utils import get_safe_path
from utils.response_utils import success_response, error_response
from utils.chunk_session import DEFAULT_CHUNK_SIZE
from config import get_repo_manager
import base64


def register(app):
    @app.route("/chunk/download", methods=["POST"])
    @require_auth
    @log_request
    def chunk_download():
        """
        Download a specific chunk of a file.

        Body parameters:
            - repository: str (required)
            - path: str (required)
            - chunk_index: int (required) - 0-based
            - chunk_size: int (optional, default 5MB)

        Returns:
            - content: str (base64-encoded chunk data)
            - chunk_index: int
            - chunk_size: int (actual bytes in this chunk)
            - total_chunks: int
            - is_last: bool
        """
        try:
            data = request.get_json()
            repo_code = data["repository"]
            file_path = data["path"]
            chunk_index = data["chunk_index"]
            chunk_size = data.get("chunk_size", DEFAULT_CHUNK_SIZE)

            repo_manager = get_repo_manager()
            real_path = get_safe_path(repo_manager, repo_code, file_path)

            if not real_path.exists():
                return error_response(f"File not found: {file_path}", 404)
            if not real_path.is_file():
                return error_response(f"Not a file: {file_path}", 400)

            file_size = real_path.stat().st_size
            total_chunks = (file_size + chunk_size - 1) // chunk_size if file_size > 0 else 1

            if chunk_index < 0 or chunk_index >= total_chunks:
                return error_response(
                    f"Invalid chunk_index: {chunk_index}, valid range: 0-{total_chunks - 1}"
                )

            offset = chunk_index * chunk_size
            read_size = min(chunk_size, file_size - offset)

            with open(real_path, "rb") as f:
                f.seek(offset)
                chunk_data = f.read(read_size)

            content_b64 = base64.b64encode(chunk_data).decode("ascii")

            return success_response({
                "path": file_path,
                "repository": repo_code,
                "content": content_b64,
                "encoding": "base64",
                "chunk_index": chunk_index,
                "chunk_size": len(chunk_data),
                "total_size": file_size,
                "total_chunks": total_chunks,
                "is_last": chunk_index == total_chunks - 1,
            })

        except KeyError as e:
            return error_response(f"Missing required field: {e}")
        except Exception as e:
            return error_response(str(e))
