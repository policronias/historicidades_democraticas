# Historicidades Democráticas — Descrição Técnica Completa

> Documento preparado para orientar planejamento de melhorias técnicas, novos recursos e evolução arquitetural do software. Descreve o estado real do código (não a intenção original), levantado por leitura direta de `app.py` e dos módulos em `modules/`.
>
> **Última atualização**: 2026-08-29 (página inicial 🏠 Início; busca por "Variações" migrada de dicionário fixo para stemming RSLP + índice de stems na aba Config; download automático da base e do cache via GitHub Releases; branch de deploy renomeada `master` → `main`)

## 1. Propósito e contexto

**Historicidades Democráticas** é uma plataforma de pesquisa acadêmica (Streamlit, Python) para explorar, buscar, anotar e analisar um corpus de correspondência histórica brasileira: a **Base SAIC**, composta por **72.719 cartas/sugestões de cidadãos** enviadas ao processo constituinte (Assembleia Nacional Constituinte). O projeto é conduzido por Walderez Ramalho (UDESC) e roda tanto localmente quanto publicamente em **Streamlit Community Cloud**, protegido por senha.

Cada "carta" é um registro com texto livre (`texto`) e metadados sociodemográficos e catalográficos: `linha`, `nome`, `destinatario`, `catalogo`, `indexacao`, `origem`, `data`, `data2`, `formul`, `dv`, `municipio`, `uf`, `cep`, `sexo`, `morador`, `instrucao`, `estado_civil`, `faixa_etaria`, `faixa_renda`, `atividade`, além de `anotacoes` (nota do pesquisador) e `series` (vínculo a séries temáticas).

A base principal (`cartas_db.json`) tem **~103 MB** e é carregada inteiramente em memória — não há banco de dados relacional nem paginação em disco. A fonte bruta é uma planilha (`sugestoes_constituintes_72k.xlsx`, ~29 MB), convertida para JSON pelo conversor embutido na interface (aba ⚙️ Configurações).

## 2. Arquitetura geral

```
app.py                       # Aplicação Streamlit (~3.610 linhas), single-page: 🏠 Início + 9 abas de trabalho
modules/
  __init__.py                 # Agregador de exports públicos dos módulos
  data_manager.py       (334) # Carga/troca de bases, índices, cache de JSON parseado em memória de módulo; download automático (garantir_base_baixada / garantir_cache_baixado) via GitHub Releases
  search_engine.py      (631) # Busca avançada (operadores), highlight; modo "Variações" delega a StemmingEngine
  semantic_engine.py    (463) # Embeddings RoBERTa, cache .npz, busca por similaridade cosseno
  semantic_engine_cache.py (75) # get_model_cached / get_embeddings_cached (@st.cache_resource, compartilhado entre sessões)
  series_manager.py     (352) # Séries temáticas, índice invertido carta→séries
  annotation_manager.py (225) # Anotações por carta + caderno de pesquisa, persistência JSON atômica + filelock
  export_manager.py    (1623) # CSV/JSON/Parquet/HTML/PDF/ZIP — exportação unificada
  frequency_analyzer.py (301) # Análise de frequência de termos (aba 9)
  stemming_engine.py    (446) # Variações lexicais por radical RSLP (NLTK); índice invertido stem→formas/cartas em cache/stems_*.pkl
  search_suggestions.py (152) # Autocomplete / sugestões de termos a partir do histórico de buscas
  feedback_manager.py   (104) # Helpers de feedback visual (st.status, progress bars, mensagens padronizadas)
  cache_manager.py      (239) # CONSOLIDADO: funções cacheadas de dados + estado de lazy-load das abas 6–9 + cache de resultados de busca em session_state
  ui_manager.py         (248) # CONSOLIDADO: CSS mínimo (só tipografia), tema em .streamlit/config.toml, _CHART_THEME/_BRAND_PALETTE, helpers Plotly, policronias_mark_svg()
  config_manager.py      (79) # Constantes (PAGE_CONFIG, METADATA_FIELDS, ANALYSIS_FIELDS, EMBEDDING_MODEL, HIGHLIGHT_PALETTE, MESSAGES) — sem paths
  memory_monitor.py      (70) # Monitor de memória do processo (psutil), ativável via query string ?debug=memory
sessions/current_session.json  # Único arquivo de estado persistido (anotações, caderno, séries)
cache/embeddings_*.npz         # Cache de embeddings por base de dados (baixado automaticamente)
cache/stems_*.pkl              # Índice de stems RSLP por base de dados (baixado automaticamente)
scripts/
  backup_sessao.py             # Script auxiliar — backup manual da sessão
  consolidar_buscas.py   (321) # Script auxiliar — consolidação de múltiplos CSVs de busca
  precompute_embeddings.py (197) # Script CLI para pré-computar embeddings (evita timeout do Streamlit Cloud)
tests/                         # pytest — test_search_engine, test_series_manager, test_annotation_manager, conftest
```

