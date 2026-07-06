from clients.PostgreSqlManager import PostgreSqlManager
from streamlit_folium import st_folium
from services.utils import page_setup
from datetime import datetime
import streamlit as st
import pandas as pd
import psycopg2
import folium


page_setup(page_name="home")

if not st.session_state.get("logged_in", False):
    st.error("Precisa de iniciar sessão para aceder a esta página.")
    st.switch_page("pages/login.py")
    st.stop()

# Inicializa o modo de visualização no estado da sessão, se não existir
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "mapa"

# Inicializa o estado para controlar o diálogo do evento
if "show_event_dialog_id" not in st.session_state:
    st.session_state.show_event_dialog_id = None

# Novo estado para rastrear o último clique processado e evitar reaberturas
if "last_processed_click" not in st.session_state:
    st.session_state.last_processed_click = None

# Novo estado para controlar o scroll automático ao criar um evento
if "last_map_create_click" not in st.session_state:
    st.session_state.last_map_create_click = None

# Flag para controlar a execução do script de scroll
if "scroll_to_form" not in st.session_state:
    st.session_state.scroll_to_form = False

user_info = st.session_state.get("user_info", {})
with st.sidebar:
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

    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.divider()
    if st.button("Logout ⏻", help="Sair da Conta", key="logout_button", use_container_width=True):
        st.session_state.logged_in = False
        if "user_info" in st.session_state:
            del st.session_state.user_info
        st.switch_page("pages/login.py")


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
        SELECT
            e.titulo,
            e.descricao,
            e.horario,
            e.data,
            u.nome AS nome_organizador,
            e.idusuario,
            e.idcategoria,
            e.idpublico_alvo,
            en.referencia
        FROM evento e
        JOIN local l ON e.idlocal = l.id_local
        JOIN endereco en ON l.idendereco = en.id_endereco
        JOIN usuario u ON e.idusuario = u.cpf
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

@st.cache_data(ttl=15)
def fetch_event_comments(event_id):
    """Busca os comentários de um evento, juntando o nome do autor."""
    query = """
        SELECT
            c.texto,
            u.nome AS autor
        FROM comentario c
        JOIN usuario u ON c.idusuario = u.cpf
        WHERE c.idevento = %s
        ORDER BY c.id_comentario ASC;
    """
    try:
        comments_df = db_manager.execute_query(query, params=(event_id,))
        return comments_df.to_dict('records')
    except Exception as e:
        st.error(f"Erro ao carregar comentários: {e}")
        return []

