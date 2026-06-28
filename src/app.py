import streamlit as st
from services.utils import setup_enviroment

setup_enviroment()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.switch_page("pages/home.py" if st.session_state.logged_in else "pages/login.py")