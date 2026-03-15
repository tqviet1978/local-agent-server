from flask import request
from auth import require_auth
from logger import log_request
from utils.path_utils import get_safe_path
from utils.response_utils import success_response, error_response
from utils.post_command_helper import execute_post_command
from config import get_repo_manager


def register(app):
    @app.route("/file/upload", methods=["POST"])
    @require_auth
    @log_request
    def file_upload():
        """Upload file via multipart form-data (for large files)
        
        Form fields:
            - post_cmd: str (optional) - bash command to execute after upload
        """
        try:
            repo_code = request.form.get("repository")
            path = request.form.get("path")
            post_cmd = request.form.get("post_cmd")

            if not repo_code:
                return error_response("Missing required field: repository")
            if not path:
                return error_response("Missing required field: path")
            if "file" not in request.files:
                return error_response("Missing required field: file")

            uploaded_file = request.files["file"]
            if uploaded_file.filename == "":
                return error_response("No file selected")

            repo_manager = get_repo_manager()
            real_path = get_safe_path(repo_manager, repo_code, path)
            real_path.parent.mkdir(parents=True, exist_ok=True)
            uploaded_file.save(real_path)
            file_size = real_path.stat().st_size

            response_data = {
                "path": path,
                "repository": repo_code,
                "size": file_size,
                "original_filename": uploaded_file.filename
            }

            if post_cmd:
                try:
                    repo_path = get_safe_path(repo_manager, repo_code, "")
                    post_result = execute_post_command(post_cmd, repo_path)
                    response_data["post_cmd"] = post_result
                except Exception as e:
                    response_data["post_cmd"] = {"error": str(e)}

            return success_response(response_data)
        except Exception as e:
            return error_response(str(e))
