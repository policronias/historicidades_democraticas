# CLAUDE.md

Plataforma **Historicidades Democráticas** — análise, busca semântica e arquivamento de correspondência histórica brasileira.

## Abas (app.py)

| # | Aba | Função |
|---|-----|--------|
| 1 | 🔍 Explorar | Navegação por ID, busca avançada, highlight de termos |
| 2 | 📓 Caderno | Anotações por carta + caderno de pesquisa livre |
| 3 | 🗂️ Séries | Criar/editar séries temáticas, adicionar cartas |
| 4 | 📥 Exportar | CSV, JSON, Parquet, HTML, PDF, ZIP — busca, série ou base completa |
| 5 | ⚙️ Config | Carregar/trocar base; converter XLSX/CSV → JSON |
| 6 | 📊 Gráficos | Gráficos Plotly interativos (demográficos e geográficos) |
| 7 | 🎯 Filtros | Filtragem multidimensional (sexo, UF, faixa etária, renda…) |
| 8 | 🧠 Semântica | Busca por similaridade RoBERTa, paginada, com threshold |

## Módulos (`modules/`)

- `data_manager.py` — CRUD cartas, índices (nome, série), load/upload/switch de base
- `search_engine.py` — busca avançada (`"frase"`, `+obrig`, `-excl`, `termo*`), variações morfológicas, highlight regex
- `semantic_engine.py` — embeddings `paraphrase-multilingual-mpnet-base-v2`, cache `.npy` por base
- `series_manager.py` — séries temáticas; índice invertido O(1) `carta_id → [séries]`
- `annotation_manager.py` — anotações por carta + caderno; persistência em `sessions/current_session.json`
- `export_manager.py` — CSV, JSON, **Parquet** (pyarrow), HTML+Plotly, PDF (reportlab+matplotlib), ZIP
- `cache_manager.py` — `@st.cache_data` (ttl=60) para DataFrames e dados de gráficos
- `ui_manager.py` — CSS global, cabeçalho, paleta de cores
- `config_manager.py` — paths, constantes, `get_field_groups()` para filtros

## Arquitetura — decisões não-óbvias

- **Sidebar "Gerenciar Séries"** é compartilhada entre abas 1, 7 e 8 via `sidebar_series_context` no session state. Não duplicar lógica de séries por aba.
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
