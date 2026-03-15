from flask import request, Response, send_file
from pathlib import Path
import mimetypes
from auth import require_auth
from logger import log_request
from utils.path_utils import get_safe_path
from utils.response_utils import error_response
from config import get_repo_manager


# Extended MIME types for common file types
MIME_TYPES = {
    # Images
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".bmp": "image/bmp",
    
    # Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    
    # Archives
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".gzip": "application/gzip",
    ".rar": "application/vnd.rar",
    ".7z": "application/x-7z-compressed",
    
    # Audio
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    
    # Video
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    
    # Code & Text
    ".json": "application/json",
    ".xml": "application/xml",
    ".html": "text/html",
    ".htm": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    
    # Executables & binaries
    ".exe": "application/vnd.microsoft.portable-executable",
    ".dll": "application/x-msdownload",
    ".so": "application/x-sharedlib",
    ".dylib": "application/x-mach-binary",
    ".wasm": "application/wasm",
    
    # Fonts
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}


def get_mime_type(file_path: Path) -> str:
    """Get MIME type from file extension"""
    ext = file_path.suffix.lower()
    
    # Check our extended list first
    if ext in MIME_TYPES:
        return MIME_TYPES[ext]
    
    # Fallback to mimetypes module
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "application/octet-stream"


def register(app):
    @app.route("/file/download", methods=["GET", "POST"])
    @require_auth
    @log_request
    def file_download():
        """Download file with proper MIME type
        
        GET: /file/download?repository=repo&path=file.pdf&filename=custom.pdf
        POST: {"repository": "repo", "path": "file.pdf", "filename": "custom.pdf"}
        
        Returns: File content with appropriate Content-Type and Content-Disposition headers
        """
        try:
            # Handle both GET (query params) and POST (JSON body)
            if request.method == "GET":
                repo_code = request.args.get("repository")
                file_path = request.args.get("path")
                filename = request.args.get("filename")
            else:
                data = request.get_json()
                repo_code = data.get("repository")
                file_path = data.get("path")
                filename = data.get("filename")
            
            if not repo_code:
                return error_response("Missing repository parameter")
            if not file_path:
                return error_response("Missing path parameter")
            
            repo_manager = get_repo_manager()
            real_path = get_safe_path(repo_manager, repo_code, file_path)
            
            if not real_path.exists():
                return error_response(f"File not found: {file_path}", 404)
            
            if not real_path.is_file():
                return error_response(f"Not a file: {file_path}")
            
            # Determine filename for Content-Disposition
            download_filename = filename or real_path.name
            
            # Get MIME type
            mime_type = get_mime_type(real_path)
            
            # Use Flask's send_file for efficient file serving
            return send_file(
                real_path,
                mimetype=mime_type,
                as_attachment=True,
                download_name=download_filename
            )
            
        except KeyError as e:
            return error_response(f"Missing required field: {e}")
        except Exception as e:
            return error_response(str(e))