**Observação arquitetural**: `app.py` é uma aplicação Streamlit de execução única (script top-to-bottom, reexecutado a cada interação), sem funções `main()` nem roteamento — a aba **🏠 Início** (`tab_home`) e os 9 blocos `with tabX:` são simplesmente seções sequenciais do mesmo script. Esse é o modelo de execução padrão do Streamlit.

**Download automático de artefatos grandes**: o repositório de código **não** versiona `cartas_db.json` (~103 MB) nem `cache/*`. No topo de `app.py`, `garantir_base_baixada()` e `garantir_cache_baixado()` (em `data_manager.py`) baixam esses arquivos das GitHub Releases (`policronias/historicidades-democraticas-dados`, tag `dados-v1`) via `requests` caso ausentes — idempotente, roda uma vez por ambiente.

**Refatoração realizada (2026-07-18)**:
- ✅ **`cache_manager.py` consolidado**: funções cacheadas (`build_df_fast()`, `compute_chart_data_cached()`, `build_semantic_csv_cached()`) removidas de `app.py` e importadas de `modules.cache_manager`
- ✅ **`ui_manager.py` integrado**: CSS removido de `app.py` (98 linhas); `configure_page_style()` chamada no startup
- ✅ **Redução de `app.py`**: 3378 → 3281 linhas (-97 linhas de duplicação); melhor separação de responsabilidades
- ✅ **Nenhuma perda de funcionalidade**: todas as APIs mantidas idênticas; aplicação 100% funcional

**Migração para tema nativo + redesign do cabeçalho (2026-08-23)**:
- ✅ **Theming movido para `.streamlit/config.toml`**: CSS manual de cores substituído por `[theme.light]`/`[theme.dark]` nativos do Streamlit (dois modos: "Papel de Arquivo" claro, "Grafite Noturno" escuro), habilitando o seletor de tema nativo (menu ☰ > Settings). `get_color_scheme()` foi removida; `configure_page_style()` agora só define a tipografia serif do texto da carta.
- ✅ **`_CHART_THEME` em `ui_manager.py`**: como gráficos Plotly não herdam o tema nativo, as cores de `config.toml` são replicadas manualmente nesse dict (`light`/`dark`) e expostas via `get_accent_color()`, `get_plotly_color_palette()`, `get_plotly_sequential_scale()`.
- ✅ **Cabeçalho da sidebar redesenhado**: ícone + título + botão "🏠 Home" (que chamava `reset_context()`) substituído por título HTML estilizado usando `get_accent_color()`. `reset_context()` ficou sem uso após a mudança e foi removida de `ui_manager.py` e dos exports de `modules/__init__.py`.
- ✅ **Dead code removido** (2026-08-23): `show_academic_header()`, `show_footer()` e `sidebar_section()` — nunca chamadas em `app.py` — removidas de `ui_manager.py` e dos exports de `modules/__init__.py`.

## 3. As abas da aplicação

