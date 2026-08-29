"""
UI Manager - Gerencia estilos CSS e elementos de interface
Extraído de app.py para melhor organização e manutenção.

Theming: identidade visual "Policronias do presente" — cores e fontes vêm
do tema nativo do Streamlit (.streamlit/config.toml, seções [theme.light] /
[theme.dark]). O CSS aqui fica restrito ao que o config.toml não cobre —
hoje, só a tipografia serif do texto da carta (não há "terceira fonte"
para corpo de leitura no theming nativo, apenas font/headingFont/codeFont).
"""

import streamlit as st


def configure_page_style():
    """
    Aplica CSS mínimo — apenas tipografia sem cor, complementar ao tema
    nativo definido em .streamlit/config.toml. Deve ser chamado no início
    da aplicação, após st.set_page_config().
    """
    st.markdown("""
<style>
    /* Tipografia do texto da carta — sem cor/background, só leitura longa.
       Cores vêm do container nativo (st.container(border=True)) em volta. */
    .letter-text {
        font-family: 'Newsreader', Georgia, 'Iowan Old Style', 'Palatino Linotype', Palatino, serif;
        font-size: 18px;
        line-height: 1.7;
        width: 100%;
        white-space: pre-wrap;
        word-wrap: break-word;
        padding: 4px 2px;
    }

    .letter-text.letter-text--compact {
        max-height: 300px;
        overflow-y: auto;
    }

    .letter-text mark {
        padding: 2px 4px;
        border-radius: 0;
    }
</style>
""", unsafe_allow_html=True)


def render_letter_text(texto: str, compact: bool = False, accent: str = None):
    """
    Renderiza o texto de uma carta em tipografia serif de leitura longa,
    dentro de um container nativo (respeita o tema claro/escuro ativo).

    Uso:
        render_letter_text(carta['texto'])
        render_letter_text(texto_destacado, compact=True)  # já com <mark> embutido
        render_letter_text(texto_destacado, compact=True, accent="#9c3a26")  # com faixa lateral colorida (ex: cor do termo em Frequência)

    Args:
        texto: Texto da carta, opcionalmente já contendo tags <mark> de highlight.
        compact: Se True, usa altura menor com scroll (para previews em expander).
        accent: Cor opcional para uma faixa lateral esquerda (ex: cor do termo destacado).
    """
    classes = "letter-text letter-text--compact" if compact else "letter-text"
    style = f' style="border-left: 4px solid {accent}; padding-left: 12px;"' if accent else ""
    with st.container(border=True):
        st.markdown(f'<div class="{classes}"{style}>{texto}</div>', unsafe_allow_html=True)


def _current_theme_mode() -> str:
    """
    Retorna 'light' ou 'dark' com base no tema ativo (st.context.theme.type).
    Streamlit só expõe o tipo do tema, não os valores de cor — por isso as
    cores usadas em gráficos Plotly (que não herdam CSS) ficam replicadas
    em _CHART_THEME, espelhando .streamlit/config.toml.
    """
    theme_type = st.context.theme.type if st.context.theme else None
    return theme_type if theme_type in ("light", "dark") else "dark"


_CHART_THEME = {
    "light": {
        "font_color": "#1b1815",
        "grid_color": "#cdc4ae",
        "legend_bg": "rgba(248, 245, 236, 0.75)",
        "legend_border": "#cdc4ae",
        "accent": "#9c3a26",
        "sequential_scale": ["#f1ede2", "#9c3a26"],
        "categorical": ["#9c3a26", "#5c6a4c", "#1b1815", "#c98a2e", "#4f6472", "#9c8f7d"],
    },
    "dark": {
        "font_color": "#c9c2b0",
        "grid_color": "#3a352d",
        "legend_bg": "rgba(27, 24, 21, 0.6)",
        "legend_border": "#3a352d",
        "accent": "#d97a5e",
        "sequential_scale": ["#252019", "#d97a5e"],
        "categorical": ["#d97a5e", "#9aa886", "#c9c2b0", "#d9a24e", "#8fa3b0", "#9c8f7d"],
    },
}


# ── Identidade "Policronias do presente" ────────────────────────────────
# Paleta de marca do tema ativo, espelhando .streamlit/config.toml.
# Claro = "papel de arquivo"; escuro = paleta reversa Policronias.
_BRAND_PALETTE = {
    "light": {
        "paper": "#f1ede2", "card": "#f8f5ec", "ink": "#1b1815",
        "ink_soft": "#56514a", "stamp": "#9c3a26", "moss": "#5c6a4c",
        "thread": "#cdc4ae",
    },
    "dark": {
        "paper": "#1b1815", "card": "#252019", "ink": "#c9c2b0",
        "ink_soft": "#9c8f7d", "stamp": "#d97a5e", "moss": "#9aa886",
        "thread": "#3a352d",
    },
}


def get_brand_palette() -> dict:
    """Cores da identidade Policronias para o tema claro/escuro ativo."""
    return _BRAND_PALETTE[_current_theme_mode()]


