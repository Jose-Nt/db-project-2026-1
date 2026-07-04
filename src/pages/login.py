from clients.PostgreSqlManager import PostgreSqlManager
from services.utils import page_setup
from datetime import date
import streamlit as st
import pandas as pd
import psycopg2
import streamlit.components.v1 as components

page_setup(page_name="login")

if st.session_state.get("logged_in", False):
    st.switch_page("pages/home.py")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    </style>
""", unsafe_allow_html=True)

db_manager = PostgreSqlManager()

_, center_col, _ = st.columns([1, 1.3, 1])

with center_col:
    st.markdown("""
        <div class="login-header">
            <h1>UniEvents - <span style="color: #FF4D8D;">Participe</span> de <span style="color: #FF4D8D;">eventos</span> no campus!</h1>
        </div>
    """, unsafe_allow_html=True)

    with st.container(border=False):
        login_tab, register_tab = st.tabs(["Login", "Registrar"])

        with login_tab:
            with st.form("login_form"):
                cpf = st.text_input("CPF", max_chars=11)
                senha = st.text_input("Senha", type="password")
                submitted = st.form_submit_button("Entrar", use_container_width=True)

                if submitted:
                    if not cpf or not senha:
                        st.error("Por favor, insira o seu CPF e senha.")
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
                                st.error("CPF ou senha inválidos. Por favor, verifique ou registe-se.")
                        except psycopg2.Error as e:
                            st.error(f"Ocorreu um erro de base de dados durante o login: {e}")

        with register_tab:
            with st.form("register_form"):
                st.subheader("Crie a sua conta")

                try:
                    departamentos_df = db_manager.execute_query("SELECT id_departamento, nome FROM departamento")
                    tipos_usuario_df = db_manager.execute_query("SELECT id_tipo_usuario, nome FROM tipo_usuario")

                    departamentos = {row['nome']: row['id_departamento'] for index, row in departamentos_df.iterrows()}
                    tipos_usuario = {row['nome']: row['id_tipo_usuario'] for index, row in tipos_usuario_df.iterrows()}

                    nome = st.text_input("Nome Completo")
                    cpf_reg = st.text_input("CPF (apenas números)", max_chars=11, key="cpf_reg")
                    data_nasc = st.date_input("Data de Nascimento", min_value=date(1920, 1, 1), max_value=date.today())
                    senha_reg = st.text_input("Senha", type="password", key="senha_reg")
                    confirma_senha_reg = st.text_input("Confirme a sua Senha", type="password", key="confirma_senha_reg")
                    
                    dep_selecionado = st.selectbox("Departamento", options=list(departamentos.keys()))
                    tipo_selecionado = st.selectbox("Tipo de Utilizador", options=list(tipos_usuario.keys()))

                    register_submitted = st.form_submit_button("Registar", use_container_width=True)

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
                                st.error("Este CPF já está registado. Tente iniciar sessão.")
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
                                    st.success("Utilizador registado com sucesso! Vá para a aba 'Login' para entrar.")
                                except psycopg2.Error as e:
                                    st.error(f"Ocorreu um erro de base de dados durante o registo: {e}")
                
                except psycopg2.Error as e:
                    st.error(f"Não foi possível carregar os dados para o formulário: {e}")

# --- SCRIPT PARA O ENTER PULAR CAMPOS ---
components.html("""
    <script>
        const doc = window.parent.document;
        
        if (!doc.getElementById('enter-tab-script')) {
            const marker = doc.createElement('div');
            marker.id = 'enter-tab-script';
            doc.body.appendChild(marker);
            
            doc.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    const active = doc.activeElement;
                    
                    if (active && active.tagName === 'INPUT') {
                        e.preventDefault(); 
                        
                        // Seleciona todos os campos que queremos navegar
                        const allElements = Array.from(doc.querySelectorAll('input:not([type="hidden"]), button'));
                        
                        // Filtro rígido:
                        // 1. Remove qualquer botão que contenha um elemento SVG (o "olhinho" é um SVG)
                        // 2. Garante que o botão tenha texto visível (evita botões decorativos)
                        const focusables = allElements.filter(el => {
                            if (el.tagName === 'BUTTON') {
                                const hasSvg = el.querySelector('svg') !== null;
                                const hasText = el.textContent.trim().length > 0;
                                return hasText && !hasSvg;
                            }
                            return true;
                        });
                        
                        const index = focusables.indexOf(active);
                        if (index > -1 && index < focusables.length - 1) {
                            focusables[index + 1].focus();
                        }
                    }
                }
            });
        }
    </script>
""", height=0, width=0)