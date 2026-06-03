"""MCP tools for NAS server.

Provides 7 file operation tools + 3 download tools (aria2 + subliminal).

All paths are validated through the security sandbox before any filesystem
operation is performed.
"""

import json
import os
import shutil
from pathlib import Path

from mcp import types

from .config import ServerConfig
from .mcp_logger import log_tool_call
from .download_tools import (
    DOWNLOAD_TOOL_DESCRIPTIONS,
    DOWNLOAD_TOOL_SCHEMAS,
    _DOWNLOAD_TOOL_DISPATCH,
)
from .sandbox import (
    PathNotFoundError,
    PathTraversalError,
    PermissionDeniedError,
    SandboxError,
    format_error_response,
    validate_path,
)

# JSON Schema definitions for each tool's input
TOOL_SCHEMAS = {
    "list_directory": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path to list"},
            "recursive": {
                "type": "boolean",
                "description": "List recursively (default: false)",
                "default": False,
            },
        },
        "required": ["path"],
    },
    "read_file": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to read"},
        },
        "required": ["path"],
    },
    "write_file": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to write"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    },
    "delete_file": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to delete"},
        },
        "required": ["path"],
    },
    "create_directory": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path to create"},
            "parents": {
                "type": "boolean",
                "description": "Create parent directories (default: true)",
                "default": True,
            },
        },
        "required": ["path"],
    },
    "delete_directory": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path to delete"},
            "recursive": {
                "type": "boolean",
                "description": "Delete recursively (default: false)",
                "default": False,
            },
        },
        "required": ["path"],
    },
    "move_file": {
        "type": "object",
        "properties": {
            "source": {"type": "string", "description": "Source path"},
            "destination": {"type": "string", "description": "Destination path"},
        },
        "required": ["source", "destination"],
    },
}


def _error_json(error: SandboxError) -> str:
    """Convert a SandboxError to a JSON error response string."""
    return json.dumps(format_error_response(error))


def _op_error_json(message: str) -> str:
    """Create a JSON error response for filesystem operation errors."""
    return json.dumps({"error": {"code": "OPERATION_ERROR", "message": message}})


async def _list_directory(arguments: dict, config: ServerConfig) -> str:
    """List directory contents."""
    path_str = arguments["path"]
    recursive = arguments.get("recursive", False)

    try:
        resolved = validate_path(path_str, config.root_dir, must_exist=True)
    except SandboxError as e:
        return _error_json(e)

    if not resolved.is_dir():
        return _op_error_json(f"Path is not a directory: {path_str}")

    entries = []
    if recursive:
        for item in sorted(resolved.rglob("*")):
            rel = str(item.relative_to(resolved))
            entry = {"name": rel, "type": "directory" if item.is_dir() else "file"}
            if item.is_file():
                entry["size"] = item.stat().st_size
            entries.append(entry)
    else:
        for item in sorted(resolved.iterdir()):
            entry = {"name": item.name, "type": "directory" if item.is_dir() else "file"}
            if item.is_file():
                entry["size"] = item.stat().st_size
            entries.append(entry)

    return json.dumps({"entries": entries})


async def _read_file(arguments: dict, config: ServerConfig) -> str:
    """Read file content."""
    path_str = arguments["path"]

    try:
        resolved = validate_path(path_str, config.root_dir, must_exist=True)
    except SandboxError as e:
        return _error_json(e)

    if not resolved.is_file():
        return _op_error_json(f"Path is not a file: {path_str}")

    try:
        content = resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = resolved.read_text(encoding="latin-1")
        except Exception as e:
            return _op_error_json(f"Cannot read file: {e}")

    return json.dumps({"content": content, "path": str(resolved)})


async def _write_file(arguments: dict, config: ServerConfig) -> str:
    """Write content to a file."""
    path_str = arguments["path"]
    content = arguments["content"]

    try:
        resolved = validate_path(path_str, config.root_dir, must_exist=False)
    except SandboxError as e:
        return _error_json(e)

    # Auto-create parent directories
    resolved.parent.mkdir(parents=True, exist_ok=True)

    try:
        bytes_written = resolved.write_text(content, encoding="utf-8")
    except Exception as e:
        return _op_error_json(f"Cannot write file: {e}")

    # write_text returns None in older Python, calculate manually
    actual_bytes = len(content.encode("utf-8"))
    return json.dumps({"path": str(resolved), "bytes_written": actual_bytes})


async def _delete_file(arguments: dict, config: ServerConfig) -> str:
    """Delete a file."""
    path_str = arguments["path"]

    try:
        resolved = validate_path(path_str, config.root_dir, must_exist=True)
    except SandboxError as e:
        return _error_json(e)

    if not resolved.is_file():
        return _op_error_json(f"Path is not a file: {path_str}")

    resolved.unlink()
    return json.dumps({"deleted": str(resolved)})


async def _create_directory(arguments: dict, config: ServerConfig) -> str:
    """Create a directory."""
    path_str = arguments["path"]
    parents = arguments.get("parents", True)

    try:
        resolved = validate_path(path_str, config.root_dir, must_exist=False)
    except SandboxError as e:
        return _error_json(e)

    try:
        resolved.mkdir(parents=parents, exist_ok=True)
    except FileNotFoundError:
        return _op_error_json(
            f"Cannot create directory, parent does not exist: {path_str}"
        )
    except OSError as e:
        return _op_error_json(f"Cannot create directory: {e}")

    return json.dumps({"created": str(resolved)})


