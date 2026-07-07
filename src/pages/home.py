from clients.PostgreSqlManager import PostgreSqlManager
from streamlit_folium import st_folium
from services.utils import page_setup
from datetime import datetime
import streamlit as st
import pandas as pd
import psycopg2
import folium
import base64


page_setup(page_name="home")

if not st.session_state.get("logged_in", False):
    st.error("Precisa de iniciar sessão para aceder a esta página.")
    st.switch_page("pages/login.py")
    st.stop()

# Inicializa o modo de visualização no estado da sessão, se não existir
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "mapa"

# Novo estado para rastrear o último clique processado e evitar reaberturas
if "last_processed_click" not in st.session_state:
    st.session_state.last_processed_click = None

# Novo estado para controlar o scroll automático ao criar um evento
if "last_map_create_click" not in st.session_state:
    st.session_state.last_map_create_click = None

# Flag para controlar a execução do script de scroll
if "scroll_to_form" not in st.session_state:
    st.session_state.scroll_to_form = False

# Inicializa o ID do evento a ser mostrado no diálogo
if "show_event_dialog_id" not in st.session_state:
    st.session_state.show_event_dialog_id = None

user_info = st.session_state.get("user_info", {})
with st.sidebar:
    # Exibe a foto de perfil se ela existir
    if 'foto' in user_info and user_info['foto']:
        # Converte os bytes da imagem para base64
        b64_foto = base64.b64encode(user_info['foto']).decode()
        st.markdown(f"""
            <style>
            /* Reduz o espaçamento no topo da barra lateral para a foto subir */
            [data-testid="stSidebar"] > div:first-child {{
                padding-top: 1rem;
            }}
            .profile-pic-container {{
                display: flex;
                justify-content: center;
                margin-bottom: 1.5rem;
            }}
            .profile-pic {{
                width: 120px;
                height: 120px;
                border-radius: 50%;
                object-fit: cover;
                border: 4px solid #FF4D8D;
            }}
            </style>
            <div class="profile-pic-container">
                <img src="data:image/png;base64,{b64_foto}" class="profile-pic">
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="login-header">
        <h1 style="font-weight: bold;">
            Bem-vindo(a),
            <span style="color: #FF4D8D; font-weight: bold;">
                {user_info.get('nome', 'Utilizador').split()[0]}
            </span>!
        </h1>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # Botões para alternar a visualização
    if st.button("Mapa de eventos", use_container_width=True):
        st.session_state.view_mode = "mapa"
    if st.button("Lista de eventos", use_container_width=True):
        st.session_state.view_mode = "lista"
    if st.button("Perfil", use_container_width=True):
        st.session_state.view_mode = "perfil"

    if st.button("Logout ⏻", help="Sair da Conta", key="logout_button", use_container_width=True):
        st.session_state.logged_in = False
        if "user_info" in st.session_state:
            del st.session_state.user_info
        st.switch_page("pages/login.py")


# --- Lógica de Banco de Dados ---
db_manager = PostgreSqlManager()

@st.cache_data(ttl=30)
def fetch_eventos_from_db(filter_date):
    """Busca e formata os eventos da base de dados."""
    query = """
        SELECT
            id_evento,
            titulo,
            categoria_nome AS categoria,
            latitude AS lat,
            horario,
            longitude AS lon,
            participantes,
            limite_participantes
        FROM vw_eventos_detalhados
        WHERE data = %s;
    """
    try:
        eventos_df = db_manager.execute_query(query, params=(filter_date,))
        return eventos_df.to_dict('records')
    except Exception as e:
        st.error(f"Erro ao procurar eventos: {e}")
        return []

@st.cache_data(ttl=3600)
def fetch_form_data():
    """Busca dados para preencher os formulários (categorias, publicos)."""
    try:
        categorias_df = db_manager.execute_query("SELECT id_categoria, nome FROM categoria")
        publicos_df = db_manager.execute_query("SELECT id_publico, nome FROM publico_alvo")
        departamentos_df = db_manager.execute_query("SELECT id_departamento, nome FROM departamento")
        tipos_usuario_df = db_manager.execute_query("SELECT id_tipo_usuario, nome FROM tipo_usuario")
        return categorias_df, publicos_df, departamentos_df, tipos_usuario_df
    except Exception as e:
        st.error(f"Erro ao carregar dados do formulário: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=30)
def fetch_event_details(event_id):
    """Busca os detalhes completos de um evento específico."""
    query = """
        SELECT *
        FROM vw_eventos_detalhados
        WHERE id_evento = %s;
    """
    try:
        details_df = db_manager.execute_query(query, params=(event_id,))
        if not details_df.empty:
            return details_df.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Erro ao procurar detalhes do evento: {e}")
        return None

@st.dialog("Detalhes do Evento")
def show_event_dialog(event_details, event_id):
    """Exibe os detalhes de um evento num diálogo nativo do Streamlit."""
    is_owner = event_details['idusuario'] == user_info['cpf']

    if is_owner:
        tab_info, tab_edit = st.tabs(["Informações", "Gerenciar Evento"])
    else:
        tab_info = st.container()
        tab_edit = None

    with tab_info:
        st.subheader(event_details['titulo'])
        # A usar dados trazidos da nova View do SQL
        st.write(f"**Organizador(a):** {event_details['nome_organizador']}")
        st.write(f"**Descrição:** {event_details['descricao']}")
        st.write(f"**Ponto de Referência:** {event_details['referencia']}")
        st.write(f"**Categoria:** {event_details['categoria_nome']}")
        st.write(f"**Data:** {event_details['data'].strftime('%d/%m/%Y')} às {event_details['horario'].strftime('%H:%M')}")
        
        # --- Lógica do Limite de Participantes e Inscrição ---
        participantes_atuais = event_details['participantes']
        limite = event_details['limite_participantes']
        st.markdown(f"**Vagas Ocupadas:** `{participantes_atuais}` de `{limite}`")
        st.progress(min(participantes_atuais / limite, 1.0))

        check_query = "SELECT 1 FROM participacao WHERE idusuario = %s AND idevento = %s"
        already_participating = not db_manager.execute_query(check_query, params=(user_info['cpf'], event_id)).empty

        if already_participating:
            st.success("✅ A sua presença está confirmada neste evento!")
            # Criador não pode abandonar o próprio evento, só outros utilizadores
            if not is_owner:
                if st.button("Cancelar Inscrição", use_container_width=True):
                    try:
                        conn = db_manager.connect_to_db()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM participacao WHERE idusuario = %s AND idevento = %s", (user_info['cpf'], event_id))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao sair do evento: {e}")
        elif participantes_atuais >= limite:
            st.error("🚨 O evento encontra-se lotado!")
            st.button("Participar", disabled=True, use_container_width=True)
        else:
            if st.button("Participar", use_container_width=True):
                try:
                    participacao_df = pd.DataFrame([{
                        "idusuario": user_info['cpf'],
                        "idevento": event_id,
                        "data_inscricao": datetime.now().date()
                    }])
                    db_manager.insert_data_into_table(participacao_df, "participacao")
                    st.success(f"Presença confirmada!")
                    st.cache_data.clear() 
                    st.rerun()
                except psycopg2.Error as e:
                    st.error(f"Erro ao registar participação: {e}")

    if tab_edit:
        with tab_edit:
            st.subheader("Editar Detalhes")
            with st.form(f"form_edit_{event_id}"):
                categorias_map = {row['nome']: row['id_categoria'] for _, row in categorias_df.iterrows()}
                publicos_map = {row['nome']: row['id_publico'] for _, row in publicos_df.iterrows()}
                
                id_to_cat = {v: k for k, v in categorias_map.items()}
                id_to_pub = {v: k for k, v in publicos_map.items()}

                cat_atual = id_to_cat.get(event_details['idcategoria'])
                pub_atual = id_to_pub.get(event_details['idpublico_alvo'])
                
                cat_index = list(categorias_map.keys()).index(cat_atual) if cat_atual in categorias_map else 0
                pub_index = list(publicos_map.keys()).index(pub_atual) if pub_atual in publicos_map else 0

                edit_titulo = st.text_input("Título", value=event_details['titulo'])
                edit_desc = st.text_area("Descrição", value=event_details['descricao'])
                
                col1, col2 = st.columns(2)
                with col1: edit_data = st.date_input("Data", value=event_details['data'])
                with col2: edit_horario = st.time_input("Horário", value=event_details['horario'])
                
                col3, col4 = st.columns(2)
                with col3: edit_cat = st.selectbox("Categoria", options=list(categorias_map.keys()), index=cat_index)
                with col4: edit_pub = st.selectbox("Público-Alvo", options=list(publicos_map.keys()), index=pub_index)

                # Novo campo para atualizar capacidade
                edit_capacidade = st.number_input("Limite de Participantes", min_value=1, max_value=5000, value=event_details['limite_participantes'])

                btn_salvar = st.form_submit_button("Salvar Alterações", use_container_width=True)
                
                if btn_salvar:
                    if edit_capacidade < event_details['participantes']:
                        st.error("O limite não pode ser menor que o número atual de participantes inscritos.")
                    else:
                        update_data = {
                            "titulo": edit_titulo,
                            "descricao": edit_desc,
                            "data": edit_data,
                            "horario": edit_horario,
                            "idcategoria": categorias_map[edit_cat],
                            "idpublico_alvo": publicos_map[edit_pub],
                            "limite_participantes": edit_capacidade
                        }
                        try:
                            db_manager.update_table("evento", update_data, "id_evento = %s", (event_id,))
                            st.success("Evento atualizado com sucesso!")
                            st.cache_data.clear()
                            st.rerun()
                        except psycopg2.Error as e:
                            st.error(f"Erro ao atualizar o evento: {e}")

            st.divider()
            st.subheader("Exclusão de Evento")
            if st.button("🚨 Excluir Evento", use_container_width=True):
                try:
                    db_manager.execute_non_query("DELETE FROM participacao WHERE idevento = %s", (event_id,))
                    db_manager.execute_non_query("DELETE FROM comentario WHERE idevento = %s", (event_id,))
                    db_manager.delete_rows_by_condition("evento", "id_evento", event_id)
                    
                    st.success("Evento excluído com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                except psycopg2.Error as e:
                    st.error(f"Erro ao excluir o evento: {e}")

# Busca os dados que podem ser usados em múltiplas visualizações (mapa, perfil)
categorias_df, publicos_df, departamentos_df, tipos_usuario_df = fetch_form_data()

# --- Renderização Condicional da Página ---

if st.session_state.view_mode == "mapa":
    st.title("UniEvents - Darcy Ribeiro")

    selected_date = st.date_input(
        "Data dos eventos",
        value=datetime.now().date(),
        key="date_filter_map"
    )
    eventos = fetch_eventos_from_db(selected_date)

    UNB_LAT, UNB_LON = -15.7635, -47.8708

    # --- Renderização do Mapa ---
    st.write("📍 Explore ou Clique no Mapa para Criar um Evento")

    m = folium.Map(
        location=[UNB_LAT, UNB_LON], zoom_start=15, min_zoom=14, max_zoom=18,
        max_bounds=True, min_lat=-15.7800, max_lat=-15.7500, min_lon=-47.8900, max_lon=-47.8500
    )

    for ev in eventos:
        cor = "blue"
        if ev["categoria"] == "HH": cor = "orange"
        elif ev["categoria"] == "Esporte": cor = "green"
        elif ev["categoria"] == "Game": cor = "purple"
        
        if ev["participantes"] >= ev["limite_participantes"]: 
            cor = "red" # Fica vermelho se lotar!

        folium.Marker(
            [ev["lat"], ev["lon"]],
            tooltip=ev["titulo"] + (" (LOTADO)" if ev["participantes"] >= ev["limite_participantes"] else ""),
            icon=folium.Icon(color=cor, icon="info-sign")
        ).add_to(m)

    mapa_interativo = st_folium(m, width="100%", height=500, key="unb_map")

    clicked_marker_coords = mapa_interativo.get("last_object_clicked")

    if clicked_marker_coords:
        clicked_lat, clicked_lon = clicked_marker_coords['lat'], clicked_marker_coords['lng']
        selected_event = next((ev for ev in eventos if ev['lat'] == clicked_lat and ev['lon'] == clicked_lon), None)
        if selected_event:
            event_details = fetch_event_details(selected_event['id_evento'])
            if event_details:
                show_event_dialog(event_details, selected_event['id_evento'])

    st.divider()

    # --- Painel de Ações (Criar Evento ou Instruções) ---
    coordenadas_clicadas = mapa_interativo.get("last_clicked")

    if coordenadas_clicadas:
        st.subheader("✨ Criar Novo Evento")
        st.info(f"Local selecionado: Lat: {coordenadas_clicadas['lat']:.4f} | Lon: {coordenadas_clicadas['lng']:.4f}")
        with st.form("form_novo_evento", clear_on_submit=True):
            categorias_map = {row['nome']: row['id_categoria'] for _, row in categorias_df.iterrows()}
            publicos_map = {row['nome']: row['id_publico'] for _, row in publicos_df.iterrows()}
            novo_titulo = st.text_input("Nome do Evento", placeholder="Ex: Grupo de Estudos de BD")
            nova_desc = st.text_area("Descrição", placeholder="Detalhes sobre o evento...")
            nova_referencia = st.text_input("Ponto de Referência", placeholder="Ex: Em frente à entrada da BCE")
            
            col_data, col_hora = st.columns(2)
            with col_data: nova_data = st.date_input("Data do Evento", min_value=datetime.now().date())
            with col_hora: novo_horario = st.time_input("Horário do Evento")
            
            col_cat, col_pub = st.columns(2)
            with col_cat: nova_cat_nome = st.selectbox("Categoria", options=categorias_map.keys())
            with col_pub: novo_publico_nome = st.selectbox("Público-Alvo", options=publicos_map.keys())
            
            # Adicionando o campo Limite de Vagas ao formulário
            nova_capacidade = st.number_input("Limite de Participantes (Vagas)", min_value=1, max_value=5000, value=20, help="Quantas pessoas podem participar deste evento?")

            botao_salvar = st.form_submit_button("Publicar no Campus", use_container_width=True)
            
            if botao_salvar:
                if all([novo_titulo, nova_desc, nova_referencia, nova_data, novo_horario, nova_cat_nome, novo_publico_nome]):
                    try:
                        params = [
                            str(novo_titulo),
                            str(nova_desc),
                            str(nova_referencia),
                            float(coordenadas_clicadas['lat']),
                            float(coordenadas_clicadas['lng']),
                            novo_horario,
                            nova_data,
                            str(user_info['cpf']),
                            int(publicos_map[novo_publico_nome]),
                            int(categorias_map[nova_cat_nome]),
                            int(nova_capacidade) # Novo parâmetro exigido pelo backend
                        ]
                        
                        db_manager.call_procedure('create_full_event', params)
                        st.success("Evento criado com sucesso! O seu utilizador já foi inscrito automaticamente.")
                        st.cache_data.clear(); st.rerun()
                    except psycopg2.Error as e: 
                        st.error(f"Ocorreu um erro ao criar o evento: {e}")
                else: 
                    st.warning("Por favor, preencha todos os campos do evento.")
    else:
        st.subheader("ℹ️ Como funciona?")
        st.markdown("1. Navegue pelo mapa.\n2. Clique em qualquer local para criar um evento.\n3. Preencha os detalhes do evento.\n4.Clique no ícone de algum evento para ver os detalhes.\n5. Use o botão **'Lista de eventos'** na barra lateral para visualizar fora do mapa.")

elif st.session_state.view_mode == "lista":
    st.title("UniEvents - Darcy Ribeiro")

    selected_date = st.date_input(
        "Data dos eventos",
        value=datetime.now().date(),
        key="date_filter_list"
    )
    eventos = fetch_eventos_from_db(selected_date)

    st.divider()

    if not eventos: 
        st.info("Nenhum evento ativo para esta data. Que tal criar o primeiro no mapa?")

    for ev in eventos:
        col_info, col_btn = st.columns([4, 1])
        with col_info:
            lotado_tag = "🔴 LOTADO" if ev['participantes'] >= ev['limite_participantes'] else f"`{ev['participantes']}/{ev['limite_participantes']} vagas`"
            st.markdown(f"**{ev['titulo']}** | 🏷️ *{ev['categoria']}* — {lotado_tag}")
        with col_btn:
            if st.button("Detalhes", key=f"btn_details_{ev['id_evento']}", use_container_width=True):
                event_details = fetch_event_details(ev['id_evento'])
                if event_details:
                    show_event_dialog(event_details, ev['id_evento'])

elif st.session_state.view_mode == "perfil":
    st.header("Meu Perfil")

    user_info = st.session_state.get("user_info", {})
    departamentos_map = {row['nome']: row['id_departamento'] for _, row in departamentos_df.iterrows()}
    tipos_usuario_map = {row['nome']: row['id_tipo_usuario'] for _, row in tipos_usuario_df.iterrows()}
    
    id_to_departamento = {v: k for k, v in departamentos_map.items()}
    id_to_tipo_usuario = {v: k for k, v in tipos_usuario_map.items()}

    st.divider()
    with st.form("form_update_profile"):
        st.subheader("Dados Pessoais")

        st.text_input("CPF", value=user_info.get('cpf'), disabled=True)
        st.date_input("Data de Nascimento", value=user_info.get('data_nasc'), disabled=True)
        nova_foto = st.file_uploader("Alterar Foto de Perfil (opcional)", type=['png', 'jpg', 'jpeg'])
        nome = st.text_input("Nome Completo", value=user_info.get('nome'))
        
        dep_atual_nome = id_to_departamento.get(user_info.get('iddepartamento'))
        dep_selecionado_nome = st.selectbox("Departamento", options=departamentos_map.keys(), index=list(departamentos_map.keys()).index(dep_atual_nome) if dep_atual_nome in departamentos_map else 0)

        tipo_atual_nome = id_to_tipo_usuario.get(user_info.get('idtipo_usuario'))
        tipo_selecionado_nome = st.selectbox("Tipo de Usuário", options=tipos_usuario_map.keys(), index=list(tipos_usuario_map.keys()).index(tipo_atual_nome) if tipo_atual_nome in tipos_usuario_map else 0)

        st.subheader("Alterar Senha")
        nova_senha = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password")
        confirma_nova_senha = st.text_input("Confirme a Nova Senha", type="password")

        botao_salvar = st.form_submit_button("Guardar Alterações", use_container_width=True)

        if botao_salvar:
            update_data = {
                "nome": nome,
                "iddepartamento": departamentos_map[dep_selecionado_nome],
                "idtipo_usuario": tipos_usuario_map[tipo_selecionado_nome]
            }

            if nova_foto:
                update_data["foto"] = nova_foto.getvalue()

            if nova_senha:
                if nova_senha == confirma_nova_senha:
                    if len(nova_senha) >= 6:
                        update_data["senha"] = nova_senha
                    else:
                        st.error("A nova senha deve ter no mínimo 6 caracteres.")
                        st.stop()
                else:
                    st.error("As novas palavras-passe não coincidem.")
                    st.stop()
            
            try:
                db_manager.update_table("usuario", update_data, "cpf = %s", (user_info['cpf'],))
                st.success("Perfil atualizado com sucesso! Será redirecionado para a página de início de sessão.")
                st.session_state.logged_in = False
                del st.session_state.user_info
                st.switch_page("pages/login.py")
            except psycopg2.Error as e:
                st.error(f"Ocorreu um erro ao atualizar o perfil: {e}")