import streamlit as st
from admin_dashboard import show_admin
from public_dashboard import show_public

# -----------------------------
# Session state for login
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Public", "Admin"])

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

if page == "Public":
    show_public()
else:
    # -----------------------------
    # Admin login
    # -----------------------------
    if not st.session_state.logged_in:
        st.sidebar.subheader("Admin Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        login_button = st.sidebar.button("Login")

        if login_button:
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.success("Login successful! ✅")
            else:
                st.error("Invalid credentials. Try again.")
    if st.session_state.logged_in:
        show_admin()
