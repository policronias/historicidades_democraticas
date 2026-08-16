"""
Historicidades Democráticas - Plataforma de Análise das sugestões dos cidadãos (Base SAIC)
Interface completa em Streamlit para navegação, busca, anotações e análise das fontes

Por: Walderez Ramalho (UDESC)
"""

import streamlit as st
import os
import time
import csv
import math
from datetime import datetime
from io import StringIO
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules import (
    DataManager,
    SearchEngine,
    AnnotationManager,
    SeriesManager,
    ExportManager,
    SemanticEngine,
    StemmingEngine,
    FrequencyAnalyzer,
    build_df_fast,
    compute_chart_data_cached,
    build_semantic_csv_cached,
    FeedbackManager,
    SearchSuggestions,
    initialize_tab_state,
    mark_tab_loaded,
    is_tab_loaded,
    initialize_search_cache,
    get_cached_search,
    cache_search_result,
)
from modules.config_manager import EMBEDDING_MODEL
from modules.ui_manager import (
    configure_page_style,
    get_color_scheme,
    get_plotly_color_palette,
    breadcrumb_nav,
    reset_context,
)


# ============================================================================
# CONFIGURAÇÃO STREAMLIT
# ============================================================================

st.set_page_config(
    page_title="Historicidades Democráticas",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

configure_page_style()


# ============================================================================
# INICIALIZAÇÃO DO SESSION STATE
# ============================================================================

@st.cache_data(ttl=60)
def get_available_databases():
    """Retorna lista de todos os arquivos .json disponíveis, excluindo pastas de sistema."""
    dbs = []
    exclude_dirs = {'.venv', '.vscode', '.git', '.claude', '__pycache__', 'node_modules', '.env'}

    # Procura na raiz
    try:
        for file in os.listdir('.'):
            if file.endswith('.json'):
                dbs.append(file)
    except:
        pass

    # Procura em subpastas (apenas nível 1)
    try:
        for folder in os.listdir('.'):
            if os.path.isdir(folder) and folder not in exclude_dirs:
                for file in os.listdir(folder):
                    if file.endswith('.json'):
                        dbs.append(f'{folder}/{file}')
    except:
        pass

    return sorted(set(dbs))


def initialize_session():
    """Inicializa variáveis de sessão."""
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
        # Usa a base selecionada na sessão ou padrão
        db_to_load = st.session_state.get('selected_database', 'cartas_db.json')
        success, msg = st.session_state.data_manager.load_database(db_to_load)

    if 'search_engine' not in st.session_state:
        st.session_state.search_engine = SearchEngine()

    if 'annotation_manager' not in st.session_state:
        st.session_state.annotation_manager = AnnotationManager()

    if 'series_manager' not in st.session_state:
        st.session_state.series_manager = SeriesManager()

    if 'current_carta_id' not in st.session_state:
        ids = st.session_state.data_manager.get_ids_cartas()
        st.session_state.current_carta_id = ids[0] if ids else None

    if 'search_results' not in st.session_state:
        st.session_state.search_results = []

    if 'highlighted_terms' not in st.session_state:
        st.session_state.highlighted_terms = []

    if 'edit_mode_serie' not in st.session_state:
        st.session_state.edit_mode_serie = {}

    if 'search_scope' not in st.session_state:
        st.session_state.search_scope = "Somente Texto"

    if 'highlight_active' not in st.session_state:
        st.session_state.highlight_active = True

    if 'wildcard_matches' not in st.session_state:
        st.session_state.wildcard_matches = {}

    if 'highlight_use_regex' not in st.session_state:
        st.session_state.highlight_use_regex = False

    if 'filter_results' not in st.session_state:
        st.session_state.filter_results = []

    if 'active_filters' not in st.session_state:
        st.session_state.active_filters = {}

    if 'semantic_engine' not in st.session_state:
        st.session_state.semantic_engine = SemanticEngine(model_name=EMBEDDING_MODEL)

    if 'stemming_engine' not in st.session_state:
        st.session_state.stemming_engine = StemmingEngine()

    if 'highlight_use_stemming' not in st.session_state:
        st.session_state.highlight_use_stemming = False

    if 'semantic_results' not in st.session_state:
        st.session_state.semantic_results = []

    if 'semantic_page' not in st.session_state:
        st.session_state.semantic_page = 1

    if 'cached_series_list' not in st.session_state:
        st.session_state.cached_series_list = None
        st.session_state.cached_series_list_valid = False

    if 'semantic_expand_state' not in st.session_state:
        st.session_state.semantic_expand_state = {}  # Lazy-load state para expanders

    if 'sem_carta_gerenciar' not in st.session_state:
        st.session_state.sem_carta_gerenciar = None  # Carta com painel de séries aberto

    if 'serie_page' not in st.session_state:
        st.session_state.serie_page = 1

    if 'sidebar_series_carta_id' not in st.session_state:
        st.session_state.sidebar_series_carta_id = None

    if 'sidebar_series_context' not in st.session_state:
        st.session_state.sidebar_series_context = 'explorar'

    # Cachear nome_index (used in navigation and filters)
    if 'nome_index' not in st.session_state:
        st.session_state.nome_index = st.session_state.data_manager.get_nome_index()

    # Cachear series list (used in multiple places)
    if 'series_list_cache' not in st.session_state:
        st.session_state.series_list_cache = st.session_state.series_manager.get_todas_series()
        st.session_state.series_list_cache_valid = True

    # Fase 1: Lazy Loading e Search Cache
    initialize_tab_state()
    initialize_search_cache()

    # Fase 3: Search Suggestions e Quick Filters
    if 'search_suggestions' not in st.session_state:
        ss = SearchSuggestions()
        ss.initialize_suggestions()
        st.session_state.search_suggestions_manager = ss


initialize_session()


# Cache de managers — evita múltiplos lookups de st.session_state por rerun
dm = st.session_state.data_manager
am = st.session_state.annotation_manager
sm = st.session_state.series_manager
se = st.session_state.search_engine
sem_e = st.session_state.semantic_engine
stem_e = st.session_state.stemming_engine

# Cache local de get_todas_cartas() — evita 40+ chamadas no mesmo render
_todas_cartas = dm.get_todas_cartas()



# ============================================================================
# BARRA LATERAL - INFORMAÇÕES E NAVEGAÇÃO
# ============================================================================

with st.sidebar:
    # Header com Home button
    col_header, col_home = st.columns([3, 1])
    with col_header:
        st.markdown("# 📚 **Historicidades Democráticas**")
        st.markdown("<sub style='color: var(--text-secondary); font-size: 18px;'>Por Walderez Ramalho</sub>", unsafe_allow_html=True)
    with col_home:
        if st.button("🏠", key="home_button", help="Voltar ao início"):
            reset_context()
            st.session_state.semantic_page = 1
            st.session_state.current_carta_id = None
            st.rerun()

    st.markdown("---")

    # ════════════════════════════════════════════════════════════
    # SEÇÃO: BASE DE DADOS
    # ════════════════════════════════════════════════════════════

    st.subheader("📂 Base de Dados")
    available_dbs = get_available_databases()
    current_db = st.session_state.get('selected_database', 'cartas_db.json')

    selected_db = st.selectbox(
        "Escolha a base para trabalhar:",
        options=available_dbs,
        index=available_dbs.index(current_db) if current_db in available_dbs else 0,
        key="db_selector"
    )

    # Se mudou a base, recarrega
    if selected_db != st.session_state.get('selected_database'):
        st.session_state.selected_database = selected_db
        dm.load_database(selected_db)
        st.session_state.nome_index = dm.get_nome_index()
        st.rerun()

    st.markdown("---")

    # Informações da sessão
    st.subheader("📊 Sessão Atual")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Base Carregada",
            dm.current_database_name or "Nenhuma"
        )
    with col2:
        st.metric(
            "Total de Cartas",
            dm.get_total_cartas()
        )

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Séries",
            sm.total_series()
        )
    with col2:
        st.metric(
            "Anotações",
            am.contar_anotacoes()
        )

    # Informações da carta atual
    if st.session_state.current_carta_id:
        st.subheader("📄 Carta Atual")
        carta = dm.get_carta(st.session_state.current_carta_id)
        if carta:
            st.write(f"**ID:** {st.session_state.current_carta_id}")
            st.write(f"**Autor:** {carta.get('nome', 'N/A')}")

            # Ícone de anotação
            if am.tem_anotacao(st.session_state.current_carta_id):
                st.write("📝 Tem anotação")

            # Séries da carta
            series_carta = sm.get_series_carta(st.session_state.current_carta_id)
            if series_carta:
                st.write("🗂️ **Séries:**")
                for serie in series_carta:
                    st.write(f"  • {serie}")

    st.markdown("---")

    # Última atualização
    st.markdown(f"**Última atualização:**")
    st.caption(am.get_ultimo_update())

    # Botão para nova sessão
    st.markdown("---")
    with st.form("new_session_form"):
        if st.form_submit_button("🆕 Nova Sessão", use_container_width=True):
            if am.contar_anotacoes() > 0 or sm.total_series() > 0:
                st.warning("⚠️ Você tem dados não salvos!")
                st.info("Use a aba 'Configurações' para fazer backup antes de começar nova sessão")
            else:
                am.limpar_sessao()
                sm.series = {}
                st.success("✅ Sessão iniciada!")
                st.rerun()

    # Conversor de base de dados
    st.markdown("---")
    st.subheader("🔄 Conversor de Base")

    with st.expander("📥 Converter XLSX/CSV para JSON"):
        st.markdown("Selecione um arquivo XLSX ou CSV para converter para JSON com todos os metadados.")

        uploaded_file = st.file_uploader(
            "Escolha o arquivo:",
            type=['xlsx', 'csv'],
            key="converter_file"
        )

        if uploaded_file:
            with st.form("convert_file_form"):
                if st.form_submit_button("🔄 Converter Arquivo", use_container_width=True):
                    try:
                        # Lê o arquivo
                        if uploaded_file.name.endswith('.xlsx'):
                            df = pd.read_excel(uploaded_file)
                        else:
                            df = pd.read_csv(uploaded_file, encoding='utf-8')

                        st.info(f"📖 Lido: {len(df)} registros")

                        # Converte para JSON
                        def processar_linha(row, idx):
                            try:
                                linha = str(row.get('LINHA_BASE_SAIC') or row.get('ID') or idx)
                                nome = str(row.get('NOME', '')).strip() or 'Anônimo'
                                texto = str(row.get('SUGESTAO.TEXTO') or row.get('TEXTO', '')).strip()

                                # Metadados
                                destinatario = str(row.get('DESTINATARIO', '')).strip() or None
                                catalogo = str(row.get('CATALOGO', '')).strip() or None
                                indexacao = str(row.get('INDEXACAO', '')).strip() or None
                                origem = str(row.get('ORIGEM', '')).strip() or None
                                data = str(row.get('DATA', '')).strip() or None
                                formul = str(row.get('FORMUL', '')).strip() or None
                                dv = str(row.get('DV', '')).strip() or None
                                data2 = str(row.get('DATA2', '')).strip() or None
                                municipio = str(row.get('MUNICIPIO', '')).strip() or None
                                uf = str(row.get('UF', '')).strip() or None
                                cep = str(row.get('CEP', '')).strip() or None
                                sexo = str(row.get('SEXO', '')).strip() or None
                                morador = str(row.get('MORADOR', '')).strip() or None
                                instrucao = str(row.get('INSTRUCAO', '')).strip() or None
                                estado_civil = str(row.get('ESTADO CIVIL', '')).strip() or None
                                faixa_etaria = str(row.get('FAIXA ETÁRIA', '')).strip() or None
                                faixa_renda = str(row.get('FAIXA RENDA', '')).strip() or None
                                atividade = str(row.get('ATIVIDADE', '')).strip() or None

                            except Exception as e:
                                linha = str(idx)
                                nome = 'Anônimo'
                                texto = ''
                                destinatario = None
                                catalogo = None
                                indexacao = None
                                origem = None
                                data = None
                                formul = None
                                dv = None
                                data2 = None
                                municipio = None
                                uf = None
                                cep = None
                                sexo = None
                                morador = None
                                instrucao = None
                                estado_civil = None
                                faixa_etaria = None
                                faixa_renda = None
                                atividade = None

                            return {
                                'linha': linha,
                                'nome': nome,
                                'destinatario': destinatario,
                                'catalogo': catalogo,
                                'indexacao': indexacao,
                                'texto': texto,
                                'origem': origem,
                                'data': data,
                                'formul': formul,
                                'dv': dv,
                                'data2': data2,
                                'municipio': municipio,
                                'uf': uf,
                                'cep': cep,
                                'sexo': sexo,
                                'morador': morador,
                                'instrucao': instrucao,
                                'estado_civil': estado_civil,
                                'faixa_etaria': faixa_etaria,
                                'faixa_renda': faixa_renda,
                                'atividade': atividade,
                                'anotacoes': '',
                                'series': [],
                            }

                        registros = df.apply(lambda row: processar_linha(row, row.name), axis=1)
                        dados = {reg['linha']: reg for reg in registros}

                        # Cria o JSON para download
                        json_str = json.dumps(dados, ensure_ascii=False, indent=2)

                        st.success(f"✅ Conversão concluída! {len(dados)} cartas")

                        st.download_button(
                            label="💾 Baixar JSON",
                            data=json_str,
                            file_name="cartas_db_convertido.json",
                            mime="application/json",
                            use_container_width=True
                        )

                    except Exception as e:
                        st.error(f"❌ Erro na conversão: {str(e)}")

    # Gerenciar Séries
    st.markdown("---")
    st.subheader("🗂️ Gerenciar Séries")

    _sb_context = st.session_state.get('sidebar_series_context', 'explorar')
    if _sb_context == 'explorar':
        _sb_carta_id = st.session_state.current_carta_id
    else:
        _sb_carta_id = st.session_state.get('sidebar_series_carta_id')

    if not st.session_state.series_list_cache_valid:
        st.session_state.series_list_cache = sm.get_todas_series()
        st.session_state.series_list_cache_valid = True
    _sb_todas_series = st.session_state.series_list_cache

    if not _sb_carta_id:
        st.caption("ℹ️ Navegue para uma carta no Explorador.")
    elif not _sb_todas_series:
        st.caption("ℹ️ Crie séries na aba 🗂️ Séries Temáticas.")
    else:
        _sb_carta = dm.get_carta(_sb_carta_id)
        if _sb_carta:
            _sb_nome = str(_sb_carta.get('nome', 'N/A'))
            if _sb_context == 'semantica':
                st.caption(f"🧠 **Busca Semântica** — carta #{_sb_carta_id}")
            elif _sb_context == 'filtro':
                st.caption(f"🎯 **Filtros** — carta #{_sb_carta_id}")
            else:
                st.caption(f"🔍 **Explorador** — carta #{_sb_carta_id}")
            st.caption(f"**{_sb_nome[:28]}{'...' if len(_sb_nome) > 28 else ''}**")

            _sb_series_atuais = sm.get_series_carta(_sb_carta_id)

            # Exibe séries atuais da carta
            if _sb_series_atuais:
                st.markdown("**Séries vinculadas:**")
                for _s in _sb_series_atuais:
                    st.caption(f"🗂️ {_s}")
            else:
                st.caption("_Nenhuma série vinculada ainda_")

            _sb_ms_key = f"sb_ms_{_sb_carta_id}"
            st.multiselect(
                "Alterar séries:",
                options=_sb_todas_series,
                default=[s for s in _sb_series_atuais if s in _sb_todas_series],
                key=_sb_ms_key,
            )

            def _do_save_sb(_cid=_sb_carta_id, _ms_key=_sb_ms_key):
                novas = st.session_state.get(_ms_key, [])
                _ok, _ = sm.atualizar_series_carta(_cid, novas)
                if _ok:
                    st.session_state['_sb_just_saved'] = True

            st.button(
                "💾 Salvar",
                on_click=_do_save_sb,
                use_container_width=True,
                type="primary",
                key=f"sb_save_{_sb_carta_id}"
            )

            if st.session_state.pop('_sb_just_saved', False):
                st.success("✅ Séries atualizadas!")

            if _sb_context in ('semantica', 'filtro'):
                def _voltar_explorar():
                    st.session_state.sidebar_series_context = 'explorar'
                    st.session_state.sidebar_series_carta_id = None

                st.button(
                    "🔍 Voltar para Explorador",
                    on_click=_voltar_explorar,
                    use_container_width=True,
                    key="sb_voltar_explorar"
                )
        else:
            st.caption(f"⚠️ Carta #{_sb_carta_id} não encontrada.")


