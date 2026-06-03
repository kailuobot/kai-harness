"""MCP download tools for NAS server.

Provides 3 tools: download_movie, download_subtitle, download_status.
- download_movie: adds a download task via aria2 JSON-RPC
- download_subtitle: fetches Chinese subtitles via subliminal CLI
- download_status: queries aria2 for task progress
"""

import asyncio
import json
import uuid
from pathlib import Path

from .config import ServerConfig
from .sandbox import SandboxError, format_error_response, validate_path


DOWNLOAD_TOOL_SCHEMAS = {
    "download_movie": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Download URL or magnet link",
            },
            "dir": {
                "type": "string",
                "description": "Target directory on NAS (relative to root_dir or absolute within sandbox)",
            },
        },
        "required": ["url"],
    },
    "download_subtitle": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the video file on NAS",
            },
        },
        "required": ["path"],
    },
    "download_status": {
        "type": "object",
        "properties": {
            "gid": {
                "type": "string",
                "description": "aria2 download GID. If omitted, returns all active downloads.",
            },
        },
        "required": [],
    },
}

DOWNLOAD_TOOL_DESCRIPTIONS = {
    "download_movie": "Download a movie via aria2. Accepts HTTP/HTTPS URLs or magnet links.",
    "download_subtitle": "Download Chinese subtitles for a video file using subliminal.",
    "download_status": "Check download progress. Query a specific GID or list all active downloads.",
}


def _error_json(error: SandboxError) -> str:
    return json.dumps(format_error_response(error))


def _op_error_json(message: str) -> str:
    return json.dumps({"error": {"code": "OPERATION_ERROR", "message": message}})


async def _aria2_rpc(config: ServerConfig, method: str, params: list | None = None) -> dict:
    """Call aria2 JSON-RPC endpoint."""
    import aiohttp

    url = f"http://{config.aria2_host}:{config.aria2_port}/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": [],
    }

    if config.aria2_secret:
        payload["params"].append(f"token:{config.aria2_secret}")

    if params:
        payload["params"].extend(params)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            if "error" in result:
                raise RuntimeError(result["error"].get("message", "aria2 RPC error"))
            return result.get("result", {})


async def _download_movie(arguments: dict, config: ServerConfig) -> str:
    """Add a download task to aria2."""
    url = arguments["url"]
    dir_path = arguments.get("dir")

    if not url.startswith(("http://", "https://", "magnet:")):
        return _op_error_json("URL must be http://, https://, or magnet: link")

    options = {}
    if dir_path:
        try:
            resolved = validate_path(dir_path, config.root_dir, must_exist=False)
            options["dir"] = str(resolved)
        except SandboxError as e:
            return _error_json(e)
    else:
        options["dir"] = str(config.root_dir)

    try:
        if url.startswith("magnet:"):
            gid = await _aria2_rpc(config, "aria2.addUri", [[url], options])
        else:
            gid = await _aria2_rpc(config, "aria2.addUri", [[url], options])
        return json.dumps({"gid": gid, "status": "added", "dir": options["dir"]})
    except Exception as e:
        return _op_error_json(f"aria2 RPC failed: {e}")


async def _download_subtitle(arguments: dict, config: ServerConfig) -> str:
    """Download Chinese subtitles using subliminal."""
    path_str = arguments["path"]

    try:
        resolved = validate_path(path_str, config.root_dir, must_exist=True)
    except SandboxError as e:
        return _error_json(e)

    if not resolved.is_file():
        return _op_error_json(f"Path is not a file: {path_str}")

    cmd = [
        "subliminal", "download",
        "-l", "zh",
        str(resolved),
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return _op_error_json(
                f"subliminal failed (exit {proc.returncode}): {stderr.decode().strip()}"
            )

        return json.dumps({
            "status": "completed",
            "video": str(resolved),
            "output": stdout.decode().strip(),
        })
    except FileNotFoundError:
        return _op_error_json("subliminal not found. Install with: pip install subliminal")
    except Exception as e:
        return _op_error_json(f"subliminal execution failed: {e}")


async def _download_status(arguments: dict, config: ServerConfig) -> str:
    """Query aria2 download progress."""
    gid = arguments.get("gid")

    try:
        if gid:
            status = await _aria2_rpc(config, "aria2.tellStatus", [gid])
            return json.dumps(_format_status(status))
        else:
            active = await _aria2_rpc(config, "aria2.tellActive", [])
            waiting = await _aria2_rpc(config, "aria2.tellWaiting", [0, 10])
            tasks = []
            for item in (active if isinstance(active, list) else []):
                tasks.append(_format_status(item))
            for item in (waiting if isinstance(waiting, list) else []):
                tasks.append(_format_status(item))
            return json.dumps({"tasks": tasks, "count": len(tasks)})
    except Exception as e:
        return _op_error_json(f"aria2 RPC failed: {e}")


def _format_status(status: dict) -> dict:
    """Extract key fields from aria2 status response."""
    total = int(status.get("totalLength", 0))
    completed = int(status.get("completedLength", 0))
    speed = int(status.get("downloadSpeed", 0))
    progress = (completed / total * 100) if total > 0 else 0

    files = []
    for f in status.get("files", []):
        path = f.get("path", "")
        if path:
            files.append(Path(path).name)

    return {
        "gid": status.get("gid", ""),
        "status": status.get("status", "unknown"),
        "progress": round(progress, 1),
        "totalLength": total,
        "completedLength": completed,
        "downloadSpeed": speed,
        "files": files,
    }


_DOWNLOAD_TOOL_DISPATCH = {
    "download_movie": _download_movie,
    "download_subtitle": _download_subtitle,
    "download_status": _download_status,
}
