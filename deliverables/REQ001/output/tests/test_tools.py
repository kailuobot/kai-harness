"""Tests for MCP file operation tools."""

import json
from pathlib import Path

import pytest

from nas_mcp_server.config import ServerConfig
from nas_mcp_server.tools import register_tools


# --- Fixtures ---


@pytest.fixture
def sandbox_root(tmp_path):
    """Create a sandbox root directory with sample content."""
    # Create sample files and directories
    (tmp_path / "file1.txt").write_text("hello world")
    (tmp_path / "file2.txt").write_text("second file")
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "nested.txt").write_text("nested content")
    (sub / "deep").mkdir()
    (sub / "deep" / "level2.txt").write_text("deep file")
    return tmp_path


@pytest.fixture
def config(sandbox_root):
    """Create a server config pointing to sandbox root."""
    return ServerConfig(root_dir=sandbox_root, port=8080)


@pytest.fixture
def tool_handlers(config):
    """Register tools and return a dict of {tool_name: handler_fn}."""
    from nas_mcp_server.server import create_server

    server = create_server(config)
    register_tools(server, config)
    return server._tool_handlers


# --- list_directory tests ---


class TestListDirectory:
    """Tests for list_directory tool."""

    @pytest.mark.asyncio
    async def test_list_root(self, tool_handlers, sandbox_root):
        handler = tool_handlers["list_directory"]
        result = await handler({"path": str(sandbox_root)})
        entries = json.loads(result)["entries"]
        names = [e["name"] for e in entries]
        assert "file1.txt" in names
        assert "file2.txt" in names
        assert "subdir" in names

    @pytest.mark.asyncio
    async def test_list_includes_type_and_size(self, tool_handlers, sandbox_root):
        handler = tool_handlers["list_directory"]
        result = await handler({"path": str(sandbox_root)})
        entries = json.loads(result)["entries"]
        file_entry = next(e for e in entries if e["name"] == "file1.txt")
        assert file_entry["type"] == "file"
        assert file_entry["size"] == 11  # "hello world"
        dir_entry = next(e for e in entries if e["name"] == "subdir")
        assert dir_entry["type"] == "directory"

    @pytest.mark.asyncio
    async def test_list_recursive(self, tool_handlers, sandbox_root):
        handler = tool_handlers["list_directory"]
        result = await handler({"path": str(sandbox_root), "recursive": True})
        entries = json.loads(result)["entries"]
        # Should contain nested paths
        names = [e["name"] for e in entries]
        assert any("nested.txt" in n for n in names)

    @pytest.mark.asyncio
    async def test_list_nonexistent_path(self, tool_handlers, sandbox_root):
        handler = tool_handlers["list_directory"]
        result = await handler({"path": str(sandbox_root / "nonexistent")})
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_list_path_traversal(self, tool_handlers, sandbox_root):
        handler = tool_handlers["list_directory"]
        result = await handler({"path": str(sandbox_root / ".." / "..")})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_TRAVERSAL"


# --- read_file tests ---


class TestReadFile:
    """Tests for read_file tool."""

    @pytest.mark.asyncio
    async def test_read_existing_file(self, tool_handlers, sandbox_root):
        handler = tool_handlers["read_file"]
        result = await handler({"path": str(sandbox_root / "file1.txt")})
        parsed = json.loads(result)
        assert parsed["content"] == "hello world"

    @pytest.mark.asyncio
    async def test_read_nested_file(self, tool_handlers, sandbox_root):
        handler = tool_handlers["read_file"]
        result = await handler({"path": str(sandbox_root / "subdir" / "nested.txt")})
        parsed = json.loads(result)
        assert parsed["content"] == "nested content"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, tool_handlers, sandbox_root):
        handler = tool_handlers["read_file"]
        result = await handler({"path": str(sandbox_root / "nope.txt")})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_read_path_traversal(self, tool_handlers, sandbox_root):
        handler = tool_handlers["read_file"]
        result = await handler({"path": str(sandbox_root / ".." / "etc" / "passwd")})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_TRAVERSAL"


