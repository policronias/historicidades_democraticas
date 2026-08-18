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
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap');

    /* Paleta de cores QVR: responsiva a prefers-color-scheme */
    :root {
        /* Tema Dark — Paleta QVR profissional */
        --ink: #0a0e13;
        --panel: #141b23;
        --panel-2: #1a242e;
        --line: #3a4d5c;
        --text: #f3efe3;
        --muted: #a9b6c2;
        --brass: #c99a5e;
        --brass-bright: #eec98a;
        --pass: #6fc191;
        --block: #e2727a;
        --warn: #e8b563;

        /* Aliases para compatibilidade */
        --bg-primary: #0a0e1f;
        --bg-secondary: #1a1f2e;
        --bg-tertiary: #252b3a;
        --text-primary: #f3efe3;
        --text-secondary: #a9b6c2;
        --accent-color: #c99a5e;
        --accent-hover: #b45309;
        --primary-color: #2b2d33;
        --primary-hover: #45474e;
        --border-color: #3a4d5c;
        --gold: #c99a5e;
        --gold-bright: #eec98a;
        --green: #6fc191;
        --coral: #e2727a;
        --bg-light: #252b3a;
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
            --bg-primary: #f9fafb;
            --bg-secondary: #eeebe5;
            --bg-tertiary: #e5e7eb;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --border-color: #ddd9d2;
            --bg-light: #eeebe5;
        }
    }

    /* Fonte e espaçamento base */
    body {
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
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
        background-color: var(--bg-secondary);
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }

    .streamlit-expanderHeader:hover {
        background-color: var(--bg-tertiary);
    }

    /* Buttons — Estilo QVR Brass com melhor contraste */
    .stButton > button {
        background: rgba(201, 154, 94, 0.25) !important;
        color: #0a0e13 !important;
        border: 1.5px solid var(--brass) !important;
        border-radius: 6px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        font-family: 'Manrope', sans-serif !important;
        font-size: 13px !important;
        transition: all 0.15s ease !important;
        cursor: pointer !important;
        text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3) !important;
    }

    .stButton > button:hover {
        background: rgba(201, 154, 94, 0.4) !important;
        color: #0a0e13 !important;
        box-shadow: 0 0 0 2px rgba(201, 154, 94, 0.3), 0 2px 4px rgba(0, 0, 0, 0.2) !important;
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
        background-color: var(--bg-secondary);
        border-radius: 8px;
        padding: 16px;
        border: 1px solid var(--border-color);
    }

    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: var(--bg-primary);
    }

    /* Success/Error messages */
    .stSuccess {
        background-color: rgba(16, 185, 129, 0.15);
        color: #6ee7b7;
        border-radius: 6px;
        border-left: 4px solid var(--green);
    }

    .stError {
        background-color: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border-radius: 6px;
        border-left: 4px solid #ef4444;
    }

    .stWarning {
        background-color: rgba(217, 119, 6, 0.15);
        color: #fdba74;
        border-radius: 6px;
        border-left: 4px solid var(--gold);
    }

    /* Info message */
    .stInfo {
        background-color: rgba(14, 165, 233, 0.15);
        color: #7dd3fc;
        border-radius: 6px;
        border-left: 4px solid #0ea5e9;
    }

    /* Headers — Tipografia Serif caracterful */
    h1, h2, h3 {
        font-family: 'Source Serif 4', Georgia, 'Iowan Old Style', 'Palatino Linotype', Palatino, serif;
        color: var(--text-primary);
        font-weight: 600;
        letter-spacing: 0.015em;
        text-wrap: balance;
    }

    /* Cabeçalho da sidebar — Brass bright, efeito profissional */
    section[data-testid="stSidebar"] h1 {
        border-bottom: 2px solid var(--brass);
        padding-bottom: 12px;
        margin-bottom: 20px;
        color: var(--brass-bright);
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.02em;
    }

    /* Horizontal line */
    hr {
        border-color: var(--border-color);
    }

    /* Code blocks */
    .stCodeBlock {
        background-color: var(--bg-secondary);
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
        <h3 style="color: #8b6f47; margin-bottom: 0;">Historicidades Democráticas</h3>
        <p style="margin-top: 0; font-weight: 600; color: var(--text-secondary);">Plataforma de Análise de Documentos Históricos</p>
        <p style="color: var(--text-secondary); font-size: 14px;">Navegue, busque, anote e analise correspondência histórica constitucional.</p>
        """, unsafe_allow_html=True)


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
    Paleta suave e confortável, alinhada à paleta do programa (âmbar/grafite).

    Returns:
        Lista de cores em formato hex para uso em color_discrete_sequence
    """
    return [
        '#d4a574',  # Âmbar suave primário
        '#9ca3af',  # Grafite suave primário
        '#e8c9a0',  # Âmbar claro pastel
        '#c9b899',  # Grafite suave secundário
        '#b8956e',  # Âmbar médio
        '#6b7280',  # Grafite médio
        '#a7f3d0',  # Verde suave (complementar)
        '#bfdbfe',  # Azul suave (complementar)
        '#fecaca',  # Rosa suave (complementar)
        '#fcd34d',  # Amarelo suave
        '#d8b4fe',  # Roxo suave
        '#86efac',  # Verde claro suave
    ]


def get_color_scheme() -> dict:
    """
    Retorna o esquema de cores do tema escuro/dourado.

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
        'text_primary': '#f5f5f5',
        'text_secondary': '#b0b8cc',
        'bg_primary': '#0a0e1f',
        'bg_secondary': '#1a1f2e',
        'bg_tertiary': '#252b3a',
        'gold': '#d97706',
        'gold_bright': '#fbbf24',
        'green': '#10b981',
        'coral': '#ff6b6b',
        'border': '#404657',
    }


def sidebar_section(title: str, icon: str = ""):
    """
    Cria uma seção formatada na sidebar

    Uso:
        sidebar_section("🔍 BUSCAR & EXPLORAR")
    """
    if icon and not title.startswith(icon):
        title = f"{icon} {title}"
    st.markdown(f"### {title}")
    st.markdown('<div style="height: 2px; background: var(--border-color); margin: 8px 0;"></div>', unsafe_allow_html=True)


def breadcrumb_nav(*items):
    """
    Mostra breadcrumb de navegação

    Uso:
        breadcrumb_nav("Explorador", "Carta #42", "Anotações")
        # Mostra: 📍 Explorador > Carta #42 > Anotações
    """
    breadcrumb_text = " > ".join(items)
    st.caption(f"📍 {breadcrumb_text}")


def reset_context():
    """Reseta contexto de navegação mantendo session data"""
    if 'current_carta_id' in st.session_state:
        st.session_state.current_carta_id = None
    if 'search_results' in st.session_state:
        st.session_state.search_results = []
    if 'semantic_results' in st.session_state:
        st.session_state.semantic_results = []


def get_plotly_theme_template():
    """
    Retorna um dicionário de configurações para aplicar o tema do programa
    em gráficos Plotly, incluindo layouts, fontes e cores.
    """
    return {
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'font': {'family': 'Manrope, sans-serif', 'color': '#f3efe3'},
        'xaxis': {'showgrid': True, 'gridwidth': 1, 'gridcolor': '#3a4d5c'},
        'yaxis': {'showgrid': True, 'gridwidth': 1, 'gridcolor': '#3a4d5c'},
        'title': {'font': {'size': 16, 'color': '#f3efe3'}, 'x': 0.5, 'xanchor': 'center'},
    }


def apply_plotly_theme(fig):
    """
    Aplica o tema visual do programa a um gráfico Plotly.

    Uso:
        fig = px.bar(...)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    """
    theme = get_plotly_theme_template()
    fig.update_layout(
        plot_bgcolor=theme['plot_bgcolor'],
        paper_bgcolor=theme['paper_bgcolor'],
        font=theme['font'],
        showlegend=True,
        legend=dict(x=1.0, y=1.0, bgcolor='rgba(0,0,0,0.3)', bordercolor='#3a4d5c', borderwidth=1)
    )
    fig.update_xaxes(showgrid=theme['xaxis']['showgrid'], gridwidth=theme['xaxis']['gridwidth'], gridcolor=theme['xaxis']['gridcolor'])
    fig.update_yaxes(showgrid=theme['yaxis']['showgrid'], gridwidth=theme['yaxis']['gridwidth'], gridcolor=theme['yaxis']['gridcolor'])
    return fig


def format_pie_labels(fig):
    """
    Formata rótulos de gráficos de pizza com valores negritados para melhor legibilidade.

    Uso:
        fig = px.pie(...)
        format_pie_labels(fig)
        st.plotly_chart(fig, use_container_width=True)
    """
    fig.update_traces(
        textposition='inside',
        textfont=dict(size=12, color='#f3efe3', family='Manrope', weight='bold'),
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
    )
    return fig
