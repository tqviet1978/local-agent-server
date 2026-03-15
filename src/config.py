"""Repository configuration management"""

import json
from pathlib import Path


class RepositoryManager:
    """Manage multiple code repositories"""

    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        with open(config_path, "r") as f:
            config = json.load(f)
            self.full_config = config

        self.repositories = config.get("repositories", {})
        self._validate_repositories()

    def _validate_repositories(self):
        """Validate all repository paths exist"""
        for code, repo in self.repositories.items():
            if repo.get("enabled", True):
                path = Path(repo["path"])
                if not path.exists():
                    print(f"⚠️  Warning: Repository '{code}' path does not exist: {path}")

    def get_repository(self, repo_code):
        """Get repository by code"""
        if repo_code not in self.repositories:
            raise ValueError(f"Repository not found: {repo_code}")

        repo = self.repositories[repo_code]

        if not repo.get("enabled", True):
            raise ValueError(f"Repository is disabled: {repo_code}")

        return repo

    def list_repositories(self):
        """List all enabled repositories"""
        return {code: repo for code, repo in self.repositories.items() if repo.get("enabled", True)}

    def add_repository(self, code, path, description=None, enabled=True):
        """Add a new repository to the manager"""
        # Validate code
        code = code.lower().strip()
        if not code:
            raise ValueError("Repository code cannot be empty")

        if code in self.repositories:
            raise ValueError(f"Repository already exists: {code}")

        # Validate path
        repo_path = Path(path).resolve()
        if not repo_path.exists():
            raise ValueError(f"Path does not exist: {path}")

        if not repo_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        # Add to repositories
        self.repositories[code] = {
            "path": str(repo_path),
            "description": description or code,
            "enabled": enabled,
        }

        # Save to config file
        self._save_config()

        return self.repositories[code]

    def remove_repository(self, code):
        """Remove a repository from the manager"""
        if code not in self.repositories:
            raise ValueError(f"Repository not found: {code}")

        removed = self.repositories.pop(code)
        self._save_config()

        return removed

    def _save_config(self):
        """Save current repositories to config file"""
        self.full_config["repositories"] = self.repositories

        with open(self.config_path, "w") as f:
            json.dump(self.full_config, f, indent=2)

    def reload_config(self):
        """Reload configuration from file"""
        with open(self.config_path, "r") as f:
            config = json.load(f)
            self.full_config = config

        self.repositories = config.get("repositories", {})
        self._validate_repositories()

        return len(self.repositories)

    def resolve_path(self, repo_code, relative_path):
        """Resolve relative path to absolute path within repository"""
        repo = self.get_repository(repo_code)
        base_path = Path(repo["path"]).resolve()

        # Resolve the full path
        if relative_path:
            full_path = (base_path / relative_path).resolve()
        else:
            full_path = base_path

        # Security: ensure path is within repository
        if not str(full_path).startswith(str(base_path)):
            raise ValueError(f"Path outside repository: {relative_path}")

        return full_path


# Global repository manager instance
repo_manager = None


def init_repo_manager(config_path="config.json"):
    """Initialize global repository manager"""
    global repo_manager
    repo_manager = RepositoryManager(config_path)
    return repo_manager


def get_repo_manager():
    """Get global repository manager"""
    if repo_manager is None:
        raise RuntimeError("Repository manager not initialized")
    return repo_manager
