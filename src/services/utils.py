from dotenv import load_dotenv
import streamlit as st
import os


def setup_enviroment(
    ) -> None:
    """
    Setup the enviroment to execute the app locally with .env. 
    """
    env_path = os.path.join(os.getcwd(), "src", "config", ".env")
    load_dotenv(dotenv_path=env_path)


def page_setup(
        page_name : str | None = None
    ) -> None:
    """
    Setup the initial config for each page.
    """
    st.set_page_config(
        page_title="UniEvents",
        page_icon="src/images/page-icon.jpg",
        layout="wide",
        initial_sidebar_state="expanded" if page_name == "home" else "collapsed"
    )

    def load_css(file_path):
        try:
            with open(file_path, encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            # Se o arquivo específico da página não existir, não faz nada.
            pass

    # Carrega o CSS comum a todas as páginas
    load_css("src/styles/common.css")

    # Carrega o CSS específico da página, se existir
    if page_name:
        load_css(f"src/styles/{page_name}.css")