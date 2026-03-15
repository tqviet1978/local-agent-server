"""
Validation Helper - Shared validation logic for file operations
"""
import subprocess
from pathlib import Path


# File extension to validator mapping
VALIDATORS = {
    ".py": {
        "command": ["python3", "-m", "py_compile", "{file}"],
        "type": "python"
    },
    ".js": {
        "command": ["node", "--check", "{file}"],
        "type": "javascript"
    },
    ".mjs": {
        "command": ["node", "--check", "{file}"],
        "type": "javascript"
    },
    ".json": {
        "command": ["python3", "-c", "import json; json.load(open('{file}'))"],
        "type": "json"
    },
    ".yaml": {
        "command": ["python3", "-c", "import yaml; yaml.safe_load(open('{file}'))"],
        "type": "yaml"
    },
    ".yml": {
        "command": ["python3", "-c", "import yaml; yaml.safe_load(open('{file}'))"],
        "type": "yaml"
    },
    ".sh": {
        "command": ["bash", "-n", "{file}"],
        "type": "bash"
    },
    ".bash": {
        "command": ["bash", "-n", "{file}"],
        "type": "bash"
    },
}


def validate_file(file_path: Path) -> dict:
    """
    Validate file syntax based on extension.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        dict with keys:
            - valid: bool
            - type: str (validation type, e.g., "python")
            - errors: list[str] (only if valid=False)
            - message: str (only if no validator available)
    """
    extension = file_path.suffix.lower()
    validator = VALIDATORS.get(extension)
    
    if not validator:
        return {
            "valid": True,
            "type": None,
            "message": f"No validator for extension {extension}"
        }
    
    # Build command
    command = [part.replace("{file}", str(file_path)) for part in validator["command"]]
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return {
                "valid": True,
                "type": validator["type"]
            }
        else:
            error_output = result.stderr or result.stdout
            errors = [line.strip() for line in error_output.strip().split('\n') if line.strip()]
            return {
                "valid": False,
                "type": validator["type"],
                "errors": errors
            }
            
    except subprocess.TimeoutExpired:
        return {
            "valid": False,
            "type": validator["type"],
            "errors": ["Validation timed out"]
        }
    except FileNotFoundError as e:
        return {
            "valid": False,
            "type": validator["type"],
            "errors": [f"Validator not found: {e}"]
        }
    except Exception as e:
        return {
            "valid": False,
            "type": validator["type"],
            "errors": [str(e)]
        }
