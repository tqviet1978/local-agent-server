"""Path validation and resolution utilities"""

from pathlib import Path


def get_safe_path(repo_manager, repo_code, relative_path):
    """
    Get safe path within repository

    Args:
        repo_manager: RepositoryManager instance
        repo_code: Repository code
        relative_path: Relative path within repository

    Returns:
        Path object

    Raises:
        ValueError: If path is invalid or outside repository
    """
    # Resolve path using repository manager
    return repo_manager.resolve_path(repo_code, relative_path)


def validate_relative_path(path):
    """Validate that path is relative and safe"""
    if not path:
        return True

    # Check for absolute path
    if Path(path).is_absolute():
        raise ValueError("Absolute paths not allowed")

    # Check for path traversal
    if ".." in Path(path).parts:
        raise ValueError("Path traversal not allowed")

    return True
