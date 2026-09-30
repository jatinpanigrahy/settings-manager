"""Settings Manager Application.

A refined, responsive configuration dashboard built with Streamlit.
Provides intuitive management of application preferences with client-side
backup and restore capabilities.
"""

import html
from typing import Optional
import streamlit as st
from utils import export_settings, get_demo_settings, import_settings


def load_custom_css(file_path: str = "assets/style.css") -> None:
    """Inject custom application styles from an external stylesheet.

    Args:
        file_path: Path to the CSS stylesheet.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as css_file:
            st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def set_notification(message_type: str, text: str) -> None:
    """Queue a notification message for display.

    Args:
        message_type: Alert category ('success', 'error', 'info').
        text: Notification message copy.
    """
    st.session_state.notification = (message_type, text)


def format_display_label(key: str) -> str:
    """Format raw configuration keys into clean labels.

    Args:
        key: Raw dictionary key (e.g., 'font_size').

    Returns:
        str: Clean title-cased label (e.g., 'Font Size').
    """
    return key.replace("_", " ").title()


def format_display_value(value: str) -> str:
    """Format preference values for polished display presentation.

    Args:
        value: Raw preference value.

    Returns:
        str: Polished display string.
    """
    return str(value).strip()


# --- 1. Application Configuration ---
st.set_page_config(
    page_title="Settings Manager",
    page_icon="assets/favicon.svg",
    layout="wide",
)

load_custom_css()

# --- 2. State Initialization ---
if "user_settings" not in st.session_state:
    st.session_state.user_settings = get_demo_settings()

if "notification" not in st.session_state:
    st.session_state.notification = None


# --- 3. Top Header with Floating Popover Window ---
header_col, action_col = st.columns([3.8, 1.2], gap="large")

with header_col:
    st.title("Settings Manager")
    st.markdown("A refined workspace to configure, manage, and preserve your system preferences.")

with action_col:
    # Add vertical spacing so the button aligns nicely with the title
    st.write("")
    with st.popover("Backup & Data", use_container_width=True):
        st.subheader("Data Management")
        st.caption("Export your preferences to a local file or restore from a backup.")

        # 3.1 Export Configuration
        json_data = export_settings(st.session_state.user_settings)
        st.download_button(
            label="Export Preferences",
            data=json_data,
            file_name="settings.json",
            mime="application/json",
            use_container_width=True,
        )

        st.divider()

        # 3.2 Restore Configuration
        uploaded_file = st.file_uploader(
            "Restore from File",
            type=["json"],
            help="Upload a configuration file to restore preferences.",
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            is_valid, payload = import_settings(file_bytes)

            if is_valid and isinstance(payload, dict):
                if payload != st.session_state.user_settings:
                    st.session_state.user_settings = payload
                    set_notification("success", "Preferences restored successfully.")
                    st.rerun()
            else:
                set_notification("error", str(payload))

        st.divider()

        # 3.3 Preset Actions
        if st.button("Restore Defaults", use_container_width=True):
            st.session_state.user_settings = get_demo_settings()
            set_notification("success", "Preferences restored to defaults.")
            st.rerun()

        if st.button("Clear All Preferences", use_container_width=True):
            st.session_state.user_settings = {}
            set_notification("info", "All preferences have been cleared.")
            st.rerun()


# --- 4. Flash Notifications ---
if st.session_state.notification:
    msg_type, msg_text = st.session_state.notification
    if msg_type == "success":
        st.success(msg_text)
    elif msg_type == "error":
        st.error(msg_text)
    elif msg_type == "info":
        st.info(msg_text)
    st.session_state.notification = None


# --- 5. Main Dashboard Layout (Split View: 62% Left, 38% Right) ---
left_col, right_col = st.columns([1.65, 1], gap="large")

# 5.1 Left Column: Active Preferences (Prominent Badge View)
with left_col:
    st.subheader("Active Preferences")

    settings_dict = st.session_state.user_settings

    if not settings_dict:
        st.markdown(
            """
            <div class="empty-state-box">
                <div class="empty-state-icon">⚙️</div>
                <div class="empty-state-title">No Preferences Found</div>
                <div class="empty-state-subtitle">Add a preference on the right or restore default presets below.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Load Default Presets", type="primary", use_container_width=True):
            st.session_state.user_settings = get_demo_settings()
            set_notification("success", "Default preferences loaded.")
            st.rerun()
    else:
        # Build clean HTML rows with formatted uppercase badge styling
        rows_html = []
        for key, value in settings_dict.items():
            display_label = html.escape(format_display_label(key))
            display_val = html.escape(format_display_value(value))
            rows_html.append(
                f'<div class="setting-row">'
                f'<span class="setting-key">{display_label}</span>'
                f'<span class="setting-value">{display_val}</span>'
                f'</div>'
            )

        list_container_html = f'<div class="setting-list-container">{"".join(rows_html)}</div>'
        st.markdown(list_container_html, unsafe_allow_html=True)


# 5.2 Right Column: Configure Preferences (CRUD Actions)
with right_col:
    st.subheader("Configure Preferences")
    tab_add, tab_update, tab_delete = st.tabs(["Add", "Update", "Delete"])

    # --- Tab 1: Add Setting ---
    with tab_add:
        with st.form("add_setting_form", clear_on_submit=True):
            new_key = st.text_input("Preference Name", placeholder="e.g., Language").strip().lower()
            new_val = st.text_input("Preference Value", placeholder="e.g., English").strip()
            submit_add = st.form_submit_button("Add Preference", use_container_width=True)

            if submit_add:
                if not new_key or not new_val:
                    set_notification("error", "Both name and value are required.")
                elif new_key in st.session_state.user_settings:
                    set_notification("error", f"Preference '{format_display_label(new_key)}' already exists.")
                else:
                    st.session_state.user_settings[new_key] = new_val
                    set_notification("success", f"Preference '{format_display_label(new_key)}' added.")
                st.rerun()

    # --- Tab 2: Update Setting ---
    with tab_update:
        if not settings_dict:
            st.info("No preferences available to update.")
        else:
            with st.form("update_setting_form"):
                target_key = st.selectbox(
                    "Select Preference to Update",
                    options=list(settings_dict.keys()),
                    format_func=format_display_label,
                )
                current_val = settings_dict.get(target_key, "")
                updated_val = st.text_input(
                    "New Value",
                    value=current_val,
                    placeholder="Enter updated value",
                ).strip()
                submit_update = st.form_submit_button("Save Changes", use_container_width=True)

                if submit_update:
                    if not updated_val:
                        set_notification("error", "Value cannot be empty.")
                    else:
                        st.session_state.user_settings[target_key] = updated_val
                        set_notification("success", f"Preference '{format_display_label(target_key)}' updated.")
                    st.rerun()

    # --- Tab 3: Delete Setting ---
    with tab_delete:
        if not settings_dict:
            st.info("No preferences available to remove.")
        else:
            with st.form("delete_setting_form"):
                delete_key = st.selectbox(
                    "Select Preference to Remove",
                    options=list(settings_dict.keys()),
                    format_func=format_display_label,
                )
                submit_delete = st.form_submit_button(
                    "Remove Preference",
                    type="primary",
                    use_container_width=True,
                )

                if submit_delete:
                    if delete_key in st.session_state.user_settings:
                        del st.session_state.user_settings[delete_key]
                        set_notification("success", f"Preference '{format_display_label(delete_key)}' removed.")
                    st.rerun()
