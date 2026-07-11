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
    /* Paleta de cores: azul/cinza acadêmico */
    :root {
        --primary-color: #1e3a8a;
        --secondary-color: #3b82f6;
        --accent-color: #fbbf24;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --bg-light: #f9fafb;
        --border-color: #e5e7eb;
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
        background-color: #f3f4f6;
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
        background-color: var(--secondary-color);
        box-shadow: 0 4px 6px rgba(30, 58, 138, 0.15);
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
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1);
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
        background-color: #f3f4f6;
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
        color: var(--primary-color);
        font-weight: 600;
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


def get_color_scheme() -> dict:
    """
    Retorna o esquema de cores usado na aplicação.
    
    Returns:
        Dicionário com variáveis de cor
    """
    return {
        'primary': '#1e3a8a',
        'secondary': '#3b82f6',
        'accent': '#fbbf24',
        'success': '#10b981',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'info': '#0ea5e9',
        'text_primary': '#1f2937',
        'text_secondary': '#6b7280',
        'bg_light': '#f9fafb',
        'border': '#e5e7eb',
    }