# --- write_file tests ---


class TestWriteFile:
    """Tests for write_file tool."""

    @pytest.mark.asyncio
    async def test_write_new_file(self, tool_handlers, sandbox_root):
        handler = tool_handlers["write_file"]
        target = str(sandbox_root / "new_file.txt")
        result = await handler({"path": target, "content": "new content"})
        parsed = json.loads(result)
        assert parsed["path"] == target
        assert parsed["bytes_written"] == 11
        assert (sandbox_root / "new_file.txt").read_text() == "new content"

    @pytest.mark.asyncio
    async def test_write_creates_parent_dirs(self, tool_handlers, sandbox_root):
        handler = tool_handlers["write_file"]
        target = str(sandbox_root / "a" / "b" / "c.txt")
        result = await handler({"path": target, "content": "deep write"})
        parsed = json.loads(result)
        assert parsed["bytes_written"] == 10
        assert Path(target).read_text() == "deep write"

    @pytest.mark.asyncio
    async def test_write_overwrites_existing(self, tool_handlers, sandbox_root):
        handler = tool_handlers["write_file"]
        target = str(sandbox_root / "file1.txt")
        result = await handler({"path": target, "content": "overwritten"})
        parsed = json.loads(result)
        assert parsed["bytes_written"] == 11
        assert (sandbox_root / "file1.txt").read_text() == "overwritten"

    @pytest.mark.asyncio
    async def test_write_path_traversal(self, tool_handlers, sandbox_root):
        handler = tool_handlers["write_file"]
        target = str(sandbox_root / ".." / "escape.txt")
        result = await handler({"path": target, "content": "bad"})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_TRAVERSAL"


# --- delete_file tests ---


class TestDeleteFile:
    """Tests for delete_file tool."""

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, tool_handlers, sandbox_root):
        handler = tool_handlers["delete_file"]
        target = str(sandbox_root / "file1.txt")
        result = await handler({"path": target})
        parsed = json.loads(result)
        assert parsed["deleted"] == target
        assert not (sandbox_root / "file1.txt").exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, tool_handlers, sandbox_root):
        handler = tool_handlers["delete_file"]
        target = str(sandbox_root / "ghost.txt")
        result = await handler({"path": target})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_delete_path_traversal(self, tool_handlers, sandbox_root):
        handler = tool_handlers["delete_file"]
        target = str(sandbox_root / ".." / "escape.txt")
        result = await handler({"path": target})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_TRAVERSAL"


# --- create_directory tests ---


class TestCreateDirectory:
    """Tests for create_directory tool."""

    @pytest.mark.asyncio
    async def test_create_single_dir(self, tool_handlers, sandbox_root):
        handler = tool_handlers["create_directory"]
        target = str(sandbox_root / "newdir")
        result = await handler({"path": target})
        parsed = json.loads(result)
        assert parsed["created"] == target
        assert (sandbox_root / "newdir").is_dir()

    @pytest.mark.asyncio
    async def test_create_nested_dirs(self, tool_handlers, sandbox_root):
        handler = tool_handlers["create_directory"]
        target = str(sandbox_root / "a" / "b" / "c")
        result = await handler({"path": target, "parents": True})
        parsed = json.loads(result)
        assert parsed["created"] == target
        assert Path(target).is_dir()

    @pytest.mark.asyncio
    async def test_create_no_parents_fails(self, tool_handlers, sandbox_root):
        handler = tool_handlers["create_directory"]
        target = str(sandbox_root / "x" / "y" / "z")
        result = await handler({"path": target, "parents": False})
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_create_existing_dir_ok(self, tool_handlers, sandbox_root):
        handler = tool_handlers["create_directory"]
        target = str(sandbox_root / "subdir")
        result = await handler({"path": target})
        parsed = json.loads(result)
        assert parsed["created"] == target

    @pytest.mark.asyncio
    async def test_create_path_traversal(self, tool_handlers, sandbox_root):
        handler = tool_handlers["create_directory"]
        target = str(sandbox_root / ".." / "escape_dir")
        result = await handler({"path": target})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_TRAVERSAL"


