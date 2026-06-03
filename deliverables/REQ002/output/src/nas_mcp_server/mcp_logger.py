"""MCP call logging module.

Writes structured logs for every MCP tool invocation to
NAS_ROOT_DIR/mcp-log/{date}.log.
"""

import json
from datetime import datetime
from pathlib import Path


def _get_log_file(root_dir: Path) -> Path:
    log_dir = root_dir / "mcp-log"
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"{today}.log"


def log_tool_call(
    root_dir: Path,
    caller: str,
    tool_name: str,
    arguments: dict,
    success: bool,
    result: str | None = None,
    error: str | None = None,
) -> None:
    """Append a tool call log entry.

    Args:
        root_dir: NAS root directory (log goes to root_dir/mcp-log/).
        caller: Identity of the caller (e.g. client session info).
        tool_name: Name of the MCP tool invoked.
        arguments: Parameters passed to the tool.
        success: Whether the call succeeded.
        result: Brief result summary on success.
        error: Error reason on failure.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "caller": caller,
        "tool": tool_name,
        "arguments": arguments,
        "success": success,
    }
    if success:
        entry["result"] = result or "ok"
    else:
        entry["error"] = error or "unknown"

    log_file = _get_log_file(root_dir)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
