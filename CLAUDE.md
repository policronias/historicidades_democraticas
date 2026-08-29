# CLAUDE.md

Plataforma **Historicidades Democráticas** — análise, busca semântica e arquivamento de correspondência histórica brasileira.

## Abas (app.py)

| # | Aba | Função |
|---|-----|--------|
| 0 | 🏠 Início | Página de entrada: logomarca Policronias + cartões que descrevem e abrem cada aba |
| 1 | 🔍 Explorar | Navegação por ID, busca avançada, highlight de termos |
| 2 | 📓 Caderno | Anotações por carta + caderno de pesquisa livre |
| 3 | 🗂️ Séries | Criar/editar séries temáticas, adicionar cartas |
| 4 | 📥 Exportar | CSV, JSON, Parquet, HTML, PDF, ZIP — busca, série ou base completa |
| 5 | ⚙️ Config | Carregar/trocar base; converter XLSX/CSV → JSON |
| 6 | 📊 Gráficos | Gráficos Plotly interativos (demográficos e geográficos) |
| 7 | 🎯 Filtros | Filtragem multidimensional (sexo, UF, faixa etária, renda…) |
| 8 | 🧠 Semântica | Busca por similaridade RoBERTa, paginada, com threshold |
| 9 | 📈 Frequência | Análise comparativa de múltiplos termos, ocorrências, visualização |

## Módulos (`modules/`) — refatorados para modularidade

- `data_manager.py` — CRUD cartas, índices (nome, série), load/upload/switch de base
- `search_engine.py` — busca avançada (`"frase"`, `+obrig`, `-excl`, `termo*`), variações morfológicas, highlight regex
- `semantic_engine.py` — embeddings `paraphrase-multilingual-mpnet-base-v2`, busca por similaridade, cache
- `series_manager.py` — séries temáticas; índice invertido O(1) `carta_id → [séries]`
- `annotation_manager.py` — anotações por carta + caderno; persistência em `sessions/current_session.json`
- `export_manager.py` — exportação: CSV, JSON, **Parquet** (pyarrow), HTML+Plotly, PDF (reportlab+matplotlib), ZIP
- `frequency_analyzer.py` — análise de frequência de termos, múltiplas cores, gráficos Plotly
- `stemming_engine.py` — processamento de stemming/stemming com RSLP
- **`cache_manager.py` (consolidado)** — funções cacheadas: `build_df_fast()`, `compute_chart_data_cached()`, `build_semantic_csv_cached()`
- **`ui_manager.py` (consolidado)** — `configure_page_style()` (CSS mínimo, só tipografia da carta), `get_accent_color()`, `get_plotly_color_palette()`, `get_plotly_sequential_scale()`, `apply_plotly_theme()`, `render_letter_text()`, `breadcrumb_nav()`
- `config_manager.py` — constantes, paths, paleta de cores, grupos de campos
- `memory_monitor.py` — monitor de memória do processo (psutil), exibido na sidebar via `?debug=true`

## Arquitetura — decisões não-óbvias

### Identidade visual "Policronias do presente" (2026-08-29)
- **Sistema de marca**: projeto de pesquisa UDESC/PPGH do Prof. Walderez Ramalho. Sistema "papel de arquivo" — papel `#F1EDE2`, tinta `#1B1815`, **selo `#9C3A26`** (terracota de carimbo) para ênfase/links/datação; musgo `#5C6A4C` é acento secundário raro. **Nunca selo + musgo juntos em grande área.** Cantos sempre retos (`baseRadius = "none"`). Fontes: Newsreader (títulos, itálico 500), IBM Plex Sans (corpo/interface), IBM Plex Mono (metadados/datas). Skill de referência: `policronias-do-presente-design`.
- **Cores vêm de `.streamlit/config.toml`** (`[theme.light]`/`[theme.dark]`), não de CSS custom — habilita o seletor nativo de tema (menu ☰ > Settings). Claro = papel Policronias; escuro = paleta reversa (fundo `#1B1815`, texto `#C9C2B0`, acento `#D97A5E`). `configure_page_style()` só aplica CSS que o theming nativo não cobre (tipografia serif Newsreader do texto da carta).
- **Gráficos Plotly não herdam o tema nativo** (Streamlit só expõe `st.context.theme.type`, não os valores de cor) — por isso `modules/ui_manager.py` mantém `_CHART_THEME`, um dict `light`/`dark` que espelha manualmente as cores do `config.toml`. Ao alterar uma cor no `config.toml`, replicar em `_CHART_THEME`. As paletas de série (`FrequencyAnalyzer.COLOR_PALETTE`, `HIGHLIGHT_PALETTE` em `config_manager.py`) também seguem a família Policronias.
- **`get_color_scheme()` não existe mais** — função antiga de uma versão anterior do theming (CSS manual); qualquer referência a ela em código ou docs está obsoleta.