A interface tem uma aba **🏠 Início** (`tab_home`, ~app.py:849-898 — logomarca Policronias via `policronias_mark_svg()` + 9 cartões de `TAB_FEATURES` que descrevem e abrem cada aba; navegação programática por `st.tabs(TAB_LABELS, key="main_tabs", on_change="rerun")` + callback `_goto_tab`) seguida de 9 abas de trabalho (`st.tabs`). A **Busca Avançada + "Ir para Carta" + histórico** ficam dentro da aba 🔍 Explorar Cartas (`render_explorar_search_tools()`, ~app.py:531), não mais acima das abas. Faixas de linha abaixo são aproximadas (o script cresce a cada feature):

| # | Aba | Arquivo/linhas | Função |
|---|-----|-----------------|--------|
| 1 | 🔍 Explorar Cartas | app.py:~903-1117 | Navegação sequencial (anterior/próxima/dropdown), metadados completos, anotação inline, painel de séries |
| 2 | 📓 Caderno | app.py:~1122-1150 | Anotação por carta + caderno de pesquisa livre em Markdown |
| 3 | 🗂️ Séries Temáticas | app.py:~1155-1563 | CRUD de séries, multiselect de cartas, paginação (25/página), download unificado |
| 4 | 📥 Exportar | app.py:~1568-1936 | Exportação de busca, série, filtro, caderno e base completa em múltiplos formatos |
| 5 | ⚙️ Configurações | app.py:~1941-2178 | Seleção/upload de base, backup/restore de sessão, conversor XLSX/CSV → JSON, pré-computar índice de stems, limpeza |
| 6 | 📊 Gráficos e Tabelas | app.py:~2183-2416 | Gráficos Plotly demográficos/geográficos/temáticos sobre busca, filtro ou base inteira |
| 7 | 🎯 Filtros | app.py:~2431-2862 | Filtro multidimensional por campo (sexo, UF, faixa etária, renda, etc.) |
| 8 | 🧠 Busca Semântica | app.py:~2867-3362 | Busca por similaridade de embeddings RoBERTa, paginada, com threshold ajustável |
| 9 | 📈 Análise de Frequência | app.py:~3367-3605 | Análise comparativa multi-termo (ver §6) |

A **sidebar** é compartilhada entre as abas 1, 7 e 8 via `st.session_state.sidebar_series_context` (`'explorar'`, `'filtro'`, `'semantica'`), evitando duplicar a lógica de gerenciamento de séries em cada aba — um painel único (`💾 Salvar` / multiselect) reage ao contexto de onde o usuário veio.

## 4. Busca avançada e busca textual (`search_engine.py`)

Sintaxe suportada, com parser de tokens próprio (`_parse_query`, não usa regex de query completo):
- `"frase exata"` — correspondência literal de substring
- `+termo` — obrigatório (AND)
- `-termo` — exclusão (NOT)
- `termo*` — wildcard de prefixo (`\w*`)
- termos soltos — pelo menos um deve casar (OR)

Duas variantes de matching:
- **Simples**: normalização de acentos (NFD/Unicode) e substring case-insensitive por padrão.
- **Variações lexicais (stemming RSLP)**: o modo "Variações" delega a `StemmingEngine` (`modules/stemming_engine.py`) — não há mais dicionário `LEXICAL_VARIATIONS`. Duas palavras são variações uma da outra quando compartilham o mesmo **radical RSLP** (Removedor de Sufixos da Língua Portuguesa, NLTK), sem lista pré-selecionada de termos. Requer um **índice de stems** invertido (`stem → formas / carta_id → contagem`) pré-computado e salvo em `cache/stems_{base}.pkl` (botão na aba ⚙️ Configurações). Antes de radicalizar, as palavras passam por `_normalize()` (NFD, remoção de acentos) tanto na indexação quanto na consulta — o RSLP é sensível a acento e "historia"/"história" produziriam radicais diferentes sem isso. Radicais mais curtos que `MIN_STEM_LENGTH` caem para substring exata (accent-insensível), regra estrutural para evitar colisões ortográficas (ex.: "jus" casando "jusante").

