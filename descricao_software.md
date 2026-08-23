# Historicidades Democráticas — Descrição Técnica Completa

> Documento preparado para orientar planejamento de melhorias técnicas, novos recursos e evolução arquitetural do software. Descreve o estado real do código (não a intenção original), levantado por leitura direta de `app.py` e dos módulos em `modules/`.
>
> **Última atualização**: 2026-07-18 (pós-refatoração de cache e UI)

## 1. Propósito e contexto

**Historicidades Democráticas** é uma plataforma de pesquisa acadêmica (Streamlit, Python) para explorar, buscar, anotar e analisar um corpus de correspondência histórica brasileira: a **Base SAIC**, composta por **72.719 cartas/sugestões de cidadãos** enviadas ao processo constituinte (Assembleia Nacional Constituinte). O projeto é conduzido por Walderez Ramalho (UDESC) e roda tanto localmente quanto publicamente em **Streamlit Community Cloud**, protegido por senha.

Cada "carta" é um registro com texto livre (`texto`) e metadados sociodemográficos e catalográficos: `linha`, `nome`, `destinatario`, `catalogo`, `indexacao`, `origem`, `data`, `data2`, `formul`, `dv`, `municipio`, `uf`, `cep`, `sexo`, `morador`, `instrucao`, `estado_civil`, `faixa_etaria`, `faixa_renda`, `atividade`, além de `anotacoes` (nota do pesquisador) e `series` (vínculo a séries temáticas).

A base principal (`cartas_db.json`) tem **~103 MB** e é carregada inteiramente em memória — não há banco de dados relacional nem paginação em disco. A fonte bruta é uma planilha (`sugestoes_constituintes_72k.xlsx`, ~29 MB), convertida para JSON pelo conversor embutido na interface (aba ⚙️ Configurações).

## 2. Arquitetura geral

```
app.py                      # Aplicação Streamlit (~3.281 linhas), single-page com 9 abas
modules/
  __init__.py                # Agregador de exports públicos dos módulos
  data_manager.py       (272) # Carga/troca de bases, índices, cache de JSON parseado em memória de módulo
  search_engine.py      (527) # Busca avançada (operadores), variações lexicais, highlight
  semantic_engine.py    (385) # Embeddings RoBERTa, cache .npz, busca por similaridade cosseno
  series_manager.py     (345) # Séries temáticas, índice invertido carta→séries
  annotation_manager.py (218) # Anotações por carta + caderno de pesquisa, persistência JSON atômica
  export_manager.py    (1573) # CSV/JSON/Parquet/HTML/PDF/ZIP — exportação unificada
  frequency_analyzer.py (300) # Análise de frequência de termos (aba 9, agora documentada)
  stemming_engine.py    (~80) # Processamento de stemming/stemming com RSLP
  cache_manager.py      (127) # CONSOLIDADO: funções cacheadas (build_df_fast, compute_chart_data_cached, build_semantic_csv_cached)
  ui_manager.py         (210) # CONSOLIDADO: CSS centralizado, configure_page_style(), get_color_scheme()
  config_manager.py     (156) # Constantes, paths, paleta de cores, grupos de campos
sessions/current_session.json  # Único arquivo de estado persistido (anotações, caderno, séries)
cache/embeddings_*.npz         # Cache de embeddings por base de dados
scripts/
  consolidar_buscas.py   (321) # Script auxiliar — consolidação de múltiplos CSVs de busca
  precompute_embeddings.py (197) # Script CLI para pré-computar embeddings (evita timeout do Streamlit Cloud)
```

**Observação arquitetural**: `app.py` é uma aplicação Streamlit de execução única (script top-to-bottom, reexecutado a cada interação), sem funções `main()` nem roteamento — os 9 blocos `with tabX:` são simplesmente seções sequenciais do mesmo script. Esse é o modelo de execução padrão do Streamlit. 

