"""Configuration and serialization utilities for the Settings Manager.

This module provides pure, decoupled functions to handle multi-profile state,
settings templates, type inference, JSON serialization, input sanitization,
and fallback presets. Isolating data operations from the presentation layer maintains
strict separation of concerns and full unit-testability.
"""

import json
from typing import Any, Union


def get_default_profiles() -> dict[str, dict[str, str]]:
    """Provide standard initial configuration profiles.

    Returns:
        dict[str, dict[str, str]]: Default profiles (Work, Gaming, Personal),
        each containing standard key-value settings.
    """
    return {
        "Work": {
            "theme": "Dark",
            "brightness": "85%",
            "volume": "30%",
            "notifications": "Disabled",
            "color": "#4F46E5",
            "font_size": "15px",
        },
        "Gaming": {
            "theme": "Dark",
            "brightness": "100%",
            "volume": "85%",
            "notifications": "Disabled",
            "color": "#10B981",
            "font_size": "16px",
        },
        "Personal": {
            "theme": "Light",
            "brightness": "75%",
            "volume": "60%",
            "notifications": "Enabled",
            "color": "#06B6D4",
            "font_size": "14px",
        },
    }


def get_demo_settings() -> dict[str, str]:
    """Provide a curated set of starter settings for the default profile.

    Returns:
        dict[str, str]: Key-value settings for the default profile.
    """
    return get_default_profiles()["Work"].copy()


def get_preference_templates() -> dict[str, dict[str, Any]]:
    """Return the registry of standard configuration presets and their metadata.

    Returns:
        dict[str, dict[str, Any]]: Templates mapping configuration names to their
        control types, options or limits, and default values.
    """
    return {
        "Theme": {
            "type": "choice",
            "options": ["Light", "Dark", "System Default"],
            "default": "Dark",
            "description": "Visual theme and color mode",
        },
        "Brightness": {
            "type": "slider",
            "min": 0,
            "max": 100,
            "step": 5,
            "unit": "%",
            "default": 80,
            "description": "Display backlight luminance",
        },
        "Volume": {
            "type": "slider",
            "min": 0,
            "max": 100,
            "step": 5,
            "unit": "%",
            "default": 60,
            "description": "Audio output volume",
        },
        "Notifications": {
            "type": "toggle",
            "options": ["Enabled", "Disabled"],
            "default": "Enabled",
            "description": "System alerts and notification banners",
        },
        "Color": {
            "type": "color",
            "default": "#4F46E5",
            "description": "Primary highlight color for interface elements",
        },
        "Font Size": {
            "type": "choice",
            "options": ["12px", "14px", "16px", "18px", "20px"],
            "default": "16px",
            "description": "Base interface typography scale",
        },
    }


def detect_value_type(value: Any) -> str:
    """Infer the appropriate control type from a configuration value.

    Args:
        value: The configuration value to evaluate.

    Returns:
        str: Detected type category ('color', 'slider', 'toggle', or 'text').
    """
    if not isinstance(value, str):
        value = str(value)
    val = value.strip()

    # Hex color code detection (e.g., '#4F46E5' or '#fff')
    if val.startswith("#") and len(val) in (4, 7):
        hex_digits = set("0123456789abcdefABCDEF")
        if all(c in hex_digits for c in val[1:]):
            return "color"

    # Percentage or bounded numeric slider detection (e.g., '80%', '50')
    if val.endswith("%") and val[:-1].strip().isdigit():
        return "slider"
    if val.isdigit() and 0 <= int(val) <= 100:
        return "slider"

    # Boolean toggle detection
    if val.lower() in ("enabled", "disabled", "on", "off", "true", "false"):
        return "toggle"

    return "text"


def parse_slider_value(value: Any, default: int = 50) -> int:
    """Safely extract an integer percentage from a slider-compatible value.

    Args:
        value: Input value (e.g., '80%', '65', 70, 'invalid').
        default: Fallback integer if parsing fails.

    Returns:
        int: Value bounded between 0 and 100.
    """
    val = str(value).strip().rstrip("%").strip()
    try:
        num = int(val)
        return max(0, min(100, num))
    except (ValueError, TypeError):
        return default


def export_settings(settings: dict[str, Any]) -> str:
    """Serialize the current application settings dictionary into a formatted JSON string.

    Args:
        settings: The active dictionary of key-value configuration pairs or bundle structure.

    Returns:
        str: A human-readable, indented JSON string ready for file download.
    """
    return json.dumps(settings, indent=2)


def import_settings(
    raw_data: Union[str, bytes],
) -> tuple[bool, Union[dict[str, Any], str]]:
    """Validate, parse, and sanitize uploaded JSON configuration data.

    Supports both single-profile configuration objects and multi-profile bundles
    containing a top-level 'profiles' registry.

    Args:
        raw_data: The uploaded content as either a UTF-8 byte stream or a decoded string.

    Returns:
        tuple[bool, Union[dict[str, Any], str]]: A two-element tuple where:
            - The first element is True on success, or False on validation failure.
            - The second element is the sanitized dictionary on success,
              or a descriptive, user-friendly error message on failure.
    """
    # 1. Normalize byte payloads (from file uploaders) to string
    if isinstance(raw_data, bytes):
        try:
            raw_data = raw_data.decode("utf-8")
        except UnicodeDecodeError:
            return False, "File encoding must be UTF-8."

    # 2. Reject empty file submissions
    if not raw_data.strip():
        return False, "The uploaded file is empty."

    # 3. Parse JSON syntax with error isolation
    try:
        parsed_data = json.loads(raw_data)
    except json.JSONDecodeError as err:
        return False, f"Invalid JSON syntax: {err.msg}"

    # 4. Enforce root dictionary structure
    if not isinstance(parsed_data, dict):
        return False, "Settings file must contain a JSON object (key-value pairs)."

    # 5. Handle multi-profile bundle format
    if "profiles" in parsed_data and isinstance(parsed_data["profiles"], dict):
        sanitized_bundle: dict[str, Any] = {
            "version": int(parsed_data.get("version", 2)),
            "active_profile": str(parsed_data.get("active_profile", "Work")).strip(),
            "profiles": {},
        }
        for prof_name, prof_data in parsed_data["profiles"].items():
            clean_name = str(prof_name).strip()
            if not clean_name or not isinstance(prof_data, dict):
                continue
            sanitized_profile: dict[str, str] = {}
            for k, v in prof_data.items():
                clean_k = str(k).strip()
                if clean_k:
                    sanitized_profile[clean_k] = str(v).strip()
            sanitized_bundle["profiles"][clean_name] = sanitized_profile

        if not sanitized_bundle["profiles"]:
            return False, "Multi-profile bundle contains no valid profiles."

        if sanitized_bundle["active_profile"] not in sanitized_bundle["profiles"]:
            sanitized_bundle["active_profile"] = next(iter(sanitized_bundle["profiles"]))

        return True, sanitized_bundle

    # 6. Handle single-profile flat dictionary format (backward compatible)
    sanitized_settings: dict[str, str] = {}
    for key, value in parsed_data.items():
        normalized_key = str(key).strip()
        if not normalized_key:
            continue
        sanitized_settings[normalized_key] = str(value).strip()

    return True, sanitized_settings
