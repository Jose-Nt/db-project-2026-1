from dotenv import load_dotenv
import streamlit as st
import os

try:
    env_path = os.path.join(os.getcwd(), "src", "config", ".env")
    load_dotenv(dotenv_path=env_path)
except:
    pass

st.switch_page("pages/login.py")