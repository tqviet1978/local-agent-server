from flask import request
import subprocess
from auth import require_auth
from logger import log_request
from utils.path_utils import get_safe_path
from utils.response_utils import success_response, error_response
from config import get_repo_manager


def register(app):
    @app.route("/command/execute", methods=["POST"])
    @require_auth
    @log_request
    def command_execute():
        """Chạy shell command"""
        try:
            data = request.get_json()
            repo_code = data["repository"]
            command = data["command"]

            repo_manager = get_repo_manager()
            repo_path = get_safe_path(repo_manager, repo_code, "")

            result = subprocess.run(
                command, shell=True, cwd=repo_path, capture_output=True, text=True
            )

            return success_response(
                {
                    "command": command,
                    "repository": repo_code,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
        except Exception as e:
            return error_response(str(e))