async def _delete_directory(arguments: dict, config: ServerConfig) -> str:
    """Delete a directory."""
    path_str = arguments["path"]
    recursive = arguments.get("recursive", False)

    try:
        resolved = validate_path(path_str, config.root_dir, must_exist=True)
    except SandboxError as e:
        return _error_json(e)

    if not resolved.is_dir():
        return _op_error_json(f"Path is not a directory: {path_str}")

    if not recursive:
        # Check if directory is empty
        if any(resolved.iterdir()):
            return _op_error_json(
                f"Directory is not empty: {path_str}. Use recursive=true to delete."
            )
        try:
            resolved.rmdir()
        except OSError as e:
            return _op_error_json(f"Cannot delete directory: {e}")
    else:
        try:
            shutil.rmtree(str(resolved))
        except OSError as e:
            return _op_error_json(f"Cannot delete directory: {e}")

    return json.dumps({"deleted": str(resolved)})


async def _move_file(arguments: dict, config: ServerConfig) -> str:
    """Move a file or directory."""
    source_str = arguments["source"]
    dest_str = arguments["destination"]

    # Validate source (must exist)
    try:
        resolved_source = validate_path(source_str, config.root_dir, must_exist=True)
    except SandboxError as e:
        return _error_json(e)

    # Validate destination (may not exist yet)
    try:
        resolved_dest = validate_path(dest_str, config.root_dir, must_exist=False)
    except SandboxError as e:
        return _error_json(e)

    try:
        shutil.move(str(resolved_source), str(resolved_dest))
    except Exception as e:
        return _op_error_json(f"Cannot move: {e}")

    return json.dumps({"source": str(resolved_source), "destination": str(resolved_dest)})


TOOL_DESCRIPTIONS = {
    "list_directory": "List directory contents (files, types, sizes). Supports recursive listing.",
    "read_file": "Read text content of a file. Handles encoding issues.",
    "write_file": "Write text content to a file. Creates parent directories if needed.",
    "delete_file": "Delete a file. Returns error if file does not exist.",
    "create_directory": "Create a directory. Supports recursive parent creation.",
    "delete_directory": "Delete a directory. Non-recursive mode fails on non-empty dirs.",
    "move_file": "Move a file or directory from source to destination.",
}

# Map tool names to handler functions
_TOOL_DISPATCH = {
    "list_directory": _list_directory,
    "read_file": _read_file,
    "write_file": _write_file,
    "delete_file": _delete_file,
    "create_directory": _create_directory,
    "delete_directory": _delete_directory,
    "move_file": _move_file,
}


def register_tools(server, config: ServerConfig) -> None:
    """Register all tools (file operations + download) on the MCP server.

    Uses @server.list_tools() and @server.call_tool() decorators
    from the mcp SDK to register tools with the MCP tool router.

    Args:
        server: MCP Server instance.
        config: Server configuration with root_dir for sandbox.
    """
    # Store handlers on server for testing access
    server._tool_handlers = {}  # type: ignore[attr-defined]

    # Create bound handlers for file operation tools
    for name, handler_fn in _TOOL_DISPATCH.items():

        async def _make_handler(args, _fn=handler_fn):
            return await _fn(args, config)

        server._tool_handlers[name] = _make_handler

    # Create bound handlers for download tools
    for name, handler_fn in _DOWNLOAD_TOOL_DISPATCH.items():

        async def _make_download_handler(args, _fn=handler_fn):
            return await _fn(args, config)

        server._tool_handlers[name] = _make_download_handler

    # Merge all schemas and descriptions
    all_schemas = {**TOOL_SCHEMAS, **DOWNLOAD_TOOL_SCHEMAS}
    all_descriptions = {**TOOL_DESCRIPTIONS, **DOWNLOAD_TOOL_DESCRIPTIONS}
    all_dispatch = {**_TOOL_DISPATCH, **_DOWNLOAD_TOOL_DISPATCH}

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        tools = []
        for name, schema in all_schemas.items():
            tools.append(types.Tool(
                name=name,
                description=all_descriptions[name],
                inputSchema=schema,
            ))
        return tools

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name not in all_dispatch:
            text = json.dumps({
                "error": {
                    "code": "UNKNOWN_TOOL",
                    "message": f"Unknown tool: {name}",
                }
            })
            try:
                log_tool_call(
                    root_dir=config.root_dir,
                    caller="mcp-client",
                    tool_name=name,
                    arguments=arguments,
                    success=False,
                    error=f"Unknown tool: {name}",
                )
            except Exception:
                pass
            return [types.TextContent(type="text", text=text)]

        result = await all_dispatch[name](arguments, config)

        try:
            result_data = json.loads(result)
            is_error = "error" in result_data
            if is_error:
                err_val = result_data["error"]
                error_msg = err_val.get("message", "unknown") if isinstance(err_val, dict) else str(err_val)
            else:
                error_msg = None
        except (json.JSONDecodeError, ValueError):
            is_error = False
            error_msg = None

        try:
            log_tool_call(
                root_dir=config.root_dir,
                caller="mcp-client",
                tool_name=name,
                arguments=arguments,
                success=not is_error,
                result=None if is_error else "ok",
                error=error_msg,
            )
        except Exception:
            pass

        return [types.TextContent(type="text", text=result)]