# ============================================================================
# BUSCA AVANÇADA - FORA DAS ABAS
# ============================================================================

st.header("🔎 Busca Avançada")

# Tooltip com instruções de busca
with st.expander("ℹ️ Como usar a busca avançada"):
    st.markdown("""
    **Operadores disponíveis:**
    - **Aspas duplas**: `"frase exata"` → busca pela frase exatamente como escrita
    - **Plus (+)**: `+termo` → termo é obrigatório (deve estar presente)
    - **Menos (-)**: `-termo` → termo será excluído dos resultados
    - **Asterisco (*)**: `termin*` → encontra qualquer palavra que comece com "termin"

    **Exemplos:**
    - `"direitos sociais"` → busca pela frase exata
    - `+constituição -república` → deve conter "constituição", mas não "república"
    - `educ* liberdade` → encontra "educação", "educador", etc. E/ou "liberdade"
    - `"voto universal" +mulher` → frase exata + termo obrigatório
    """)

    # ========== TERMOS FREQUENTES ==========
    st.subheader("💡 Termos Frequentes")
    ss = st.session_state.search_suggestions_manager
    trending_terms = ss.get_trending_terms(5)

    col1, col2, col3 = st.columns(3)
    for i, term in enumerate(trending_terms):
        col = [col1, col2, col3][i % 3]
        with col:
            if st.button(f"🔍 {term}", use_container_width=True, key=f"quick_{term}"):
                st.session_state.search_term = term
                st.rerun()

    st.markdown("---")

with st.form("search_form"):
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        termo_busca = st.text_input("Digite o termo ou expressão a buscar:", key="search_term")

    with col2:
        tipo_busca = st.radio(
            "Tipo:",
            ["Simples", "Variações"],
            index=1,
            horizontal=True
        )

    with col3:
        escopo_busca = st.radio(
            "Escopo:",
            ["Somente Texto", "Base Inteira"],
            horizontal=True,
            index=0 if st.session_state.search_scope == "Somente Texto" else 1
        )

    with col4:
        case_sensitive = st.checkbox("Case-sensitive", value=False, key="case_sens")
        st.session_state.highlight_active = st.checkbox(
            "Destacar termos", value=st.session_state.highlight_active, key="highlight_toggle"
        )

    form_submit = st.form_submit_button("🔍 Buscar", use_container_width=True)

# Executar busca quando submit
if form_submit and termo_busca:
    # Atualizar frequência de termos para sugestões
    st.session_state.search_suggestions_manager.update_frequency(termo_busca)

    st.session_state.search_scope = escopo_busca
    st.session_state.search_tipo = tipo_busca
    _search_key = (termo_busca, tipo_busca, escopo_busca, case_sensitive)
    _query_key = f"advanced_{termo_busca}_{tipo_busca}_{escopo_busca}_{case_sensitive}"

    # Tentar recuperar do cache
    _cached = get_cached_search(_query_key)
    if _cached:
        FeedbackManager.success(f"✅ Cache: {len(_cached['ids'])} cartas encontradas")
        ids_resultado, ocorrencias = _cached['ids'], _cached['ocorrencias']
    elif _search_key != st.session_state.get('_last_search_key'):
        if escopo_busca == "Somente Texto":
            search_fields = {'texto'}
        else:
            search_fields = {'texto', 'nome', 'destinatario', 'catalogo', 'indexacao', 'origem'}

        _use_variations = (tipo_busca == "Variações")
        _stem_index = None
        _erro_busca = None

        if _use_variations:
            try:
                _stem_index = stem_e.load_index(_todas_cartas, dm.current_database_name)
            except FileNotFoundError as _e:
                _erro_busca = str(_e)

        if _erro_busca:
            st.error(f"❌ {_erro_busca}")
            ids_resultado, ocorrencias = [], {}
        else:
            try:
                ids_resultado, ocorrencias = se.search_advanced(
                    _todas_cartas,
                    termo_busca,
                    case_sensitive=case_sensitive,
                    use_variations=_use_variations,
                    search_fields=search_fields,
                    stem_index=_stem_index
                )
                # Guardar em cache
                cache_search_result(_query_key, {'ids': ids_resultado, 'ocorrencias': ocorrencias})
            except RuntimeError as _e:
                st.error(f"❌ {_e}")
                ids_resultado, ocorrencias = [], {}

        if '*' in termo_busca:
            wildcart_pattern = termo_busca.replace("*", r"\w*")
            regex_pat = rf'\b{wildcart_pattern}\b'
            st.session_state.highlighted_terms = [regex_pat]
            st.session_state.highlight_use_regex = True
            st.session_state.highlight_use_stemming = False
            st.session_state.wildcard_matches = se.get_wildcard_matches(
                _todas_cartas, termo_busca, case_sensitive
            )
        elif _use_variations:
            st.session_state.highlighted_terms = [termo_busca] if ids_resultado else []
            st.session_state.highlight_use_regex = False
            st.session_state.highlight_use_stemming = True
            st.session_state.wildcard_matches = {}
            st.session_state._last_variacoes = (
                se.get_variacoes_info(termo_busca, _stem_index) if _stem_index else [termo_busca]
            )
        else:
            st.session_state.highlighted_terms = [termo_busca]
            st.session_state.highlight_use_regex = False
            st.session_state.highlight_use_stemming = False
            st.session_state.wildcard_matches = {}

        st.session_state.search_results = ids_resultado
        st.session_state._last_ocorrencias = ocorrencias
        st.session_state._last_search_key = _search_key

        if ids_resultado and st.session_state.current_carta_id not in ids_resultado:
            st.session_state.current_carta_id = ids_resultado[0]
            st.rerun()

# Exibir resultados (mesmo sem novo submit)
ids_resultado = st.session_state.get('search_results', [])
ocorrencias = st.session_state.get('_last_ocorrencias', {})

if ids_resultado:
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Cartas encontradas", len(ids_resultado))
    col_b.metric("Ocorrências totais", sum(ocorrencias.values()) if ocorrencias else 0)
    col_c.metric("Escopo", st.session_state.search_scope)

    # Mostrar variações quando usando "Variações" (calculado no momento da busca
    # e cacheado em session_state -- evita recarregar o índice de stems a cada rerun)
    tipo_busca_atual = st.session_state.get('search_tipo', 'Variações')
    if tipo_busca_atual == "Variações" and termo_busca:
        variacoes = st.session_state.get('_last_variacoes', [])
        if len(variacoes) > 1:
            st.caption(f"**Variações encontradas:** {' | '.join(variacoes)}")

    # Mostrar termos capturados por wildcard
    if st.session_state.wildcard_matches:
        n_formas = len(st.session_state.wildcard_matches)
        with st.expander(f"🔍 Termos capturados pelo wildcard ({n_formas} formas distintas)"):
            wc_df = pd.DataFrame(
                sorted(st.session_state.wildcard_matches.items(), key=lambda x: -x[1]),
                columns=['Termo', 'Frequência']
            )
            st.dataframe(wc_df, use_container_width=True, hide_index=True, height=200)

    # Botão para limpar filtro
    with st.form("clear_filter_form"):
        if st.form_submit_button("🔄 Limpar Filtro", use_container_width=True):
            st.session_state.highlighted_terms = []
            st.session_state.search_results = []
            st.session_state.wildcard_matches = {}
            st.session_state.highlight_use_regex = False
            st.session_state.highlight_use_stemming = False
            st.session_state._last_search_key = None
            st.rerun()
elif form_submit:
    st.warning("❌ Nenhuma carta encontrada para este termo.")

st.markdown("---")

# ============================================================================
# NAVEGAÇÃO RÁPIDA POR ID
# ============================================================================

st.subheader("🎯 Ir para Carta")

with st.form("go_to_id_form"):
    col_id_input, col_id_btn = st.columns([3, 1])

    with col_id_input:
        id_input = st.text_input(
            "Digite o ID da carta:",
            placeholder="Ex: 1, 42, 100",
            key="direct_id_input"
        )

    with col_id_btn:
        form_submit_id = st.form_submit_button("🔗 Ir", use_container_width=True)

if form_submit_id:
    if id_input.strip():
        todas_ids = dm.get_ids_cartas()
        # Converter para string para garantir compatibilidade com tipos
        id_input_str = str(id_input.strip())
        if id_input_str in [str(id) for id in todas_ids]:
            st.session_state.current_carta_id = id_input_str
            st.success(f"✅ Navegando para carta #{id_input_str}!")
            st.rerun()
        else:
            st.error(f"❌ Carta #{id_input_str} não encontrada na base de dados.")
    else:
        st.warning("⚠️ Digite um ID para buscar.")

# ============================================================================
# HISTÓRICO DE BUSCAS
# ============================================================================

with st.expander("📜 Histórico de Buscas Recentes"):
    if st.session_state.search_history and len(st.session_state.search_history) > 0:
        st.caption(f"Últimas {min(10, len(st.session_state.search_history))} buscas:")
        for h in reversed(st.session_state.search_history[-10:]):
            col_btn, col_info = st.columns([3, 1])
            with col_btn:
                if st.button(f"🔍 {h['query'][:50]}", key=f"history_{h['query']}"):
                    st.session_state.search_termo = h['query'].split('_')[0]  # Extrair termo da chave
                    st.rerun()
            with col_info:
                st.caption(f"{h.get('count', 0)} resultados")
    else:
        st.caption("Nenhuma busca anterior ainda")

# ============================================================================
# FILTROS RÁPIDOS
# ============================================================================

with st.expander("⚡ Filtros Rápidos"):
    st.caption("Aplicar filtros aos resultados de busca:")

    if "quick_filters" not in st.session_state:
        st.session_state.quick_filters = {
            "century_xx": False,
            "only_with_data": False,
            "only_with_location": False,
        }

    st.session_state.quick_filters["century_xx"] = st.checkbox(
        "📅 Apenas século XX (1900-2000)",
        value=st.session_state.quick_filters.get("century_xx", False),
        key="filter_century_xx"
    )

    st.session_state.quick_filters["only_with_data"] = st.checkbox(
        "📆 Apenas com data preenchida",
        value=st.session_state.quick_filters.get("only_with_data", False),
        key="filter_with_data"
    )

    st.session_state.quick_filters["only_with_location"] = st.checkbox(
        "📍 Apenas com localização (município/UF)",
        value=st.session_state.quick_filters.get("only_with_location", False),
        key="filter_with_location"
    )

    if any(st.session_state.quick_filters.values()):
        st.info(f"✅ {sum(st.session_state.quick_filters.values())} filtro(s) ativo(s)")

st.markdown("---")

# ============================================================================
# ABAS PRINCIPAIS
# ============================================================================

# Pré-computa séries uma única vez por render — compartilhado entre todas as abas
if not st.session_state.series_list_cache_valid:
    st.session_state.series_list_cache = sm.get_todas_series()
    st.session_state.series_list_cache_valid = True
_todas_series = st.session_state.series_list_cache

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "🔍 Explorar Cartas",
    "📓 Caderno",
    "🗂️ Séries Temáticas",
    "📥 Exportar",
    "⚙️ Configurações",
    "📊 Gráficos e Tabelas",
    "🎯 Filtros",
    "🧠 Busca Semântica",
    "📈 Análise de Frequência"
])


# ============================================================================
# ABA 1: EXPLORAR CARTAS
# ============================================================================

