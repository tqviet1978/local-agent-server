from flask import jsonify
from config import get_repo_manager


def register(app):
    @app.route("/health", methods=["GET"])
    def health():
        """Health check"""
        try:
            repo_manager = get_repo_manager()
            repos = repo_manager.list_repositories()

            return jsonify({"status": "healthy", "repositories_count": len(repos)})
        except Exception as e:
            return jsonify({"status": "unhealthy", "error": str(e)}), 500
