"""Settings Manager Application.

A refined, responsive settings dashboard built with Streamlit.
Provides multi-profile management, type-aware settings controls,
and client-side JSON persistence.
"""

import html
import streamlit as st

from utils import (
    detect_value_type,
    export_settings,
    get_default_profiles,
    get_preference_templates,
    import_settings,
    parse_slider_value,
)


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


def render_display_badge(value: str) -> str:
    """Render an HTML badge with visual swatches or status indicators.

    Args:
        value: Raw setting value.

    Returns:
        str: Formatted HTML string.
    """
    safe_val = html.escape(str(value).strip())
    val_lower = safe_val.lower()

    # Hex color code with visual color dot
    if safe_val.startswith("#") and len(safe_val) in (4, 7):
        hex_digits = set("0123456789abcdefABCDEF")
        if all(c in hex_digits for c in safe_val[1:]):
            return f'<span class="color-dot" style="background-color: {safe_val};"></span><span>{safe_val}</span>'

    # Boolean toggle with glowing status dot
    if val_lower in ("enabled", "on", "true"):
        return f'<span class="status-dot enabled"></span><span>{safe_val}</span>'
    if val_lower in ("disabled", "off", "false"):
        return f'<span class="status-dot disabled"></span><span>{safe_val}</span>'

    return f"<span>{safe_val}</span>"


# --- Modal Confirmation Dialogs ---

@st.dialog("Create New Profile")
def create_profile_dialog() -> None:
    """Modal dialog for creating a new named configuration profile."""
    st.markdown("Create a separate configuration profile for your workspace settings.")
    profile_name = st.text_input("Profile Name", placeholder="e.g., Studio, Travel, Reading").strip()
    active_prof = st.session_state.active_profile
    copy_active = st.checkbox(f"Copy settings from current profile ('{active_prof}')", value=True)

    st.write("")
    col_submit, col_cancel = st.columns(2)
    with col_submit:
        if st.button("Create Profile", type="primary", use_container_width=True):
            if not profile_name:
                st.error("Please enter a profile name.")
            elif profile_name in st.session_state.profiles:
                st.error("A profile with this name already exists.")
            else:
                if copy_active:
                    st.session_state.profiles[profile_name] = st.session_state.profiles[active_prof].copy()
                else:
                    st.session_state.profiles[profile_name] = {}
                st.session_state.active_profile = profile_name
                st.session_state.profile_pill_selector = profile_name
                set_notification("success", f"Created and switched to profile '{profile_name}'.")
                st.rerun()
    with col_cancel:
        if st.button("Cancel", key="cancel_create_profile_btn", use_container_width=True):
            st.session_state.profile_pill_selector = st.session_state.active_profile
            st.rerun()


@st.dialog("Delete Active Profile")
def delete_profile_dialog() -> None:
    """Modal dialog for removing the currently active profile."""
    active_prof = st.session_state.active_profile
    st.markdown(
        f"Are you sure you want to delete the **'{active_prof}'** profile? "
        "All saved settings within this profile will be permanently removed."
    )
    st.write("")
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Yes, Delete Profile", type="primary", use_container_width=True):
            del st.session_state.profiles[active_prof]
            st.session_state.active_profile = next(iter(st.session_state.profiles))
            st.session_state.profile_pill_selector = st.session_state.active_profile
            set_notification("info", f"Deleted profile '{active_prof}'. Switched to '{st.session_state.active_profile}'.")
            st.rerun()
    with col_cancel:
        if st.button("Cancel", key="cancel_delete_profile_btn", use_container_width=True):
            st.rerun()


@st.dialog("Restore Starter Profiles")
def restore_defaults_dialog() -> None:
    """Modal dialog for restoring factory starter profiles."""
    st.markdown(
        "Are you sure you want to restore the default starter profiles? "
        "This will reset all profiles (*Work*, *Gaming*, *Personal*) to standard presets."
    )
    st.write("")
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Yes, Restore Defaults", type="primary", use_container_width=True):
            st.session_state.profiles = get_default_profiles()
            st.session_state.active_profile = "Work"
            st.session_state.profile_pill_selector = "Work"
            set_notification("success", "Starter profiles restored successfully.")
            st.rerun()
    with col_cancel:
        if st.button("Cancel", key="cancel_restore_btn", use_container_width=True):
            st.rerun()