Escopo de busca: **"Somente Texto"** (campo `texto`) vs **"Base Inteira"** (`texto`, `nome`, `destinatario`, `catalogo`, `indexacao`, `origem`).

O **highlight** usa um padrão StringBuilder (concatenação de lista + `join` único) explicitamente para evitar complexidade O(n²) de concatenação repetida de strings — comentário no código confirma que essa foi uma otimização deliberada. `highlight_multiple_terms` suporta múltiplas cores simultâneas, deduplicando sobreposições.

## 5. Busca semântica (`semantic_engine.py`, aba 8)

- **Modelo**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (RoBERTa multilíngue, 768 dimensões, janela de 512 tokens), carregado **lazy** (só na primeira chamada) e mantido em memória. `config_manager.py` define `EMBEDDING_MODEL` com esse valor e `app.py` instancia `SemanticEngine(model_name=EMBEDDING_MODEL)` (~app.py:146) — constante e uso agora sincronizados.
  - **Cache compartilhado entre sessões**: o modelo (`get_model_cached`) e a matriz de embeddings (`get_embeddings_cached`) ficam em `@st.cache_resource` via `modules/semantic_engine_cache.py` — no Streamlit Cloud, cada sessão nova reaproveita a mesma cópia do modelo (~420 MB) em vez de recarregá-la. A chave do cache de embeddings inclui o nome da base para não retornar embeddings da base errada ao trocar de base.
- **Pré-computação**: botão explícito "⚡ Pré-computar Embeddings" (não é automático) — processa em batches de 32, salva `.npz` comprimido (`embeddings` float32 normalizado L2 + `ids`) em `cache/embeddings_{nome_base}.npz`. Leva **15–40 minutos em CPU** para as 72 mil cartas; há também um script CLI equivalente (`scripts/precompute_embeddings.py`) para rodar fora da UI, para contornar timeout do Streamlit Community Cloud. Na prática o `.npz` (e o `stems_*.pkl`) são baixados prontos das GitHub Releases na primeira execução (ver §2).
- **Validação de cache**: compara o conjunto de IDs salvos com os IDs atuais da base — se divergir, considera desatualizado e exige reindexação manual (nunca recomputa silenciosamente).
- **Texto indexado por carta**: concatenação de `texto | catalogo | indexacao`, truncada a 1800 caracteres (~450 tokens) para não estourar a janela de 512 tokens do modelo.
- **Busca**: normaliza a query, calcula similaridade cosseno via produto escalar vetorizado numpy (sem loop Python) contra toda a matriz. A UI busca **sem threshold** (score completo de todas as 72 mil cartas) e aplica o corte dinamicamente no slider — permitindo recalcular o histograma de distribuição de scores sem nova busca.
- **Paginação**: 50 resultados por página, com expanders lazy-load (estado de expansão rastreado em `session_state.semantic_expand_state`) para não renderizar texto de milhares de cartas de uma vez.

## 6. Análise de Frequência (`frequency_analyzer.py`, aba 9)

Funcionalidade:
- Aceita múltiplos termos separados por `,`, `;` ou `|`.
- Cada termo é configurável independentemente como **Exato** (substring) ou **Radical** (wildcard `termo\w*` via regex).
- Para cada termo: conta ocorrências totais, número de documentos únicos, gera cor automática de uma paleta fixa de 12 cores.
- Produz tabela resumo + dois gráficos Plotly comparativos (ocorrências totais vs. número de cartas) + detalhamento expansível por termo com preview de texto destacado (5 primeiras cartas) e tabela paginada (50 cartas).
- É funcionalmente adjacente à busca avançada, mas otimizado para **comparação lado a lado de múltiplos termos** (ex.: comparar frequência de "liberdade" vs. "igualdade" na base inteira), o que a busca avançada não faz.

## 7. Séries temáticas (`series_manager.py`)

