"""
Chunk Session Manager

Manages upload sessions for chunked file transfer.
Sessions track which chunks have been received and handle
merging them into the final file.
"""

import os
import uuid
import time
import shutil
import threading
from pathlib import Path


# Default config
DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024  # 5MB
SESSION_EXPIRE_SECONDS = 3600  # 1 hour
CLEANUP_INTERVAL = 300  # 5 minutes

# In-memory session store
_sessions = {}
_lock = threading.Lock()


def _get_temp_dir():
    """Get temp directory for chunk storage"""
    tmp = Path("/tmp/chunk_sessions")
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp


def create_session(filename, total_size, total_chunks, target_path, repo_code):
    """Create a new upload session"""
    session_id = uuid.uuid4().hex[:16]
    session_dir = _get_temp_dir() / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    session = {
        "id": session_id,
        "filename": filename,
        "total_size": total_size,
        "total_chunks": total_chunks,
        "received_chunks": set(),
        "target_path": str(target_path),
        "repo_code": repo_code,
        "session_dir": str(session_dir),
        "created_at": time.time(),
        "updated_at": time.time(),
    }

    with _lock:
        _sessions[session_id] = session

    return session_id


def get_session(session_id):
    """Get session info, returns None if not found or expired"""
    with _lock:
        session = _sessions.get(session_id)
        if session is None:
            return None
        # Check expiry
        if time.time() - session["created_at"] > SESSION_EXPIRE_SECONDS:
            _cleanup_session(session_id)
            return None
        return session.copy()


def save_chunk(session_id, chunk_index, chunk_data):
    """
    Save a chunk to the session's temp directory.
    Returns (success: bool, error: str|None)
    """
    with _lock:
        session = _sessions.get(session_id)
        if session is None:
            return False, "Session not found or expired"

        if chunk_index < 0 or chunk_index >= session["total_chunks"]:
            return False, f"Invalid chunk_index: {chunk_index}, expected 0-{session['total_chunks'] - 1}"

        if chunk_index in session["received_chunks"]:
            # Idempotent — allow re-upload of same chunk
            pass

        chunk_path = Path(session["session_dir"]) / f"chunk_{chunk_index:06d}"
        with open(chunk_path, "wb") as f:
            f.write(chunk_data)

        session["received_chunks"].add(chunk_index)
        session["updated_at"] = time.time()

    return True, None


def get_progress(session_id):
    """Get upload progress for a session"""
    with _lock:
        session = _sessions.get(session_id)
        if session is None:
            return None

        return {
            "session_id": session_id,
            "total_chunks": session["total_chunks"],
            "received_chunks": len(session["received_chunks"]),
            "missing_chunks": sorted(
                set(range(session["total_chunks"])) - session["received_chunks"]
            ),
            "complete": len(session["received_chunks"]) == session["total_chunks"],
            "percent": round(
                len(session["received_chunks"]) / session["total_chunks"] * 100, 1
            ),
        }


def merge_chunks(session_id):
    """
    Merge all received chunks into the target file.
    Returns (success: bool, error: str|None, file_size: int)
    """
    with _lock:
        session = _sessions.get(session_id)
        if session is None:
            return False, "Session not found or expired", 0

        if len(session["received_chunks"]) != session["total_chunks"]:
            missing = sorted(
                set(range(session["total_chunks"])) - session["received_chunks"]
            )
            return False, f"Missing chunks: {missing}", 0

        target_path = Path(session["target_path"])
        session_dir = Path(session["session_dir"])

    # Merge outside lock to avoid blocking
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as out_f:
            for i in range(session["total_chunks"]):
                chunk_path = session_dir / f"chunk_{i:06d}"
                with open(chunk_path, "rb") as chunk_f:
                    while True:
                        block = chunk_f.read(65536)
                        if not block:
                            break
                        out_f.write(block)

        file_size = target_path.stat().st_size

        # Cleanup temp files
        _cleanup_session(session_id)

        return True, None, file_size

    except Exception as e:
        return False, str(e), 0


def cancel_session(session_id):
    """Cancel and cleanup a session"""
    with _lock:
        _cleanup_session(session_id)


def _cleanup_session(session_id):
    """Remove session data and temp files (must be called under _lock)"""
    session = _sessions.pop(session_id, None)
    if session:
        session_dir = Path(session["session_dir"])
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)


def cleanup_expired():
    """Remove all expired sessions"""
    now = time.time()
    with _lock:
        expired = [
            sid for sid, s in _sessions.items()
            if now - s["created_at"] > SESSION_EXPIRE_SECONDS
        ]
        for sid in expired:
            _cleanup_session(sid)
    return len(expired)


def list_sessions():
    """List all active sessions (for debugging)"""
    with _lock:
        result = []
        for sid, s in _sessions.items():
            result.append({
                "session_id": sid,
                "filename": s["filename"],
                "total_chunks": s["total_chunks"],
                "received": len(s["received_chunks"]),
                "created_at": s["created_at"],
            })
        return result