@st.dialog("Clear Profile Settings")
def clear_settings_dialog() -> None:
    """Modal dialog for clearing all settings from the active profile."""
    active_prof = st.session_state.active_profile
    st.markdown(f"Are you sure you want to clear all settings in **'{active_prof}'**? Unsaved changes will be lost.")
    st.write("")
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Yes, Clear Settings", type="primary", use_container_width=True):
            st.session_state.profiles[active_prof] = {}
            set_notification("info", f"All settings in '{active_prof}' have been cleared.")
            st.rerun()
    with col_cancel:
        if st.button("Cancel", key="cancel_clear_btn", use_container_width=True):
            st.rerun()


# --- 1. Page Configuration & Assets ---
st.set_page_config(
    page_title="Settings Manager",
    page_icon="assets/favicon.svg",
    layout="wide",
)

load_custom_css()

# --- 2. Session State Initialization ---
if "profiles" not in st.session_state:
    st.session_state.profiles = get_default_profiles()

if "active_profile" not in st.session_state or st.session_state.active_profile not in st.session_state.profiles:
    st.session_state.active_profile = next(iter(st.session_state.profiles))

if "notification" not in st.session_state:
    st.session_state.notification = None

if "show_create_profile_dialog" not in st.session_state:
    st.session_state.show_create_profile_dialog = False

if "profile_pill_selector" not in st.session_state or st.session_state.profile_pill_selector not in st.session_state.profiles:
    st.session_state.profile_pill_selector = st.session_state.active_profile

active_profile = st.session_state.active_profile
current_settings: dict[str, str] = st.session_state.profiles[active_profile]


# --- 3. Top Header with Backup & Restore Menu ---
header_col, action_col = st.columns([3.2, 1.8], gap="medium")

with header_col:
    st.title("SETTINGS MANAGER")
    st.markdown("A clean workspace to customize, organize, and back up your application settings.")

with action_col:
    st.write("")
    with st.popover("Backup & Restore", use_container_width=True):
        st.subheader("Data Portability")

        # Export Section
        st.markdown("**Export Settings**")
        export_mode = st.radio("Export Scope", ["Active Profile", "All Profiles (Bundle)"], horizontal=True)

        if export_mode == "Active Profile":
            export_payload = export_settings(current_settings)
            export_filename = f"{active_profile.lower().replace(' ', '_')}_settings.json"
            download_label = f"Download '{active_profile}' JSON"
        else:
            bundle_data = {
                "version": 2,
                "active_profile": active_profile,
                "profiles": st.session_state.profiles,
            }
            export_payload = export_settings(bundle_data)
            export_filename = "settings_backup_bundle.json"
            download_label = "Download Complete Bundle"

        st.download_button(
            label=download_label,
            data=export_payload,
            file_name=export_filename,
            mime="application/json",
            use_container_width=True,
        )

        st.divider()

        # Import Section
        st.markdown("**Import Settings**")
        uploaded_file = st.file_uploader(
            "Upload JSON File",
            type=["json"],
            help="Select a single profile or a full backup bundle.",
        )
        if uploaded_file is not None:
            if st.button("Apply Imported Settings", type="primary", use_container_width=True):
                success, result = import_settings(uploaded_file.getvalue())
                if success and isinstance(result, dict):
                    if "profiles" in result and isinstance(result["profiles"], dict):
                        st.session_state.profiles = result["profiles"]
                        st.session_state.active_profile = result.get("active_profile", next(iter(result["profiles"])))
                        st.session_state.profile_pill_selector = st.session_state.active_profile
                        set_notification("success", f"Restored {len(result['profiles'])} profiles from backup bundle.")
                    else:
                        st.session_state.profiles[active_profile] = result
                        set_notification("success", f"Imported {len(result)} settings into '{active_profile}'.")
                    st.rerun()
                else:
                    st.error(str(result))

        st.divider()

        # Management Actions
        st.markdown("**Profile Actions**")
        if st.button("Restore Starter Profiles", use_container_width=True):
            restore_defaults_dialog()

        if len(st.session_state.profiles) > 1:
            if st.button(f"Delete '{active_profile}' Profile", use_container_width=True):
                delete_profile_dialog()


# --- 4. Notification Banner ---
if st.session_state.notification:
    notif_type, notif_text = st.session_state.notification
    if notif_type == "success":
        st.success(notif_text)
    elif notif_type == "error":
        st.error(notif_text)
    else:
        st.info(notif_text)
    st.session_state.notification = None


# --- 5. Understated Metric Counters Strip ---
total_settings = len(current_settings)
total_profiles = len(st.session_state.profiles)

