from clients.PostgreSqlManager import PostgreSqlManager
from streamlit_folium import st_folium
from services.utils import page_setup
from datetime import datetime
import streamlit as st
import pandas as pd
import psycopg2
import folium
import os

page_setup(page_name="home")

if not st.session_state.get("logged_in", False):
    st.error("Precisa de iniciar sessão para aceder a esta página.")
    st.switch_page("pages/login.py")
    st.stop()

# Inicializa o modo de visualização no estado da sessão, se não existir
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "mapa"

user_info = st.session_state.get("user_info", {})
with st.sidebar:
    st.title(f"Bem-vindo(a), {user_info.get('nome', 'Utilizador').split()[0]}!")
    st.divider()

    # Botões para alternar a visualização
    if st.button("Mapa de eventos", use_container_width=True):
        st.session_state.view_mode = "mapa"
    if st.button("Lista de eventos", use_container_width=True):
        st.session_state.view_mode = "lista"
    if st.button("Perfil", use_container_width=True):
        st.session_state.view_mode = "perfil"

# --- Lógica de Base de Dados ---
db_manager = PostgreSqlManager()

@st.cache_data(ttl=30)
def fetch_eventos_from_db(filter_date):
    """Busca e formata os eventos da base de dados."""
    query = """
        SELECT
            e.id_evento,
            e.titulo,
            c.nome AS categoria,
            en.latitude AS lat,
            e.horario,
            en.longitude AS lon,
            (SELECT COUNT(*) FROM participacao p WHERE p.idevento = e.id_evento) AS participantes
        FROM evento e
        JOIN categoria c ON e.idcategoria = c.id_categoria
        JOIN local l ON e.idlocal = l.id_local
        JOIN endereco en ON l.idendereco = en.id_endereco
        WHERE e.data = %s;
    """
    try:
        eventos_df = db_manager.execute_query(query, params=(filter_date,))
        return eventos_df.to_dict('records')
    except Exception as e:
        st.error(f"Erro ao procurar eventos: {e}")
        return []

