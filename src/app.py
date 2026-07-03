import streamlit as st

st.set_page_config(
    page_title="UniEvents",
    page_icon="src/images/page-icon.jpg",
    layout="wide",
    initial_sidebar_state="auto"
)

if st.session_state.get("logged_in"):
    st.switch_page("pages/home.py")
else:
    st.switch_page("pages/login.py")