metric_strip_html = (
    f'<div class="metric-strip">'
    f'<div class="metric-stat">'
    f'<span class="metric-label">Active Profile</span>'
    f'<span class="metric-value">{html.escape(active_profile)}</span>'
    f'</div>'
    f'<div class="metric-stat">'
    f'<span class="metric-label">Total Settings</span>'
    f'<span class="metric-value">{total_settings}</span>'
    f'</div>'
    f'<div class="metric-stat">'
    f'<span class="metric-label">Saved Profiles</span>'
    f'<span class="metric-value">{total_profiles}</span>'
    f'</div>'
    f'</div>'
)
st.markdown(metric_strip_html, unsafe_allow_html=True)


# --- 6. Profile Navigation Strip ---
def on_profile_pill_change() -> None:
    """Handle profile pill selection or new profile trigger without locking widget state."""
    chosen = st.session_state.get("profile_pill_selector")
    if chosen == "+ New Profile":
        st.session_state.show_create_profile_dialog = True
        st.session_state.profile_pill_selector = st.session_state.active_profile
    elif chosen and chosen in st.session_state.profiles:
        st.session_state.active_profile = chosen


profile_options = list(st.session_state.profiles.keys()) + ["+ New Profile"]
profile_nav_col, _ = st.columns([1.62, 1.0], gap="large")

with profile_nav_col:
    if st.session_state.get("profile_pill_selector") not in profile_options:
        st.session_state.profile_pill_selector = active_profile

    st.pills(
        label="Profiles",
        options=profile_options,
        key="profile_pill_selector",
        on_change=on_profile_pill_change,
        selection_mode="single",
        label_visibility="collapsed",
    )

    if st.session_state.get("show_create_profile_dialog"):
        st.session_state.show_create_profile_dialog = False
        create_profile_dialog()

st.write("")


# --- 7. Main Split Layout ---
col_display, col_controls = st.columns([1.62, 1.0], gap="large")

# === Left Column: Active Settings Overview ===
with col_display:
    st.subheader(f"{active_profile} Settings")

    if not current_settings:
        st.markdown(
            f'<div class="empty-state-box">'
            f'<div class="empty-state-icon">📋</div>'
            f'<div class="empty-state-title">No Settings Saved</div>'
            f'<div class="empty-state-subtitle">The \'{html.escape(active_profile)}\' profile has no saved settings yet. Use the management panel to add one.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        rows_html = "".join(
            f'<div class="setting-row">'
            f'<span class="setting-key">{html.escape(format_display_label(k))}</span>'
            f'<span class="setting-value">{render_display_badge(v)}</span>'
            f'</div>'
            for k, v in current_settings.items()
        )
        container_html = f'<div class="setting-list-container">{rows_html}</div>'
        st.markdown(container_html, unsafe_allow_html=True)

        st.write("")
        clear_btn_col, _ = st.columns([1.5, 2.5])
        with clear_btn_col:
            if st.button("Clear All Settings", use_container_width=True):
                clear_settings_dialog()


