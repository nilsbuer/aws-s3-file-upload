"""
Exceptions module template for UAC Universal Extensions.

This module provides:
- Base ExecutionError class
- Standard exception types (DataValidationError, ConnectionError, etc.)
- ErrorManager singleton for error collection
- Exit code conventions

CUSTOMIZE:
- Add custom exception types for your extension
- Modify ErrorManager methods if needed
"""
from typing import Optional

class ExecutionError(Exception):
    """
    The default error raised by an extension.

    All extension errors must inherit from it.

    Attrs:
        exit_code: The exit code of the extension (for UAC)
        message: The error message for status description
    """

    exit_code: int = 1
    message: str = "Execution Failed"

    def __init__(self, message: Optional[str] = None):
        """
        Initialize exception.

        Args:
            message: Optional message that will be appended to the default message.

        Note:
            To return result data with errors, use error_manager.set_result()
            before raising the exception.
        """
        if message:
            self.message = f"{self.message}: {message}"

        super().__init__(self.message)

class DataValidationError(ExecutionError):
    """Raised when an input field is invalid."""
    exit_code = 20
    message = "Data Validation Error"

class UnexpectedSystemError(ExecutionError):
    """Raised for unexpected system errors."""
    exit_code = 1
    message = "System Error"

class AWSConnectionError(ExecutionError):
    """Raised when connection to AWS S3 endpoint fails.

    Covers network errors including endpoint unreachable, connection timeouts,
    and read timeouts. Transient error (exit code 1).
    """
    exit_code = 1
    message = "AWS Connection Error"

class AWSAuthenticationError(ExecutionError):
    """Raised when AWS authentication fails.

    Covers invalid access keys, invalid secret keys, or missing credentials.
    Non-transient user configuration error (exit code 1).
    """
    exit_code = 1
    message = "AWS Authentication Error"

class AWSAccessDeniedError(ExecutionError):
    """Raised when user lacks required IAM permissions.

    Covers AccessDenied errors from AWS, indicating insufficient s3:ListBucket
    or s3:PutObject permissions. Non-transient user configuration error (exit code 1).
    """
    exit_code = 1
    message = "AWS Access Denied"

class AWSBucketNotFoundError(ExecutionError):
    """Raised when S3 bucket does not exist or is not accessible.

    Covers NoSuchBucket errors from AWS. Non-transient user configuration error (exit code 1).
    """
    exit_code = 1
    message = "AWS Bucket Not Found"

class FileValidationError(ExecutionError):
    """Raised when source file validation fails for Upload File action.

    Covers file not found, not a regular file, or permission denied errors.
    Non-transient user input error (exit code 2).
    """
    exit_code = 2
    message = "File Validation Error"

class UnexpectedError(ExecutionError):
    """Raised for unexpected system or extension errors.

    Used for errors not caught by specific error handlers, such as bugs in
    extension code. Transient error (exit code 1).
    """
    exit_code = 1
    message = "Unexpected Error"
