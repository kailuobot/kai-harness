"""Security sandbox for path validation and access control.

All file operations must pass through validate_path() before accessing
the filesystem. This ensures no path traversal attacks can escape the
configured root directory.
"""

from pathlib import Path


class SandboxError(Exception):
    """Base exception for sandbox security violations."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class PathTraversalError(SandboxError):
    """Raised when a path attempts to escape the root directory."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Path traversal denied: '{path}' escapes the root directory",
            error_code="PATH_TRAVERSAL",
        )


class PathNotFoundError(SandboxError):
    """Raised when a path does not exist (for read operations)."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Path not found: '{path}'",
            error_code="PATH_NOT_FOUND",
        )


class PermissionDeniedError(SandboxError):
    """Raised when an operation is not permitted."""

    def __init__(self, path: str, reason: str = "") -> None:
        detail = f": {reason}" if reason else ""
        super().__init__(
            f"Permission denied for path '{path}'{detail}",
            error_code="PERMISSION_DENIED",
        )


def format_error_response(error: SandboxError) -> dict:
    """Format a SandboxError into a standardized error response dict.

    Returns:
        Dict with 'error' key containing code and message.
    """
    return {
        "error": {
            "code": error.error_code,
            "message": error.message,
        }
    }


def validate_path(
    path: str,
    root_dir: Path,
    *,
    must_exist: bool = True,
) -> Path:
    """Validate and resolve a path, ensuring it stays within root_dir.

    Args:
        path: The user-supplied path string (absolute or relative to root).
        root_dir: The sandbox root directory (must be absolute and exist).
        must_exist: If True (default), raise PathNotFoundError when the
            resolved path does not exist. Set to False for write operations
            where the target may not yet exist.

    Returns:
        The resolved absolute Path guaranteed to be within root_dir.

    Raises:
        PathTraversalError: If the path escapes root_dir.
        PathNotFoundError: If must_exist=True and the path does not exist.
        PermissionDeniedError: If the path is empty or root_dir is invalid.
    """
    if not path or path.strip() == "":
        raise PermissionDeniedError(path, reason="empty path is not allowed")

    # Ensure root_dir is absolute and resolved
    resolved_root = root_dir.resolve()

    # Build the candidate path
    candidate = Path(path)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (resolved_root / candidate).resolve()

    # Check that resolved path is within root_dir
    if not _is_within_root(resolved, resolved_root):
        raise PathTraversalError(path)

    # Existence check for read operations
    if must_exist and not resolved.exists():
        raise PathNotFoundError(path)

    # For write operations, verify the parent directory is within root
    if not must_exist:
        parent = resolved.parent
        if not _is_within_root(parent, resolved_root):
            raise PathTraversalError(path)

    return resolved


def _is_within_root(path: Path, root: Path) -> bool:
    """Check if path is equal to or a descendant of root."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
