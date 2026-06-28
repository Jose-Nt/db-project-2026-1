from clients.PostgreSqlManager import PostgreSqlManager
from services.utils import page_setup
from datetime import date
import streamlit as st
import pandas as pd


page_setup()

if st.session_state.get("logged_in", False):
    st.switch_page("pages/home.py")

st.title("Bem-vindo(a)!")

db_manager = PostgreSqlManager()

login_tab, register_tab = st.tabs(["Login", "Registrar"])

with login_tab:
    with st.form("login_form"):
        cpf = st.text_input("CPF", max_chars=11)
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            if not cpf or not senha:
                st.error("Por favor, insira seu CPF e senha.")
            else:
                try:
                    user_df = db_manager.execute_query(
                        "SELECT * FROM usuario WHERE cpf = %s AND senha = %s",
                        params=(cpf, senha)
                    )
                    if not user_df.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_info = user_df.iloc[0].to_dict()
                        st.success("Login bem-sucedido!")
                        st.switch_page("pages/home.py")
                    else:
                        st.error("CPF ou senha inválidos. Por favor, verifique ou registre-se.")
                except Exception as e:
                    st.error(f"Ocorreu um erro durante o login: {e}")

with register_tab:
    with st.form("register_form"):
        st.subheader("Crie sua conta")

        try:
            departamentos_df = db_manager.execute_query("SELECT id_departamento, nome FROM departamento")
            tipos_usuario_df = db_manager.execute_query("SELECT id_tipo_usuario, nome FROM tipo_usuario")

            departamentos = {row['nome']: row['id_departamento'] for index, row in departamentos_df.iterrows()}
            tipos_usuario = {row['nome']: row['id_tipo_usuario'] for index, row in tipos_usuario_df.iterrows()}

            nome = st.text_input("Nome Completo")
            cpf_reg = st.text_input("CPF (apenas números)", max_chars=11, key="cpf_reg")
            data_nasc = st.date_input("Data de Nascimento", min_value=date(1920, 1, 1), max_value=date.today())
            senha_reg = st.text_input("Senha", type="password", key="senha_reg")
            confirma_senha_reg = st.text_input("Confirme sua Senha", type="password", key="confirma_senha_reg")
            
            dep_selecionado = st.selectbox("Departamento", options=list(departamentos.keys()))
            tipo_selecionado = st.selectbox("Tipo de Usuário", options=list(tipos_usuario.keys()))

            register_submitted = st.form_submit_button("Registrar")

            if register_submitted:
                if not all([nome, cpf_reg, data_nasc, senha_reg, confirma_senha_reg, dep_selecionado, tipo_selecionado]):
                    st.error("Por favor, preencha todos os campos.")
                elif senha_reg != confirma_senha_reg:
                    st.error("As senhas não coincidem.")
                elif len(senha_reg) < 6:
                    st.error("A senha deve ter no mínimo 6 caracteres.")
                elif len(cpf_reg) != 11 or not cpf_reg.isdigit():
                    st.error("CPF inválido. Deve conter 11 dígitos numéricos.")
                else:
                    user_exists_df = db_manager.execute_query(
                        "SELECT cpf FROM usuario WHERE cpf = %s",
                        params=(cpf_reg,)
                    )
                    if not user_exists_df.empty:
                        st.error("Este CPF já está cadastrado. Tente fazer o login.")
                    else:
                        new_user_data = {
                            "cpf": [cpf_reg],
                            "iddepartamento": [departamentos[dep_selecionado]],
                            "idtipo_usuario": [tipos_usuario[tipo_selecionado]],
                            "nome": [nome],
                            "data_nasc": [data_nasc],
                            "senha": [senha_reg]
                        }
                        new_user_df = pd.DataFrame(new_user_data)
                        try:
                            db_manager.insert_data_into_table(new_user_df, "usuario")
                            st.success("Usuário registrado com sucesso! Agora você pode fazer o login.")
                        except Exception as e:
                            st.error(f"Ocorreu um erro durante o registro: {e}")
        
        except Exception as e:
            st.error(f"Não foi possível carregar os dados para o formulário de registro: {e}")