- Estrutura em memória: `Dict[nome_serie] -> {cartas: set, descricao: str, criada_em: iso}`.
- **Índice invertido** `carta_id -> {nomes_de_série}` mantido em paralelo (`_carta_index`), reconstruído sob demanda (`_rebuild_carta_index`) para operações que alteram várias séries de uma vez (criar/deletar/renomear), mas atualizado incrementalmente nas operações comuns (adicionar/remover carta) — evita O(n) em cada toggle.
- `atualizar_series_carta` reconcilia a lista completa de séries de uma carta com uma única chamada a `save_session()`, independente de quantas séries mudaram — desenhado para o padrão de UI "multiselect + botão salvar" da sidebar.
- Persistência: escrita atômica (`arquivo.tmp` + `os.replace`) para não corromper `sessions/current_session.json` em caso de crash durante a gravação — mesmo padrão replicado em `annotation_manager.py`.

## 8. Anotações e caderno (`annotation_manager.py`)

- Duas camadas de anotação: por carta (`Dict[carta_id, texto]`) e caderno de pesquisa global (string Markdown livre).
- Auto-save a cada mudança (sem botão "salvar" explícito na maioria dos fluxos).
- `save_session()` só recebe `series` explicitamente quando chamado a partir do `SeriesManager`; caso contrário, relê o arquivo para não sobrescrever séries com dados obsoletos — acoplamento implícito entre os dois managers via um único arquivo compartilhado (`sessions/current_session.json`), sem lock de concorrência (assume uso single-user).

## 9. Exportação (`export_manager.py`, aba 4 + botões espalhados)

O módulo mais extenso do projeto (1.573 linhas). Funções-chave:

| Função | Formato/escopo |
|---|---|
| `exportar_serie_csv` / `_json` | Série individual |
| `exportar_todas_series_csv` / `_json` / `_pdf` | Todas as séries agregadas |
| `exportar_caderno_markdown` / `_txt` | Caderno de pesquisa |
| `exportar_zip_completo` | ZIP unificado (séries + caderno) |
| `exportar_pdf` | PDF de série/busca/filtro — usa ReportLab, com gráficos **matplotlib** embutidos (não Plotly) |
| `exportar_parquet` | Base/resultado via pandas+pyarrow; achata `series` em coluna `series_tematicas` com separador `" \| "` |
| `gerar_relatorio_html` / `_busca_html` / `_filtros_html` | Relatório analítico HTML com gráficos **Plotly interativos** embutidos via `to_html` |

**Decisão arquitetural não-óbvia**: existem **dois caminhos de geração de gráfico completamente distintos** — um para PDF (`_gerar_graficos_pdf`, matplotlib, estático) e outro para HTML (`_gerar_graficos_html`, Plotly, interativo) — porque ReportLab não renderiza Plotly. Qualquer novo gráfico de exportação precisa ser implementado duas vezes.

A busca semântica paginada (aba 8) tem uma armadilha de UX documentada no CLAUDE.md: os botões de exportação exportam **todos** os resultados acima do threshold, não apenas a página visível — comportamento correto mas potencialmente surpreendente.

## 10. Filtros (aba 7) e Gráficos (aba 6)

- Filtros multidimensionais sobre `ANALYSIS_FIELDS` (`sexo`, `estado_civil`, `faixa_etaria`, `morador`, `instrucao`, `faixa_renda`, `uf`, `municipio`, `atividade`, `origem`, `catalogo`, `indexacao`), com valores únicos computados e cacheados por sessão (chave = hash de `(tem_busca_ativa, tamanho_universo)`).
- Gráficos (aba 6) operam sobre três escopos possíveis — busca ativa, filtro ativo ou base inteira — com indicador de contexto explícito, evitando ambiguidade sobre "gráfico de quê".
- `cache_manager.compute_chart_data_cached` pré-computa todos os `value_counts()` de uma vez (compartilhado entre abas 6 e 8) em vez de recalcular por gráfico individual.

