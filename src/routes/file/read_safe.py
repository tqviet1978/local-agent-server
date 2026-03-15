"""
/file/read_safe - Safe file reading without JSON parsing issues

This API reads files and returns content properly encoded without
control character issues that plague /command/execute + cat
"""

from flask import request
from auth import require_auth
from logger import log_request
from utils.path_utils import get_safe_path
from utils.response_utils import success_response, error_response
from utils.error_codes import (
    ErrorCode,
    file_not_found_error,
    permission_denied_error
)
from config import get_repo_manager
import base64
import mimetypes


def register(app):
    @app.route("/file/read_safe", methods=["POST"])
    @require_auth
    @log_request
    def file_read_safe():
        """
        Safe file reading with proper encoding
        
        Body parameters:
            - repository: str (required)
            - path: str (required)
            - encoding: str (default: "utf-8", or "base64" for binary)
            - line_start: int (optional, 1-indexed)
            - line_end: int (optional, inclusive)
        
        Returns proper encoding without JSON control character issues
        """
        try:
            data = request.get_json()
            repo_code = data["repository"]
            file_path = data["path"]
            encoding = data.get("encoding", "utf-8")
            line_start = data.get("line_start")
            line_end = data.get("line_end")
            
            repo_manager = get_repo_manager()
            real_path = get_safe_path(repo_manager, repo_code, file_path)
            
            # Check if file exists
            if not real_path.exists():
                error = file_not_found_error(file_path, repo_code)
                return error_response(error, 404)
            
            if not real_path.is_file():
                return error_response(
                    ErrorCode.INVALID_FILE_TYPE,
                    400
                )
            
            # Get file info
            file_size = real_path.stat().st_size
            mime_type = mimetypes.guess_type(str(real_path))[0] or "application/octet-stream"
            
            # Read file based on encoding
            try:
                if encoding == "base64":
                    # Binary mode
                    with open(real_path, "rb") as f:
                        content = base64.b64encode(f.read()).decode('ascii')
                    
                    return success_response({
                        "path": file_path,
                        "repository": repo_code,
                        "content": content,
                        "encoding": "base64",
                        "size": file_size,
                        "mime_type": mime_type,
                        "binary": True
                    })
                else:
                    # Text mode
                    with open(real_path, "r", encoding=encoding) as f:
                        if line_start is not None and line_end is not None:
                            # Read specific line range
                            lines = f.readlines()
                            # Convert to 0-indexed
                            start_idx = max(0, line_start - 1)
                            end_idx = min(len(lines), line_end)
                            content = ''.join(lines[start_idx:end_idx])
                            
                            return success_response({
                                "path": file_path,
                                "repository": repo_code,
                                "content": content,
                                "encoding": encoding,
                                "size": file_size,
                                "mime_type": mime_type,
                                "line_range": {
                                    "start": line_start,
                                    "end": line_end,
                                    "actual_lines": end_idx - start_idx
                                }
                            })
                        else:
                            # Read entire file
                            content = f.read()
                            
                            return success_response({
                                "path": file_path,
                                "repository": repo_code,
                                "content": content,
                                "encoding": encoding,
                                "size": file_size,
                                "mime_type": mime_type,
                                "lines": content.count('\n') + 1 if content else 0
                            })
            
            except PermissionError:
                error = permission_denied_error(file_path, "read")
                return error_response(error, 403)
            
            except UnicodeDecodeError:
                return error_response(
                    ErrorCode.FILE_READ_ERROR,
                    400
                ).add_detail("reason", f"Cannot decode file with encoding: {encoding}")\
                 .add_suggestion("Try encoding='base64' for binary files")
        
        except KeyError as e:
            return error_response(
                ErrorCode.MISSING_REQUIRED_FIELD,
                400
            ).add_detail("field", str(e))
        
        except Exception as e:
            return error_response(str(e), 500)