**Refatoração realizada (2026-07-18)**:
- ✅ **`cache_manager.py` consolidado**: funções cacheadas (`build_df_fast()`, `compute_chart_data_cached()`, `build_semantic_csv_cached()`) removidas de `app.py` e importadas de `modules.cache_manager`
- ✅ **`ui_manager.py` integrado**: CSS removido de `app.py` (98 linhas); `configure_page_style()` chamada no startup; `get_color_scheme()` acessível
- ✅ **Redução de `app.py`**: 3378 → 3281 linhas (-97 linhas de duplicação); melhor separação de responsabilidades
- ✅ **Nenhuma perda de funcionalidade**: todas as APIs mantidas idênticas; aplicação 100% funcional

## 3. As 9 abas da aplicação

A interface é organizada em uma área de **Busca Avançada + Navegação por ID** (fora das abas, sempre visível) e 9 abas (`st.tabs`):

| # | Aba | Arquivo/linhas | Função |
|---|-----|-----------------|--------|
| 1 | 🔍 Explorar Cartas | app.py:828-1035 | Navegação sequencial (anterior/próxima/dropdown), metadados completos, anotação inline, painel de séries |
| 2 | 📓 Caderno | app.py:1040-1067 | Anotação por carta + caderno de pesquisa livre em Markdown |
| 3 | 🗂️ Séries Temáticas | app.py:1072-1433 | CRUD de séries, multiselect de cartas, paginação (25/página), download unificado |
| 4 | 📥 Exportar | app.py:1438-1805 | Exportação de busca, série, filtro, caderno e base completa em múltiplos formatos |
| 5 | ⚙️ Configurações | app.py:1810-1959 | Seleção/upload de base, backup/restore de sessão, limpeza |
| 6 | 📊 Gráficos e Tabelas | app.py:1964-2154 | Gráficos Plotly demográficos/geográficos/temáticos sobre busca, filtro ou base inteira |
| 7 | 🎯 Filtros | app.py:2159-2579 | Filtro multidimensional por campo (sexo, UF, faixa etária, renda, etc.) |
| 8 | 🧠 Busca Semântica | app.py:2581-3062 | Busca por similaridade de embeddings RoBERTa, paginada, com threshold ajustável |
| 9 | 📈 Análise de Frequência | app.py:3063-3298 | **Aba não documentada no README/CLAUDE.md atual** — análise comparativa multi-termo (ver §6) |

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
- **Variações lexicais**: dicionário `LEXICAL_VARIATIONS` fixo (11 entradas: história, democracia, constituição, governo, povo, direito, liberdade, justiça, igualdade, educação, saúde) mapeando para regex de flexões; para termos fora do dicionário, gera um padrão automático `\b{termo}\w*\b`.

Escopo de busca: **"Somente Texto"** (campo `texto`) vs **"Base Inteira"** (`texto`, `nome`, `destinatario`, `catalogo`, `indexacao`, `origem`).

O **highlight** usa um padrão StringBuilder (concatenação de lista + `join` único) explicitamente para evitar complexidade O(n²) de concatenação repetida de strings — comentário no código confirma que essa foi uma otimização deliberada. `highlight_multiple_terms` suporta múltiplas cores simultâneas, deduplicando sobreposições.

## 5. Busca semântica (`semantic_engine.py`, aba 8)

- **Modelo**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (RoBERTa multilíngue, 768 dimensões, janela de 512 tokens), carregado **lazy** (só na primeira chamada) e mantido em memória.
  - **Inconsistência a resolver**: `config_manager.py` define `EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'`, mas essa constante **não é usada em lugar nenhum** — `SemanticEngine()` é instanciado sem argumentos em `app.py:287`, usando o default do próprio construtor (mpnet). É configuração morta/enganosa que vale limpar ou sincronizar.
