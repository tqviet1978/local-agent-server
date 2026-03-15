"""
/chunk/upload - Upload a single chunk

Receives one chunk of a file as multipart form-data.
Each chunk is stored temporarily and merged when complete.
Idempotent: re-uploading the same chunk_index overwrites safely.
"""

from flask import request
from auth import require_auth
from logger import log_request
from utils.response_utils import success_response, error_response
from utils.chunk_session import save_chunk, get_progress


def register(app):
    @app.route("/chunk/upload", methods=["POST"])
    @require_auth
    @log_request
    def chunk_upload():
        """
        Upload a single chunk.

        Form fields:
            - session_id: str (required)
            - chunk_index: int (required) - 0-based index
            - file: binary (required) - chunk data

        Returns:
            - chunk_index: int
            - received_chunks: int
            - total_chunks: int
            - percent: float
        """
        try:
            session_id = request.form.get("session_id")
            chunk_index = request.form.get("chunk_index")

            if not session_id:
                return error_response("Missing required field: session_id")
            if chunk_index is None:
                return error_response("Missing required field: chunk_index")
            if "file" not in request.files:
                return error_response("Missing required field: file")

            chunk_index = int(chunk_index)
            uploaded = request.files["file"]
            chunk_data = uploaded.read()

            if len(chunk_data) == 0:
                return error_response("Empty chunk data")

            success, err = save_chunk(session_id, chunk_index, chunk_data)
            if not success:
                return error_response(err)

            progress = get_progress(session_id)
            if progress is None:
                return error_response("Session not found after save")

            return success_response({
                "session_id": session_id,
                "chunk_index": chunk_index,
                "chunk_size": len(chunk_data),
                "received_chunks": progress["received_chunks"],
                "total_chunks": progress["total_chunks"],
                "percent": progress["percent"],
            })

        except ValueError:
            return error_response("chunk_index must be an integer")
        except Exception as e:
            return error_response(str(e))