## 11. Gerenciamento de dados e múltiplas bases (`data_manager.py`, aba 5)

- Suporta múltiplas bases JSON simultâneas (`loaded_databases: Dict[filename, dict]`), com troca via sidebar.
- **Cache de módulo em nível de processo** (`_PARSED_DB_CACHE`, fora da classe) indexado por `(caminho_absoluto, mtime)` — evita reparsear um JSON de 100+ MB a cada rerun do Streamlit ou nova sessão do navegador, desde que o arquivo não tenha mudado em disco. Isso é uma otimização crítica dado que Streamlit reexecuta o script inteiro a cada interação.
- Detecção automática de formato: se o JSON tiver `{"cartas": [...]}` (formato de resultado de busca exportado), normaliza para `{id: {...}}` na carga — permite recarregar um export como uma "base" de trabalho.
- Na primeira execução, `garantir_base_baixada()` / `garantir_cache_baixado()` baixam `cartas_db.json` e `cache/*` das GitHub Releases se ausentes (ver §2).
- Conversor XLSX/CSV → JSON implementado no formulário da aba ⚙️ Configurações.
- A aba ⚙️ Configurações também expõe o botão "⚡ Pré-computar Índice de Stems" (seção "🧬 Índice de Stems"), que gera `cache/stems_{base}.pkl` via `StemmingEngine.compute_stem_index()` — pré-requisito para a busca em modo "Variações". Status (cache existe / válido / nº de cartas indexadas / nº de radicais) via `StemmingEngine.get_status()`; validação por comparação do conjunto de IDs, reindexação manual se a base mudar.

## 12. Cache e performance

- `compute_chart_data_cached` (com `ttl=3600`) está consolidada em `cache_manager.py`; a duplicação com uma versão inline em `app.py` foi resolvida no refactor de 2026-07-18 (ver item "Resolvidos" abaixo).
- `get_available_databases()` cacheado com `ttl=60` para não escanear o disco a cada rerun.
- Managers (`dm`, `am`, `sm`, `se`, `sem_e`) são extraídos do `session_state` para variáveis locais no topo do script — comentário explícito no código: "evita múltiplos lookups de `st.session_state` por rerun".
- `_todas_cartas = dm.get_todas_cartas()` também é cacheado localmente por render pelo mesmo motivo (evita "40+ chamadas no mesmo render").

## 13. Segurança e implantação

- Sem chamadas a APIs externas de IA — embeddings rodam 100% localmente (download único do modelo via Hugging Face Hub, ~420 MB).
- Nenhum dado do usuário é enviado a servidores. O único tráfego de saída (além do modelo) é o download de `cartas_db.json` e `cache/*` das GitHub Releases do projeto (`policronias/historicidades-democraticas-dados`), na primeira execução, quando ausentes.
- Dados e sessão persistidos apenas em arquivos locais (`cartas_db.json`, `sessions/current_session.json`, `cache/*.npz`, `cache/*.pkl`).
- Deploy público via **Streamlit Community Cloud**, protegido por senha de acesso (mecanismo nativo do Streamlit Cloud, não implementado em código — não há autenticação de usuários/roles na aplicação). Cloud redeploya automaticamente a cada push em `origin/main` no GitHub (`policronias/historicidades_democraticas`) — não há passo de deploy manual separado do `git push`. (A branch era `master` até 2026-08; hoje é `main`.)
- Local e Cloud rodam exatamente o mesmo `app.py`/`modules/` — não há branch ou config divergente por ambiente.
- Testes automatizados existem em `tests/` (`pytest`), ver §15 "Resolvidos".

## 14. Dependências principais