- **Pré-computação**: botão explícito "⚡ Pré-computar Embeddings" (não é automático) — processa em batches de 32, salva `.npz` comprimido (`embeddings` float32 normalizado L2 + `ids`) em `cache/embeddings_{nome_base}.npz`. Leva **15–40 minutos em CPU** para as 72 mil cartas; há também um script CLI equivalente (`scripts/precompute_embeddings.py`) para rodar fora da UI, presumivelmente para contornar timeout do Streamlit Community Cloud.
- **Validação de cache**: compara o conjunto de IDs salvos com os IDs atuais da base — se divergir, considera desatualizado e exige reindexação manual (nunca recomputa silenciosamente).
- **Texto indexado por carta**: concatenação de `texto | catalogo | indexacao`, truncada a 1800 caracteres (~450 tokens) para não estourar a janela de 512 tokens do modelo.
- **Busca**: normaliza a query, calcula similaridade cosseno via produto escalar vetorizado numpy (sem loop Python) contra toda a matriz. A UI busca **sem threshold** (score completo de todas as 72 mil cartas) e aplica o corte dinamicamente no slider — permitindo recalcular o histograma de distribuição de scores sem nova busca.
- **Paginação**: 50 resultados por página, com expanders lazy-load (estado de expansão rastreado em `session_state.semantic_expand_state`) para não renderizar texto de milhares de cartas de uma vez.

## 6. Análise de Frequência (`frequency_analyzer.py`, aba 9)

Módulo e aba **presentes no código mas ausentes da documentação existente** (README.md e CLAUDE.md descrevem só 8 abas). Funcionalidade:
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
- Conversor XLSX/CSV → JSON implementado no formulário da aba ⚙️ Configurações (lines 333-451 em `app.py`).

## 12. Cache e performance

- `compute_chart_data_cached` (com `ttl=3600`) está consolidada em `cache_manager.py`; a duplicação com uma versão inline em `app.py` foi resolvida no refactor de 2026-07-18 (ver item "Resolvidos" abaixo).
- `get_available_databases()` cacheado com `ttl=60` para não escanear o disco a cada rerun.
- Managers (`dm`, `am`, `sm`, `se`, `sem_e`) são extraídos do `session_state` para variáveis locais no topo do script — comentário explícito no código: "evita múltiplos lookups de `st.session_state` por rerun".
- `_todas_cartas = dm.get_todas_cartas()` também é cacheado localmente por render pelo mesmo motivo (evita "40+ chamadas no mesmo render").

## 13. Segurança e implantação

- Sem chamadas a APIs externas de IA — embeddings rodam 100% localmente (download único do modelo via Hugging Face Hub, ~420 MB).
- Dados e sessão persistidos apenas em arquivos locais (`cartas_db.json`, `sessions/current_session.json`, `cache/*.npz`).
- Deploy público via **Streamlit Community Cloud**, protegido por senha de acesso (mecanismo nativo do Streamlit Cloud, não implementado em código — não há autenticação de usuários/roles na aplicação).
- Sem testes automatizados (`pytest`, etc.) identificados no projeto.

## 14. Dependências principais

`streamlit==1.28.1` · `pandas==2.1.3` · `plotly==5.20.0` · `sentence-transformers>=2.2.0` · `numpy>=1.24.0` · `reportlab>=4.0.0` · `matplotlib>=3.6.0` · `pyarrow>=14.0.0` · `openpyxl>=3.1.0` · `tqdm>=4.64.0`.

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
1. **Escala e memória**: base inteira (72.719 cartas, ~103 MB de JSON) carregada em memória do processo Streamlit a cada sessão; embeddings adicionam outra matriz (72.719 × 768 float32 ≈ 224 MB) quando carregados. Em ambientes com recursos limitados (Streamlit Cloud free tier) isso é um teto de escala real caso a base cresça.
2. **PDF vs HTML — dois pipelines de gráfico**: qualquer novo tipo de gráfico exige implementação separada em matplotlib (PDF) e Plotly (HTML). O cálculo dos dados já é unificado (`CHART_SPECS` + `_contar_campo()` em `export_manager.py`, usados por ambos os pipelines); só a etapa de renderização diverge (~80 linhas no total). A causa **não** é o ReportLab ser incapaz de renderizar Plotly — ele consegue, desde que a figura seja rasterizada antes via `kaleido`. A causa real é que `kaleido` não está instalado no projeto, e foi uma decisão deliberada não adicioná-lo: embute um Chromium headless (dependência pesada) e adiciona segundos de latência por gráfico exportado, sem ganho real numa duplicação já pequena e isolada — avaliado e descartado em 2026-08-23.
