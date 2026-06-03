"""Tests for manifest.json validity and completeness."""

import json
from pathlib import Path

import pytest

MANIFEST_PATH = Path(__file__).parent.parent / "manifest.json"


@pytest.fixture
def manifest():
    """Load and parse manifest.json."""
    assert MANIFEST_PATH.exists(), f"manifest.json not found at {MANIFEST_PATH}"
    content = MANIFEST_PATH.read_text(encoding="utf-8")
    data = json.loads(content)
    return data


class TestManifestFormat:
    """Test that manifest.json is valid JSON with correct structure."""

    def test_manifest_is_valid_json(self):
        """manifest.json must be parseable as JSON."""
        content = MANIFEST_PATH.read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, dict)

    def test_required_top_level_fields(self, manifest):
        """All required top-level fields must be present."""
        required_fields = ["name", "version", "description", "transport", "tools"]
        for field in required_fields:
            assert field in manifest, f"Missing required field: {field}"

    def test_name_field(self, manifest):
        """name must be a non-empty string."""
        assert isinstance(manifest["name"], str)
        assert len(manifest["name"]) > 0
        assert manifest["name"] == "nas-file-manager"

    def test_version_field(self, manifest):
        """version must follow semver format."""
        version = manifest["version"]
        assert isinstance(version, str)
        parts = version.split(".")
        assert len(parts) == 3, "Version must be semver (x.y.z)"
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' is not numeric"

    def test_description_field(self, manifest):
        """description must be a non-empty string."""
        assert isinstance(manifest["description"], str)
        assert len(manifest["description"]) > 0


class TestManifestTransport:
    """Test transport configuration."""

    def test_transport_is_dict(self, manifest):
        """transport must be an object."""
        assert isinstance(manifest["transport"], dict)

    def test_transport_type(self, manifest):
        """transport.type must be 'sse'."""
        assert manifest["transport"]["type"] == "sse"

    def test_transport_url(self, manifest):
        """transport.url must be a valid URL string."""
        url = manifest["transport"]["url"]
        assert isinstance(url, str)
        assert url.startswith("http")
        assert "/sse" in url


class TestManifestTools:
    """Test tools list completeness and structure."""

    EXPECTED_TOOLS = [
        "list_directory",
        "read_file",
        "write_file",
        "delete_file",
        "create_directory",
        "delete_directory",
        "move_file",
    ]

    def test_tools_is_list(self, manifest):
        """tools must be a non-empty list."""
        assert isinstance(manifest["tools"], list)
        assert len(manifest["tools"]) > 0

    def test_tools_count(self, manifest):
        """Must have exactly 7 tools."""
        assert len(manifest["tools"]) == 7

    def test_all_expected_tools_present(self, manifest):
        """All 7 expected tools must be present."""
        tool_names = [t["name"] for t in manifest["tools"]]
        for expected in self.EXPECTED_TOOLS:
            assert expected in tool_names, f"Missing tool: {expected}"

    def test_each_tool_has_required_fields(self, manifest):
        """Each tool must have name, description, and inputSchema."""
        for tool in manifest["tools"]:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool '{tool.get('name')}' missing 'description'"
            assert "inputSchema" in tool, f"Tool '{tool.get('name')}' missing 'inputSchema'"

    def test_each_tool_description_non_empty(self, manifest):
        """Each tool description must be a non-empty string."""
        for tool in manifest["tools"]:
            assert isinstance(tool["description"], str)
            assert len(tool["description"]) > 0, f"Tool '{tool['name']}' has empty description"

    def test_each_tool_input_schema_is_object_type(self, manifest):
        """Each inputSchema must be a JSON Schema with type 'object'."""
        for tool in manifest["tools"]:
            schema = tool["inputSchema"]
            assert isinstance(schema, dict)
            assert schema.get("type") == "object", (
                f"Tool '{tool['name']}' inputSchema type must be 'object'"
            )

    def test_each_tool_input_schema_has_properties(self, manifest):
        """Each inputSchema must have a 'properties' field."""
        for tool in manifest["tools"]:
            schema = tool["inputSchema"]
            assert "properties" in schema, (
                f"Tool '{tool['name']}' inputSchema missing 'properties'"
            )

    def test_each_tool_input_schema_has_required(self, manifest):
        """Each inputSchema must have a 'required' field."""
        for tool in manifest["tools"]:
            schema = tool["inputSchema"]
            assert "required" in schema, (
                f"Tool '{tool['name']}' inputSchema missing 'required'"
            )
            assert isinstance(schema["required"], list)