@st.dialog("Detalhes do Evento")
def show_event_dialog(event_details, event_id):
    """Exibe os detalhes de um evento num diálogo nativo do Streamlit."""
    # Verifica se o usuário atual é o criador do evento
    is_owner = event_details['idusuario'] == user_info['cpf']

    # Define as abas a serem exibidas
    tab_titles = ["Informações", "Comentários"]
    if is_owner:
        tab_titles.append("Gerenciar Evento")
    
    tabs = st.tabs(tab_titles)
    tab_info = tabs[0]
    tab_comments = tabs[1]
    tab_edit = tabs[2] if is_owner else None
    
    with tab_info:
        st.subheader(event_details['titulo'])
        st.write(f"**Organizador(a):** {event_details['nome_organizador']}")
        st.write(f"**Descrição:** {event_details['descricao']}")
        st.write(f"**Ponto de Referência:** {event_details['referencia']}")
        st.write(f"**Data:** {event_details['data'].strftime('%d/%m/%Y')} às {event_details['horario'].strftime('%H:%M')}")
        
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

    with tab_comments:
        st.subheader("💬 Comentários")
        comments = fetch_event_comments(event_id)
        
        # Área para exibir comentários existentes
        with st.container(height=200):
            if not comments:
                st.info("Ainda não há comentários. Seja o primeiro a comentar!")
            for comment in comments:
                st.markdown(f"**{comment['autor'].split()[0]}:** {comment['texto']}")
        
        st.divider()

        # Área para adicionar um novo comentário
        new_comment = st.text_area("Deixe seu comentário:", key=f"comment_input_{event_id}")
        if st.button("Comentar", key=f"comment_btn_{event_id}", use_container_width=True):
            if new_comment:
                comment_df = pd.DataFrame([{"idusuario": user_info['cpf'], "idevento": event_id, "texto": new_comment}])
                db_manager.insert_data_into_table(comment_df, "comentario")
                st.success("Comentário adicionado!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Escreva algo para comentar.")

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

                btn_salvar = st.form_submit_button("Salvar Alterações", use_container_width=True)
                
                if btn_salvar:
                    update_data = {
                        "titulo": edit_titulo,
                        "descricao": edit_desc,
                        "data": edit_data,
                        "horario": edit_horario,
                        "idcategoria": categorias_map[edit_cat],
                        "idpublico_alvo": publicos_map[edit_pub]
                    }
                    try:
                        db_manager.update_table("evento", update_data, "id_evento = %s", (event_id,))
                        st.success("Evento atualizado com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    except psycopg2.Error as e:
                        st.error(f"Erro ao atualizar o evento: {e}")

            st.divider()
            st.subheader("Exclusão de evento")
            if st.button("🚨 Excluir Evento", use_container_width=True):
                try:
                    # Precisamos apagar as dependências PRIMEIRO devido às Foreign Keys
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

        folium.Marker(
            [ev["lat"], ev["lon"]],
            tooltip=ev["titulo"],
            icon=folium.Icon(color=cor, icon="info-sign")
        ).add_to(m)

    mapa_interativo = st_folium(m, width="100%", height=500, key="unb_map")

    current_click = mapa_interativo.get("last_object_clicked")

    # Verifica se houve um clique NOVO e se ele é diferente do último que já processamos
    if current_click and current_click != st.session_state.last_processed_click:
        # Armazena o clique atual para que não seja processado novamente em um rerun
        st.session_state.last_processed_click = current_click
        
        clicked_lat, clicked_lon = current_click['lat'], current_click['lng']
        selected_event = next((ev for ev in eventos if ev['lat'] == clicked_lat and ev['lon'] == clicked_lon), None)
        if selected_event:
            # Define o ID do evento para ser exibido
            st.session_state.show_event_dialog_id = selected_event['id_evento']

    # Mostra o diálogo se um ID de evento estiver definido no estado da sessão
    if st.session_state.show_event_dialog_id:
        event_details = fetch_event_details(st.session_state.show_event_dialog_id)
        if event_details:
            show_event_dialog(event_details, st.session_state.show_event_dialog_id)
        st.session_state.show_event_dialog_id = None # Limpa o ID para que o diálogo não reabra sozinho
    
    st.divider()

    # --- Painel de Ações (Criar Evento ou Instruções) ---
    coordenadas_clicadas = mapa_interativo.get("last_clicked")

    # 1. Detecta um novo clique no mapa e define a flag para rolar a página
    if coordenadas_clicadas and coordenadas_clicadas != st.session_state.get("last_map_create_click"):
        st.session_state.last_map_create_click = coordenadas_clicadas
        st.session_state.scroll_to_form = True

    if coordenadas_clicadas:
        st.markdown("<div id='create-event-form-anchor'></div>", unsafe_allow_html=True)
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
            nova_cat_nome = st.selectbox("Categoria", options=categorias_map.keys())
            novo_publico_nome = st.selectbox("Público-Alvo", options=publicos_map.keys())
            botao_salvar = st.form_submit_button("Publicar no Campus", use_container_width=True)
            
            if botao_salvar:
                if all([novo_titulo, nova_desc, nova_referencia, nova_data, novo_horario, nova_cat_nome, novo_publico_nome]):
                    try:
                        # CORREÇÃO AQUI: Forçar explicitamente os tipos de dados para o Postgres não se confundir
                        params = [
                            str(novo_titulo),
                            str(nova_desc),
                            str(nova_referencia),
                            float(coordenadas_clicadas['lat']), # Assegura que é FLOAT
                            float(coordenadas_clicadas['lng']), # Assegura que é FLOAT
                            novo_horario,
                            nova_data,
                            str(user_info['cpf']),
                            int(publicos_map[novo_publico_nome]),
                            int(categorias_map[nova_cat_nome])
                        ]
                        
                        db_manager.call_procedure('create_full_event', params)
                        st.success("Evento criado com sucesso! O mapa será atualizado.")
                        st.cache_data.clear(); st.rerun()
                    except psycopg2.Error as e: 
                        st.error(f"Ocorreu um erro ao criar o evento: {e}")
                else: 
                    st.warning("Por favor, preencha todos os campos do evento.")
        
        # 2. Verifica a flag APÓS o formulário ser renderizado
        if st.session_state.scroll_to_form:
            # Injeta o JavaScript para rolar até a âncora
            st.components.v1.html(
                """
                <script>
                    document.getElementById('create-event-form-anchor').scrollIntoView({ behavior: 'smooth', block: 'start' });
                </script>
                """,
                height=0
            )
            st.session_state.scroll_to_form = False # 3. Reseta a flag
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
            st.markdown(f"**{ev['titulo']}** | 🏷️ *{ev['categoria']}* — `{ev['participantes']} participantes`")
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
    
    # Inverte os mapas para encontrar o nome a partir do ID
    id_to_departamento = {v: k for k, v in departamentos_map.items()}
    id_to_tipo_usuario = {v: k for k, v in tipos_usuario_map.items()}

    st.divider()
    with st.form("form_update_profile"):
        st.subheader("Dados Pessoais")

        # Campos não editáveis
        st.text_input("CPF", value=user_info.get('cpf'), disabled=True)
        st.date_input("Data de Nascimento", value=user_info.get('data_nasc'), disabled=True)

        # Campos editáveis
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
                
                # Limpa a sessão e redireciona para o login
                st.session_state.logged_in = False
                del st.session_state.user_info
                st.switch_page("pages/login.py")

            except psycopg2.Error as e:
                st.error(f"Ocorreu um erro ao atualizar o perfil: {e}")