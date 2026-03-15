import subprocess
from typing import Dict


def execute_post_command(command: str, repo_path: str) -> Dict:
    """
    Execute post-operation command trong repository context
    
    Args:
        command: Bash command string
        repo_path: Repository root path (working directory)
        
    Returns:
        Dict chứa kết quả execution (format giống command/execute)
    """
    result = subprocess.run(
        command, shell=True, cwd=repo_path, capture_output=True, text=True
    )
    
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
