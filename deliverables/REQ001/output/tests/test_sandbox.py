"""Unit tests for the security sandbox module."""

import os
import tempfile
from pathlib import Path

import pytest

from nas_mcp_server.sandbox import (
    PathNotFoundError,
    PathTraversalError,
    PermissionDeniedError,
    SandboxError,
    format_error_response,
    validate_path,
)


@pytest.fixture
def sandbox_root(tmp_path):
    """Create a temporary sandbox root with test files."""
    # Create directory structure
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.txt").write_text("hello")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "file.csv").write_text("a,b,c")
    (tmp_path / "top.txt").write_text("top level")
    return tmp_path


class TestValidatePathNormal:
    """Tests for normal (valid) path resolution."""

    def test_relative_path_within_root(self, sandbox_root):
        result = validate_path("docs/readme.txt", sandbox_root)
        assert result == (sandbox_root / "docs" / "readme.txt").resolve()

    def test_absolute_path_within_root(self, sandbox_root):
        abs_path = str(sandbox_root / "top.txt")
        result = validate_path(abs_path, sandbox_root)
        assert result == (sandbox_root / "top.txt").resolve()

    def test_root_directory_itself(self, sandbox_root):
        result = validate_path(".", sandbox_root)
        assert result == sandbox_root.resolve()

    def test_subdirectory(self, sandbox_root):
        result = validate_path("docs", sandbox_root)
        assert result == (sandbox_root / "docs").resolve()

    def test_write_mode_nonexistent_file(self, sandbox_root):
        """Write operations allow non-existent target paths."""
        result = validate_path("docs/new_file.txt", sandbox_root, must_exist=False)
        assert result == (sandbox_root / "docs" / "new_file.txt").resolve()

    def test_write_mode_existing_file(self, sandbox_root):
        """Write operations also work for existing files."""
        result = validate_path("top.txt", sandbox_root, must_exist=False)
        assert result == (sandbox_root / "top.txt").resolve()

    def test_nested_relative_path(self, sandbox_root):
        result = validate_path("data/file.csv", sandbox_root)
        assert result == (sandbox_root / "data" / "file.csv").resolve()


class TestValidatePathTraversal:
    """Tests for path traversal attack prevention."""

    def test_dotdot_escape(self, sandbox_root):
        with pytest.raises(PathTraversalError):
            validate_path("../etc/passwd", sandbox_root)

    def test_dotdot_in_middle(self, sandbox_root):
        with pytest.raises(PathTraversalError):
            validate_path("docs/../../etc/passwd", sandbox_root)

    def test_multiple_dotdot(self, sandbox_root):
        with pytest.raises(PathTraversalError):
            validate_path("../../../tmp/evil", sandbox_root)

    def test_absolute_path_outside_root(self, sandbox_root):
        with pytest.raises(PathTraversalError):
            validate_path("/etc/passwd", sandbox_root)

    def test_absolute_path_sibling_directory(self, sandbox_root):
        # Create a sibling directory to ensure it's outside root
        sibling = sandbox_root.parent / "sibling"
        sibling.mkdir(exist_ok=True)
        try:
            with pytest.raises(PathTraversalError):
                validate_path(str(sibling), sandbox_root)
        finally:
            sibling.rmdir()

    def test_symlink_escape(self, sandbox_root):
        """Symlinks that resolve outside root must be rejected."""
        # Create a symlink inside root that points outside
        link_path = sandbox_root / "evil_link"
        link_path.symlink_to("/tmp")
        try:
            with pytest.raises(PathTraversalError):
                validate_path("evil_link", sandbox_root)
        finally:
            link_path.unlink()

    def test_symlink_escape_nested(self, sandbox_root):
        """Symlink to file outside root via nested path."""
        outside_file = Path(tempfile.mktemp())
        outside_file.write_text("secret")
        link_path = sandbox_root / "docs" / "sneaky"
        link_path.symlink_to(outside_file)
        try:
            with pytest.raises(PathTraversalError):
                validate_path("docs/sneaky", sandbox_root)
        finally:
            link_path.unlink()
            outside_file.unlink()

    def test_dotdot_write_mode(self, sandbox_root):
        """Path traversal must be blocked even in write mode."""
        with pytest.raises(PathTraversalError):
            validate_path("../outside.txt", sandbox_root, must_exist=False)


class TestValidatePathEdgeCases:
    """Tests for boundary and edge cases."""

    def test_empty_path(self, sandbox_root):
        with pytest.raises(PermissionDeniedError):
            validate_path("", sandbox_root)

    def test_whitespace_only_path(self, sandbox_root):
        with pytest.raises(PermissionDeniedError):
            validate_path("   ", sandbox_root)

    def test_nonexistent_file_read_mode(self, sandbox_root):
        with pytest.raises(PathNotFoundError):
            validate_path("no_such_file.txt", sandbox_root)

    def test_nonexistent_nested_path_read_mode(self, sandbox_root):
        with pytest.raises(PathNotFoundError):
            validate_path("no/such/dir/file.txt", sandbox_root)

    def test_root_dir_as_dot(self, sandbox_root):
        """Passing '.' resolves to the root directory itself."""
        result = validate_path(".", sandbox_root)
        assert result == sandbox_root.resolve()

    def test_trailing_slash(self, sandbox_root):
        result = validate_path("docs/", sandbox_root)
        assert result == (sandbox_root / "docs").resolve()

    def test_double_slash_in_path(self, sandbox_root):
        result = validate_path("docs//readme.txt", sandbox_root)
        assert result == (sandbox_root / "docs" / "readme.txt").resolve()

    def test_dot_in_path(self, sandbox_root):
        """Single dot components should resolve normally."""
        result = validate_path("./docs/./readme.txt", sandbox_root)
        assert result == (sandbox_root / "docs" / "readme.txt").resolve()

    def test_write_to_nonexistent_parent_still_validates(self, sandbox_root):
        """Write mode: parent doesn't exist but path is within root."""
        result = validate_path(
            "newdir/newfile.txt", sandbox_root, must_exist=False
        )
        assert result == (sandbox_root / "newdir" / "newfile.txt").resolve()


class TestErrorFormatting:
    """Tests for error response formatting."""

    def test_format_traversal_error(self):
        err = PathTraversalError("../evil")
        response = format_error_response(err)
        assert response["error"]["code"] == "PATH_TRAVERSAL"
        assert "../evil" in response["error"]["message"]

    def test_format_not_found_error(self):
        err = PathNotFoundError("missing.txt")
        response = format_error_response(err)
        assert response["error"]["code"] == "PATH_NOT_FOUND"
        assert "missing.txt" in response["error"]["message"]

    def test_format_permission_error(self):
        err = PermissionDeniedError("/secret", reason="read-only zone")
        response = format_error_response(err)
        assert response["error"]["code"] == "PERMISSION_DENIED"
        assert "/secret" in response["error"]["message"]
        assert "read-only zone" in response["error"]["message"]

    def test_sandbox_error_base_class(self):
        err = SandboxError("generic issue", "GENERIC")
        assert err.error_code == "GENERIC"
        assert err.message == "generic issue"
        response = format_error_response(err)
        assert response["error"]["code"] == "GENERIC"

    def test_permission_error_no_reason(self):
        err = PermissionDeniedError("/path")
        response = format_error_response(err)
        assert response["error"]["code"] == "PERMISSION_DENIED"
        assert "/path" in response["error"]["message"]