def policronias_mark_svg(px: int = 120) -> str:
    """
    Símbolo da marca "Policronias do presente" — três círculos concêntricos
    deslocados (tinta / selo / musgo), única forma circular do sistema.

    O anel de tinta usa ``currentColor`` (herda a cor de texto real do tema
    ativo, sem depender de st.context.theme); selo e musgo vêm da paleta de
    marca. Renderizado sobre fundo transparente — sem moldura.
    """
    c = get_brand_palette()
    return (
        f'<svg width="{px}" height="{px}" viewBox="0 0 106 100" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="Símbolo Policronias do presente" '
        f'style="display:block;margin:0 auto">'
        f'<circle cx="50" cy="50" r="47.5" stroke="currentColor" stroke-width="5"/>'
        f'<circle cx="68" cy="48" r="33.5" stroke="{c["stamp"]}" stroke-width="5"/>'
        f'<circle cx="30" cy="62" r="23.25" stroke="{c["moss"]}" stroke-width="3.5"/>'
        f'</svg>'
    )


def get_accent_color() -> str:
    """
    Retorna a cor de destaque (accent) do tema claro/escuro ativo, em hex.

    Uso: elementos HTML customizados que não herdam cor do tema nativo
    (ex: título estilizado na sidebar).
    """
    return _CHART_THEME[_current_theme_mode()]["accent"]


def get_plotly_color_palette() -> list:
    """
    Retorna a paleta categórica de cores para gráficos Plotly, alinhada ao
    tema claro/escuro ativo.

    Returns:
        Lista de cores em formato hex para uso em color_discrete_sequence
    """
    return _CHART_THEME[_current_theme_mode()]["categorical"]


def get_plotly_sequential_scale() -> list:
    """
    Retorna uma escala contínua de 2 cores (fundo secundário → accent),
    alinhada ao tema claro/escuro ativo, para uso em color_continuous_scale.
    """
    return _CHART_THEME[_current_theme_mode()]["sequential_scale"]


def get_plotly_theme_template() -> dict:
    """
    Retorna um dicionário de configurações para aplicar o tema ativo
    (claro/escuro) em gráficos Plotly, incluindo layouts, fontes e cores.
    """
    theme = _CHART_THEME[_current_theme_mode()]
    return {
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'font': {'family': "'IBM Plex Sans', sans-serif", 'color': theme['font_color']},
        'xaxis': {'showgrid': True, 'gridwidth': 1, 'gridcolor': theme['grid_color']},
        'yaxis': {'showgrid': True, 'gridwidth': 1, 'gridcolor': theme['grid_color']},
        'title': {'font': {'size': 16, 'color': theme['font_color']}, 'x': 0.5, 'xanchor': 'center'},
        'legend_bg': theme['legend_bg'],
        'legend_border': theme['legend_border'],
    }


def apply_plotly_theme(fig):
    """
    Aplica o tema visual (claro/escuro ativo) a um gráfico Plotly.

    Uso:
        fig = px.bar(...)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True, theme=None)  # theme=None: evita que o Streamlit sobrescreva as cores já definidas acima
    """
    theme = get_plotly_theme_template()
    fig.update_layout(
        plot_bgcolor=theme['plot_bgcolor'],
        paper_bgcolor=theme['paper_bgcolor'],
        font=theme['font'],
        showlegend=True,
        legend=dict(x=1.0, y=1.0, bgcolor=theme['legend_bg'], bordercolor=theme['legend_border'], borderwidth=1)
    )
    fig.update_xaxes(showgrid=theme['xaxis']['showgrid'], gridwidth=theme['xaxis']['gridwidth'], gridcolor=theme['xaxis']['gridcolor'], automargin=True)
    fig.update_yaxes(showgrid=theme['yaxis']['showgrid'], gridwidth=theme['yaxis']['gridwidth'], gridcolor=theme['yaxis']['gridcolor'], automargin=True)
    return fig


def format_pie_labels(fig):
    """
    Formata rótulos de gráficos de pizza com valores negritados para melhor legibilidade.
    O texto do rótulo fica sobre a cor da fatia (não sobre o fundo da página),
    por isso usa o papel Policronias (#f8f5ec) fixo, válido nos dois temas.

    Uso:
        fig = px.pie(...)
        format_pie_labels(fig)
        st.plotly_chart(fig, use_container_width=True, theme=None)  # theme=None: evita que o Streamlit sobrescreva as cores já definidas acima
    """
    fig.update_traces(
        textposition='inside',
        textfont=dict(size=12, color='#f8f5ec', family="'IBM Plex Sans', sans-serif", weight='bold'),
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
    )
    return fig


def breadcrumb_nav(*items):
    """
    Mostra breadcrumb de navegação

    Uso:
        breadcrumb_nav("Explorador", "Carta #42", "Anotações")
        # Mostra: 📍 Explorador > Carta #42 > Anotações
    """
    breadcrumb_text = " > ".join(items)
    st.caption(f"📍 {breadcrumb_text}")