with tab1:
    st.header("🔍 Explorador de Cartas")
    breadcrumb_nav("Home", "Explorador de Cartas")

    # Seção de navegação
    st.subheader("📍 Navegação")

    # Determinar lista de navegação baseada em filtro de busca
    if st.session_state.search_results:
        nav_ids = st.session_state.search_results
        is_filtered = True
    else:
        nav_ids = dm.get_ids_cartas()
        is_filtered = False

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if nav_ids:
            # Sincronizar o selectbox com a carta atual (sem index=, evita conflito de estado)
            st.session_state.nav_select = st.session_state.current_carta_id

            try:
                current_idx_nav = nav_ids.index(st.session_state.current_carta_id)
            except ValueError:
                current_idx_nav = 0

            _nome_index = st.session_state.nome_index

            def format_carta_option(x):
                nome = _nome_index.get(x, 'N/A')
                return f"#{x} - {nome[:30]}..."

            st.selectbox(
                "Pular para carta (por ID):",
                options=nav_ids,
                format_func=format_carta_option,
                key="nav_select"
            )

            if st.session_state.nav_select != st.session_state.current_carta_id:
                st.session_state.current_carta_id = st.session_state.nav_select
                st.session_state.sidebar_series_context = 'explorar'

    with col2:
        def _explorar_anterior():
            if nav_ids:
                try:
                    idx = nav_ids.index(st.session_state.current_carta_id)
                    if idx > 0:
                        st.session_state.current_carta_id = nav_ids[idx - 1]
                        st.session_state.sidebar_series_context = 'explorar'
                except ValueError:
                    pass
        st.button("⬅️ Anterior", use_container_width=True, key="explorar_btn_anterior",
                  on_click=_explorar_anterior)

    with col3:
        def _explorar_proximo():
            if nav_ids:
                try:
                    idx = nav_ids.index(st.session_state.current_carta_id)
                    if idx < len(nav_ids) - 1:
                        st.session_state.current_carta_id = nav_ids[idx + 1]
                        st.session_state.sidebar_series_context = 'explorar'
                except ValueError:
                    pass
        st.button("Próximo ➡️", use_container_width=True, key="explorar_btn_proximo",
                  on_click=_explorar_proximo)

    # Exibição da carta
    if st.session_state.current_carta_id:
        carta = dm.get_carta(st.session_state.current_carta_id)

        if carta:
            try:
                current_idx_display = nav_ids.index(st.session_state.current_carta_id) + 1
                total_display = len(nav_ids)
            except ValueError:
                current_idx_display = 1
                total_display = 1

            if is_filtered:
                st.markdown(f"### 📄 Exibindo carta **{current_idx_display}** de **{total_display}** — 🔍 *Filtro ativo*")
            else:
                st.markdown(f"### 📄 Exibindo carta **{current_idx_display}** de **{total_display}**")

            # Card com informações
            col1, col2, col3 = st.columns([1, 2, 2])
            with col1:
                st.markdown(f"**ID:** `{st.session_state.current_carta_id}`")
            with col2:
                st.markdown(f"**Autor:** {carta.get('nome', 'N/A')}")
            with col3:
                # Concatena município e UF
                municipio = carta.get('municipio')
                uf = carta.get('uf')
                if municipio and uf and municipio != 'None' and uf != 'None':
                    local = f"{municipio}/{uf}"
                else:
                    local = "N/A"
                st.markdown(f"**Local:** {local}")

            col1, col2, col3 = st.columns([1, 2, 2])
            with col1:
                st.write("")  # Espaço vazio
            with col2:
                st.markdown(f"**Destinatário:** {carta.get('destinatario', 'N/A')}")

            # Texto da carta (com destaque se houver buscas)
            st.subheader("📖 Texto")

            texto = carta.get('texto', '')

            # Aplica destaques se houver termos buscados e destaque ativo
            if st.session_state.highlighted_terms and st.session_state.highlight_active:
                cores_destaque = ["#fbbf24", "#f97316", "#06b6d4", "#34d399", "#c084fc"]
                texto_destacado = se.highlight_multiple_terms(
                    texto,
                    st.session_state.highlighted_terms,
                    cores_destaque[:len(st.session_state.highlighted_terms)],
                    use_regex=st.session_state.highlight_use_regex,
                    use_stemming=st.session_state.get('highlight_use_stemming', False)
                )
                st.markdown(texto_destacado, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 4px; padding: 15px; min-height: 300px; overflow-y: auto; font-family: monospace; white-space: pre-wrap; word-wrap: break-word; color: var(--text-primary);">
                {texto}
                </div>
                """, unsafe_allow_html=True)

            # Anotações da Carta
            st.markdown("---")
            st.subheader("📌 Anotações da Carta")

            anotacao_atual = am.get_anotacao(st.session_state.current_carta_id)

            nova_anotacao = st.text_area(
                "Escreva suas anotações:",
                value=anotacao_atual,
                height=100,
                key="anotacao_area_explorar"
            )

            if nova_anotacao != anotacao_atual:
                am.set_anotacao(
                    st.session_state.current_carta_id,
                    nova_anotacao
                )
                st.success("💾 Anotação salva!")

            # Metadados - Apresentação compacta
            st.markdown("---")
            st.subheader("📋 Metadados da Carta")

            # Formata a data para DD/MM/YYYY
            data_raw = carta.get('data') or 'N/A'
            if data_raw != 'N/A' and str(data_raw) != 'None':
                try:
                    # Tenta fazer parse da data
                    data_obj = pd.to_datetime(data_raw)
                    data_formatada = data_obj.strftime('%d/%m/%Y')
                except:
                    data_formatada = str(data_raw).split()[0] if ' ' in str(data_raw) else str(data_raw)
            else:
                data_formatada = 'N/A'

            metadados = {
                "Origem": carta.get('origem') or 'N/A',
                "Data": data_formatada,
                "Sexo": carta.get('sexo') or 'N/A',
                "Instrução": carta.get('instrucao') or 'N/A',
                "Estado Civil": carta.get('estado_civil') or 'N/A',
                "Faixa Etária": carta.get('faixa_etaria') or 'N/A',
                "Faixa Renda": carta.get('faixa_renda') or 'N/A',
                "Atividade": carta.get('atividade') or 'N/A',
                "Morador": carta.get('morador') or 'N/A',
                "CEP": carta.get('cep') or 'N/A',
            }

            # Layout em colunas compactas - primeiros 10 metadados
            cols = st.columns(5)
            for idx, (chave, valor) in enumerate(metadados.items()):
                with cols[idx % 5]:
                    valor_display = str(valor)[:30] + "..." if len(str(valor)) > 30 else str(valor)
                    st.write(f"**{chave}:**")
                    st.caption(valor_display)

            # Catálogo e Indexação em linha separada para ampliar espaço
            st.markdown("---")
            col_cat, col_idx = st.columns(2)

            with col_cat:
                catalogo = carta.get('catalogo') or 'N/A'
                st.write("**Catálogo:**")
                st.caption(catalogo)

            with col_idx:
                indexacao = carta.get('indexacao') or 'N/A'
                st.write("**Indexação:**")
                st.caption(indexacao)

            st.markdown("---")
            st.caption("🗂️ Gerencie as séries desta carta na barra lateral.")

        else:
            st.error("❌ Carta não encontrada!")


# ============================================================================
# ABA 2: ANOTAÇÕES
# ============================================================================

with tab2:
    st.header("📓 Caderno de Pesquisa")
    breadcrumb_nav("Home", "Caderno de Pesquisa")

    caderno_atual = am.get_caderno_pesquisa()

    novo_caderno = st.text_area(
        "Escreva suas notas de pesquisa (Markdown suportado):",
        value=caderno_atual,
        height=250,
        key="caderno_area"
    )

    if novo_caderno != caderno_atual:
        am.set_caderno_pesquisa(novo_caderno)
        st.success("💾 Caderno salvo!")

    with st.form("add_quick_note_form"):
        if st.form_submit_button("➕ Adicionar Nota Rápida", use_container_width=True):
            if st.session_state.current_carta_id:
                carta = dm.get_carta(st.session_state.current_carta_id)
                nota = f"**Carta #{st.session_state.current_carta_id}** ({carta.get('nome', 'N/A')}): "
                am.append_caderno_pesquisa(nota)
                st.success("✅ Nota adicionada ao caderno!")
                st.rerun()
            else:
                st.warning("⚠️ Selecione uma carta primeiro")


# ============================================================================
# ABA 3: SÉRIES TEMÁTICAS
# ============================================================================

with tab3:
    st.header("🗂️ Séries Temáticas")
    breadcrumb_nav("Home", "Séries Temáticas")

    col1, col2 = st.columns([1, 2])

    # ========== GERENCIAR SÉRIES ==========
    with col1:
        st.subheader("➕ Criar Nova Série")

        nome_serie = st.text_input("Nome da série:", key="new_serie_name")
        descricao_serie = st.text_area("Descrição (opcional):", height=100, key="new_serie_desc")

        with st.form("create_serie_form"):
            if st.form_submit_button("✅ Criar Série", use_container_width=True):
                if nome_serie.strip():
                    success, msg = sm.criar_serie(nome_serie, descricao_serie)
                    if success:
                        st.session_state.series_list_cache_valid = False
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("⚠️ Digite um nome para a série")

        st.markdown("---")

        st.subheader("📋 Minhas Séries")

        series_list = _todas_series

        if series_list:
            # Dropdown para selecionar série
            if 'manage_serie_select' not in st.session_state:
                st.session_state.manage_serie_select = series_list[0]

            serie_para_gerenciar = st.selectbox(
                "Selecione uma série para gerenciar:",
                options=series_list,
                index=series_list.index(st.session_state.manage_serie_select) if st.session_state.manage_serie_select in series_list else 0,
                key="manage_serie_select"
            )

            info = sm.get_info_serie(serie_para_gerenciar)
            st.markdown(f"**{serie_para_gerenciar}** — {info['total_cartas']} cartas")
            st.caption(f"_{info['descricao']}_" if info.get('descricao') else "Sem descrição")

            # Botões de ação
            col_edit, col_del = st.columns(2)

            with col_edit:
                if st.button(f"✏️ Editar", key=f"edit_serie_btn_{serie_para_gerenciar}", use_container_width=True):
                    st.session_state.edit_mode_serie[serie_para_gerenciar] = True
                    st.rerun()

            with col_del:
                with st.form(f"delete_serie_form_{serie_para_gerenciar}"):
                    st.write(f"**Deletar '{serie_para_gerenciar}'?**")
                    st.caption("Isso removerá todos os vínculos desta série.")
                    if st.form_submit_button("🗑️ Confirmar exclusão", type="secondary", use_container_width=True):
                        success, msg = sm.deletar_serie(serie_para_gerenciar)
                        if success:
                            st.session_state.series_list_cache_valid = False
                            st.session_state.manage_serie_select = series_list[0] if len(series_list) > 1 else None
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            # Modo edição da série
            if st.session_state.edit_mode_serie.get(serie_para_gerenciar, False):
                st.markdown("---")
                st.subheader("✏️ Editar Série")

                novo_nome_serie = st.text_input(
                    "Nome da série:",
                    value=serie_para_gerenciar,
                    key=f"edit_manage_serie_nome_{serie_para_gerenciar}"
                )
                nova_descricao = st.text_area(
                    "Descrição:",
                    value=info.get('descricao', ''),
                    height=80,
                    key=f"edit_manage_serie_desc_{serie_para_gerenciar}"
                )

                with st.form(f"edit_manage_serie_form_{serie_para_gerenciar}"):
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Salvar", use_container_width=True):
                            nome_final = novo_nome_serie.strip() or serie_para_gerenciar
                            has_error = False
                            renamed = False
                            if nome_final != serie_para_gerenciar:
                                _ok_r, _msg_r = sm.renomear_serie(serie_para_gerenciar, nome_final)
                                if not _ok_r:
                                    st.error(_msg_r)
                                    has_error = True
                                else:
                                    renamed = True
                            if not has_error:
                                sm.editar_descricao_serie(nome_final, nova_descricao)
                                st.session_state.edit_mode_serie[serie_para_gerenciar] = False
                                if renamed:
                                    st.session_state.manage_serie_select = nome_final
                                st.session_state.series_list_cache_valid = False
                                st.success("✅ Série atualizada!")
                                st.rerun()
                    with col_cancel:
                        if st.form_submit_button("❌ Cancelar", type="secondary", use_container_width=True):
                            st.session_state.edit_mode_serie[serie_para_gerenciar] = False
                            st.rerun()
        else:
            st.info("ℹ️ Nenhuma série criada ainda")

    # ========== EDITAR SÉRIE SELECIONADA ==========
    with col2:
        if st.session_state.current_carta_id:
            st.subheader("📌 Séries da Carta Atual")

            carta = dm.get_carta(st.session_state.current_carta_id)
            st.caption(f"**#{st.session_state.current_carta_id}** - {carta.get('nome', 'N/A') if carta else 'N/A'}")

            series_da_carta = sm.get_series_carta(st.session_state.current_carta_id)

            # Seleção de séries
            series_selecionadas = st.multiselect(
                "Selecione as séries para esta carta:",
                options=_todas_series,
                default=series_da_carta,
                key="serie_multiselect"
            )

            # Atualizar associações — uma única chamada + um único save_session()
            if set(series_selecionadas) != set(series_da_carta):
                sm.atualizar_series_carta(
                    st.session_state.current_carta_id, series_selecionadas
                )
                st.success("✅ Séries atualizadas!")

            st.markdown("---")

            # Visualizar série completa
            st.subheader("📚 Visualizar Série Completa")

            if _todas_series:
                serie_selecionada = st.selectbox("Escolha uma série:", _todas_series, key="view_serie_select")

                info = sm.get_info_serie(serie_selecionada)
                st.markdown(f"### {serie_selecionada}")
                st.write(f"**Descrição:** {info['descricao'] or 'N/A'}")
                st.write(f"**Total de cartas:** {info['total_cartas']}")

                # Listar cartas — paginadas para evitar centenas de expanders
                cartas_serie = info['cartas']
                if cartas_serie:
                    _TAM_PAG_S = 25
                    _total_c_s = len(cartas_serie)
                    _total_pags_s = max(1, math.ceil(_total_c_s / _TAM_PAG_S))
                    # Resetar página se série mudou
                    if st.session_state.get('_serie_view_atual') != serie_selecionada:
                        st.session_state.serie_page = 1
                        st.session_state['_serie_view_atual'] = serie_selecionada
                    _pag_s = max(1, min(st.session_state.serie_page, _total_pags_s))
                    _ini_s = (_pag_s - 1) * _TAM_PAG_S
                    _fim_s = min(_ini_s + _TAM_PAG_S, _total_c_s)
                    _cartas_pag_s = cartas_serie[_ini_s:_fim_s]

                    if _total_pags_s > 1:
                        _cp1, _cp2, _cp3 = st.columns([1, 2, 1])
                        with _cp1:
                            if st.button("← Anterior", key="serie_pag_ant", use_container_width=True,
                                         disabled=(_pag_s <= 1)):
                                st.session_state.serie_page -= 1
                                st.rerun()
                        with _cp2:
                            st.caption(f"Página {_pag_s} de {_total_pags_s} "
                                       f"({_ini_s+1}–{_fim_s} de {_total_c_s} cartas)")
                        with _cp3:
                            if st.button("Próxima →", key="serie_pag_prox", use_container_width=True,
                                         disabled=(_pag_s >= _total_pags_s)):
                                st.session_state.serie_page += 1
                                st.rerun()

                    _rerun_serie_view = False
                    for _idx_s, carta_id in enumerate(_cartas_pag_s, _ini_s + 1):
                        carta = dm.get_carta(carta_id)
                        if carta:
                            nome = carta.get('nome', 'N/A') if isinstance(carta, dict) else 'N/A'
                            uf_s = carta.get('uf') or 'N/A'
                            with st.expander(f"#{_idx_s} — [{carta_id}] {nome} — {uf_s}"):
                                st.caption(
                                    f"📚 **Catálogo:** {carta.get('catalogo') or 'N/A'} &nbsp;·&nbsp; "
                                    f"🗺️ **UF:** {uf_s} &nbsp;·&nbsp; "
                                    f"📅 **Faixa etária:** {carta.get('faixa_etaria') or 'N/A'} &nbsp;·&nbsp; "
                                    f"🎓 **Instrução:** {carta.get('instrucao') or 'N/A'}"
                                )
                                st.markdown("**Texto da carta:**")
                                _texto_s = carta.get('texto', '') or ''
                                st.markdown(
                                    f'<div style="background-color: var(--bg-tertiary); border: 1px solid var(--border-color); '
                                    f'border-radius: 4px; padding: 12px; font-family: monospace; '
                                    f'white-space: pre-wrap; word-wrap: break-word; color: var(--text-primary); '
                                    f'max-height: 300px; overflow-y: auto;">{_texto_s}</div>',
                                    unsafe_allow_html=True
                                )
                                st.markdown("")
                                _col_abrir_s, _col_remover_s = st.columns(2)
                                with _col_abrir_s:
                                    with st.form(f"abrir_carta_form_{carta_id}_{_idx_s}"):
                                        if st.form_submit_button(
                                            "→ Abrir na aba Explorar",
                                            use_container_width=True
                                        ):
                                            st.session_state.current_carta_id = carta_id
                                            st.session_state.sidebar_series_context = 'explorar'
                                            _rerun_serie_view = True
                                            break
                                with _col_remover_s:
                                    with st.form(f"remover_carta_form_{carta_id}_{_idx_s}"):
                                        st.write(f"**Remover carta #{carta_id} desta série?**")
                                        if st.form_submit_button(
                                            "🗑️ Confirmar remoção",
                                            type="secondary",
                                            use_container_width=True
                                        ):
                                            sm.remover_carta_serie(serie_selecionada, carta_id)
                                            st.success(f"✅ Carta #{carta_id} removida da série '{serie_selecionada}'!")
                                            _rerun_serie_view = True
                                            break
                        else:
                            st.warning(f"⚠️ Carta #{carta_id} não encontrada na base atual")

                    if _rerun_serie_view:
                        st.rerun()

                    st.markdown("")
                    _csv_serie = ExportManager.exportar_serie_csv(
                        _todas_cartas,
                        cartas_serie,
                        serie_selecionada,
                        am.get_todas_anotacoes(),
                        series=sm.series
                    )
                    _col_csv_s3, _col_parquet_s3, _col_pdf_s3 = st.columns(3)
                    with _col_csv_s3:
                        st.download_button(
                            label=f"⬇️ Baixar série '{serie_selecionada}' em CSV",
                            data=_csv_serie,
                            file_name=f"serie_{serie_selecionada.replace(' ', '_')}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key="serie_download_csv"
                        )
                    with _col_parquet_s3:
                        _pq_s3_idx = {}
                        for _ns3, _si3 in sm.series.items():
                            for _cid3 in _si3['cartas']:
                                _pq_s3_idx.setdefault(_cid3, []).append(_ns3)
                        _pq_s3 = ExportManager.exportar_parquet(
                            _todas_cartas,
                            cartas_serie,
                            am.get_todas_anotacoes(),
                            series_idx=_pq_s3_idx
                        )
                        st.download_button(
                            label=f"🗃️ Parquet da série",
                            data=_pq_s3,
                            file_name=f"serie_{serie_selecionada.replace(' ', '_')}.parquet",
                            mime="application/octet-stream",
                            use_container_width=True,
                            key="serie_download_parquet"
                        )
                    with _col_pdf_s3:
                        if st.button("📄 Gerar PDF da série", key="serie_gen_pdf", use_container_width=True):
                            with FeedbackManager.operation_status("📄 Gerando PDF da série..."):
                                _pdf_s3 = ExportManager.exportar_pdf(
                                    _todas_cartas,
                                    cartas_serie,
                                    f"Série: {serie_selecionada}",
                                    am.get_todas_anotacoes(),
                                    series=sm.series
                                )
                            st.download_button(
                                label=f"💾 Baixar PDF da série '{serie_selecionada}'",
                                data=_pdf_s3,
                                file_name=f"serie_{serie_selecionada.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="serie_download_pdf"
                            )

                st.markdown("---")

                # Editar série
                with st.form(f"toggle_edit_serie_form_{serie_selecionada}"):
                    if st.form_submit_button(f"✏️ Editar '{serie_selecionada}'", use_container_width=True):
                        st.session_state.edit_mode_serie[serie_selecionada] = True
                        st.rerun()

                if st.session_state.edit_mode_serie.get(serie_selecionada, False):
                    st.subheader("✏️ Editar Série")

                    novo_nome_serie = st.text_input(
                        "Nome da série:",
                        value=serie_selecionada,
                        key="edit_serie_nome"
                    )
                    nova_descricao = st.text_area(
                        "Descrição:",
                        value=info.get('descricao', ''),
                        key="edit_serie_desc"
                    )

                    with st.form(f"edit_serie_form_{serie_selecionada}"):
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Salvar", use_container_width=True):
                                nome_final = novo_nome_serie.strip() or serie_selecionada
                                has_error = False
                                renamed = False
                                if nome_final != serie_selecionada:
                                    _ok_r, _msg_r = sm.renomear_serie(
                                        serie_selecionada, nome_final
                                    )
                                    if not _ok_r:
                                        st.error(_msg_r)
                                        has_error = True
                                    else:
                                        renamed = True
                                if not has_error:
                                    sm.editar_descricao_serie(
                                        nome_final, nova_descricao
                                    )
                                    st.session_state.edit_mode_serie[serie_selecionada] = False
                                    if renamed:
                                        st.session_state['view_serie_select'] = nome_final
                                    st.session_state.series_list_cache_valid = False
                                    st.success("✅ Série atualizada!")
                                    st.rerun()
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar", type="secondary", use_container_width=True):
                                st.session_state.edit_mode_serie[serie_selecionada] = False
                                st.rerun()

        else:
            st.warning("⚠️ Selecione uma carta para ver suas séries")

        # ---- DOWNLOAD UNIFICADO DE TODAS AS SÉRIES ----
        if _todas_series:
            st.markdown("---")
            st.subheader("📦 Download Unificado — Todas as Séries")
            st.caption(
                "Arquivo único com todas as cartas vinculadas a séries temáticas. "
                "Cada carta aparece uma única vez, com uma coluna/campo indicando todas as séries às quais pertence."
            )
            _unif_col_csv, _unif_col_parquet, _unif_col_pdf = st.columns(3)
            with _unif_col_csv:
                _csv_unif = ExportManager.exportar_todas_series_csv(
                    sm.series,
                    _todas_cartas,
                    am.get_todas_anotacoes()
                )
                st.download_button(
                    label="⬇️ Baixar CSV Unificado (todas as séries)",
                    data=_csv_unif,
                    file_name=f"todas_series_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="unif_download_csv"
                )
            with _unif_col_parquet:
                _pq_unif_idx = {}
                for _nsu, _siu in sm.series.items():
                    for _cidu in _siu['cartas']:
                        _pq_unif_idx.setdefault(_cidu, []).append(_nsu)
                _unif_all_ids = list(_pq_unif_idx.keys())
                _pq_unif = ExportManager.exportar_parquet(
                    _todas_cartas,
                    _unif_all_ids,
                    am.get_todas_anotacoes(),
                    series_idx=_pq_unif_idx
                )
                st.download_button(
                    label="🗃️ Parquet Unificado (todas as séries)",
                    data=_pq_unif,
                    file_name=f"todas_series_{datetime.now().strftime('%Y%m%d_%H%M')}.parquet",
                    mime="application/octet-stream",
                    use_container_width=True,
                    key="unif_download_parquet"
                )
            with _unif_col_pdf:
                if st.button(
                    "📄 Gerar PDF Unificado (todas as séries)",
                    key="unif_gen_pdf",
                    use_container_width=True
                ):
                    with FeedbackManager.operation_status("📄 Gerando PDF unificado..."):
                        _pdf_unif = ExportManager.exportar_todas_series_pdf(
                            sm.series,
                            _todas_cartas,
                            am.get_todas_anotacoes()
                        )
                    st.download_button(
                        label="💾 Baixar PDF Unificado",
                        data=_pdf_unif,
                        file_name=f"todas_series_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="unif_download_pdf"
                    )


# ============================================================================
# ABA 4: EXPORTAR
# ============================================================================

with tab4:
    st.header("📥 Exportar Dados")
    breadcrumb_nav("Home", "Exportar Dados")

    st.info("ℹ️ Exporte seus dados em diversos formatos para análise externa ou backup.")

    # ========== EXPORTAR RESULTADOS DA BUSCA ==========
    if st.session_state.search_results:
        st.subheader("🔍 Exportar Resultados da Busca")
        termo_label = se.last_search_term or "busca"
        n_cartas = len(st.session_state.search_results)
        st.info(f"Filtro ativo: **{termo_label}** — **{n_cartas}** cartas")

        col_exp_csv, col_exp_json, col_exp_html, col_exp_parquet, col_exp_pdf = st.columns(5)

        with col_exp_csv:
            csv_data = ExportManager.exportar_serie_csv(
                _todas_cartas,
                st.session_state.search_results,
                f"busca_{termo_label}",
                am.get_todas_anotacoes(),
                series=sm.series
            )
            st.download_button(
                label="💾 Baixar CSV",
                data=csv_data,
                file_name=f"busca_{termo_label[:30].replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_exp_json:
            json_data = ExportManager.exportar_serie_json(
                _todas_cartas,
                st.session_state.search_results,
                f"busca_{termo_label}",
                am.get_todas_anotacoes()
            )
            st.download_button(
                label="💾 Baixar JSON",
                data=json_data,
                file_name=f"busca_{termo_label[:30].replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True
            )

        with col_exp_html:
            html_busca = ExportManager.gerar_relatorio_busca_html(
                _todas_cartas,
                st.session_state.search_results,
                se.last_results,
                termo_label,
                st.session_state.search_scope,
                am.get_todas_anotacoes(),
                st.session_state.wildcard_matches
            )
            st.download_button(
                label="📄 Relatório HTML",
                data=html_busca,
                file_name=f"relatorio_{termo_label[:30].replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True
            )

        with col_exp_parquet:
            _parquet_busca_idx = {}
            for _ns, _si in sm.series.items():
                for _cid in _si['cartas']:
                    _parquet_busca_idx.setdefault(_cid, []).append(_ns)
            _parquet_busca = ExportManager.exportar_parquet(
                _todas_cartas,
                st.session_state.search_results,
                am.get_todas_anotacoes(),
                series_idx=_parquet_busca_idx
            )
            st.download_button(
                label="🗃️ Parquet",
                data=_parquet_busca,
                file_name=f"busca_{termo_label[:30].replace(' ', '_')}.parquet",
                mime="application/octet-stream",
                use_container_width=True,
                key="busca_download_parquet"
            )

        with col_exp_pdf:
            if st.button("📄 Gerar PDF", key="busca_gen_pdf", use_container_width=True):
                with FeedbackManager.operation_status("📄 Gerando PDF dos resultados..."):
                    _pdf_busca = ExportManager.exportar_pdf(
                        _todas_cartas,
                        st.session_state.search_results,
                        f"Busca: {termo_label}",
                        am.get_todas_anotacoes(),
                        series=sm.series
                    )
                st.download_button(
                    label="💾 Baixar PDF",
                    data=_pdf_busca,
                    file_name=f"busca_{termo_label[:30].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="busca_download_pdf"
                )

        st.markdown("---")

    col1, col2 = st.columns(2)

    # ========== EXPORTAR SÉRIE ==========
    with col1:
        st.subheader("🗂️ Exportar Série Individual")

        if not st.session_state.series_list_cache_valid:
            st.session_state.series_list_cache = sm.get_todas_series()
            st.session_state.series_list_cache_valid = True
        series_list = st.session_state.series_list_cache

        if series_list:
            serie_export = st.selectbox("Escolha a série:", series_list, key="export_serie_select")

            col_csv, col_json, col_parquet, col_pdf = st.columns(4)

            with col_csv:
                if st.button("📊 CSV", key="export_serie_csv", use_container_width=True):
                    cartas_serie = sm.get_cartas_serie(serie_export)
                    csv_data = ExportManager.exportar_serie_csv(
                        _todas_cartas,
                        cartas_serie,
                        serie_export,
                        am.get_todas_anotacoes(),
                        series=sm.series
                    )
                    st.download_button(
                        label="💾 Baixar CSV",
                        data=csv_data,
                        file_name=f"serie_{serie_export.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )

            with col_json:
                if st.button("📋 JSON", key="export_serie_json", use_container_width=True):
                    cartas_serie = sm.get_cartas_serie(serie_export)
                    json_data = ExportManager.exportar_serie_json(
                        _todas_cartas,
                        cartas_serie,
                        serie_export,
                        am.get_todas_anotacoes()
                    )
                    st.download_button(
                        label="💾 Baixar JSON",
                        data=json_data,
                        file_name=f"serie_{serie_export.replace(' ', '_')}.json",
                        mime="application/json"
                    )

            with col_parquet:
                if st.button("🗃️ Parquet", key="export_serie_parquet", use_container_width=True):
                    cartas_serie = sm.get_cartas_serie(serie_export)
                    _pq_serie_idx = {}
                    for _ns, _si in sm.series.items():
                        for _cid in _si['cartas']:
                            _pq_serie_idx.setdefault(_cid, []).append(_ns)
                    _pq_serie = ExportManager.exportar_parquet(
                        _todas_cartas,
                        cartas_serie,
                        am.get_todas_anotacoes(),
                        series_idx=_pq_serie_idx
                    )
                    st.download_button(
                        label="💾 Baixar Parquet",
                        data=_pq_serie,
                        file_name=f"serie_{serie_export.replace(' ', '_')}.parquet",
                        mime="application/octet-stream"
                    )

            with col_pdf:
                if st.button("📄 PDF", key="export_serie_pdf", use_container_width=True):
                    cartas_serie = sm.get_cartas_serie(serie_export)
                    with FeedbackManager.operation_status("📄 Gerando PDF da série..."):
                        _pdf_serie_exp = ExportManager.exportar_pdf(
                            _todas_cartas,
                            cartas_serie,
                            f"Série: {serie_export}",
                            am.get_todas_anotacoes(),
                            series=sm.series
                        )
                    st.download_button(
                        label="💾 Baixar PDF",
                        data=_pdf_serie_exp,
                        file_name=f"serie_{serie_export.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.warning("⚠️ Crie uma série primeiro para exportar")

    # ========== EXPORTAR CADERNO ==========
    with col2:
        st.subheader("📖 Exportar Caderno de Pesquisa")

        caderno = am.get_caderno_pesquisa()

        if caderno:
            col_txt, col_md = st.columns(2)

            with col_txt:
                txt_data = ExportManager.exportar_caderno_txt(caderno)
                st.download_button(
                    label="💾 TXT",
                    data=txt_data,
                    file_name="caderno_pesquisa.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            with col_md:
                md_data = ExportManager.exportar_caderno_markdown(caderno)
                st.download_button(
                    label="💾 Markdown",
                    data=md_data,
                    file_name="caderno_pesquisa.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        else:
            st.info("ℹ️ Seu caderno está vazio")

    st.markdown("---")

    # ========== EXPORTAR TUDO ==========
    st.subheader("🎁 Exportar Tudo")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📦 Todas as Séries (JSON)", use_container_width=True):
            json_data = ExportManager.exportar_todas_series_json(
                sm.series,
                _todas_cartas,
                am.get_todas_anotacoes()
            )
            st.download_button(
                label="💾 Baixar JSON Completo",
                data=json_data,
                file_name="todas_series.json",
                mime="application/json",
                use_container_width=True
            )

    with col2:
        if st.button("🤐 Pacote ZIP Completo", use_container_width=True):
            zip_data = ExportManager.exportar_zip_completo(
                sm.series,
                _todas_cartas,
                am.get_todas_anotacoes(),
                am.get_caderno_pesquisa()
            )
            st.download_button(
                label="💾 Baixar ZIP",
                data=zip_data,
                file_name="historicidades_democraticas.zip",
                mime="application/zip",
                use_container_width=True
            )

    with col1:
        if st.button("🗃️ Parquet da Base Completa", use_container_width=True,
                     key="btn_parquet_base"):
            _all_ids_pq = list(_todas_cartas.keys())
            _pq_base_idx = {}
            for _ns, _si in sm.series.items():
                for _cid in _si['cartas']:
                    _pq_base_idx.setdefault(_cid, []).append(_ns)
            _pq_base = ExportManager.exportar_parquet(
                _todas_cartas,
                _all_ids_pq,
                am.get_todas_anotacoes(),
                series_idx=_pq_base_idx
            )
            st.download_button(
                label="💾 Baixar Parquet — Base Completa",
                data=_pq_base,
                file_name=f"base_completa_{datetime.now().strftime('%Y%m%d_%H%M')}.parquet",
                mime="application/octet-stream",
                use_container_width=True,
                key="download_parquet_base"
            )

    st.markdown("")

    # PDF de todas as séries (só aparece se houver séries criadas)
    if not st.session_state.series_list_cache_valid:
        st.session_state.series_list_cache = sm.get_todas_series()
        st.session_state.series_list_cache_valid = True
    _series_list_tudo = st.session_state.series_list_cache
    if _series_list_tudo:
        if st.button("📄 PDF de Todas as Séries", use_container_width=True):
            _todos_ids = []
            for _sn in _series_list_tudo:
                _todos_ids.extend(sm.get_cartas_serie(_sn))
            _todos_ids = list(dict.fromkeys(_todos_ids))
            with FeedbackManager.operation_status("📄 Gerando PDF de todas as séries..."):
                _pdf_todas = ExportManager.exportar_pdf(
                    _todas_cartas,
                    _todos_ids,
                    "Todas as Séries Temáticas",
                    am.get_todas_anotacoes(),
                    series=sm.series
                )
            st.download_button(
                label="💾 Baixar PDF — Todas as Séries",
                data=_pdf_todas,
                file_name=f"todas_series_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    # PDF da base completa
    _n_base = len(_todas_cartas)
    st.caption(
        f"A base carregada possui **{_n_base:,}** cartas. "
        "Para bases muito grandes a geração pode demorar alguns minutos."
    )
    if st.button("📄 PDF da Base Completa Carregada", use_container_width=True,
                 key="btn_pdf_base_completa"):
        _all_ids = list(_todas_cartas.keys())
        with st.spinner(f"Gerando PDF de {len(_all_ids):,} cartas... aguarde."):
            _pdf_base = ExportManager.exportar_pdf(
                _todas_cartas,
                _all_ids,
                "Base Completa — Historicidades Democráticas",
                am.get_todas_anotacoes(),
                series=sm.series
            )
        st.download_button(
            label="💾 Baixar PDF — Base Completa",
            data=_pdf_base,
            file_name=f"base_completa_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_pdf_base"
        )

    st.markdown("---")

    # ========== RELATÓRIO HTML ==========
    st.subheader("📄 Relatório Analítico da Base")

    st.caption(
        "Gera relatório completo com estatísticas gerais, gráficos interativos (distribuição por sexo, "
        "UF, faixa etária, instrução, renda, atividade, zona urbana/rural, origem e catálogos), "
        "tabelas geográficas, séries temáticas e caderno de pesquisa."
    )

    if st.button("📊 Gerar Relatório Analítico Completo", use_container_width=True):
        with FeedbackManager.operation_status("📊 Gerando relatório com gráficos..."):
            html_report = ExportManager.gerar_relatorio_html(
                sm.series,
                _todas_cartas,
                am.get_todas_anotacoes(),
                am.get_caderno_pesquisa()
            )
        st.download_button(
            label="💾 Baixar Relatório HTML",
            data=html_report,
            file_name=f"relatorio_analitico_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            use_container_width=True
        )


# ============================================================================
# ABA 5: CONFIGURAÇÕES
# ============================================================================

with tab5:
    st.header("⚙️ Configurações")
    breadcrumb_nav("Home", "Configurações")

    # ========== BASES DE DADOS ==========
    st.subheader("🗄️ Gerenciamento de Bases de Dados")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Base Atual")
        st.info(f"📁 {dm.current_database_name or 'Nenhuma'}")
        st.caption(f"{dm.get_total_cartas()} cartas")

    with col2:
        st.markdown("#### Carregar Base")
        uploaded_file = st.file_uploader(
            "Selecione um arquivo JSON:",
            type=['json'],
            key="upload_db"
        )

        if uploaded_file:
            file_content = uploaded_file.getvalue().decode('utf-8')
            filename = uploaded_file.name
            success, msg = dm.upload_database(file_content, filename)

            if success:
                st.session_state.nome_index = dm.get_nome_index()
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")

    # ========== BACKUP E RESTORE ==========
    st.subheader("💾 Backup e Restore")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Fazer Backup")
        if st.button("📦 Exportar Sessão Completa", use_container_width=True):
            session_data = {
                'anotacoes': am.anotacoes,
                'caderno_pesquisa': am.caderno_pesquisa,
                'series': {
                    nome: {
                        'cartas': list(info['cartas']),
                        'descricao': info.get('descricao', ''),
                        'criada_em': info.get('criada_em', '')
                    }
                    for nome, info in sm.series.items()
                },
                'timestamp': datetime.now().isoformat()
            }

            import json as json_module
            backup_json = json_module.dumps(session_data, ensure_ascii=False, indent=2)

            st.download_button(
                label="💾 Baixar Backup",
                data=backup_json,
                file_name=f"backup_historicidades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    with col2:
        st.markdown("#### Restaurar Backup")
        backup_file = st.file_uploader(
            "Selecione arquivo de backup:",
            type=['json'],
            key="restore_backup"
        )

        if backup_file:
            try:
                import json as json_module
                backup_data = json_module.loads(backup_file.getvalue().decode('utf-8'))

                with st.form("restore_backup_form"):
                    st.write("**Restaurar este backup?** Isso sobrescreverá suas anotações e séries atuais.")
                    if st.form_submit_button("✅ Confirmar restauração", use_container_width=True):
                        am.anotacoes = backup_data.get('anotacoes', {})
                        am.caderno_pesquisa = backup_data.get('caderno_pesquisa', '')
                        am.save_session()

                        # Restaurar séries
                        series_backup = backup_data.get('series', {})
                        sm.series = {}
                        for nome, info in series_backup.items():
                            sm.series[nome] = {
                                'cartas': set(info.get('cartas', [])),
                                'descricao': info.get('descricao', ''),
                                'criada_em': info.get('criada_em', '')
                            }
                        sm.save_session()

                        st.success("✅ Backup restaurado com sucesso!")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ Erro ao restaurar: {str(e)}")

    st.markdown("---")

    # ========== INFORMAÇÕES GERAIS ==========
    st.subheader("ℹ️ Informações da Sessão")

    info_col1, info_col2, info_col3 = st.columns(3)

    with info_col1:
        st.metric("Anotações", am.contar_anotacoes())

    with info_col2:
        st.metric("Séries", sm.total_series())

    with info_col3:
        st.metric(
            "Cartas nas Séries",
            sm.total_cartas_series()
        )

    st.markdown("---")

    # ========== ÍNDICE DE STEMS (BUSCA POR VARIAÇÕES) ==========
    st.subheader("🧬 Índice de Stems (Busca por Variações)")
    st.caption(
        "A busca em modo 'Variações' (aba Explorar) reconhece automaticamente "
        "flexões de qualquer palavra (radical RSLP), sem depender de uma lista "
        "fixa de termos. Requer este índice pré-computado."
    )

    _db_name_stem = dm.current_database_name
    _cartas_stem = _todas_cartas

    _status_stem = stem_e.get_status(_db_name_stem, _cartas_stem)

    _col_st1, _col_st2, _col_st3, _col_st4 = st.columns(4)
    _col_st1.metric(
        "Cache existe",
        "✅ Sim" if _status_stem['cache_existe'] else "❌ Não"
    )
    _col_st2.metric(
        "Cache válido",
        "✅ Sim" if _status_stem['cache_valido'] else "⚠️ Não"
    )
    _col_st3.metric(
        "Cartas indexadas",
        f"{_status_stem['total_indexado']:,}" if _status_stem['total_indexado'] > 0 else "—"
    )
    _col_st4.metric(
        "Radicais distintos",
        f"{_status_stem['total_radicais']:,}" if _status_stem['total_radicais'] > 0 else "—"
    )

    _stem_cache_valido = _status_stem['cache_valido']

    if _stem_cache_valido:
        st.success("✅ O índice de stems está pronto. A busca por 'Variações' já pode ser usada.")
    elif not _status_stem['cache_existe']:
        st.info(
            "ℹ️ **Índice de stems não encontrado.** "
            "É necessário pré-computá-lo antes de usar a busca em modo 'Variações'. "
            "O processo ocorre **uma única vez por base de dados** e pode levar alguns minutos."
        )
    else:
        st.warning(
            "⚠️ **Cache desatualizado.** A base de dados foi alterada desde a última indexação. "
            "Clique no botão abaixo para reindexar."
        )

    if st.button(
        "⚡ Pré-computar Índice de Stems",
        disabled=_stem_cache_valido,
        use_container_width=True,
        key="btn_computar_stems"
    ):
        _barra_progresso_stem = st.progress(0)
        _texto_status_stem = st.empty()

        def _callback_progresso_stem(atual: int, total_c: int) -> None:
            pct = atual / total_c
            _barra_progresso_stem.progress(pct)
            _texto_status_stem.text(
                f"Processando… {atual:,}/{total_c:,} cartas ({pct * 100:.1f}%)"
            )

        _t0_stem = time.time()
        _ok_stem, _msg_stem = stem_e.compute_stem_index(
            cartas=_cartas_stem,
            db_name=_db_name_stem,
            progress_callback=_callback_progresso_stem
        )
        _tempo_stem = time.time() - _t0_stem

        _barra_progresso_stem.progress(1.0)
        _texto_status_stem.empty()

        if _ok_stem:
            st.success(
                f"✅ Indexação concluída!  \n"
                f"{_msg_stem}  \n"
                f"Tempo total: {_tempo_stem:.0f}s ({_tempo_stem / 60:.1f} min)"
            )
        else:
            st.error(f"❌ Erro na indexação: {_msg_stem}")

        st.rerun()

    st.markdown("---")

    # ========== LIMPEZA ==========
    st.subheader("🗑️ Limpeza de Dados")

    col1, col2 = st.columns(2)

    with col1:
        with st.form("clear_annotations_form"):
            st.write("**Limpar TODAS as anotações?** Isso não pode ser desfeito.")
            if st.form_submit_button("🗑️ Confirmar limpeza", type="secondary", use_container_width=True):
                am.anotacoes = {}
                am.save_session()
                st.success("✅ Anotações limpas!")
                st.rerun()

    with col2:
        with st.form("clear_notebook_form"):
            st.write("**Limpar o caderno de pesquisa?** Isso não pode ser desfeito.")
            if st.form_submit_button("🗑️ Confirmar limpeza", type="secondary", use_container_width=True):
                am.caderno_pesquisa = ""
                am.save_session()
                st.success("✅ Caderno limpo!")
                st.rerun()


# ============================================================================
# ABA 6: GRÁFICOS E TABELAS
# ============================================================================

with tab6:
    # Lazy load: Tab carrega apenas quando clicado
    if not is_tab_loaded(6):
        st.info("⏳ Carregando gráficos e tabelas na primeira visualização...")
        mark_tab_loaded(6)
        st.rerun()

    st.header("📊 Gráficos e Tabelas")
    breadcrumb_nav("Home", "Gráficos e Tabelas")

    # ========== SELETOR DE ESCOPO ==========
    st.subheader("Escopo dos Dados")

    col_escopo, col_spacer = st.columns([3, 1])
    with col_escopo:
        escopo = st.radio(
            "Selecione o escopo para análise:",
            ["Base Toda", "Resultado da Busca de Termos", "Resultado da Busca Semântica", "Por Filtro(s)", "Por Série(s)"],
            horizontal=True,
            label_visibility="collapsed"
        )

    # ========== LÓGICA DE SELEÇÃO DO DATAFRAME ==========
    todas_cartas = _todas_cartas
    cartas_filtradas = {}
    contexto_str = ""

    if escopo == "Base Toda":
        cartas_filtradas = todas_cartas
        contexto_str = f"Base Toda ({len(cartas_filtradas)} cartas)"

    elif escopo == "Resultado da Busca de Termos":
        if not st.session_state.search_results:
            st.warning("⚠️ Nenhuma busca realizada. Realize uma busca avançada acima para usar este escopo.")
            cartas_filtradas = {}
        else:
            ids_busca = set(st.session_state.search_results)
            cartas_filtradas = {k: v for k, v in todas_cartas.items() if k in ids_busca}
            contexto_str = f"Resultado da Busca de Termos ({len(cartas_filtradas)} cartas)"

    elif escopo == "Resultado da Busca Semântica":
        _threshold_t6 = st.session_state.get("semantic_threshold", 0.35)
        _sem_ids = [
            r[0] for r in st.session_state.semantic_results
            if r[1] >= _threshold_t6
        ] if st.session_state.semantic_results else []
        if not _sem_ids:
            if not st.session_state.semantic_results:
                st.warning("⚠️ Nenhuma busca semântica realizada. Execute uma consulta na aba '🧠 Busca Semântica' para usar este escopo.")
            else:
                st.warning(f"⚠️ Nenhuma carta acima do threshold atual ({_threshold_t6:.2f}). Ajuste o slider na aba '🧠 Busca Semântica'.")
            cartas_filtradas = {}
        else:
            ids_sem = set(_sem_ids)
            cartas_filtradas = {k: v for k, v in todas_cartas.items() if k in ids_sem}
            contexto_str = f"Resultado da Busca Semântica — threshold ≥ {_threshold_t6:.2f} ({len(cartas_filtradas)} cartas)"

    elif escopo == "Por Filtro(s)":
        if not st.session_state.filter_results:
            st.warning("⚠️ Nenhum filtro aplicado. Configure os filtros na aba '🎯 Filtros' para usar este escopo.")
            cartas_filtradas = {}
        else:
            ids_filtro = set(st.session_state.filter_results)
            cartas_filtradas = {k: v for k, v in todas_cartas.items() if k in ids_filtro}
            n_filtros = len(st.session_state.active_filters)
            contexto_str = f"Por Filtro(s) - {n_filtros} filtro(s) ativo(s) ({len(cartas_filtradas)} cartas)"

    else:  # Por Série(s)
        if not _todas_series:
            st.warning("⚠️ Nenhuma série criada. Crie séries temáticas na aba 'Séries Temáticas' para usar este escopo.")
            cartas_filtradas = {}
        else:
            series_selecionadas = st.multiselect(
                "Selecione uma ou mais séries:",
                _todas_series,
                default=[_todas_series[0]] if _todas_series else []
            )

            if series_selecionadas:
                ids_series = set()
                for serie in series_selecionadas:
                    ids_series.update(sm.get_cartas_serie(serie))
                cartas_filtradas = {k: v for k, v in todas_cartas.items() if k in ids_series}
                serie_names = ", ".join(series_selecionadas)
                contexto_str = f"Série(s): {serie_names} ({len(cartas_filtradas)} cartas)"
            else:
                cartas_filtradas = {}
                contexto_str = "Nenhuma série selecionada"

    # ========== INDICADOR DE CONTEXTO ==========
    if cartas_filtradas:
        st.info(f"📍 Exibindo {len(cartas_filtradas)} cartas — {contexto_str}")

        # Pré-computa contagens com cache — evita value_counts em 72K linhas por render
        _db_name = dm.current_database_name
        _card_ids_t6 = tuple(sorted(cartas_filtradas.keys()))
        _cd = compute_chart_data_cached(_db_name, _card_ids_t6, len(_todas_cartas))
        colunas_disponiveis = set(_cd['_columns'])
        _plotly_colors = get_plotly_color_palette()

        # ========== SEÇÃO A: PERFIL DEMOGRÁFICO ==========
        with st.expander("👤 Perfil Demográfico", expanded=True):
            if not any(col in colunas_disponiveis for col in ['sexo', 'estado_civil', 'faixa_etaria', 'morador']):
                st.info("ℹ️ Essa base não contém dados demográficos detalhados.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    if 'sexo' in _cd:
                        st.plotly_chart(px.pie(values=_cd['sexo']['values'], names=_cd['sexo']['names'],
                                               hole=0.4, title="Distribuição por Sexo",
                                               color_discrete_sequence=_plotly_colors), use_container_width=True)
                    if 'estado_civil' in _cd:
                        st.plotly_chart(px.pie(values=_cd['estado_civil']['values'], names=_cd['estado_civil']['names'],
                                               hole=0.4, title="Estado Civil",
                                               color_discrete_sequence=_plotly_colors), use_container_width=True)
                with col2:
                    if 'faixa_etaria' in _cd:
                        _d = _cd['faixa_etaria']
                        _fig = px.bar(x=_d['names'], y=_d['values'], title="Faixa Etária",
                                      labels={'x': 'Faixa Etária', 'y': 'Quantidade'},
                                      color_discrete_sequence=[_plotly_colors[0]])
                        _fig.update_xaxes(tickangle=-45)
                        st.plotly_chart(_fig, use_container_width=True)
                    if 'morador' in _cd:
                        st.plotly_chart(px.pie(values=_cd['morador']['values'], names=_cd['morador']['names'],
                                               hole=0.4, title="Zona (Urbana/Rural)",
                                               color_discrete_sequence=_plotly_colors), use_container_width=True)

            col3, col4 = st.columns(2)
            with col3:
                if 'instrucao' in _cd:
                    _d = _cd['instrucao']
                    st.plotly_chart(px.bar(x=_d['values'], y=_d['names'], orientation='h', title="Escolaridade",
                                           color_discrete_sequence=[_plotly_colors[0]]),
                                    use_container_width=True)
            with col4:
                if 'faixa_renda' in _cd:
                    _d = _cd['faixa_renda']
                    st.plotly_chart(px.bar(x=_d['values'], y=_d['names'], orientation='h', title="Faixa de Renda",
                                           color_discrete_sequence=[_plotly_colors[0]]),
                                    use_container_width=True)

        # ========== SEÇÃO B: LOCALIDADE ==========
        with st.expander("📍 Localidade", expanded=True):
            if not any(col in colunas_disponiveis for col in ['uf', 'municipio']):
                st.info("ℹ️ Essa base não contém dados de localidade.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    if 'uf' in _cd:
                        _d = _cd['uf']
                        _fig = px.bar(x=_d['names'][:15], y=_d['values'][:15],
                                      title="Cartas por UF (Top 15)", labels={'x': 'Estado', 'y': 'Quantidade'},
                                      color_discrete_sequence=[_plotly_colors[0]])
                        _fig.update_xaxes(tickangle=-45)
                        st.plotly_chart(_fig, use_container_width=True)
                with col2:
                    if 'municipio' in _cd:
                        _d = _cd['municipio']
                        st.subheader("Municípios Mais Frequentes (Top 20)")
                        st.dataframe(pd.DataFrame({'Município': _d['names'][:20], 'Quantidade': _d['values'][:20]}),
                                     use_container_width=True, hide_index=True)
                if 'uf' in _cd:
                    st.subheader("Cartas por Estado (Todos)")
                    _d = _cd['uf']
                    _uf_df = pd.DataFrame({'Estado': _d['names'][::-1], 'Quantidade': _d['values'][::-1]})
                    st.plotly_chart(px.bar(_uf_df, x='Quantidade', y='Estado', orientation='h',
                                           title="Distribuição Geográfica das Cartas por Estado",
                                           color='Quantidade', color_continuous_scale=['#2b2d33', '#d97706']),
                                    use_container_width=True)

        # ========== SEÇÃO C: CONTEÚDO TEMÁTICO ==========
        with st.expander("📚 Conteúdo Temático", expanded=True):
            if not any(col in colunas_disponiveis for col in ['atividade', 'origem', 'catalogo', 'indexacao']):
                st.info("ℹ️ Essa base não contém dados temáticos/catalográficos.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    if 'atividade' in _cd:
                        _d = _cd['atividade']
                        st.plotly_chart(px.bar(x=_d['values'], y=_d['names'], orientation='h',
                                               title="Atividade/Ocupação",
                                               labels={'x': 'Quantidade', 'y': 'Atividade'},
                                               color_discrete_sequence=[_plotly_colors[0]]),
                                        use_container_width=True)
                    if 'origem' in _cd:
                        _d = _cd['origem']
                        _fig = px.bar(x=_d['names'], y=_d['values'], title="Cartas por Origem (Lote)",
                                      labels={'x': 'Origem', 'y': 'Quantidade'},
                                      color_discrete_sequence=[_plotly_colors[0]])
                        _fig.update_xaxes(tickangle=-45)
                        st.plotly_chart(_fig, use_container_width=True)
                with col2:
                    if 'catalogo' in _cd:
                        _d = _cd['catalogo']
                        st.plotly_chart(px.bar(x=_d['values'][:15], y=_d['names'][:15], orientation='h',
                                               title="Catálogos Mais Frequentes (Top 15)",
                                               color_discrete_sequence=[_plotly_colors[0]]),
                                        use_container_width=True)
                    if 'indexacao' in _cd:
                        _d = _cd['indexacao']
                        st.plotly_chart(px.bar(x=_d['values'][:20], y=_d['names'][:20], orientation='h',
                                               title="Indexações Mais Frequentes (Top 20)",
                                               color_discrete_sequence=[_plotly_colors[0]]),
                                        use_container_width=True)

    else:
        st.error("❌ Nenhuma carta disponível para o escopo selecionado. Ajuste suas opções.")


# ============================================================================
# ABA 7: FILTROS
# ============================================================================

def _get_unique_values_from_dict(cartas_dict, campo):
    """Calcula valores únicos diretamente do dicionário (para subconjuntos filtrados)."""
    valores = set()
    for carta in cartas_dict.values():
        valor = carta.get(campo)
        if valor and str(valor).strip() and str(valor) != 'nan' and str(valor) != 'None':
            valores.add(str(valor).strip())
    return sorted(list(valores))


with tab7:
    # Lazy load: Tab carrega apenas quando clicado
    if not is_tab_loaded(7):
        st.info("⏳ Carregando filtros na primeira visualização...")
        mark_tab_loaded(7)
        st.rerun()

    st.header("🎯 Filtros Avançados")
    breadcrumb_nav("Home", "Filtros Avançados")

    st.markdown("Utilize os filtros abaixo para buscar cartas por suas características. Você pode combinar múltiplos filtros simultaneamente.")

    # Determinar o universo de cartas baseado em search_results
    if st.session_state.search_results:
        # Se há resultados da busca avançada, usar aquele universo
        ids_universo = set(st.session_state.search_results)
        cartas_universo = {k: v for k, v in _todas_cartas.items() if k in ids_universo}
        universo_info = f"🔍 Filtros aplicados ao escopo da busca avançada ({len(cartas_universo)} cartas)"
    else:
        # Caso contrário, usar base inteira
        cartas_universo = _todas_cartas
        universo_info = f"📚 Filtros aplicados à base inteira ({len(cartas_universo)} cartas)"

    st.caption(universo_info)
    st.markdown("---")

    # Campos filtráveis
    campos_filtro = {
        'sexo': '👥 Sexo',
        'faixa_etaria': '📅 Faixa Etária',
        'estado_civil': '💑 Estado Civil',
        'faixa_renda': '💰 Faixa de Renda',
        'atividade': '💼 Atividade/Ocupação',
        'instrucao': '🎓 Instrução',
        'morador': '🏘️ Zona (Urbana/Rural)',
        'uf': '🗺️ Estado (UF)',
        'municipio': '🏙️ Município',
        'catalogo': '📚 Catálogo',
        'indexacao': '📇 Indexação',
        'destinatario': '📮 Destinatário'
    }

    st.subheader("⚙️ Configurar Filtros")

    # Pré-computa todos os unique values em UMA ÚNICA passagem
    _uv_key_tab7 = (bool(st.session_state.search_results), len(cartas_universo))
    if st.session_state.get('_uv_tab7_key') != _uv_key_tab7:
        if not st.session_state.search_results:
            _uv_tab7 = {c: dm.get_campo_unique_values(c) for c in campos_filtro}
        else:
            # Duplo loop otimizado: itera sobre subset de cartas
            _uv_acc = {c: set() for c in campos_filtro}
            for _carta_uv in cartas_universo.values():
                for _campo_uv in campos_filtro:
                    _v = _carta_uv.get(_campo_uv)
                    if _v and str(_v).strip() and str(_v) != 'nan' and str(_v) != 'None':
                        _uv_acc[_campo_uv].add(str(_v).strip())
            _uv_tab7 = {c: sorted(list(vals)) for c, vals in _uv_acc.items()}
        st.session_state['_uv_tab7_key'] = _uv_key_tab7
        st.session_state['_uv_tab7'] = _uv_tab7
    else:
        _uv_tab7 = st.session_state['_uv_tab7']

    # Layout dos filtros em colunas
    cols = st.columns(3)

    for idx, (campo, label) in enumerate(campos_filtro.items()):
        col = cols[idx % 3]

        with col:
            valores_unicos = _uv_tab7.get(campo, [])

            st.multiselect(
                label,
                options=valores_unicos,
                default=st.session_state.active_filters.get(campo, []),
                key=f"filter_{campo}"
            )

            valores = st.session_state.get(f"filter_{campo}", [])
            if valores:
                st.session_state.active_filters[campo] = valores
            elif campo in st.session_state.active_filters:
                del st.session_state.active_filters[campo]

    st.markdown("---")

    # Aplicar filtros (com cache por chave para evitar reprocessamento a cada rerun)
    if st.session_state.active_filters:
        _filter_key = (
            json.dumps(st.session_state.active_filters, sort_keys=True),
            bool(st.session_state.search_results)
        )

        if _filter_key != st.session_state.get('_last_filter_key'):
            cartas_filtradas = {}

            for carta_id, carta in cartas_universo.items():
                incluir_carta = True

                for campo, valores_selecionados in st.session_state.active_filters.items():
                    valor_carta = str(carta.get(campo, '')).strip()
                    valores_correspondentes = [str(v).strip() for v in valores_selecionados]

                    if valor_carta and valor_carta != 'nan' and valor_carta != 'None':
                        if valor_carta not in valores_correspondentes:
                            incluir_carta = False
                            break
                    else:
                        if valores_selecionados:
                            incluir_carta = False
                            break

                if incluir_carta:
                    cartas_filtradas[carta_id] = carta

            st.session_state.filter_results = list(cartas_filtradas.keys())
            st.session_state._last_filter_key = _filter_key
    else:
        st.session_state.filter_results = []
        st.session_state._last_filter_key = None

    # Exibir resultados dos filtros
    st.subheader("📋 Resultados")

    n_filtros_ativos = len(st.session_state.active_filters)
    n_resultados = len(st.session_state.filter_results)

    if n_filtros_ativos > 0:
        filtros_info = " + ".join([
            f"{campos_filtro.get(k, k)}: {len(v)} opção(ões)"
            for k, v in st.session_state.active_filters.items()
        ])
        st.info(f"🔍 **{n_resultados}** carta(s) encontrada(s) com: {filtros_info}")

        if st.session_state.filter_results:
            ids_resultado = st.session_state.filter_results

            # Garante que filter_nav_select aponta para um ID válido
            if st.session_state.get('filter_nav_select') not in ids_resultado:
                st.session_state.filter_nav_select = ids_resultado[0]

            # Navegação e seleção
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                _filter_nome_index = st.session_state.nome_index

                st.selectbox(
                    "Selecionar carta dos resultados:",
                    options=ids_resultado,
                    format_func=lambda x: f"#{x} - {_filter_nome_index.get(x, 'N/A')[:40]}...",
                    key="filter_nav_select"
                )

                _sel = st.session_state.filter_nav_select
                if _sel != st.session_state.current_carta_id:
                    st.session_state.current_carta_id = _sel
                    st.session_state.sidebar_series_carta_id = _sel
                    st.session_state.sidebar_series_context = 'filtro'

            with col2:
                def _filter_anterior():
                    _sel = st.session_state.get('filter_nav_select')
                    try:
                        idx = ids_resultado.index(_sel)
                        if idx > 0:
                            _new = ids_resultado[idx - 1]
                            st.session_state.filter_nav_select = _new
                            st.session_state.current_carta_id = _new
                            st.session_state.sidebar_series_carta_id = _new
                            st.session_state.sidebar_series_context = 'filtro'
                    except ValueError:
                        pass
                st.button("⬅️ Anterior", use_container_width=True, key="filter_btn_anterior",
                          on_click=_filter_anterior)

            with col3:
                def _filter_proximo():
                    _sel = st.session_state.get('filter_nav_select')
                    try:
                        idx = ids_resultado.index(_sel)
                        if idx < len(ids_resultado) - 1:
                            _new = ids_resultado[idx + 1]
                            st.session_state.filter_nav_select = _new
                            st.session_state.current_carta_id = _new
                            st.session_state.sidebar_series_carta_id = _new
                            st.session_state.sidebar_series_context = 'filtro'
                    except ValueError:
                        pass
                st.button("Próximo ➡️", use_container_width=True, key="filter_btn_proximo",
                          on_click=_filter_proximo)

            st.markdown("---")

            # Exibe a carta apontada por filter_nav_select (sempre válido)
            _carta_id_filtro = st.session_state.filter_nav_select
            carta = dm.get_carta(_carta_id_filtro)

            if carta:
                try:
                    current_idx_display = ids_resultado.index(_carta_id_filtro) + 1
                except ValueError:
                    current_idx_display = 1

                st.markdown(f"### 📄 Carta **{current_idx_display}** de **{len(ids_resultado)}**")

                col1, col2, col3 = st.columns([1, 2, 2])
                with col1:
                    st.markdown(f"**ID:** `{_carta_id_filtro}`")
                with col2:
                    st.markdown(f"**Autor:** {carta.get('nome', 'N/A')}")
                with col3:
                    municipio = carta.get('municipio')
                    uf = carta.get('uf')
                    if municipio and uf and municipio != 'None' and uf != 'None':
                        local = f"{municipio}/{uf}"
                    else:
                        local = "N/A"
                    st.markdown(f"**Local:** {local}")

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write("")
                with col2:
                    st.markdown(f"**Destinatário:** {carta.get('destinatario', 'N/A')}")

                # Texto da carta
                st.subheader("📖 Texto")
                texto = carta.get('texto', '')
                st.markdown(f"""
                <div style="background-color: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 4px; padding: 15px; min-height: 200px; overflow-y: auto; font-family: monospace; white-space: pre-wrap; word-wrap: break-word; color: var(--text-primary);">
                {texto}
                </div>
                """, unsafe_allow_html=True)

                # Botão Gerenciar Séries (sidebar)
                st.markdown("")
                _is_in_sidebar_filtro = (
                    st.session_state.get('sidebar_series_carta_id') == _carta_id_filtro
                    and st.session_state.get('sidebar_series_context') == 'filtro'
                )
                if _todas_series:
                    def _toggle_painel_filtro(_cid=_carta_id_filtro):
                        if (st.session_state.get('sidebar_series_carta_id') == _cid
                                and st.session_state.get('sidebar_series_context') == 'filtro'):
                            st.session_state.sidebar_series_context = 'explorar'
                            st.session_state.sidebar_series_carta_id = None
                        else:
                            st.session_state.sidebar_series_carta_id = _cid
                            st.session_state.sidebar_series_context = 'filtro'

                    st.button(
                        "✅ Na sidebar" if _is_in_sidebar_filtro else "🗂️ Gerenciar séries",
                        key=f"filtro_mgmt_btn_{_carta_id_filtro}",
                        use_container_width=True,
                        on_click=_toggle_painel_filtro
                    )
                else:
                    st.caption("ℹ️ Nenhuma série criada. Crie uma na aba 🗂️ Séries Temáticas.")

                # Metadados
                st.subheader("📋 Metadados")

                data_raw = carta.get('data') or 'N/A'
                if data_raw != 'N/A' and str(data_raw) != 'None':
                    try:
                        data_obj = pd.to_datetime(data_raw)
                        data_formatada = data_obj.strftime('%d/%m/%Y')
                    except:
                        data_formatada = str(data_raw).split()[0] if ' ' in str(data_raw) else str(data_raw)
                else:
                    data_formatada = 'N/A'

                metadados = {
                    "Origem": carta.get('origem') or 'N/A',
                    "Data": data_formatada,
                    "Sexo": carta.get('sexo') or 'N/A',
                    "Instrução": carta.get('instrucao') or 'N/A',
                    "Estado Civil": carta.get('estado_civil') or 'N/A',
                    "Faixa Etária": carta.get('faixa_etaria') or 'N/A',
                    "Faixa Renda": carta.get('faixa_renda') or 'N/A',
                    "Atividade": carta.get('atividade') or 'N/A',
                    "Morador": carta.get('morador') or 'N/A',
                    "CEP": carta.get('cep') or 'N/A',
                }

                cols = st.columns(5)
                for idx, (chave, valor) in enumerate(metadados.items()):
                    with cols[idx % 5]:
                        valor_display = str(valor)[:30] + "..." if len(str(valor)) > 30 else str(valor)
                        st.write(f"**{chave}:**")
                        st.caption(valor_display)

                st.markdown("---")
                col_cat, col_idx = st.columns(2)

                with col_cat:
                    catalogo = carta.get('catalogo') or 'N/A'
                    st.write("**Catálogo:**")
                    st.caption(catalogo)

                with col_idx:
                    indexacao = carta.get('indexacao') or 'N/A'
                    st.write("**Indexação:**")
                    st.caption(indexacao)

        else:
            st.warning("❌ Nenhuma carta encontrada com esses filtros. Tente ajustar suas seleções.")

        st.markdown("---")

        # ========== EXPORTAR RESULTADOS DOS FILTROS ==========
        st.subheader("📥 Exportar Resultados")

        col_csv, col_json, col_parquet, col_html, col_pdf = st.columns(5)

        # Preparar nome descritivo para os filtros
        filtros_nome = "_".join([f"{k[:3]}" for k in st.session_state.active_filters.keys()])
        if not filtros_nome:
            filtros_nome = "filtros"

        with col_csv:
            csv_data = ExportManager.exportar_serie_csv(
                _todas_cartas,
                st.session_state.filter_results,
                f"filtro_{filtros_nome}",
                am.get_todas_anotacoes(),
                series=sm.series
            )
            st.download_button(
                label="💾 Baixar CSV",
                data=csv_data,
                file_name=f"filtro_{filtros_nome}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="filter_export_csv"
            )

        with col_json:
            json_data = ExportManager.exportar_serie_json(
                _todas_cartas,
                st.session_state.filter_results,
                f"filtro_{filtros_nome}",
                am.get_todas_anotacoes()
            )
            st.download_button(
                label="💾 Baixar JSON",
                data=json_data,
                file_name=f"filtro_{filtros_nome}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True,
                key="filter_export_json"
            )

        with col_parquet:
            _pq_filtro_idx = {}
            for _ns, _si in sm.series.items():
                for _cid in _si['cartas']:
                    _pq_filtro_idx.setdefault(_cid, []).append(_ns)
            _pq_filtro = ExportManager.exportar_parquet(
                _todas_cartas,
                st.session_state.filter_results,
                am.get_todas_anotacoes(),
                series_idx=_pq_filtro_idx
            )
            st.download_button(
                label="🗃️ Parquet",
                data=_pq_filtro,
                file_name=f"filtro_{filtros_nome}_{datetime.now().strftime('%Y%m%d')}.parquet",
                mime="application/octet-stream",
                use_container_width=True,
                key="filter_export_parquet"
            )

        with col_html:
            # Gerar relatório HTML apenas quando clicado (evita rerun infinito)
            if st.button("📄 Gerar Relatório HTML", key="filter_gen_html", use_container_width=True):
                with FeedbackManager.operation_status("📄 Gerando relatório HTML..."):
                    html_relatorio = ExportManager.gerar_relatorio_filtros_html(
                        cartas=_todas_cartas,
                        ids_filtrados=st.session_state.filter_results,
                        filtros_ativos=st.session_state.active_filters,
                        campos_filtro_labels=campos_filtro,
                        anotacoes=am.get_todas_anotacoes()
                    )
                st.download_button(
                    label="💾 Baixar HTML",
                    data=html_relatorio,
                    file_name=f"relatorio_filtro_{filtros_nome}_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True,
                    key="filter_download_html"
                )

        with col_pdf:
            if st.button("📄 Gerar PDF", key="filter_gen_pdf", use_container_width=True):
                with FeedbackManager.operation_status("📄 Gerando PDF dos filtrados..."):
                    _pdf_filtro = ExportManager.exportar_pdf(
                        _todas_cartas,
                        st.session_state.filter_results,
                        f"Filtros: {filtros_nome}",
                        am.get_todas_anotacoes(),
                        series=sm.series
                    )
                st.download_button(
                    label="💾 Baixar PDF",
                    data=_pdf_filtro,
                    file_name=f"filtro_{filtros_nome}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="filter_download_pdf"
                )

    else:
        st.info("ℹ️ Selecione pelo menos um filtro para começar a busca.")


# ============================================================================
# ABA 8: BUSCA SEMÂNTICA
# ============================================================================

with tab8:
    # Lazy load: Tab carrega apenas quando clicado
    if not is_tab_loaded(8):
        st.info("⏳ Carregando busca semântica na primeira visualização...")
        mark_tab_loaded(8)
        st.rerun()

    st.header("🧠 Busca Semântica por Embeddings")
    breadcrumb_nav("Home", "Busca Semântica")

    st.markdown(
        "Encontre cartas semanticamente relacionadas à sua consulta em linguagem natural, "
        "mesmo sem compartilhar palavras exatas com os textos. "
        "Utiliza o modelo **RoBERTa** multilíngue (sentence-transformers/paraphrase-multilingual-mpnet-base-v2) "
        "rodando **localmente** — sem APIs externas ou custos."
    )

    _db_name_sem = dm.current_database_name
    _cartas_sem = _todas_cartas

    # ────────────────────────────────────────────────────────────────────
    # Seção A — Status e pré-computação
    # ────────────────────────────────────────────────────────────────────
    st.subheader("⚙️ Status do Índice Semântico")

    _status_sem = sem_e.get_status(_db_name_sem, _cartas_sem)

    _col_s1, _col_s2, _col_s3, _col_s4, _col_s5 = st.columns(5)
    _col_s1.metric(
        "Modelo em memória",
        "✅ Sim" if _status_sem['modelo_carregado'] else "❌ Não"
    )
    _col_s2.metric(
        "Cache existe",
        "✅ Sim" if _status_sem['cache_existe'] else "❌ Não"
    )
    _col_s3.metric(
        "Cache válido",
        "✅ Sim" if _status_sem['cache_valido'] else "⚠️ Não"
    )
    _col_s4.metric(
        "Cartas indexadas",
        f"{_status_sem['total_indexado']:,}" if _status_sem['total_indexado'] > 0 else "—"
    )
    _col_s5.metric(
        "Tamanho do cache",
        f"{_status_sem['tamanho_mb']:.1f} MB" if _status_sem['tamanho_mb'] > 0.0 else "—"
    )

    st.markdown("---")

    _cache_valido = _status_sem['cache_valido']

    if _cache_valido:
        st.success(
            "✅ O índice semântico está pronto. Faça uma consulta na seção abaixo."
        )
    elif not _status_sem['cache_existe']:
        st.info(
            "ℹ️ **Índice semântico não encontrado.**  \n"
            "É necessário pré-computar os embeddings antes da primeira busca semântica.  \n"
            "O processo ocorre **uma única vez por base de dados** e leva 15–40 minutos em CPU."
        )
    else:
        st.warning(
            "⚠️ **Cache desatualizado.** A base de dados foi alterada desde a última indexação.  \n"
            "Clique no botão abaixo para reindexar."
        )

    if st.button(
        "⚡ Pré-computar Embeddings",
        disabled=_cache_valido,
        use_container_width=True,
        key="btn_computar_embeddings"
    ):
        st.warning(
            "⏳ **Este processo leva entre 15 e 40 minutos dependendo do hardware.**  \n"
            "O app ficará indisponível durante a computação. Não feche esta janela.  \n"
            "Na **primeira execução**, o modelo RoBERTa (~420 MB) será baixado automaticamente."
        )

        _barra_progresso = st.progress(0)
        _texto_status = st.empty()

        def _callback_progresso(atual: int, total_c: int) -> None:
            """Atualiza a barra de progresso do Streamlit a cada batch."""
            pct = atual / total_c
            _barra_progresso.progress(pct)
            _texto_status.text(
                f"Processando… {atual:,}/{total_c:,} cartas ({pct * 100:.1f}%)"
            )

        _t0 = time.time()
        _ok_comp, _msg_comp = sem_e.compute_embeddings(
            cartas=_cartas_sem,
            db_name=_db_name_sem,
            progress_callback=_callback_progresso
        )
        _tempo_comp = time.time() - _t0

        _barra_progresso.progress(1.0)
        _texto_status.empty()

        if _ok_comp:
            st.success(
                f"✅ Indexação concluída!  \n"
                f"{_msg_comp}  \n"
                f"Tempo total: {_tempo_comp:.0f}s ({_tempo_comp / 60:.1f} min)"
            )
        else:
            st.error(f"❌ Erro na indexação: {_msg_comp}")

        st.rerun()

    st.markdown("---")

    # ────────────────────────────────────────────────────────────────────
    # Seção B — Consulta
    # ────────────────────────────────────────────────────────────────────
    st.subheader("🔍 Consulta Semântica")

    with st.form("semantic_search_form"):
        _query_sem = st.text_area(
            "Digite sua consulta em linguagem natural:",
            placeholder=(
                "Exemplos:\n"
                "· medo da ditadura voltar\n"
                "· momento único na história\n"
                "· injustiça histórica não resolvida\n"
                "· trabalhadores sem terra"
            ),
            height=120,
            key="semantic_query_input"
        )

        _threshold_sem = st.slider(
            "Similaridade mínima (threshold):",
            min_value=0.0,
            max_value=1.0,
            value=0.35,
            step=0.05,
            format="%.2f",
            key="semantic_threshold",
            help=(
                "Valores mais altos = resultados mais parecidos com a query, porém menos cartas.  \n"
                "Valores mais baixos = mais cartas, porém algumas podem ser menos relevantes.  \n"
                "Recomendado: 0.30–0.45 para RoBERTa.  \n"
                "O histograma abaixo atualiza em tempo real ao mover este slider."
            )
        )

        form_submit_sem = st.form_submit_button(
            "🔍 Buscar por Similaridade",
            use_container_width=True
        )

    if form_submit_sem:
        if not _query_sem.strip():
            st.warning("⚠️ Digite uma consulta para buscar.")
        elif not _cache_valido:
            st.error(
                "❌ O índice semântico não está disponível.  \n"
                "Use o botão '⚡ Pré-computar Embeddings' acima para criar o índice primeiro."
            )
        else:
            _query_key_sem = f"semantic_{_query_sem.strip()}_{_db_name_sem}"
            _cached_sem = get_cached_search(_query_key_sem)

            if _cached_sem:
                FeedbackManager.success(f"✅ Cache: {len(_cached_sem)} resultados encontrados")
                st.session_state.semantic_results = _cached_sem
                st.session_state.semantic_page = 1
            else:
                with FeedbackManager.operation_status("🔍 Buscando similaridades..."):
                    try:
                        # Busca sem threshold e sem limite: scores retornados para toda a base.
                        # O threshold é aplicado dinamicamente na UI; a paginação é reiniciada.
                        _resultados_sem = sem_e.search(
                            query=_query_sem.strip(),
                            cartas=_cartas_sem,
                            db_name=_db_name_sem,
                            top_k=99999,
                            threshold=0.0
                        )
                        st.session_state.semantic_results = _resultados_sem
                        st.session_state.semantic_page = 1
                        # Guardar em cache
                        cache_search_result(_query_key_sem, _resultados_sem)
                    except FileNotFoundError as _e:
                        st.error(f"❌ {str(_e)}")
                        st.session_state.semantic_results = []
                    except Exception as _e:
                        st.error(f"❌ Erro durante a busca: {str(_e)}")
                        st.session_state.semantic_results = []

    # ────────────────────────────────────────────────────────────────────
    # Seção C — Resultados
    # ────────────────────────────────────────────────────────────────────
    if st.session_state.semantic_results:
        st.markdown("---")

        # Todos os scores retornados (threshold=0.0 na busca)
        _todos_resultados = st.session_state.semantic_results
        _todos_scores = [score for _, score in _todos_resultados]

        # Aplicar threshold do slider dinamicamente
        _resultados_filtrados = [
            (carta_id, score)
            for carta_id, score in _todos_resultados
            if score >= _threshold_sem
        ]

        # Métricas em destaque
        _col_m1, _col_m2 = st.columns(2)
        _col_m1.metric(
            "Cartas acima do threshold",
            f"{len(_resultados_filtrados):,}"
        )
        _col_m2.metric(
            "Cartas analisadas na base",
            f"{len(_todos_resultados):,}"
        )

        # Histograma de distribuição de scores — recomputa apenas quando os resultados mudam
        _sem_hist_key = len(_todos_resultados)
        if st.session_state.get('_sem_hist_key') != _sem_hist_key:
            _scores_arr = np.array(_todos_scores, dtype=float)
            _bins = np.arange(0.0, 1.051, 0.05)
            _hist_vals_c, _bin_edges_c = np.histogram(_scores_arr, bins=_bins)
            st.session_state['_sem_hist_key'] = _sem_hist_key
            st.session_state['_sem_hist_vals'] = _hist_vals_c.tolist()
            st.session_state['_sem_hist_bin_centers'] = [
                round((_bin_edges_c[i] + _bin_edges_c[i + 1]) / 2, 3)
                for i in range(len(_hist_vals_c))
            ]
        _hist_vals = st.session_state['_sem_hist_vals']
        _bin_centers = st.session_state['_sem_hist_bin_centers']

        _fig_hist = go.Figure()
        _fig_hist.add_trace(go.Bar(
            x=_bin_centers,
            y=_hist_vals,
            name='Cartas',
            marker_color=[
                '#ef4444' if c >= _threshold_sem else '#93c5fd'
                for c in _bin_centers
            ],
            hovertemplate='Score: %{x:.2f}<br>Cartas: %{y}<extra></extra>'
        ))
        _fig_hist.add_vline(
            x=_threshold_sem,
            line_color='red',
            line_dash='dash',
            line_width=2,
            annotation_text=f"threshold = {_threshold_sem:.2f}",
            annotation_position="top right",
            annotation_font_color='red'
        )
        _fig_hist.update_layout(
            title="Distribuição de relevância — mova o threshold para filtrar",
            xaxis_title="Score de similaridade",
            yaxis_title="Número de cartas",
            xaxis=dict(range=[0.0, 1.0], dtick=0.05),
            height=300,
            margin=dict(t=50, b=40, l=40, r=20),
            showlegend=False,
            bargap=0.05
        )
        st.plotly_chart(_fig_hist, use_container_width=True)

        if not _resultados_filtrados:
            st.info(
                f"ℹ️ Nenhuma carta encontrada com similaridade ≥ {_threshold_sem:.2f}.  \n"
                "Reduza o threshold para ver mais resultados."
            )
        else:
            st.subheader("📋 Resultados")

            # Paginação — 50 cartas por página
            _PAGE_SIZE = 50
            _total_pags = max(1, math.ceil(len(_resultados_filtrados) / _PAGE_SIZE))

            # Garantir que a página está dentro do intervalo válido
            st.session_state.semantic_page = max(
                1, min(st.session_state.semantic_page, _total_pags)
            )
            _pag_atual = st.session_state.semantic_page
            _inicio = (_pag_atual - 1) * _PAGE_SIZE
            _fim = _inicio + _PAGE_SIZE
            _resultados_pagina = _resultados_filtrados[_inicio:_fim]

            def _sem_nan(valor, fallback=''):
                """Converte None, float NaN e a string 'nan' para fallback."""
                if valor is None:
                    return fallback
                try:
                    if isinstance(valor, float) and math.isnan(valor):
                        return fallback
                except Exception:
                    pass
                if str(valor).strip().lower() == 'nan':
                    return fallback
                return str(valor).strip() or fallback

            # OTIMIZAÇÃO PHASE 1: Cache series list (evita 50 chamadas por página)
            if not st.session_state.series_list_cache_valid:
                st.session_state.series_list_cache = sm.get_todas_series()
                st.session_state.series_list_cache_valid = True
            _series_list_sem_cached = st.session_state.series_list_cache

            # OTIMIZAÇÃO PHASE 2: Pré-carregar séries de cartas do expander se necessário
            # (lazy-load: só carrega quando expander é aberto pela primeira vez)
            _series_carta_cache = {}

            _rerun_semantica = False
            for _rank_global, (_carta_id_sem, _score_sem) in enumerate(
                _resultados_pagina, _inicio + 1
            ):
                _carta_sem = dm.get_carta(_carta_id_sem)
                if not _carta_sem:
                    continue

                _nome_sem = _sem_nan(_carta_sem.get('nome'), 'N/A')
                _uf_sem = _sem_nan(_carta_sem.get('uf'), 'N/A')
                _catalogo_sem = _sem_nan(_carta_sem.get('catalogo'), 'N/A')
                _faixa_etaria_sem = _sem_nan(_carta_sem.get('faixa_etaria'), 'N/A')
                _instrucao_sem = _sem_nan(_carta_sem.get('instrucao'), 'N/A')
                _texto_sem = _sem_nan(_carta_sem.get('texto'), '')

                _titulo_exp = (
                    f"#{_rank_global} — [{_carta_id_sem}] {_nome_sem} "
                    f"— {_uf_sem} — score: {_score_sem:.3f}"
                )

                with st.expander(_titulo_exp):
                    # Metadados em linha
                    st.caption(
                        f"📚 **Catálogo:** {_catalogo_sem} &nbsp;·&nbsp; "
                        f"🗺️ **UF:** {_uf_sem} &nbsp;·&nbsp; "
                        f"📅 **Faixa etária:** {_faixa_etaria_sem} &nbsp;·&nbsp; "
                        f"🎓 **Instrução:** {_instrucao_sem}"
                    )

                    # Séries temáticas associadas
                    if _carta_id_sem not in _series_carta_cache:
                        _series_carta_cache[_carta_id_sem] = sm.get_series_carta(_carta_id_sem)

                    _series_desta_carta = _series_carta_cache[_carta_id_sem]
                    if _series_desta_carta:
                        _series_str = " &nbsp;·&nbsp; ".join([f"🗂️ {s}" for s in _series_desta_carta])
                        st.caption(f"**Séries:** {_series_str}")
                    else:
                        st.caption("**Séries:** _Nenhuma série atribuída_")

                    # Texto completo
                    st.markdown("**Texto da carta:**")
                    st.markdown(
                        f'<div style="background-color: var(--bg-tertiary); border: 1px solid var(--border-color); '
                        f'border-radius: 4px; padding: 12px; font-family: monospace; '
                        f'white-space: pre-wrap; word-wrap: break-word; color: var(--text-primary); '
                        f'max-height: 300px; overflow-y: auto;">{_texto_sem}</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown("")
                    _col_abrir, _col_series = st.columns([1, 2])

                    with _col_abrir:
                        if st.button(
                            "→ Abrir na aba Explorar",
                            key=f"sem_abrir_{_carta_id_sem}_{_rank_global}",
                            help="Define esta carta como atual e permite visualizá-la na aba 🔍 Explorar Cartas"
                        ):
                            st.session_state.current_carta_id = _carta_id_sem
                            st.session_state.sidebar_series_context = 'explorar'
                            _rerun_semantica = True
                            break

                    with _col_series:
                        if _series_list_sem_cached:
                            _is_in_sidebar = (
                                st.session_state.get('sidebar_series_carta_id') == _carta_id_sem
                                and st.session_state.get('sidebar_series_context') == 'semantica'
                            )

                            def _toggle_painel(_cid=_carta_id_sem):
                                if (st.session_state.get('sidebar_series_carta_id') == _cid
                                        and st.session_state.get('sidebar_series_context') == 'semantica'):
                                    st.session_state.sidebar_series_context = 'explorar'
                                    st.session_state.sidebar_series_carta_id = None
                                else:
                                    st.session_state.sidebar_series_carta_id = _cid
                                    st.session_state.sidebar_series_context = 'semantica'

                            st.button(
                                "✅ Na sidebar" if _is_in_sidebar else "🗂️ Gerenciar séries",
                                key=f"sem_mgmt_btn_{_carta_id_sem}_{_rank_global}",
                                use_container_width=True,
                                on_click=_toggle_painel
                            )
                        else:
                            st.caption("ℹ️ Nenhuma série criada. Crie uma na aba 🗂️ Séries Temáticas.")

            if _rerun_semantica:
                st.rerun()

            # Controles de paginação
            st.markdown("")
            _col_pag1, _col_pag2, _col_pag3 = st.columns([1, 2, 1])
            with _col_pag1:
                if st.button(
                    "← Anterior",
                    disabled=(_pag_atual <= 1),
                    use_container_width=True,
                    key="sem_pag_anterior"
                ):
                    st.session_state.semantic_page -= 1
                    st.rerun()
            with _col_pag2:
                st.markdown(
                    f"<div style='text-align:center; padding-top:6px;'>"
                    f"Página <b>{_pag_atual}</b> de <b>{_total_pags}</b>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with _col_pag3:
                if st.button(
                    "Próxima →",
                    disabled=(_pag_atual >= _total_pags),
                    use_container_width=True,
                    key="sem_pag_proxima"
                ):
                    st.session_state.semantic_page += 1
                    st.rerun()

            # Exportar CSV — TODOS os resultados acima do threshold (não apenas a página atual)
            st.markdown("---")

            _sem_ids_t = tuple(cid for cid, _ in _resultados_filtrados)
            _sem_scores_t = tuple(sc for _, sc in _resultados_filtrados)
            _csv_data_sem = build_semantic_csv_cached(
                _sem_ids_t, _sem_scores_t, _db_name_sem, _cartas_sem,
                _series=sm.series
            )

            _col_sem_csv, _col_sem_parquet, _col_sem_pdf = st.columns(3)
            with _col_sem_csv:
                st.download_button(
                    label="⬇ Exportar resultados (CSV)",
                    data=_csv_data_sem,
                    file_name=f"busca_semantica_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="sem_export_csv"
                )
            with _col_sem_parquet:
                _sem_ids_pq = [_cid for _cid, _ in _resultados_filtrados]
                _pq_sem_idx = {}
                for _nssem, _sisem in sm.series.items():
                    for _cidsem in _sisem['cartas']:
                        _pq_sem_idx.setdefault(_cidsem, []).append(_nssem)
                _pq_sem = ExportManager.exportar_parquet(
                    _todas_cartas,
                    _sem_ids_pq,
                    am.get_todas_anotacoes(),
                    series_idx=_pq_sem_idx
                )
                st.download_button(
                    label="🗃️ Exportar resultados (Parquet)",
                    data=_pq_sem,
                    file_name=f"busca_semantica_{datetime.now().strftime('%Y%m%d_%H%M')}.parquet",
                    mime="application/octet-stream",
                    use_container_width=True,
                    key="sem_export_parquet"
                )
            with _col_sem_pdf:
                if st.button("📄 Gerar PDF", key="sem_gen_pdf", use_container_width=True):
                    _sem_ids = [_cid for _cid, _ in _resultados_filtrados]
                    _sem_scores = {_cid: _sc for _cid, _sc in _resultados_filtrados}
                    with FeedbackManager.operation_status("📄 Gerando PDF da busca semântica..."):
                        _pdf_sem = ExportManager.exportar_pdf(
                            _todas_cartas,
                            _sem_ids,
                            f"Busca Semântica: {st.session_state.get('semantic_query', '')}",
                            am.get_todas_anotacoes(),
                            scores=_sem_scores,
                            series=sm.series
                        )
                    st.download_button(
                        label="💾 Baixar PDF",
                        data=_pdf_sem,
                        file_name=f"busca_semantica_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="sem_download_pdf"
                    )


# ============================================================================
# ABA 9: ANÁLISE DE FREQUÊNCIA
# ============================================================================

with tab9:
    # Lazy load: Tab carrega apenas quando clicado
    if not is_tab_loaded(9):
        st.info("⏳ Carregando análise de frequência na primeira visualização...")
        mark_tab_loaded(9)
        st.rerun()

    st.header("📈 Análise de Frequência de Termos")
    breadcrumb_nav("Home", "Análise de Frequência")

    # Inicializar frequency analyzer se não existir
    if 'frequency_analyzer' not in st.session_state:
        st.session_state.frequency_analyzer = FrequencyAnalyzer()

    fa = st.session_state.frequency_analyzer

    st.markdown("""
    **Analise a frequência de palavras, expressões e radicais na base de dados.**

    Digite os termos separados por vírgula (,), ponto-e-vírgula (;) ou pipe (|).
    Para cada termo, escolha se deseja buscar exato ou com radical (wildcard).
    """)

    # Seção de entrada
    col1, col2 = st.columns([3, 1])

    with col1:
        input_termos = st.text_area(
            "📝 Digite os termos a analisar",
            placeholder="Ex: democracia, direito, constituição",
            height=80,
            key="freq_input_termos"
        )

    with col2:
        st.markdown("**Tipo de Busca**")
        case_sensitive = st.checkbox("Case-sensitive", value=False, key="freq_case_sensitive")

    # Parse e configuração de termos
    if input_termos.strip():
        termos = fa.parse_termos(input_termos)

        if termos:
            st.markdown("---")
            st.subheader("⚙️ Configuração de Termos")

            # Usar form para evitar reruns a cada mudança de selectbox
            with st.form("freq_config_form"):
                # Criar abas para cada termo
                termo_configs = {}
                tipo_cols = st.columns(len(termos))

                for idx, termo in enumerate(termos):
                    with tipo_cols[idx % len(tipo_cols)]:
                        tipo = st.selectbox(
                            f"**{termo}**",
                            options=["Exato", "Radical"],
                            index=0,
                            key=f"freq_tipo_{idx}_{termo}"
                        )
                        termo_configs[termo] = tipo.lower()

                # Botões de análise dentro do form
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

                with col_btn1:
                    analisar_btn = st.form_submit_button("🔍 Analisar", use_container_width=True)

                with col_btn2:
                    limpar_btn = st.form_submit_button("🗑️ Limpar", use_container_width=True)

                if analisar_btn:
                    tipos = [termo_configs.get(t, 'exato') for t in termos]
                    resultado = fa.analisar_multiplos_termos(
                        _todas_cartas,
                        termos,
                        tipos,
                        case_sensitive
                    )
                    st.session_state.freq_resultado = resultado

                if limpar_btn:
                    if 'freq_resultado' in st.session_state:
                        del st.session_state.freq_resultado
                    st.rerun()

            # Exibir resultados se existirem
            if 'freq_resultado' in st.session_state:
                resultado = st.session_state.freq_resultado

                st.markdown("---")
                st.subheader("📊 Resultados da Análise")

                # Tabela resumida
                st.markdown("**Resumo de Frequências**")
                resumo_data = []
                for termo_info in resultado['termos']:
                    resumo_data.append({
                        "Termo": termo_info['termo'],
                        "Tipo": termo_info['tipo'].capitalize(),
                        "Total de Ocorrências": termo_info['total_ocorrencias'],
                        "Cartas com o Termo": termo_info['num_documentos'],
                        "% de Cobertura": f"{(termo_info['num_documentos'] / resultado['total_cartas'] * 100):.1f}%"
                    })

                df_resumo = pd.DataFrame(resumo_data)
                st.dataframe(df_resumo, use_container_width=True, hide_index=True)

                # Gráficos comparativos
                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    st.markdown("**📊 Comparação de Ocorrências**")
                    stats = fa.gerar_estatisticas_comparativas(resultado)
                    fig_ocorr = go.Figure(data=[
                        go.Bar(
                            x=stats['termos'],
                            y=stats['ocorrencias'],
                            marker=dict(color=stats['cores']),
                            text=stats['ocorrencias'],
                            textposition='auto',
                        )
                    ])
                    fig_ocorr.update_layout(
                        xaxis_title="Termo",
                        yaxis_title="Total de Ocorrências",
                        height=400,
                        showlegend=False,
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig_ocorr, use_container_width=True)

                with col_g2:
                    st.markdown("**📊 Comparação de Cartas**")
                    fig_docs = go.Figure(data=[
                        go.Bar(
                            x=stats['termos'],
                            y=stats['num_documentos'],
                            marker=dict(color=stats['cores']),
                            text=stats['num_documentos'],
                            textposition='auto',
                        )
                    ])
                    fig_docs.update_layout(
                        xaxis_title="Termo",
                        yaxis_title="Número de Cartas",
                        height=400,
                        showlegend=False,
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig_docs, use_container_width=True)

                # Detalhes por termo
                st.markdown("---")
                st.subheader("🔎 Detalhes por Termo")

                for termo_info in resultado['termos']:
                    termo = termo_info['termo']
                    cor = termo_info['cor']
                    num_docs = termo_info['num_documentos']

                    with st.expander(
                        f"📄 **{termo}** — {num_docs} cartas com {termo_info['total_ocorrencias']} ocorrências",
                        expanded=False
                    ):
                        # Listar cartas
                        cartas_com_termo = fa.obter_cartas_com_termo(
                            _todas_cartas,
                            termo,
                            eh_radical=(termo_info['tipo'] == 'radical'),
                            case_sensitive=case_sensitive
                        )

                        # Tabela com cartas
                        cartas_table_data = []
                        for carta in cartas_com_termo[:50]:  # Limite a 50 primeiras
                            cartas_table_data.append({
                                "ID": carta['carta_id'],
                                "Nome": carta['nome'][:50] + "..." if len(carta['nome']) > 50 else carta['nome'],
                                "Destinatário": carta['destinatario'][:40] + "..." if len(carta['destinatario']) > 40 else carta['destinatario'],
                                "UF": carta['uf'],
                                "Data": carta['data'],
                                "Ocorrências": carta['ocorrencias']
                            })

                        df_cartas = pd.DataFrame(cartas_table_data)
                        st.dataframe(df_cartas, use_container_width=True, hide_index=True)

                        if len(cartas_com_termo) > 50:
                            st.info(f"📌 Mostrando 50 de {len(cartas_com_termo)} cartas. Role para ver mais.")

                        # Mostrar textos com highlight das 5 primeiras cartas
                        if cartas_com_termo:
                            st.markdown("**📋 Visualizar Textos com Destaque** (primeiras 5 cartas)")
                            st.divider()

                            for idx, carta in enumerate(cartas_com_termo[:5]):
                                # Cabeçalho da carta
                                st.markdown(f"**{idx + 1}. {carta['nome']} (ID: {carta['carta_id']})**")

                                # Destaque do texto
                                texto_destacado = fa.encontrar_termo_em_texto(
                                    carta['texto'],
                                    termo,
                                    eh_radical=(termo_info['tipo'] == 'radical'),
                                    case_sensitive=case_sensitive
                                )

                                # HTML com destaque
                                if texto_destacado:
                                    texto = carta['texto']
                                    posicoes = sorted(texto_destacado, key=lambda x: x[0], reverse=True)

                                    for start, end in posicoes:
                                        match_text = texto[start:end]
                                        highlighted = f'<mark style="background-color: {cor}; padding: 2px 4px; border-radius: 3px;">{match_text}</mark>'
                                        texto = texto[:start] + highlighted + texto[end:]

                                    st.markdown(
                                        f'<div style="background-color: var(--bg-secondary); padding: 12px; border-radius: 4px; border-left: 4px solid {cor}; max-height: 250px; overflow-y: auto; font-size: 13px; color: var(--text-primary);">{texto}</div>',
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.write(carta['texto'][:500] + "..." if len(carta['texto']) > 500 else carta['texto'])

                                # Metadados em linha
                                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                                with col_m1:
                                    st.metric("Data", carta['data'], label_visibility="collapsed")
                                with col_m2:
                                    st.metric("UF", carta['uf'], label_visibility="collapsed")
                                with col_m3:
                                    st.metric("Ocorrências", f"{carta['ocorrencias']}", label_visibility="collapsed")
                                with col_m4:
                                    st.metric("Destinatário", carta['destinatario'][:30] + "..." if len(carta['destinatario']) > 30 else carta['destinatario'], label_visibility="collapsed")

                                if idx < len(cartas_com_termo[:5]) - 1:
                                    st.divider()


# ============================================================================
# RODAPÉ
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); font-size: 12px; padding: 20px; border-top: 1px solid var(--accent-color); margin-top: 8px;">
    <p>📚 <strong>Historicidades Democráticas</strong> - Plataforma de Análise de Documentos Históricos</p>
    <p>Desenvolvido para preservar e analisar correspondências constitucionais</p>
</div>
""", unsafe_allow_html=True)
