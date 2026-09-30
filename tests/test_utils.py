"""Unit test suite for the configuration utilities module."""

import json
from utils import (
    detect_value_type,
    export_settings,
    get_default_profiles,
    get_demo_settings,
    get_preference_templates,
    import_settings,
    parse_slider_value,
)


def test_get_default_profiles():
    """Verify standard profiles (Work, Gaming, Personal) are present and populated."""
    profiles = get_default_profiles()
    assert isinstance(profiles, dict)
    assert "Work" in profiles
    assert "Gaming" in profiles
    assert "Personal" in profiles

    for profile_name, settings in profiles.items():
        assert isinstance(settings, dict)
        assert len(settings) >= 5
        assert "theme" in settings
        assert "brightness" in settings
        assert "volume" in settings
        assert "notifications" in settings
        assert "color" in settings


def test_get_demo_settings():
    """Verify demo presets return expected default configuration keys."""
    defaults = get_demo_settings()
    assert isinstance(defaults, dict)
    assert len(defaults) > 0
    assert "theme" in defaults
    assert defaults["theme"] == "Dark"
    assert defaults["brightness"] == "85%"


def test_get_preference_templates():
    """Verify standard templates are registered with appropriate control types."""
    templates = get_preference_templates()
    assert isinstance(templates, dict)
    assert "Theme" in templates
    assert "Brightness" in templates
    assert "Volume" in templates
    assert "Notifications" in templates
    assert "Color" in templates
    assert "Font Size" in templates

    assert templates["Brightness"]["type"] == "slider"
    assert templates["Brightness"]["min"] == 0
    assert templates["Brightness"]["max"] == 100

    assert templates["Notifications"]["type"] == "toggle"
    assert templates["Color"]["type"] == "color"
    assert templates["Theme"]["type"] == "choice"


def test_detect_value_type():
    """Verify automatic control type inference across various value formats."""
    # Colors
    assert detect_value_type("#4F46E5") == "color"
    assert detect_value_type("#10B981") == "color"
    assert detect_value_type("#fff") == "color"
    assert detect_value_type("#invalid") == "text"

    # Sliders
    assert detect_value_type("80%") == "slider"
    assert detect_value_type("0%") == "slider"
    assert detect_value_type("100%") == "slider"
    assert detect_value_type("75") == "slider"

    # Toggles
    assert detect_value_type("Enabled") == "toggle"
    assert detect_value_type("disabled") == "toggle"
    assert detect_value_type("On") == "toggle"
    assert detect_value_type("off") == "toggle"
    assert detect_value_type("True") == "toggle"
    assert detect_value_type("false") == "toggle"

    # Text fallbacks
    assert detect_value_type("Dark") == "text"
    assert detect_value_type("System Default") == "text"
    assert detect_value_type("https://api.domain.com") == "text"


def test_parse_slider_value():
    """Verify safe numerical extraction and bounds clipping for slider values."""
    assert parse_slider_value("85%") == 85
    assert parse_slider_value("0%") == 0
    assert parse_slider_value("100%") == 100
    assert parse_slider_value(65) == 65
    assert parse_slider_value("150%") == 100
    assert parse_slider_value("-10%") == 0
    assert parse_slider_value("invalid", default=40) == 40


def test_export_settings():
    """Verify settings dictionary properly serializes into indented JSON format."""
    sample_data = {"theme": "light", "volume": "50%"}
    json_output = export_settings(sample_data)

    assert isinstance(json_output, str)
    decoded = json.loads(json_output)
    assert decoded == sample_data
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


def test_import_settings_bundle():
    """Verify multi-profile JSON bundle is parsed and structured correctly."""
    bundle_payload = json.dumps(
        {
            "version": 2,
            "active_profile": "Gaming",
            "profiles": {
                "Work": {"theme": "Dark", "brightness": "80%"},
                "Gaming": {"theme": "Dark", "brightness": "100%"},
            },
        }
    )
    success, result = import_settings(bundle_payload)

    assert success is True
    assert isinstance(result, dict)
    assert result["version"] == 2
    assert result["active_profile"] == "Gaming"
    assert "Work" in result["profiles"]
    assert result["profiles"]["Gaming"]["brightness"] == "100%"


def test_import_settings_empty_bundle():
    """Verify bundle with no valid profiles is rejected cleanly."""
    bundle_payload = '{"version": 2, "profiles": {}}'
    success, error_msg = import_settings(bundle_payload)

    assert success is False
    assert "contains no valid profiles" in error_msg


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
