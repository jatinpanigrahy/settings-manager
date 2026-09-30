"""Configuration and serialization utilities for the Settings Manager.

This module provides pure, decoupled functions to handle JSON serialization,
validation, input sanitization, and fallback presets. By isolating these data
operations from Streamlit UI code, the application maintains strict separation
of concerns and full unit-testability.
"""

import json
from typing import Any, Dict, Tuple, Union


def get_demo_settings() -> Dict[str, str]:
    """Provide a curated set of starter preferences for the initial empty state.

    Returns:
        Dict[str, str]: A dictionary containing default configuration pairs
        (theme, volume, notifications, font size).
    """
    return {
        "theme": "dark",
        "volume": "80%",
        "notifications": "enabled",
        "font_size": "medium",
    }


def export_settings(settings: Dict[str, Any]) -> str:
    """Serialize the current application settings dictionary into a formatted JSON string.

    Args:
        settings: The active dictionary of key-value configuration pairs.

    Returns:
        str: A human-readable, indented JSON string ready for file download.
    """
    return json.dumps(settings, indent=2)


def import_settings(
    raw_data: Union[str, bytes],
) -> Tuple[bool, Union[Dict[str, str], str]]:
    """Validate, parse, and sanitize uploaded JSON configuration data.

    This function safely isolates syntax errors, encoding issues, and structural
    mismatches to prevent the user interface from crashing on invalid inputs.

    Args:
        raw_data: The uploaded content as either a UTF-8 byte stream or a decoded string.

    Returns:
        Tuple[bool, Union[Dict[str, str], str]]: A two-element tuple where:
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

    # 5. Sanitize and normalize keys and values
    sanitized_settings: Dict[str, str] = {}
    for key, value in parsed_data.items():
        normalized_key = str(key).strip().lower()
        if not normalized_key:
            continue
        sanitized_settings[normalized_key] = str(value).strip()

    return True, sanitized_settings
