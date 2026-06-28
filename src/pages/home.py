import streamlit as st
from services.utils import page_setup


page_setup("home")

if not st.session_state.get("logged_in", False):
    st.error("Você precisa estar logado para acessar esta página.")
    st.switch_page("pages/login.py")

user_info = st.session_state.get("user_info", {})
st.title(f"Bem-vindo(a), {user_info.get('nome', 'Usuário')}!")

st.write("Página inicial em construção.")