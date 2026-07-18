"""
UI Manager - Gerencia estilos CSS e elementos de interface
Extraído de app.py para melhor organização e manutenção.
"""

import streamlit as st


def configure_page_style():
    """
    Configura o estilo visual da página com CSS personalizado.
    Deve ser chamado no início da aplicação, após st.set_page_config().
    """
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap');

    /* Paleta de cores: grafite/âmbar contemporâneo */
    :root {
        --primary-color: #2b2d33;
        --primary-hover: #45474e;
        --accent-color: #d97706;
        --accent-hover: #b45309;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --bg-light: #f4f4f2;
        --border-color: #ddd9d2;
    }

    /* Fonte e espaçamento base */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
    }

    /* Estilo de abas */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: 500;
        color: var(--text-secondary);
        background-color: transparent;
        border-bottom: 3px solid transparent;
    }

    .stTabs [data-baseweb="tab-list"] button:hover {
        color: var(--primary-color);
        border-bottom-color: var(--accent-color);
    }

    .stTabs [aria-selected="true"] {
        color: var(--primary-color);
        border-bottom-color: var(--primary-color) !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: var(--bg-light);
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }

    .streamlit-expanderHeader:hover {
        background-color: #eeece7;
    }

    /* Buttons */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: var(--primary-hover);
        box-shadow: 0 4px 6px rgba(217, 119, 6, 0.18);
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 10px 12px;
        font-size: 14px;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-color);
        box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.15);
    }

    /* Dataframe / Table */
    .streamlit-dataframe {
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }

    /* Metric boxes */
    .stMetric {
        background-color: var(--bg-light);
        border-radius: 8px;
        padding: 16px;
        border: 1px solid var(--border-color);
    }

    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: #eeece7;
    }

    /* Success/Error messages */
    .stSuccess {
        background-color: #d1fae5;
        color: #065f46;
        border-radius: 6px;
    }

    .stError {
        background-color: #fee2e2;
        color: #991b1b;
        border-radius: 6px;
    }

    .stWarning {
        background-color: #fef3c7;
        color: #92400e;
        border-radius: 6px;
    }

    /* Info message */
    .stInfo {
        background-color: #dbeafe;
        color: #0c2340;
        border-radius: 6px;
    }

    /* Headers */
    h1, h2, h3 {
        font-family: 'Source Serif 4', Georgia, 'Times New Roman', serif;
        color: var(--primary-color);
        font-weight: 600;
        letter-spacing: 0.015em;
    }

    /* Cabeçalho da sidebar — filete âmbar, efeito "cabeçalho de carta/documento" */
    section[data-testid="stSidebar"] h1 {
        border-bottom: 3px solid var(--accent-color);
        padding-bottom: 14px;
        margin-bottom: 4px;
    }

    /* Horizontal line */
    hr {
        border-color: var(--border-color);
    }

    /* Code blocks */
    .stCodeBlock {
        background-color: var(--bg-light);
        border: 1px solid var(--border-color);
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)


def show_academic_header():
    """
    Exibe o cabeçalho acadêmico da aplicação.
    """
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("📚")
    with col2:
        st.markdown("""
        ### Historicidades Democráticas
        **Plataforma de Análise de Documentos Históricos**
        
        Navegue, busque, anote e analise correspondência histórica constitucional.
        """)


def show_footer():
    """
    Exibe o rodapé da aplicação com informações e créditos.
    """
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("📖 Developed with Streamlit")
    with col2:
        st.caption("🔐 Data is stored locally")
    with col3:
        st.caption("✨ Research Platform")


def get_plotly_color_palette() -> list:
    """
    Retorna a paleta de cores para gráficos Plotly.
    Alinhada à paleta do programa (grafite/âmbar) com tons sóbrios.

    Returns:
        Lista de cores em formato hex para uso em color_discrete_sequence
    """
    return [
        '#d97706',  # Âmbar primário
        '#2b2d33',  # Grafite primário
        '#f59e0b',  # Âmbar claro
        '#92400e',  # Marrom âmbar escuro
        '#45474e',  # Grafite claro
        '#1f2937',  # Grafite escuro
        '#b45309',  # Âmbar hover
        '#5a5c63',  # Cinza-grafite
        '#dc2626',  # Vermelho sóbrio
        '#0369a1',  # Azul sóbrio
        '#65a30d',  # Verde sóbrio
        '#7c3aed',  # Roxo sóbrio
    ]


def get_color_scheme() -> dict:
    """
    Retorna o esquema de cores usado na aplicação.

    Returns:
        Dicionário com variáveis de cor
    """
    return {
        'primary': '#2b2d33',
        'primary_hover': '#45474e',
        'accent': '#d97706',
        'accent_hover': '#b45309',
        'success': '#10b981',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'info': '#0ea5e9',
        'text_primary': '#1f2937',
        'text_secondary': '#6b7280',
        'bg_light': '#f4f4f2',
        'border': '#ddd9d2',
    }
