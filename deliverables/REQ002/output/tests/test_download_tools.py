"""Tests for MCP download tools (aria2 + subliminal)."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nas_mcp_server.config import ServerConfig
from nas_mcp_server.download_tools import (
    _download_movie,
    _download_status,
    _download_subtitle,
)


# --- Fixtures ---


@pytest.fixture
def sandbox_root(tmp_path):
    """Create a sandbox root directory with sample video content."""
    (tmp_path / "movies").mkdir()
    (tmp_path / "movies" / "test_movie.mkv").write_bytes(b"\x00" * 1024)
    return tmp_path


@pytest.fixture
def config(sandbox_root):
    """Create a server config pointing to sandbox root with aria2 settings."""
    return ServerConfig(
        root_dir=sandbox_root,
        port=8080,
        aria2_host="localhost",
        aria2_port=6800,
        aria2_secret="mysecret",
    )


# --- download_movie tests ---


class TestDownloadMovie:
    """Tests for download_movie tool."""

    @pytest.mark.asyncio
    async def test_add_download_success(self, config):
        """aria2 RPC normal add download (mock aiohttp)."""
        mock_resp = AsyncMock()
        mock_resp.json = AsyncMock(return_value={
            "jsonrpc": "2.0",
            "id": "1",
            "result": "abc123",
        })
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("nas_mcp_server.download_tools.aiohttp.ClientSession", return_value=mock_session):
            result = await _download_movie(
                {"url": "https://example.com/movie.mkv"},
                config,
            )
        parsed = json.loads(result)
        assert parsed["gid"] == "abc123"
        assert parsed["status"] == "added"
        assert parsed["dir"] == str(config.root_dir)

    @pytest.mark.asyncio
    async def test_aria2_rpc_connection_failure(self, config):
        """aria2 RPC connection failure."""
        mock_session = AsyncMock()
        mock_session.post = MagicMock(side_effect=ConnectionError("Connection refused"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("nas_mcp_server.download_tools.aiohttp.ClientSession", return_value=mock_session):
            result = await _download_movie(
                {"url": "https://example.com/movie.mkv"},
                config,
            )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "aria2 RPC failed" in parsed["error"]["message"]

    @pytest.mark.asyncio
    async def test_invalid_url_rejected(self, config):
        """Non-valid URL scheme is rejected."""
        result = await _download_movie(
            {"url": "ftp://evil.com/file.bin"},
            config,
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "OPERATION_ERROR"
        assert "URL must be" in parsed["error"]["message"]

    @pytest.mark.asyncio
    async def test_download_dir_path_traversal(self, config, sandbox_root):
        """Download directory path traversal is rejected."""
        result = await _download_movie(
            {"url": "https://example.com/movie.mkv", "dir": str(sandbox_root / ".." / "escape")},
            config,
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_TRAVERSAL"


# --- download_subtitle tests ---


class TestDownloadSubtitle:
    """Tests for download_subtitle tool."""

    @pytest.mark.asyncio
    async def test_subliminal_success(self, config, sandbox_root):
        """subliminal normal subtitle download (mock subprocess)."""
        video_path = str(sandbox_root / "movies" / "test_movie.mkv")

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(
            return_value=(b"Downloaded 1 subtitle", b"")
        )

        with patch("nas_mcp_server.download_tools.asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            result = await _download_subtitle({"path": video_path}, config)

        parsed = json.loads(result)
        assert parsed["status"] == "completed"
        assert parsed["video"] == video_path
        assert "Downloaded 1 subtitle" in parsed["output"]
        mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_subliminal_not_installed(self, config, sandbox_root):
        """subliminal not installed raises FileNotFoundError."""
        video_path = str(sandbox_root / "movies" / "test_movie.mkv")

        with patch(
            "nas_mcp_server.download_tools.asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("subliminal not found"),
        ):
            result = await _download_subtitle({"path": video_path}, config)

        parsed = json.loads(result)
        assert "error" in parsed
        assert "subliminal not found" in parsed["error"]["message"]

    @pytest.mark.asyncio
    async def test_subliminal_file_not_exists(self, config, sandbox_root):
        """subliminal target file does not exist."""
        video_path = str(sandbox_root / "movies" / "nonexistent.mkv")

        result = await _download_subtitle({"path": video_path}, config)

        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"]["code"] == "PATH_NOT_FOUND"


# --- download_status tests ---


class TestDownloadStatus:
    """Tests for download_status tool."""

    @pytest.mark.asyncio
    async def test_status_single_gid(self, config):
        """download_status queries a single GID."""
        mock_resp = AsyncMock()
        mock_resp.json = AsyncMock(return_value={
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "gid": "abc123",
                "status": "active",
                "totalLength": "1000000",
                "completedLength": "500000",
                "downloadSpeed": "100000",
                "files": [{"path": "/tmp/movie.mkv"}],
            },
        })
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("nas_mcp_server.download_tools.aiohttp.ClientSession", return_value=mock_session):
            result = await _download_status({"gid": "abc123"}, config)

        parsed = json.loads(result)
        assert parsed["gid"] == "abc123"
        assert parsed["status"] == "active"
        assert parsed["progress"] == 50.0
        assert parsed["totalLength"] == 1000000
        assert parsed["completedLength"] == 500000
        assert parsed["downloadSpeed"] == 100000
        assert "movie.mkv" in parsed["files"]

    @pytest.mark.asyncio
    async def test_status_all_active(self, config):
        """download_status queries all active tasks when no GID provided."""
        # First call returns active tasks, second returns waiting tasks
        active_resp = AsyncMock()
        active_resp.json = AsyncMock(return_value={
            "jsonrpc": "2.0",
            "id": "1",
            "result": [
                {
                    "gid": "task1",
                    "status": "active",
                    "totalLength": "2000000",
                    "completedLength": "1000000",
                    "downloadSpeed": "50000",
                    "files": [{"path": "/tmp/file1.mkv"}],
                },
            ],
        })
        active_resp.__aenter__ = AsyncMock(return_value=active_resp)
        active_resp.__aexit__ = AsyncMock(return_value=False)

        waiting_resp = AsyncMock()
        waiting_resp.json = AsyncMock(return_value={
            "jsonrpc": "2.0",
            "id": "2",
            "result": [
                {
                    "gid": "task2",
                    "status": "waiting",
                    "totalLength": "3000000",
                    "completedLength": "0",
                    "downloadSpeed": "0",
                    "files": [{"path": "/tmp/file2.mkv"}],
                },
            ],
        })
        waiting_resp.__aenter__ = AsyncMock(return_value=waiting_resp)
        waiting_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(side_effect=[active_resp, waiting_resp])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("nas_mcp_server.download_tools.aiohttp.ClientSession", return_value=mock_session):
            result = await _download_status({}, config)

        parsed = json.loads(result)
        assert parsed["count"] == 2
        assert len(parsed["tasks"]) == 2
        gids = [t["gid"] for t in parsed["tasks"]]
        assert "task1" in gids
        assert "task2" in gids
