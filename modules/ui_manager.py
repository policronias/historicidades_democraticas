"""
UI Manager - Gerencia estilos CSS e elementos de interface
Baseado no design profissional do QVR (Qualidade, Valor e Retorno)
"""

import streamlit as st


def configure_page_style():
    """
    Configura o estilo visual da página com CSS personalizado.
    Sistema de design responsivo baseado em tokens com prefers-color-scheme.
    Deve ser chamado no início da aplicação, após st.set_page_config().
    """
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap');

    /* ════════════════════════════════════════════════════════════
       TOKENS — Sistema de Design Responsivo
       ════════════════════════════════════════════════════════════ */
    :root {
        /* Tema Dark (padrão) — Inspirado em QVR */
        --ink: #0a0e13;
        --panel: #141b23;
        --panel-2: #1a242e;
        --line: #3a4d5c;
        --text: #f3efe3;
        --muted: #a9b6c2;
        --brass: #c99a5e;
        --brass-bright: #eec98a;
        --pass: #6fc191;
        --pass-bg: rgba(111, 193, 145, 0.16);
        --block: #e2727a;
        --block-bg: rgba(226, 114, 122, 0.16);
        --warn: #e8b563;

        /* Sombras profissionais */
        --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.35);
        --shadow-md: 0 6px 20px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 16px 40px rgba(0, 0, 0, 0.45);

        /* Tipografia */
        --serif: 'Source Serif 4', Georgia, 'Iowan Old Style', 'Palatino Linotype', Palatino, serif;
        --sans: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        --mono: 'IBM Plex Mono', 'SF Mono', SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace;

        /* Transições suaves */
        --transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Tema claro (detectado automaticamente) */
    @media (prefers-color-scheme: light) {
        :root {
            --ink: #f9fafb;
            --panel: #eeebe5;
            --panel-2: #e5e7eb;
            --line: #ddd9d2;
            --text: #1f2937;
            --muted: #6b7280;
            --brass: #c99a5e;
            --brass-bright: #a67c52;
            --pass: #6fc191;
            --block: #e2727a;
            --warn: #e8b563;
        }
    }

    /* Tema escuro (detectado automaticamente) */
    @media (prefers-color-scheme: dark) {
        :root {
            --ink: #0a0e13;
            --panel: #141b23;
            --panel-2: #1a242e;
            --line: #3a4d5c;
            --text: #f3efe3;
            --muted: #a9b6c2;
        }
    }

    /* Fonte e espaçamento base */
    body {
        font-family: var(--sans);
        line-height: 1.6;
        background: radial-gradient(ellipse 1200px 700px at 50% -10%, #172129 0%, var(--ink) 55%);
        color: var(--text);
    }

    @media (prefers-color-scheme: light) {
        body {
            background: linear-gradient(135deg, #f9fafb 0%, #eeebe5 100%);
        }
    }

    /* Respeitar preferência de movimento reduzido */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.001ms !important;
            transition-duration: 0.001ms !important;
        }
    }

    /* ════════════════════════════════════════════════════════════
       COMPONENTES — Estilo refinado com Glassmorphism
       ════════════════════════════════════════════════════════════ */

    /* Estilo de abas */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 13px;
        font-weight: 500;
        color: var(--muted);
        background-color: transparent;
        border-bottom: 2px solid transparent;
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
        transition: var(--transition);
    }

    .stTabs [data-baseweb="tab-list"] button:hover {
        color: var(--text);
        background: rgba(255, 255, 255, 0.05);
    }

    .stTabs [aria-selected="true"] {
        color: var(--brass-bright);
        border-bottom-color: var(--brass);
        background: rgba(201, 154, 94, 0.1);
    }

    /* Expanders — Glassmorphism */
    .streamlit-expanderHeader {
        background: rgba(20, 27, 35, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 8px;
        border: 1px solid var(--line);
        box-shadow: var(--shadow-sm);
        transition: var(--transition);
    }

    .streamlit-expanderHeader:hover {
        background: rgba(26, 36, 46, 0.8);
        border-color: var(--brass);
    }

    @media (prefers-color-scheme: light) {
        .streamlit-expanderHeader {
            background: rgba(238, 235, 229, 0.6);
        }
        .streamlit-expanderHeader:hover {
            background: rgba(229, 231, 235, 0.8);
        }
    }

    /* Buttons — Com elegância */
    .stButton > button {
        background: rgba(201, 154, 94, 0.2);
        color: var(--brass-bright);
        border: 1px solid var(--brass);
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
        font-family: var(--sans);
        font-size: 13px;
        transition: var(--transition);
        cursor: pointer;
    }

    .stButton > button:hover {
        background: rgba(201, 154, 94, 0.3);
        box-shadow: 0 0 0 2px rgba(201, 154, 94, 0.2);
    }

    .stButton > button:active {
        transform: scale(0.98);
    }

    /* Input fields — Glassmorphic */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: rgba(20, 27, 35, 0.4) !important;
        color: var(--text) !important;
        border: 1px solid var(--line) !important;
        border-radius: 6px !important;
        padding: 10px 12px !important;
        font-size: 13px !important;
        font-family: var(--sans) !important;
        transition: var(--transition) !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--brass) !important;
        box-shadow: 0 0 0 3px rgba(201, 154, 94, 0.2) !important;
        background: rgba(20, 27, 35, 0.6) !important;
    }

    @media (prefers-color-scheme: light) {
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {
            background: rgba(238, 235, 229, 0.4) !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > select:focus {
            background: rgba(238, 235, 229, 0.6) !important;
        }
    }

    /* Dataframe / Table */
    .streamlit-dataframe {
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: var(--shadow-sm);
    }

    /* Metric boxes — Cards elegantes */
    .stMetric {
        background: rgba(20, 27, 35, 0.4);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 16px;
        box-shadow: var(--shadow-sm);
        transition: var(--transition);
    }

    .stMetric:hover {
        background: rgba(26, 36, 46, 0.6);
        border-color: var(--brass);
    }

    @media (prefers-color-scheme: light) {
        .stMetric {
            background: rgba(238, 235, 229, 0.4);
        }
        .stMetric:hover {
            background: rgba(229, 231, 235, 0.6);
        }
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(10, 14, 19, 0.95) !important;
    }

    /* Mensagens semânticas — Com cores QVR */
    .stSuccess {
        background: var(--pass-bg);
        color: var(--pass);
        border-radius: 6px;
        border-left: 4px solid var(--pass);
        padding: 12px 16px;
    }

    .stError {
        background: var(--block-bg);
        color: var(--block);
        border-radius: 6px;
        border-left: 4px solid var(--block);
        padding: 12px 16px;
    }

    .stWarning {
        background: rgba(232, 181, 99, 0.16);
        color: var(--warn);
        border-radius: 6px;
        border-left: 4px solid var(--warn);
        padding: 12px 16px;
    }

    .stInfo {
        background: rgba(156, 163, 175, 0.1);
        color: var(--muted);
        border-radius: 6px;
        border-left: 4px solid var(--line);
        padding: 12px 16px;
    }

    /* Headers — Com tipografia caracterful */
    h1, h2, h3 {
        font-family: var(--serif);
        color: var(--text);
        font-weight: 600;
        letter-spacing: 0.015em;
        text-wrap: balance;
    }

    h1 {
        font-size: 32px;
        margin-top: 32px;
        margin-bottom: 16px;
    }

    h2 {
        font-size: 24px;
        margin-top: 24px;
        margin-bottom: 12px;
    }

    h3 {
        font-size: 18px;
        margin-top: 16px;
        margin-bottom: 8px;
    }

    /* Cabeçalho da sidebar — Efeito profissional */
    section[data-testid="stSidebar"] h1 {
        border-bottom: 2px solid var(--brass);
        padding-bottom: 12px;
        margin-bottom: 20px;
        color: var(--brass-bright);
        font-size: 16px;
    }

    /* Horizontal line */
    hr {
        border-color: var(--line);
        margin: 20px 0;
    }

    /* Code blocks — Monospace com estilo */
    .stCodeBlock {
        background: rgba(10, 14, 19, 0.8);
        border: 1px solid var(--line);
        border-radius: 6px;
        box-shadow: var(--shadow-md);
        font-family: var(--mono);
    }

    code {
        font-family: var(--mono);
        font-size: 12px;
        letter-spacing: 0.5px;
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
    Alinhada à paleta QVR (Brass/Dourado elegante + Acentos semânticos).

    Returns:
        Lista de cores em formato hex para uso em color_discrete_sequence
    """
    return [
        '#c99a5e',  # Brass primário
        '#eec98a',  # Brass bright
        '#6fc191',  # Pass/Green
        '#e2727a',  # Block/Red
        '#e8b563',  # Warn/Yellow
        '#a9b6c2',  # Muted
        '#3a4d5c',  # Line/Border
        '#c99a5e',  # Repeat brass
        '#6fc191',  # Repeat green
        '#e2727a',  # Repeat red
        '#e8b563',  # Repeat yellow
        '#a9b6c2',  # Repeat muted
    ]


def get_color_scheme() -> dict:
    """
    Retorna o esquema de cores profissional baseado em QVR.
    Sistema responsivo que se adapta a prefers-color-scheme.

    Returns:
        Dicionário com variáveis de cor (tema dark)
    """
    return {
        'ink': '#0a0e13',
        'panel': '#141b23',
        'panel_2': '#1a242e',
        'line': '#3a4d5c',
        'text': '#f3efe3',
        'muted': '#a9b6c2',
        'brass': '#c99a5e',
        'brass_bright': '#eec98a',
        'pass': '#6fc191',
        'block': '#e2727a',
        'warn': '#e8b563',
        'shadow_sm': '0 1px 2px rgba(0, 0, 0, 0.35)',
        'shadow_md': '0 6px 20px rgba(0, 0, 0, 0.4)',
        'shadow_lg': '0 16px 40px rgba(0, 0, 0, 0.45)',
    }