Versões mínimas (`requirements.txt` usa `>=`; ver arquivo para a lista exata): `streamlit>=1.31.0` · `pandas>=2.2.0` · `plotly>=5.22.0` · `sentence-transformers>=2.4.0` · `nltk>=3.8.0` · `numpy>=1.26.0` · `reportlab>=4.1.0` · `matplotlib>=3.10.0` · `pyarrow>=17.0.0` · `openpyxl>=3.1.2` · `tqdm>=4.67.0` · `filelock>=3.13.0` · `psutil>=5.9.0` (usado por `modules/memory_monitor.py`, opcional/debug) · `requests` (sem pin — download automático da base e do cache).

Dev (`requirements-dev.txt`, inclui `requirements.txt`): `pytest>=8.0.0` · `pytest-cov>=5.0.0` · `pytest-mock>=3.14.0` · `hypothesis>=6.100.0`.

## 15. Oportunidades técnicas identificadas (para discussão de roadmap)

Levantamento neutro de pontos que um plano de evolução técnica provavelmente vai querer endereçar — não são bugs confirmados, são observações de arquitetura.

### Resolvidos
- ✅ **Duplicação cache/UI** (2026-07-18): `build_df_fast()`, `compute_chart_data_cached()`, `build_semantic_csv_cached()` e CSS consolidados em `cache_manager.py` e `ui_manager.py`. App.py reduzido em 97 linhas.
- ✅ **Documentação** (2026-07-18): README.md e CLAUDE.md agora documentam as 9 abas incluindo Análise de Frequência.
- ✅ **Config morta**: `EMBEDDING_MODEL` em `config_manager.py` já reflete o modelo real (`paraphrase-multilingual-mpnet-base-v2`), consumido tanto pelo default de `SemanticEngine` quanto por `app.py`. `PROJECT_DIR`/`DATA_DIR`/`BASES_DIR` não existem mais no módulo.
- ✅ **Ausência de versionamento**: projeto passou a ser um repositório git, com histórico de commits ativo.
- ✅ **Persistência single-file, single-user**: `annotation_manager.py` agora usa `filelock.FileLock` (timeout de 5s) ao salvar `sessions/current_session.json`, evitando sobrescrita silenciosa entre sessões concorrentes.
- ✅ **Sem testes automatizados**: existe `tests/` (`conftest.py`, `test_series_manager.py`, `test_annotation_manager.py`, `test_search_engine.py`) mais `test_concurrent_sessions.py` na raiz, todos executáveis via pytest.
- ✅ **Busca lexical fixa**: `LEXICAL_VARIATIONS` foi substituído por `stemming_engine.py`, que faz stemming real via RSLP (NLTK) — busca por variações lexicais deixou de depender de um dicionário fixo de termos.

### Remanescentes
1. **Escala e memória**: base inteira (72.719 cartas, ~103 MB de JSON) carregada em memória do processo Streamlit; embeddings adicionam outra matriz (72.719 × 768 float32 ≈ 224 MB) quando carregados. Mitigações já em vigor: JSON parseado fica em cache de módulo por `(path, mtime)` (`_PARSED_DB_CACHE`), e modelo + matriz de embeddings ficam em `st.cache_resource` compartilhado entre sessões (`semantic_engine_cache.py`) — uma cópia por processo, não por sessão. Ainda assim, em ambientes com recursos limitados (Streamlit Cloud free tier) isso é um teto de escala real caso a base cresça.
2. **PDF vs HTML — dois pipelines de gráfico**: qualquer novo tipo de gráfico exige implementação separada em matplotlib (PDF) e Plotly (HTML). O cálculo dos dados já é unificado (`CHART_SPECS` + `_contar_campo()` em `export_manager.py`, usados por ambos os pipelines); só a etapa de renderização diverge (~80 linhas no total). A causa **não** é o ReportLab ser incapaz de renderizar Plotly — ele consegue, desde que a figura seja rasterizada antes via `kaleido`. A causa real é que `kaleido` não está instalado no projeto, e foi uma decisão deliberada não adicioná-lo: embute um Chromium headless (dependência pesada) e adiciona segundos de latência por gráfico exportado, sem ganho real numa duplicação já pequena e isolada — avaliado e descartado em 2026-08-23.
