"""Unit test suite for the configuration utilities module."""

import json
from utils import export_settings, get_demo_settings, import_settings


def test_get_demo_settings():
    """Verify demo presets return expected default configuration keys."""
    defaults = get_demo_settings()
    assert isinstance(defaults, dict)
    assert len(defaults) > 0
    assert "theme" in defaults
    assert defaults["theme"] == "dark"


def test_export_settings():
    """Verify settings dictionary properly serializes into indented JSON format."""
    sample_data = {"theme": "light", "volume": "50%"}
    json_output = export_settings(sample_data)

    assert isinstance(json_output, str)
    # Ensure round-trip serialization validity
    decoded = json.loads(json_output)
    assert decoded == sample_data
    # Check that indentation formatting is present
    assert "\n" in json_output


def test_import_settings_valid_string():
    """Verify valid JSON string parses into sanitized settings."""
    payload = '{"theme": "dark", "volume": "high"}'
    success, result = import_settings(payload)

    assert success is True
    assert isinstance(result, dict)
    assert result["theme"] == "dark"
    assert result["volume"] == "high"


def test_import_settings_valid_bytes():
    """Verify UTF-8 encoded bytes (typical of file uploaders) parse successfully."""
    payload = b'{"notifications": "disabled", "language": "en"}'
    success, result = import_settings(payload)

    assert success is True
    assert isinstance(result, dict)
    assert result["notifications"] == "disabled"
    assert result["language"] == "en"


def test_import_settings_invalid_json():
    """Verify syntax errors in JSON return a graceful failure message."""
    bad_payload = '{"broken": json without quotes}'
    success, error_msg = import_settings(bad_payload)

    assert success is False
    assert "Invalid JSON syntax" in error_msg


def test_import_settings_non_dict_payload():
    """Verify JSON lists or scalars are rejected since settings must be key-value pairs."""
    list_payload = '["item1", "item2"]'
    success, error_msg = import_settings(list_payload)

    assert success is False
    assert "must contain a JSON object" in error_msg


def test_import_settings_empty_content():
    """Verify empty or whitespace-only payloads are caught before parsing."""
    success, error_msg = import_settings("   ")

    assert success is False
    assert "uploaded file is empty" in error_msg


def test_import_settings_invalid_encoding():
    """Verify non-UTF8 byte streams are handled cleanly without crashing."""
    bad_bytes = b"\x80abc\xff"
    success, error_msg = import_settings(bad_bytes)

    assert success is False
    assert "File encoding must be UTF-8" in error_msg