@st.cache_data(ttl=3600)
def fetch_form_data():
    """Busca dados para preencher os formulários (categorias, publicos, locais)."""
    try:
        categorias_df = db_manager.execute_query("SELECT id_categoria, nome FROM categoria")
        publicos_df = db_manager.execute_query("SELECT id_publico, nome FROM publico_alvo")
        departamentos_df = db_manager.execute_query("SELECT id_departamento, nome FROM departamento")
        tipos_usuario_df = db_manager.execute_query("SELECT id_tipo_usuario, nome FROM tipo_usuario")
        locais_df = db_manager.execute_query("SELECT id_local, nome FROM local")
        return categorias_df, publicos_df, departamentos_df, tipos_usuario_df, locais_df
    except Exception as e:
        st.error(f"Erro ao carregar dados do formulário: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=30)
def fetch_event_details(event_id):
    """Busca os detalhes completos de um evento específico."""
    query = """
        SELECT
            e.titulo,
            e.descricao,
            e.horario,
            en.referencia
        FROM evento e
        JOIN local l ON e.idlocal = l.id_local
        JOIN endereco en ON l.idendereco = en.id_endereco
        WHERE e.id_evento = %s;
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
    st.subheader(event_details['titulo'])
    st.write(f"**Descrição:** {event_details['descricao']}")
    st.write(f"**Ponto de Referência:** {event_details['referencia']}")
    st.write(f"**Horário:** {event_details['horario'].strftime('%H:%M')}")
    
    if st.button("Participar", use_container_width=True):
        try:
            # Verifica se o utilizador já participa
            check_query = "SELECT 1 FROM participacao WHERE idusuario = %s AND idevento = %s"
            already_participating = not db_manager.execute_query(check_query, params=(user_info['cpf'], event_id)).empty

            if already_participating:
                st.warning(f"Já está a participar de '{event_details['titulo']}'.")
            else:
                participacao_df = pd.DataFrame([{
                    "idusuario": user_info['cpf'],
                    "idevento": event_id,
                    "data_inscricao": datetime.now().date()
                }])
                db_manager.insert_data_into_table(participacao_df, "participacao")
                st.success(f"Presença confirmada em '{event_details['titulo']}'!")
                st.cache_data.clear() # Limpa a cache para forçar a releitura dos dados
        except psycopg2.Error as e:
            st.error(f"Erro ao registar participação: {e}")

# Busca os dados que podem ser usados em múltiplas visualizações (mapa, perfil)
categorias_df, publicos_df, departamentos_df, tipos_usuario_df, locais_df = fetch_form_data()

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
    st.write("📍 Explore os eventos no mapa e crie novos abaixo")

    # Volta ao mapa geográfico real focado estritamente na UnB
    m = folium.Map(
        location=[UNB_LAT, UNB_LON], 
        zoom_start=15, 
        min_zoom=15, 
        max_zoom=18,
        max_bounds=True, 
        min_lat=-15.7720, 
        max_lat=-15.7530, 
        min_lon=-47.8820, 
        max_lon=-47.8550
        # A linha tiles="CartoDB positron" foi removida para voltar ao mapa detalhado!
    )

    for ev in eventos:
        cor = "blue"
        if ev["categoria"] == "HH": cor = "orange"
        elif ev["categoria"] == "Esporte": cor = "green"
        elif ev["categoria"] == "Game": cor = "purple"

        folium.Marker(
            [ev["lat"], ev["lon"]],
            tooltip=ev["titulo"],
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

    # --- Painel de Ações (Criar Evento Engatilhado) ---
    st.subheader("✨ Criar Novo Evento")
    with st.form("form_novo_evento", clear_on_submit=True):
        categorias_map = {row['nome']: row['id_categoria'] for _, row in categorias_df.iterrows()}
        publicos_map = {row['nome']: row['id_publico'] for _, row in publicos_df.iterrows()}
        locais_map = {row['nome']: row['id_local'] for _, row in locais_df.iterrows()}
        
        # Menu SelectBox a puxar da Base de Dados
        local_selecionado = st.selectbox("Selecione o Edifício/Local (já registados):", options=list(locais_map.keys()))
        
        col_sala, col_andar = st.columns(2)
        with col_sala:
            sala = st.text_input("Sala / Espaço", placeholder="Ex: Anfiteatro 9")
        with col_andar:
            andar = st.text_input("Andar", placeholder="Ex: Cave")
            
        novo_titulo = st.text_input("Nome do Evento", placeholder="Ex: Grupo de Estudos de BD")
        nova_desc_base = st.text_area("Descrição", placeholder="Detalhes sobre o evento...")
        
        col_data, col_hora = st.columns(2)
        with col_data: nova_data = st.date_input("Data do Evento", min_value=datetime.now().date())
        with col_hora: novo_horario = st.time_input("Horário do Evento")
        
        col_cat, col_pub = st.columns(2)
        with col_cat: nova_cat_nome = st.selectbox("Categoria", options=categorias_map.keys())
        with col_pub: novo_publico_nome = st.selectbox("Público-Alvo", options=publicos_map.keys())
        
        botao_salvar = st.form_submit_button("Publicar no Campus", use_container_width=True)
        
        if botao_salvar:
            if all([novo_titulo, nova_desc_base, nova_data, novo_horario, nova_cat_nome, novo_publico_nome]):
                try:
                    # Anexando sala e andar na descrição para não quebrar a base de dados atual
                    descricao_completa = f"{nova_desc_base}\n\n📍 Localização interna: {sala} - {andar}" if sala or andar else nova_desc_base
                    
                    novo_evento_df = pd.DataFrame([{
                        "idusuario": user_info['cpf'],
                        "idlocal": locais_map[local_selecionado],
                        "idpublico_alvo": publicos_map[novo_publico_nome],
                        "idcategoria": categorias_map[nova_cat_nome],
                        "titulo": novo_titulo,
                        "data": nova_data,
                        "horario": novo_horario,
                        "descricao": descricao_completa
                    }])
                    
                    db_manager.insert_data_into_table(novo_evento_df, "evento")
                    st.success(f"Evento criado com sucesso em {local_selecionado}! A página será atualizada.")
                    st.cache_data.clear(); st.rerun()
                except psycopg2.Error as e: 
                    st.error(f"Ocorreu um erro ao criar o evento: {e}")
            else: 
                st.warning("Por favor, preencha todos os campos do evento.")

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
            st.markdown(f"**{ev['titulo']}** | 🏷️ *{ev['categoria']}* — `{ev['participantes']} participantes`")
        with col_btn:
            if st.button("Detalhes", key=f"btn_details_{ev['id_evento']}", use_container_width=True):
                event_details = fetch_event_details(ev['id_evento'])
                if event_details:
                    show_event_dialog(event_details, ev['id_evento'])

elif st.session_state.view_mode == "perfil":
    st.header("O Meu Perfil")

    user_info = st.session_state.get("user_info", {})
    departamentos_map = {row['nome']: row['id_departamento'] for _, row in departamentos_df.iterrows()}
    tipos_usuario_map = {row['nome']: row['id_tipo_usuario'] for _, row in tipos_usuario_df.iterrows()}
    
    # Inverte os mapas para encontrar o nome a partir do ID
    id_to_departamento = {v: k for k, v in departamentos_map.items()}
    id_to_tipo_usuario = {v: k for k, v in tipos_usuario_map.items()}

    st.divider()
    with st.form("form_update_profile"):
        st.subheader("As Suas Informações")

        # Campos não editáveis
        st.text_input("CPF", value=user_info.get('cpf'), disabled=True)
        st.date_input("Data de Nascimento", value=user_info.get('data_nasc'), disabled=True)

        # Campos editáveis
        nome = st.text_input("Nome Completo", value=user_info.get('nome'))
        
        dep_atual_nome = id_to_departamento.get(user_info.get('iddepartamento'))
        dep_selecionado_nome = st.selectbox("Departamento", options=departamentos_map.keys(), index=list(departamentos_map.keys()).index(dep_atual_nome) if dep_atual_nome in departamentos_map else 0)

        tipo_atual_nome = id_to_tipo_usuario.get(user_info.get('idtipo_usuario'))
        tipo_selecionado_nome = st.selectbox("Tipo de Utilizador", options=tipos_usuario_map.keys(), index=list(tipos_usuario_map.keys()).index(tipo_atual_nome) if tipo_atual_nome in tipos_usuario_map else 0)

        st.subheader("Alterar Palavra-passe")
        nova_senha = st.text_input("Nova Palavra-passe (deixe em branco para não alterar)", type="password")
        confirma_nova_senha = st.text_input("Confirme a Nova Palavra-passe", type="password")

        botao_salvar = st.form_submit_button("Guardar Alterações", use_container_width=True)

        if botao_salvar:
            update_data = {
                "nome": nome,
                "iddepartamento": departamentos_map[dep_selecionado_nome],
                "idtipo_usuario": tipos_usuario_map[tipo_selecionado_nome]
            }

            if nova_senha:
                if nova_senha == confirma_nova_senha:
                    if len(nova_senha) >= 6:
                        update_data["senha"] = nova_senha
                    else:
                        st.error("A nova palavra-passe deve ter no mínimo 6 caracteres.")
                        st.stop()
                else:
                    st.error("As novas palavras-passe não coincidem.")
                    st.stop()
            
            try:
                db_manager.update_table("usuario", update_data, "cpf = %s", (user_info['cpf'],))
                st.success("Perfil atualizado com sucesso! Será redirecionado para a página de início de sessão.")
                
                # Limpa a sessão e redireciona para o login
                st.session_state.logged_in = False
                del st.session_state.user_info
                st.switch_page("pages/login.py")

            except psycopg2.Error as e:
                st.error(f"Ocorreu um erro ao atualizar o perfil: {e}")