from clients.PostgreSqlManager import PostgreSqlManager
from services.utils import page_setup
from streamlit_folium import st_folium
from datetime import datetime
import streamlit as st
import pandas as pd
import folium


page_setup()

if not st.session_state.get("logged_in", False):
    st.error("Você precisa estar logado para acessar esta página.")
    st.switch_page("pages/login.py")
    st.stop()

user_info = st.session_state.get("user_info", {})
st.title(f"Olá, {user_info.get('nome', 'Usuário').split()[0]}! 🎓")
st.markdown("### Mapa de Eventos - Campus Darcy Ribeiro (UnB)")

db_manager = PostgreSqlManager()

@st.cache_data(ttl=30)
def fetch_eventos_from_db():
    """Busca e formata os eventos do banco de dados."""
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
        JOIN endereco en ON l.idendereco = en.id_endereco;
    """
    try:
        eventos_df = db_manager.execute_query(query)
        return eventos_df.to_dict('records')
    except Exception as e:
        st.error(f"Erro ao buscar eventos: {e}")
        return []

@st.cache_data(ttl=3600)
def fetch_form_data():
    """Busca dados para preencher os formulários (categorias, publicos)."""
    try:
        categorias_df = db_manager.execute_query("SELECT id_categoria, nome FROM categoria")
        publicos_df = db_manager.execute_query("SELECT id_publico, nome FROM publico_alvo")
        return categorias_df, publicos_df
    except Exception as e:
        st.error(f"Erro ao carregar dados do formulário: {e}")
        return pd.DataFrame(), pd.DataFrame()

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
        st.error(f"Erro ao buscar detalhes do evento: {e}")
        return None

@st.dialog("Detalhes do Evento")
def show_event_dialog(event_details, event_id):
    """Exibe os detalhes de um evento em um diálogo nativo do Streamlit."""
    st.subheader(event_details['titulo'])
    st.write(f"**Descrição:** {event_details['descricao']}")
    st.write(f"**Ponto de Referência:** {event_details['referencia']}")
    st.write(f"**Horário:** {event_details['horario'].strftime('%H:%M')}")
    
    if st.button("Participar", use_container_width=True):
        try:
            # Verifica se o usuário já participa
            check_query = "SELECT 1 FROM participacao WHERE idusuario = %s AND idevento = %s"
            already_participating = not db_manager.execute_query(check_query, params=(user_info['cpf'], event_id)).empty

            if already_participating:
                st.warning(f"Você já está participando de '{event_details['titulo']}'.")
            else:
                participacao_df = pd.DataFrame([{
                    "idusuario": user_info['cpf'],
                    "idevento": event_id,
                    "data_inscricao": datetime.now().date()
                }])
                db_manager.insert_data_into_table(participacao_df, "participacao")
                st.success(f"Presença confirmada em '{event_details['titulo']}'!")
                st.cache_data.clear()
        except Exception as e:
            st.error(f"Erro ao registrar participação: {e}")

eventos = fetch_eventos_from_db()
categorias_df, publicos_df = fetch_form_data()

# Linha de Métricas Superiores
col_m1, col_m2, col_m3 = st.columns(3)
total_eventos = len(eventos)
total_participantes = sum(e["participantes"] for e in eventos)

with col_m1:
    st.metric(label="Eventos Ativos", value=total_eventos)
with col_m2:
    st.metric(label="Alunos Engajados", value=total_participantes)
with col_m3:
    st.metric(label="Localização", value="Darcy Ribeiro")

st.divider()

# Divisão da tela: Esquerda (Mapa) | Direita (Painel de Ações)
col_mapa, col_acoes = st.columns([2, 1])

# Coordenadas centrais da UnB (Darcy Ribeiro)
UNB_LAT, UNB_LON = -15.7635, -47.8708

with col_mapa:
    st.subheader("📍 Explore ou Clique no Mapa para Criar um Evento")

    m = folium.Map(
        location=[UNB_LAT, UNB_LON],
        zoom_start=15,
        min_zoom=14,
        max_zoom=18,
        max_bounds=True,
        min_lat=-15.7800, max_lat=-15.7500,
        min_lon=-47.8900, max_lon=-47.8500
    )

    for ev in eventos:
        cor = "blue"
        if ev["categoria"] == "HH": cor = "orange"
        elif ev["categoria"] == "Esporte": cor = "green"
        elif ev["categoria"] == "Game": cor = "purple"

        folium.Marker(
            [ev["lat"], ev["lon"]],
            # O popup foi removido para não aparecer no mapa. O tooltip no hover continua.
            tooltip=ev["titulo"],
            icon=folium.Icon(color=cor, icon="info-sign")
        ).add_to(m)

    mapa_interativo = st_folium(m, width="100%", height=500, key="unb_map")

# Captura as coordenadas do marcador clicado, em vez do popup
clicked_marker_coords = mapa_interativo.get("last_object_clicked")
if clicked_marker_coords:
    clicked_lat = clicked_marker_coords['lat']
    clicked_lon = clicked_marker_coords['lng']

    # Encontra o evento que corresponde às coordenadas clicadas
    selected_event = None
    for ev in eventos:
        if ev['lat'] == clicked_lat and ev['lon'] == clicked_lon:
            selected_event = ev
            break

    if selected_event:
        event_details = fetch_event_details(selected_event['id_evento'])
        if event_details:
            show_event_dialog(event_details, selected_event['id_evento'])

with col_acoes:
    coordenadas_clicadas = mapa_interativo.get("last_clicked")

    if coordenadas_clicadas:
        st.subheader("✨ Criar Novo Evento")
        st.info(f"Local selecionado:\nLat: {coordenadas_clicadas['lat']:.4f} | Lon: {coordenadas_clicadas['lng']:.4f}")

        with st.form("form_novo_evento", clear_on_submit=True):
            # Mapeia nome para id para inserção no banco
            categorias_map = {row['nome']: row['id_categoria'] for _, row in categorias_df.iterrows()}
            publicos_map = {row['nome']: row['id_publico'] for _, row in publicos_df.iterrows()}

            novo_titulo = st.text_input("Nome do Evento", placeholder="Ex: Grupo de Estudos de BD")
            nova_desc = st.text_area("Descrição", placeholder="Detalhes sobre o evento...")
            nova_referencia = st.text_input("Ponto de Referência", placeholder="Ex: Em frente à entrada da BCE")
            novo_horario = st.time_input("Horário do Evento")
            nova_cat_nome = st.selectbox("Categoria", options=categorias_map.keys())
            novo_publico_nome = st.selectbox("Público-Alvo", options=publicos_map.keys())

            botao_salvar = st.form_submit_button("Publicar no Campus", use_container_width=True)

            if botao_salvar and all([novo_titulo, nova_desc, nova_referencia, novo_horario, nova_cat_nome, novo_publico_nome]):
                try:
                    # 1. Inserir endereço e obter o ID
                    endereco_df = pd.DataFrame([{
                        "referencia": nova_referencia,
                        "latitude": coordenadas_clicadas['lat'],
                        "longitude": coordenadas_clicadas['lng']
                    }])
                    db_manager.insert_data_into_table(endereco_df, "endereco")
                    id_endereco = db_manager.execute_query("SELECT MAX(id_endereco) as id FROM endereco").iloc[0]['id']

                    # 2. Inserir local e obter o ID
                    local_df = pd.DataFrame([{"idendereco": id_endereco, "nome": novo_titulo}])
                    db_manager.insert_data_into_table(local_df, "local")
                    id_local = db_manager.execute_query("SELECT MAX(id_local) as id FROM local").iloc[0]['id']

                    # 3. Inserir o evento
                    evento_df = pd.DataFrame([{
                        "idusuario": user_info['cpf'],
                        "idlocal": id_local,
                        "idpublico_alvo": publicos_map[novo_publico_nome],
                        "idcategoria": categorias_map[nova_cat_nome],
                        "titulo": novo_titulo,
                        "data": datetime.now().date(),
                        "horario": novo_horario,
                        "descricao": nova_desc
                    }])
                    db_manager.insert_data_into_table(evento_df, "evento")

                    st.success("Evento criado com sucesso! O mapa será atualizado.")
                    st.cache_data.clear() # Limpa o cache para forçar a releitura dos dados
                    st.rerun()

                except Exception as e:
                    st.error(f"Ocorreu um erro ao criar o evento: {e}")
            elif botao_salvar:
                st.warning("Por favor, preencha todos os campos do evento.")
    else:
        st.subheader("ℹ️ Como funciona?")
        st.markdown("""
        1.  Navegue pelo mapa do campus Darcy Ribeiro.
        2.  Clique em qualquer local para abrir o formulário de criação.
        3.  Use a lista abaixo para confirmar sua presença nos eventos!
        """)

st.divider()

st.subheader("📅 Lista de Eventos")

if not eventos:
    st.info("Nenhum evento ativo no momento. Que tal criar o primeiro?")

for ev in eventos:
    col_info, col_btn = st.columns([4, 1])
    with col_info:
        st.markdown(f"**{ev['titulo']}** | 🏷️ *{ev['categoria']}* — `{ev['participantes'] + 1} participantes`")
    with col_btn:
        if st.button("Participar", key=f"btn_part_{ev['id_evento']}", use_container_width=True):
            try:
                # Verifica se o usuário já participa
                check_query = "SELECT 1 FROM participacao WHERE idusuario = %s AND idevento = %s"
                already_participating = not db_manager.execute_query(check_query, params=(user_info['cpf'], ev['id_evento'])).empty

                if already_participating:
                    st.warning(f"Você já está participando de '{ev['titulo']}'.")
                else:
                    participacao_df = pd.DataFrame([{
                        "idusuario": user_info['cpf'],
                        "idevento": ev['id_evento'],
                        "data_inscricao": datetime.now().date()
                    }])
                    db_manager.insert_data_into_table(participacao_df, "participacao")
                    st.success(f"Presença confirmada em '{ev['titulo']}'!")
                    st.cache_data.clear()
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao registrar participação: {e}")