### Refatoração (2026-07)
- **`cache_manager.py` consolidado** — `build_df_fast()`, `compute_chart_data_cached()`, `build_semantic_csv_cached()` importadas de `modules.cache_manager`, não duplicadas em `app.py`
- **`ui_manager.py` integrado** — `configure_page_style()` chamada no início de `app.py`; CSS removido de inline
- **Redução de `app.py`** — 3378 → 3281 linhas (-97); cache e UI modulares; melhor separação de responsabilidades

### Lógica de Negócio
- **Aba "🏠 Início"** (primeira, `tab_home` em `app.py`) — página de entrada com a logomarca Policronias (`policronias_mark_svg()`, símbolo dos três círculos; anel de tinta usa `currentColor` p/ herdar o tema real) e 9 cartões (`TAB_FEATURES`) que descrevem e abrem cada aba. **Navegação entre abas**: `st.tabs(TAB_LABELS, key="main_tabs", on_change="rerun")` + callback `_goto_tab(label)` que faz `st.session_state.main_tabs = label`. `on_change="rerun"` habilita o rastreio de estado das abas (necessário p/ controle programático) mas **não** desliga a execução dos corpos das abas ocultas — todos os `with tabN:` continuam rodando como antes. Ao adicionar/renomear/reordenar abas, manter `TAB_LABELS`, `TAB_FEATURES` e o desempacotamento `tab_home, tab1..tab9` em sincronia (índice `i` de `TAB_FEATURES` → `TAB_LABELS[i+1]`).
- **Busca Avançada + "Ir para Carta" + Histórico de Buscas** vivem em `render_explorar_search_tools()` (função de nível de módulo) e são chamadas **só dentro de `with tab1:`** (Explorar Cartas). Antes ficavam soltas acima de `st.tabs()`, visíveis em todas as abas. A função lê globais de módulo (`dm`, `se`, `stem_e`, `_todas_cartas`, helpers de cache) e só escreve em `st.session_state.*` — nenhum outro trecho depende das variáveis locais dela (`ids_resultado`, `termo_busca`, `form_submit`, …).
- **Sidebar "Gerenciar Séries"** é compartilhada entre abas 1, 7 e 8 via `sidebar_series_context` no session state. Não duplicar lógica de séries por aba.
- **Cabeçalho da sidebar não tem mais botão Home** — removido de propósito no redesign do tema nativo (2026-08-23); `reset_context()` foi removido de `ui_manager.py` por ter ficado sem uso.
- **PDF usa matplotlib** para gráficos embutidos — reportlab não suporta Plotly. Gráficos HTML e PDF são gerados por caminhos distintos em `export_manager.py`.
- **Parquet** exporta coluna `series_tematicas` com séries separadas por ` | `; requer construção do índice invertido antes da chamada (`series_idx` dict).
- **Busca semântica paginada**: os botões de exportação exportam *todos* os resultados acima do threshold, não apenas a página atual — diferente do comportamento visual.
- **Evitar duplo `st.rerun()`** em formulários de séries: padrão `st.form` + `on_click` causa rerun duplo; usar apenas `st.rerun()` ao fim do bloco `if form_submit_button`.

## Formato de dados (`cartas_db.json`)

Chave de topo = ID da carta. Campos relevantes:
`linha`, `nome`, `destinatario`, `texto`, `origem`, `data`, `formul`, `dv`, `data2`, `municipio`, `uf`, `cep`, `sexo`, `morador`, `instrucao`, `estado_civil`, `faixa_etaria`, `faixa_renda`, `atividade`, `catalogo`, `indexacao`, `anotacoes`, `series` (lista).

## Setup

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt   # inclui pyarrow>=14.0 para Parquet
streamlit run app.py
```
