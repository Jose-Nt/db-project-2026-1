import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import psycopg2
from psycopg2.extras import RealDictCursor


st.set_page_config(
    page_title="UniEvents | UnB",
    page_icon="🎓",
    layout="wide"
)

# Injeção de CSS para polir o layout do Streamlit
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container { padding-top: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

# conexão com o banco de dados PostgreSQL
def init_connection():
    try:
        return psycopg2.connect(
            host="db", 
            database="seu_banco",
            user="seu_usuario",
            password="sua_senha",
            port="5432"
        )
    except Exception as e:
        return None

conn = init_connection()

# Funções fictícias de banco para o protótipo rodar imediatamente
if "db_eventos" not in st.session_state:
    st.session_state.db_eventos = [
        {"id": 1, "titulo": "Revisão de Cálculo I", "categoria": "Estudos", "lat": -15.7635, "lon": -47.8703, "participantes": 15},
        {"id": 2, "titulo": "HH Aplicada", "categoria": "Social", "lat": -15.7612, "lon": -47.8690, "participantes": 42},
        {"id": 3, "titulo": "Futsal", "categoria": "Esportes", "lat": -15.7669, "lon": -47.8706, "participantes": 22}
    ]


st.title("UniEvents 🎓") 
st.markdown("### Mapa de Eventos - Campus Darcy Ribeiro (UnB)")

# Linha de Métricas Superiores
col_m1, col_m2, col_m3 = st.columns(3)
total_eventos = len(st.session_state.db_eventos)
total_participantes = sum(e["participantes"] for e in st.session_state.db_eventos)

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
    
    # Criando o mapa base usando Folium
    m = folium.Map(
        location=[UNB_LAT, UNB_LON], 
        zoom_start=15,
        min_zoom=14,
        max_zoom=18,
        max_bounds=True,
        # Limita o scroll do usuário apenas ao perímetro da UnB
        min_lat=-15.7800, max_lat=-15.7500,
        min_lon=-47.8900, max_lon=-47.8500
    )
    
    # Adicionando os marcadores dos eventos existentes vindos do "banco"
    for ev in st.session_state.db_eventos:
        # Define cores baseadas na categoria
        cor = "blue"
        if ev["categoria"] == "Social": cor = "orange"
        elif ev["categoria"] == "Esportes": cor = "green"
        elif ev["categoria"] == "Jogos": cor = "purple"
        
        folium.Marker(
            [ev["lat"], ev["lon"]],
            popup=f"<b>{ev['titulo']}</b><br>Participantes: {ev['participantes']}",
            tooltip=ev["titulo"],
            icon=folium.Icon(color=cor, icon="info-sign")
        ).add_to(m)
        
    # Renderiza o mapa no Streamlit e captura interações de clique
    mapa_interativo = st_folium(m, width="100%", height=500, key="unb_map")

# Painel de Ações (Criar ou Participar)
with col_acoes:
    # Captura se o usuário clicou em algum lugar vazio do mapa
    coordenadas_clicadas = mapa_interativo.get("last_clicked")
    
    if coordenadas_clicadas:
        st.subheader("✨ Criar Novo Evento")
        st.info(f"Local selecionado:\nLat: {coordenadas_clicadas['lat']:.4f} | Lon: {coordenadas_clicadas['lng']:.4f}")
        
        # Formulário de Criação
        with st.form("form_novo_evento", clear_on_submit=True):
            novo_titulo = st.text_input("Nome do Evento", placeholder="Ex: Grupo de Estudos de BD")
            nova_cat = st.selectbox("Categoria", ["Estudos", "Social", "Esportes", "Jogos"])
            
            botao_salvar = st.form_submit_button("Publicar no Campus", use_container_width=True)
            
            if botao_salvar and novo_titulo:
                # aqui entra o insert do usuario
                novo_id = len(st.session_state.db_eventos) + 1
                st.session_state.db_eventos.append({
                    "id": novo_id,
                    "titulo": novo_titulo,
                    "categoria": nova_cat,
                    "lat": coordenadas_clicadas["lat"],
                    "lon": coordenadas_clicadas["lng"],
                    "participantes": 1
                })
                st.success("Evento criado com sucesso! Atualizando mapa...")
                st.rerun()
    else:
        st.subheader("ℹ️ Como funciona?")
        st.markdown("""
        1. Navegue pelo mapa do campus Darcy Ribeiro.
        2. Clique em qualquer local (perto do ICC, BCE, etc.) para abrir o formulário de criação.
        3. Use a lista abaixo para confirmar sua presença nos eventos da turma!
        """)

st.divider()

# lista de eventos  
st.subheader("📅 Próximos Eventos e Inscrições")

# Exibe os eventos em formato de lista interativa
for idx, ev in enumerate(st.session_state.db_eventos):
    col_info, col_btn = st.columns([4, 1])
    
    with col_info:
        st.markdown(f"**{ev['titulo']}** | 🏷️ *{ev['categoria']}* — `{ev['participantes']} alunos confirmados`")
        
    with col_btn:
        # Botão dinâmico para simular a tabela "participacoes" do banco
        if st.button(f"Participar", key=f"btn_part_{ev['id']}", use_container_width=True):
            # AQUI ENTRA O INSERT das participacoes...'
            ev["participantes"] += 1
            st.success(f"Presença confirmada em '{ev['titulo']}'!")
            st.rerun()