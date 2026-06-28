'''from services.setup import setup_enviroment
import streamlit as st
from clients.PostgreSqlManager import PostgreSqlManager

setup_enviroment()

pg_manager = PostgreSqlManager()
df = pg_manager.execute_query("SELECT * FROM local")
st.dataframe(df)

#st.switch_page("pages/login.py")'''

from src.services.utils import setup_enviroment

print(1+1)