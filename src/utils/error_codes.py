"""
Error codes and standard error responses for Local Agent Server
"""

from enum import Enum


class ErrorCode(Enum):
    """Standard error codes for API responses"""
    
    # File operation errors (1xxx)
    FILE_NOT_FOUND = (1001, "File not found")
    FILE_ALREADY_EXISTS = (1002, "File already exists")
    FILE_TOO_LARGE = (1003, "File size exceeds limit")
    INVALID_PATH = (1004, "Invalid file path")
    PERMISSION_DENIED = (1005, "Permission denied")
    FILE_READ_ERROR = (1006, "Error reading file")
    FILE_WRITE_ERROR = (1007, "Error writing file")
    INVALID_FILE_TYPE = (1008, "Invalid file type")
    FILE_LOCKED = (1009, "File is locked")
    
    # Repository errors (2xxx)
    REPO_NOT_FOUND = (2001, "Repository not found")
    REPO_ALREADY_EXISTS = (2002, "Repository already exists")
    REPO_INVALID_PATH = (2003, "Invalid repository path")
    REPO_ACCESS_DENIED = (2004, "Repository access denied")
    
    # Command execution errors (3xxx)
    COMMAND_FAILED = (3001, "Command execution failed")
    COMMAND_TIMEOUT = (3002, "Command execution timeout")
    COMMAND_NOT_ALLOWED = (3003, "Command not allowed")
    INVALID_COMMAND = (3004, "Invalid command")
    
    # Validation errors (4xxx)
    SYNTAX_ERROR = (4001, "Syntax error in file")
    VALIDATION_FAILED = (4002, "Validation failed")
    INVALID_OPERATION = (4003, "Invalid operation")
    MISSING_REQUIRED_FIELD = (4004, "Missing required field")
    INVALID_PARAMETER = (4005, "Invalid parameter value")
    
    # Search/Pattern errors (5xxx)
    PATTERN_NOT_FOUND = (5001, "Search pattern not found")
    INVALID_REGEX = (5002, "Invalid regular expression")
    SEARCH_TIMEOUT = (5003, "Search operation timeout")
    
    # General errors (9xxx)
    INTERNAL_ERROR = (9001, "Internal server error")
    NOT_IMPLEMENTED = (9002, "Feature not implemented")
    RATE_LIMIT_EXCEEDED = (9003, "Rate limit exceeded")
    INVALID_REQUEST = (9004, "Invalid request format")
    UNAUTHORIZED = (9005, "Unauthorized access")
    
    @property
    def code(self):
        """Get numeric error code"""
        return self.value[0]
    
    @property
    def message(self):
        """Get error message"""
        return self.value[1]


class ErrorResponse:
    """Builder for structured error responses"""
    
    def __init__(self, error_code: ErrorCode, custom_message: str = None):
        self.error_code = error_code
        self.custom_message = custom_message
        self.details = {}
        self.suggestions = []
    
    def add_detail(self, key: str, value):
        """Add detail to error response"""
        self.details[key] = value
        return self
    
    def add_suggestion(self, suggestion: str):
        """Add suggestion for fixing the error"""
        self.suggestions.append(suggestion)
        return self
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        error_dict = {
            "code": self.error_code.code,
            "type": self.error_code.name,
            "message": self.custom_message or self.error_code.message
        }
        
        if self.details:
            error_dict["details"] = self.details
        
        if self.suggestions:
            error_dict["suggestions"] = self.suggestions
        
        return error_dict


def create_error_response(
    error_code: ErrorCode,
    custom_message: str = None,
    details: dict = None,
    suggestions: list = None
):
    """
    Create a structured error response
    
    Args:
        error_code: ErrorCode enum value
        custom_message: Optional custom error message
        details: Optional dictionary of error details
        suggestions: Optional list of suggestions
    
    Returns:
        ErrorResponse object
    """
    error = ErrorResponse(error_code, custom_message)
    
    if details:
        for key, value in details.items():
            error.add_detail(key, value)
    
    if suggestions:
        for suggestion in suggestions:
            error.add_suggestion(suggestion)
    
    return error


# Common error response builders for convenience
def file_not_found_error(path: str, repository: str = None):
    """Create file not found error with helpful suggestions"""
    error = ErrorResponse(ErrorCode.FILE_NOT_FOUND, f"File '{path}' not found")
    error.add_detail("path", path)
    
    if repository:
        error.add_detail("repository", repository)
        error.add_suggestion(f"Check if file exists: ls {path}")
        error.add_suggestion(f"List directory: ls -la $(dirname {path})")
        error.add_suggestion(f"Search for file: find . -name $(basename {path})")
    
    return error


def permission_denied_error(path: str, operation: str = "access"):
    """Create permission denied error"""
    error = ErrorResponse(
        ErrorCode.PERMISSION_DENIED,
        f"Permission denied to {operation} '{path}'"
    )
    error.add_detail("path", path)
    error.add_detail("operation", operation)
    error.add_suggestion(f"Check file permissions: ls -la {path}")
    error.add_suggestion(f"Fix permissions: chmod 644 {path}")
    
    return error


def validation_error(file_path: str, errors: list):
    """Create validation error with details"""
    error = ErrorResponse(ErrorCode.SYNTAX_ERROR, f"Syntax errors in '{file_path}'")
    error.add_detail("file", file_path)
    error.add_detail("errors", errors)
    error.add_suggestion("Fix syntax errors before saving")
    error.add_suggestion("Use a linter to check your code")
    
    return error


def command_failed_error(command: str, returncode: int, stderr: str = None):
    """Create command execution error"""
    error = ErrorResponse(
        ErrorCode.COMMAND_FAILED,
        f"Command failed with exit code {returncode}"
    )
    error.add_detail("command", command)
    error.add_detail("returncode", returncode)
    
    if stderr:
        error.add_detail("stderr", stderr[:500])  # Limit stderr length
    
    error.add_suggestion("Check command syntax")
    error.add_suggestion("Verify required tools are installed")
    
    return error