# === Right Column: Management Controls ===
with col_controls:
    st.subheader("Manage Settings")
    tab_add, tab_update, tab_remove = st.tabs(["ADD", "UPDATE", "REMOVE"])

    templates = get_preference_templates()
    template_choices = list(templates.keys()) + ["Custom Setting..."]

    # --- TAB 1: ADD SETTING ---
    with tab_add:
        preset_choice = st.selectbox(
            "Setting Template",
            options=template_choices,
            key="add_preset_choice",
        )

        custom_control = "Slider (0-100%)"
        if preset_choice not in templates:
            custom_control = st.radio(
                "Input Control Type",
                ["Slider (0-100%)", "Toggle (On/Off)", "Color Picker", "Plain Text"],
                horizontal=True,
                key="add_custom_control_type",
            )

        with st.form("add_setting_form", clear_on_submit=True):
            if preset_choice in templates:
                tpl = templates[preset_choice]
                st.caption(tpl["description"])
                key_to_save = preset_choice.lower().replace(" ", "_")

                if tpl["type"] == "choice":
                    default_idx = tpl["options"].index(tpl["default"]) if tpl["default"] in tpl["options"] else 0
                    val_to_save = st.selectbox("Value", tpl["options"], index=default_idx)
                elif tpl["type"] == "slider":
                    slider_format = "%d%%" if tpl.get("unit") == "%" else f"%d {tpl.get('unit', '')}"
                    slider_val = st.slider(
                        f"{preset_choice} Level",
                        min_value=tpl["min"],
                        max_value=tpl["max"],
                        value=tpl["default"],
                        step=tpl["step"],
                        format=slider_format,
                    )
                    val_to_save = f"{slider_val}{tpl['unit']}"
                elif tpl["type"] == "toggle":
                    val_to_save = st.radio("Value", tpl["options"], horizontal=True)
                elif tpl["type"] == "color":
                    val_to_save = st.color_picker("Color", value=tpl["default"])
                else:
                    val_to_save = st.text_input("Value", value=str(tpl.get("default", "")))
            else:
                key_input = st.text_input("Setting Name", placeholder="e.g., Keyboard Backlight")

                if custom_control == "Slider (0-100%)":
                    slider_val = st.slider("Value", 0, 100, 50, step=5, format="%d%%")
                    val_to_save = f"{slider_val}%"
                elif custom_control == "Toggle (On/Off)":
                    val_to_save = st.radio("Value", ["Enabled", "Disabled"], horizontal=True)
                elif custom_control == "Color Picker":
                    val_to_save = st.color_picker("Value", "#4F46E5")
                else:
                    val_to_save = st.text_input("Value", placeholder="e.g., standard text")

                key_to_save = key_input.strip()

            add_submitted = st.form_submit_button("ADD SETTING", type="primary", use_container_width=True)
            if add_submitted:
                clean_key = str(key_to_save).strip().lower().replace(" ", "_")
                if not clean_key:
                    st.error("Please enter a setting name.")
                else:
                    st.session_state.profiles[active_profile][clean_key] = str(val_to_save).strip()
                    set_notification("success", f"Added '{format_display_label(clean_key)}' to '{active_profile}'.")
                    st.rerun()

    # --- TAB 2: UPDATE SETTING ---
    with tab_update:
        if not current_settings:
            st.info("No settings available to update in this profile.")
        else:
            setting_keys = list(current_settings.keys())
            selected_update_key = st.selectbox(
                "Setting to Update",
                options=setting_keys,
                format_func=format_display_label,
                key="update_key_selector",
            )
            current_raw_value = current_settings[selected_update_key]

            # Infer default control type from current value
            detected_type = detect_value_type(current_raw_value)
            type_options = ["Slider", "Toggle", "Color Picker", "Plain Text"]
            type_mapping = {
                "slider": 0,
                "toggle": 1,
                "color": 2,
                "text": 3,
            }
            default_type_idx = type_mapping.get(detected_type, 3)

            chosen_control = st.radio(
                "Control Type",
                options=type_options,
                index=default_type_idx,
                horizontal=True,
                key=f"update_control_type_{selected_update_key}",
            )

            with st.form("update_setting_form"):
                if chosen_control == "Slider":
                    existing_num = parse_slider_value(current_raw_value, default=50)
                    up_slider = st.slider("New Value", 0, 100, value=existing_num, step=5, format="%d%%")
                    updated_val = f"{up_slider}%"
                elif chosen_control == "Toggle":
                    is_enabled = current_raw_value.lower() in ("enabled", "on", "true")
                    updated_val = st.radio(
                        "New Value",
                        ["Enabled", "Disabled"],
                        index=0 if is_enabled else 1,
                        horizontal=True,
                    )
                elif chosen_control == "Color Picker":
                    color_val = (
                        current_raw_value
                        if (current_raw_value.startswith("#") and len(current_raw_value) in (4, 7))
                        else "#4F46E5"
                    )
                    updated_val = st.color_picker("New Value", value=color_val)
                else:
                    updated_val = st.text_input("New Value", value=str(current_raw_value))

                update_submitted = st.form_submit_button("UPDATE SETTING", type="primary", use_container_width=True)
                if update_submitted:
                    st.session_state.profiles[active_profile][selected_update_key] = str(updated_val).strip()
                    set_notification("success", f"Updated '{format_display_label(selected_update_key)}'.")
                    st.rerun()

    # --- TAB 3: REMOVE SETTING ---
    with tab_remove:
        if not current_settings:
            st.info("No settings available to remove in this profile.")
        else:
            with st.form("remove_setting_form"):
                selected_remove_key = st.selectbox(
                    "Setting to Remove",
                    options=list(current_settings.keys()),
                    format_func=format_display_label,
                    key="remove_key_selector",
                )
                remove_submitted = st.form_submit_button(
                    "REMOVE SETTING",
                    type="primary",
                    use_container_width=True,
                )
                if remove_submitted:
                    del st.session_state.profiles[active_profile][selected_remove_key]
                    set_notification("info", f"Removed '{format_display_label(selected_remove_key)}'.")
                    st.rerun()
