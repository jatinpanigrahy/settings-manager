import streamlit as st

st.set_page_config(
    page_title="Settings App", page_icon="assets/favicon.svg", layout="wide"
)

def load_custom_css(file_path: str = "assets/style.css") -> None:
    """Inject custom application styles from an external stylesheet."""
    try:
        with open(file_path, "r", encoding="utf-8") as css_file:
            st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


load_custom_css()

if "user_settings" not in st.session_state:
    st.session_state.user_settings = {"theme": "dark", "volume": "high"}
if "notification" not in st.session_state:
    st.session_state.notification = None

st.title("User Settings Manager")

st.info(
    "This is a simple settings dashboard. By default, the app starts with a 'theme' and 'volume' setting. You can add, update, or delete your preferences using the options below. Any changes you make will instantly update the table."
)

if st.session_state.notification:
    msg_type, msg_text = st.session_state.notification
    if msg_type == "success":
        st.success(msg_text)
    elif msg_type == "error":
        st.error(msg_text)
    st.session_state.notification = None

left_col, right_col = st.columns([1.2, 1], gap="large")

with left_col:
    st.subheader("Current Settings")
    if not st.session_state.user_settings:
        st.warning("No settings available.")
    else:
        display_dict = {
            str(k).upper(): str(v).upper()
            for k, v in st.session_state.user_settings.items()
        }
        st.table(display_dict)

with right_col:
    st.subheader("Manage Settings")
    tab1, tab2, tab3 = st.tabs(["Add", "Update", "Delete"])

    with tab1:
        with st.form("add_form", clear_on_submit=True):
            add_name = st.text_input("Setting Name").lower()
            add_value = st.text_input("Setting Value").lower()

            if st.form_submit_button("Add Setting"):
                if not add_name or not add_value:
                    st.session_state.notification = (
                        "error",
                        "Both fields are required.",
                    )
                elif add_name in st.session_state.user_settings:
                    st.session_state.notification = (
                        "error",
                        f"'{add_name}' already exists.",
                    )
                else:
                    st.session_state.user_settings[add_name] = add_value
                    st.session_state.notification = ("success", "Setting Added!")
                st.rerun()

    with tab2:
        with st.form("update_form", clear_on_submit=True):
            up_name = st.text_input("Existing Setting Name").lower()
            up_value = st.text_input("New Value").lower()

            if st.form_submit_button("Update Setting"):
                if not up_name or not up_value:
                    st.session_state.notification = (
                        "error",
                        "Both fields are required.",
                    )
                elif up_name not in st.session_state.user_settings:
                    st.session_state.notification = ("error", f"'{up_name}' not found.")
                else:
                    st.session_state.user_settings[up_name] = up_value
                    st.session_state.notification = ("success", "Setting Updated!")
                st.rerun()

    with tab3:
        with st.form("delete_form", clear_on_submit=True):
            del_name = st.text_input("Setting Name to Delete").lower()

            if st.form_submit_button("Delete Setting"):
                if not del_name:
                    st.session_state.notification = ("error", "Field required.")
                elif del_name not in st.session_state.user_settings:
                    st.session_state.notification = (
                        "error",
                        f"'{del_name}' not found.",
                    )
                else:
                    del st.session_state.user_settings[del_name]
                    st.session_state.notification = ("success", "Setting Deleted!")
                st.rerun()
