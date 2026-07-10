# UniEvents

UniEvents é uma aplicação web desenvolvida com Streamlit e Python para o gerenciamento de eventos no campus universitário Darcy Ribeiro. A plataforma permite que os usuários visualizem, criem e participem de eventos, promovendo a interação dentro da comunidade acadêmica.

O arquivo de geração do banco de dados está em: [init.sql](src/db/init.sql) (src/db/init.sql)

## Funcionalidades

- **Gerenciamento de Perfil**: Usuários podem atualizar suas informações pessoais, foto de perfil e senha.
- **Visualização de Eventos**:
  - **Mapa Interativo**: Eventos são exibidos em um mapa (usando Folium) com base em sua localização geográfica.
  - **Listagem**: Uma visão alternativa em formato de lista, filtrada por data.
- **Criação de Eventos**: Usuários podem criar novos eventos clicando diretamente no mapa.
- **Participação e Interação**:
  - Confirmação de presença em eventos.
  - Sistema de comentários para cada evento.

## Tecnologias Utilizadas

- **Aplicação**: Python, Streamlit, Docker
- **Banco de Dados**: PostgreSQL
- **Visualização de Mapas**: Folium, streamlit-folium
- **Manipulação de Dados**: Pandas
- **Comunicação com BD**: psycopg2

## Estrutura do Projeto

O projeto está organizado da seguinte forma:

```
db-project-2026-1/
├── src/
│   ├── clients/
│   │   └── PostgreSqlManager.py  # Classe para gerenciar a conexão e operações com o BD que está no Docker.
│   ├── config/
│   │   └── .env                  # Arquivo para variáveis de ambiente (credenciais do BD).
│   ├── db/
│   │   └── init.sql              # Script SQL para inicialização do banco de dados (tabelas, views, etc.).
│   ├── pages/
│   │   ├── home.py               # Página principal da aplicação (mapa, lista, perfil).
│   │   └── login.py              # Página de login e registro.
│   ├── services/
│   │   └── utils.py              # Funções utilitárias (configuração de página).
│   └── styles/                   # Estilizações das páginas e geral.
│       ├── common.css
│       ├── home.css
│       └── login.css
├── requirements.txt              # Dependências do projeto.
└── README.md
```

## Configuração e Execução

Siga os passos abaixo para configurar e executar o projeto localmente.

1.  Tenha o Docker instalado e inicializado em sua máquina.
2.  Rode o seguinte comando bash na raiz do projeto:
    ```sh
    docker compose down -v
    docker compose up --build
    ```
3.  Acesse seu LOCALHOST na porta 8501. http://localhost:8501/