# --- delete_directory tests ---


class TestDeleteDirectory:
    """Tests for delete_directory tool."""

    @pytest.mark.asyncio
    async def test_delete_empty_dir(self, tool_handlers, sandbox_root):
        handler = tool_handlers["delete_directory"]
        empty = sandbox_root / "empty_dir"
        empty.mkdir()
        result = await handler({"path": str(empty)})
        parsed = json.loads(result)
        assert parsed["deleted"] == str(empty)
        assert not empty.exists()

    @pytest.mark.asyncio
    async def test_delete_nonempty_dir_no_recursive(self, tool_handlers, sandbox_root):
        handler = tool_handlers["delete_directory"]
        result = await handler({"path": str(sandbox_root / "subdir"), "recursive": False})
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_delete_nonempty_dir_recursive(self, tool_handlers, sandbox_root):
        handler = tool_handlers["delete_directory"]
        target = str(sandbox_root / "subdir")
        result = await handler({"path": target, "recursive": True})
        parsed = json.loads(result)
        assert parsed["deleted"] == target
        assert not (sandbox_root / "subdir").exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_dir(self, tool_handlers, sandbox_root):
        handler = tool_handlers["delete_directory"]
        result = await handler({"path": str(sandbox_root / "nope_dir")})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_delete_dir_path_traversal(self, tool_handlers, sandbox_root):
        handler = tool_handlers["delete_directory"]
        target = str(sandbox_root / ".." / "escape")
        result = await handler({"path": target})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_TRAVERSAL"


# --- move_file tests ---


class TestMoveFile:
    """Tests for move_file tool."""

    @pytest.mark.asyncio
    async def test_move_file(self, tool_handlers, sandbox_root):
        handler = tool_handlers["move_file"]
        src = str(sandbox_root / "file1.txt")
        dst = str(sandbox_root / "moved.txt")
        result = await handler({"source": src, "destination": dst})
        parsed = json.loads(result)
        assert parsed["source"] == src
        assert parsed["destination"] == dst
        assert not (sandbox_root / "file1.txt").exists()
        assert (sandbox_root / "moved.txt").read_text() == "hello world"

    @pytest.mark.asyncio
    async def test_move_into_subdir(self, tool_handlers, sandbox_root):
        handler = tool_handlers["move_file"]
        src = str(sandbox_root / "file2.txt")
        dst = str(sandbox_root / "subdir" / "file2_moved.txt")
        result = await handler({"source": src, "destination": dst})
        parsed = json.loads(result)
        assert parsed["destination"] == dst
        assert Path(dst).read_text() == "second file"

    @pytest.mark.asyncio
    async def test_move_nonexistent_source(self, tool_handlers, sandbox_root):
        handler = tool_handlers["move_file"]
        src = str(sandbox_root / "ghost.txt")
        dst = str(sandbox_root / "dest.txt")
        result = await handler({"source": src, "destination": dst})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_move_source_traversal(self, tool_handlers, sandbox_root):
        handler = tool_handlers["move_file"]
        src = str(sandbox_root / ".." / "etc" / "passwd")
        dst = str(sandbox_root / "stolen.txt")
        result = await handler({"source": src, "destination": dst})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_TRAVERSAL"

    @pytest.mark.asyncio
    async def test_move_destination_traversal(self, tool_handlers, sandbox_root):
        handler = tool_handlers["move_file"]
        src = str(sandbox_root / "file1.txt")
        dst = str(sandbox_root / ".." / "escaped.txt")
        result = await handler({"source": src, "destination": dst})
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_TRAVERSAL"
