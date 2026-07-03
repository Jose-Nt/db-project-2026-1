import streamlit as st

st.set_page_config(
    page_title="UniEvents | UnB",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container { padding-top: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

if st.session_state.get("logged_in"):
    st.switch_page("pages/home.py")
else:
    st.switch_page("pages/login.py")