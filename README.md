# 📚 Historicidades Democráticas

Plataforma completa de análise de documentos históricos construída com **Streamlit**. Oferece navegação, **busca avançada** (com operadores), **busca semântica**, **análise visual**, anotações, categorização temática e exportação em múltiplos formatos de correspondência histórica brasileira.

## 🎯 Características Principais

### 0. **Página Inicial (aba 🏠 Início)**
- Logomarca do projeto **Policronias do presente** (símbolo dos três círculos) em destaque
- Cartão para cada funcionalidade, com descrição curta e botão que abre a aba correspondente

### 1. **Navegação e Busca Avançada**
- Busca por texto com operadores: `"frase exata"`, `+obrigatório`, `-exclusão`, `termo*` (wildcard)
- Busca Simples ou com **Variações Lexicais** (radical RSLP via NLTK — reconhece flexões de qualquer palavra, sem lista fixa de termos; requer índice de stems pré-computado na aba ⚙️ Configurações)
- Scope: Somente Texto ou Base Inteira
- Destaque dinâmico com regex/múltiplas cores
- Navegação por ID rápida

### 2. **Séries Temáticas**
- Criar/editar/deletar séries temáticas com descrições
- Vincular múltiplas cartas por série
- Índice invertido para O(1) de lookup
- Painel unificado na sidebar (compartilhado em Explorador, Busca Semântica, Filtros)
- Visualizar/paginar séries (25 cartas por página)
- Exportar série individual (CSV/JSON/Parquet/PDF)

### 3. **Busca Semântica**
- Embeddings com busca por similaridade semântica
- Resultados paginados com expanders lazy-load
- Integração com painel de séries
- CSV com scores de relevância

### 4. **Filtros Interativos**
- Filtro por múltiplos campos (sexo, estado civil, faixa etária, instrução, renda, etc.)
- Painel de séries acessível no contexto de filtros
- Exportar resultados de filtro

### 5. **Gráficos e Tabelas**
- Gráficos interativos (Plotly): distribuição por sexo, UF, faixa etária, instrução, renda, atividade
- Tabelas geográficas (UF × Município)
- Estatísticas gerais da base
- Cache inteligente para performance

### 6. **Anotações e Caderno**
- Anotações vinculadas a cada carta (auto-save)
- Caderno de Pesquisa global (Markdown)
- Adicionar notas rápidas de cartas ao caderno
- Persistência automática

### 7. **9 Abas Principais**
- 🔍 **Explorar Cartas**: navegação + metadados + anotações
- 📓 **Caderno**: notas de pesquisa + anotações rápidas
- 🗂️ **Séries Temáticas**: criar, editar, visualizar séries + download
- 📥 **Exportar**: CSV, JSON, Parquet, HTML, PDF, ZIP (séries, busca, base completa)
- ⚙️ **Configurações**: gerenciar bases, backup/restore, conversor XLSX/CSV, pré-computar índice de stems
- 📊 **Gráficos e Tabelas**: análise visual dos dados
- 🎯 **Filtros**: filtro avançado por campo + painel de séries
- 🧠 **Busca Semântica**: busca por similaridade semântica
- 📈 **Análise de Frequência**: análise comparativa de múltiplos termos

### 8. **Múltiplas Bases de Dados**
- Carregar/alternar entre bases JSON
- Upload de novas bases via interface
- Conversor integrado: XLSX/CSV → JSON (com todos os metadados)

### 9. **Exportação Avançada**
- **Por série**: CSV, JSON, Parquet, PDF individuais
- **Busca**: CSV, JSON, Parquet, HTML, PDF dos resultados
- **Filtros**: CSV, JSON, Parquet, HTML, PDF dos resultados
- **Busca Semântica**: CSV, Parquet, PDF com scores de similaridade
- **Caderno**: TXT, Markdown
- **Completo**: ZIP unificado, Parquet da base, PDF de todas as séries, PDF da base
- **Relatório Analítico**: HTML com gráficos interativos Plotly, tabelas e metadados

### 10. **Design & UX**
- Identidade visual **"Policronias do presente"** (projeto de pesquisa UDESC/PPGH): sistema "papel de arquivo" — papel bege `#F1EDE2`, tinta grafite `#1B1815`, selo terracota `#9C3A26` como carimbo de ênfase; cantos sempre retos (raio 0)
- Tema nativo Streamlit com dois modos: claro "Papel de arquivo" e escuro (paleta reversa Policronias, acento terracota claro `#D97A5E`), alternáveis pelo menu ☰ > Settings
- Tipografia: Newsreader (títulos), IBM Plex Sans (corpo/interface), IBM Plex Mono (metadados); serif Newsreader para leitura longa do texto das cartas
- Interface responsiva (desktop/tablet)
- Sidebar dinâmica com contexto de navegação
- Ícones intuitivos
- Cache Streamlit para performance

## 📋 Sobre os Dados

A base de dados utilizada pela plataforma (`cartas_db.json`) deriva
integralmente da **Base SAIC** — o banco de dados oficial produzido pelo
Senado Federal (PRODASEN) com as 72.719 sugestões enviadas por cidadãos
brasileiros à Assembleia Nacional Constituinte (1986–1987), disponível
publicamente em
[senado.leg.br](https://www12.senado.leg.br/noticias/constituicao-dos-sonhos/).

**Nenhum valor de célula da planilha original foi alterado.** A conversão
para o formato interno do software envolveu apenas:

1. **Normalização dos nomes de coluna** (ex.: `SUGESTAO.TEXTO` → `texto`,
   `ESTADO CIVIL` → `estado_civil`) — mudança puramente formal, sem
   impacto no conteúdo.
2. **Adição de três campos de apoio à pesquisa**, que não existem na
   planilha original do Senado:
   - `linha` — número da linha na planilha original, para rastreabilidade;
   - `anotacoes` — anotações inseridas pelo(a) pesquisador(a) durante a análise;
   - `series` — vínculo da carta a séries temáticas criadas na pesquisa.

Esses três campos são produção analítica do projeto de pesquisa e não
devem ser confundidos com dados do cidadão-autor da carta ou do
Senado/PRODASEN. Para a tabela completa de correspondência entre a
planilha original e a base do software, ver [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md).

## 🚀 Como Usar

### Instalação

```powershell
# 1. Navegue para o diretório do projeto
cd historicidades_democraticas

# 2. Crie e ative o ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instale as dependências
pip install -r requirements.txt
```

### Executar a Plataforma

```bash
streamlit run app.py
```

A aplicação será aberta em `http://localhost:8501`

### Fluxo Básico de Uso

1. **Explorar Cartas** (Aba 1)
   - Previous/Next ou dropdown para navegar
   - Metadados completos + anotações
   - Série de cartas em contexto de busca

2. **Busca Avançada** (dentro da aba 🔍 Explorar Cartas)
   - Operadores: `"frase"`, `+termo`, `-exclusão`, `termo*`
   - Tipo: Simples ou Variações
   - Escopo: Texto ou Base Inteira
   - Destaque automático com múltiplas cores

3. **Busca Semântica** (Aba 8)
   - Digite texto natural (ex: "cartas sobre educação")
   - Resultados com score de similaridade
   - Paginação + painel de séries integrado
   - Exportar como CSV ou Parquet com scores

4. **Criar e Gerenciar Séries** (Aba 3)
   - Criar série com descrição
   - Multiselect de cartas
   - Visualizar série (paginada)
   - Exportar série (CSV/JSON/PDF)

5. **Filtros Avançados** (Aba 7)
   - Filtro por sexo, estado civil, faixa etária, etc.
   - Painel de séries sincronizado
   - Exportar resultados de filtro

6. **Análise Visual** (Aba 6)
   - Gráficos: distribuição por sexo, UF, instrução, etc.
   - Tabelas geográficas
   - Estatísticas gerais

7. **Anotações e Caderno** (Aba 2)
   - Anotações por carta (auto-save)
   - Caderno global (Markdown)
   - Adicionar notas rápidas

8. **Exportar e Configurar** (Abas 4 e 5)
   - Exportar: série, busca, filtro, caderno, base completa
   - Formatos: CSV, JSON, Parquet, HTML, PDF, ZIP
   - Configurações: bases, backup/restore, conversor XLSX/CSV

## 📁 Estrutura do Projeto

```
historicidades_democraticas/
├── app.py                          # Aplicação principal Streamlit (~3610 linhas)
├── requirements.txt                # Dependências de runtime
├── requirements-dev.txt            # + pytest / hypothesis (testes)
├── cartas_db.json                  # Base de dados JSON (~72k cartas, baixada automaticamente)
├── CLAUDE.md                       # Referência de arquitetura
├── README.md                       # Este arquivo
├── descricao_software.md           # Descrição técnica completa (estado real do código)
├── .streamlit/
│   └── config.toml                 # Tema nativo (claro/escuro), fontes, raio de borda
├── modules/
│   ├── __init__.py                # Exports de todos os módulos
│   ├── data_manager.py            # CRUD, índices, load/upload de bases + download automático
│   ├── search_engine.py           # Busca avançada, wildcard, highlight; variações via StemmingEngine
│   ├── semantic_engine.py         # Embeddings RoBERTa + busca semântica cosseno
│   ├── semantic_engine_cache.py   # Cache st.cache_resource do modelo e dos embeddings (entre sessões)
│   ├── series_manager.py          # Séries temáticas, índice invertido O(1)
│   ├── annotation_manager.py      # Anotações por carta, caderno de pesquisa (persistência com filelock)
│   ├── export_manager.py          # Exportação: CSV, JSON, Parquet, HTML, PDF, ZIP
│   ├── frequency_analyzer.py      # Análise comparativa de frequência de termos
│   ├── stemming_engine.py         # Variações lexicais por radical RSLP (NLTK); índice de stems
│   ├── search_suggestions.py      # Autocomplete / sugestões de termos a partir do histórico
│   ├── feedback_manager.py        # Helpers de feedback visual (status, progress, mensagens)
│   ├── cache_manager.py           # Cache consolidado: DataFrames, gráficos, CSV, lazy-load de abas
│   ├── ui_manager.py              # CSS mínimo + helpers de cor/tema Plotly (tema nativo em config.toml)
│   ├── config_manager.py          # Constantes, campos, EMBEDDING_MODEL, HIGHLIGHT_PALETTE, mensagens
│   └── memory_monitor.py          # Monitor de memória (debug, ?debug=memory na URL)
├── scripts/
│   ├── backup_sessao.py           # Script: backup manual da sessão
│   ├── consolidar_buscas.py       # Script: consolidar múltiplos CSVs de busca
│   └── precompute_embeddings.py   # Script: pré-computar embeddings (CLI)
├── tests/                          # pytest (search_engine, series_manager, annotation_manager)
├── cache/
│   ├── embeddings_<base>.npz      # Embeddings pré-computados (baixados automaticamente)
│   └── stems_<base>.pkl           # Índice de stems RSLP (baixado automaticamente)
└── sessions/
    └── current_session.json       # Sessão atual (anotações, séries, caderno)
```

> Na primeira execução, `app.py` baixa `cartas_db.json` e os arquivos de `cache/` das **GitHub Releases** (`policronias/historicidades-democraticas-dados`) caso não estejam presentes — o repositório de código não versiona esses arquivos grandes.

## 🔧 Arquitetura Técnica

### Data Manager (`modules/data_manager.py`)
- Load/upload de bases JSON
- Múltiplas bases simultâneas
- Índices: nome_index, series_index
- CRUD cartas, contadores
- Download automático da base e do cache (GitHub Releases) na primeira execução

### Search Engine (`modules/search_engine.py`)
- Busca simples, regex, wildcard
- Modo "Variações": stemming RSLP via `StemmingEngine` (sem dicionário fixo)
- Destaque HTML com regex
- Case-sensitive/insensitive

### Semantic Engine (`modules/semantic_engine.py`)
- Embeddings `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (RoBERTa multilíngue, 768 dim)
- Busca por similaridade cosseno vetorizada (NumPy)
- Scoring de relevância + threshold dinâmico no slider
- Cache `.npz` por base; modelo e matriz em `st.cache_resource` compartilhado entre sessões (`semantic_engine_cache.py`)

### Series Manager (`modules/series_manager.py`)
- Criar/editar/deletar séries
- Índice invertido (carta → séries)
- Paginação (25 itens/página)
- Persistência automática

### Annotation Manager (`modules/annotation_manager.py`)
- Anotações por carta (auto-save)
- Caderno de pesquisa global
- Contadores, timestamps
- Persistência JSON

### Export Manager (`modules/export_manager.py`)
- CSV, JSON, **Parquet** (pandas + pyarrow), HTML, PDF (série/busca/filtro/semântica/base)
- ZIP unificado com séries + caderno
- Relatório analítico HTML com gráficos Plotly interativos
- PDF com gráficos matplotlib embutidos (reportlab)
- Markdown/TXT para caderno

### Cache Manager (`modules/cache_manager.py`)
- `@st.cache_data` para DataFrames (`build_df_fast`, `build_df_cached`)
- Pré-computa dados de gráficos (`compute_chart_data_cached`, ttl 1h)
- CSV builder cached (`build_semantic_csv_cached`)
- Estado de lazy-load das abas 6–9 + cache de resultados de busca em `session_state`

### UI Manager (`modules/ui_manager.py`)
- CSS mínimo (tipografia serif do texto da carta) — cores vêm do tema nativo Streamlit
- Paleta de marca (`get_brand_palette`) + símbolo (`policronias_mark_svg`) da identidade Policronias
- Helpers de cor/tema para Plotly (`get_accent_color`, `get_plotly_color_palette`, `get_plotly_sequential_scale`, `apply_plotly_theme`, `format_pie_labels`), já que gráficos não herdam o tema nativo automaticamente

### Config Manager (`modules/config_manager.py`)
- `PAGE_CONFIG`, `METADATA_FIELDS`, `ANALYSIS_FIELDS`
- `EMBEDDING_MODEL`, `HIGHLIGHT_PALETTE`
- `MESSAGES` (mensagens padrão) — sem paths

## 💾 Persistência

Toda a sessão é salva automaticamente em `sessions/current_session.json`:

```json
{
  "anotacoes": {
    "81": "Nota sobre a carta 81",
    "191": "Outra nota"
  },
  "caderno_pesquisa": "# Minhas Pesquisas\n\nAnotações gerais...",
  "series": {
    "Educação": {
      "cartas": ["81", "191", "250"],
      "descricao": "Cartas sobre educação",
      "criada_em": "2024-01-15T10:30:00"
    }
  },
  "ultimo_update": "2024-01-20T15:45:30.123456"
}
```

## 🎨 Customização

### Alterar Paleta de Cores
As cores vêm do tema nativo do Streamlit, em `.streamlit/config.toml` (seções `[theme.light]` e `[theme.dark]`):

```toml
[theme.light]
primaryColor = "#9c3a26"            # selo terracota — ênfase, links, datação
backgroundColor = "#f1ede2"         # papel de arquivo
secondaryBackgroundColor = "#f8f5ec"
textColor = "#1b1815"               # tinta grafite
# ... demais cores (borderColor, linkColor, chartCategoricalColors, [theme.dark], sidebars) em .streamlit/config.toml
```

Gráficos Plotly não herdam esse tema automaticamente — as mesmas cores estão replicadas em `_CHART_THEME`, em `modules/ui_manager.py`. Ao mudar uma cor no `config.toml`, atualize também `_CHART_THEME` para os gráficos acompanharem:

```python
from modules.ui_manager import get_accent_color, get_plotly_color_palette
accent = get_accent_color()             # cor de destaque do tema ativo (claro/escuro)
paleta = get_plotly_color_palette()      # paleta categórica para gráficos Plotly
```

### Busca por Variações Lexicais
Não há mais dicionário `LEXICAL_VARIATIONS`. O modo "Variações" usa **stemming RSLP** (`modules/stemming_engine.py`): duas palavras são variações quando compartilham o mesmo radical, sem lista pré-selecionada de termos. Para habilitar, pré-compute o índice de stems na aba ⚙️ Configurações → "🧬 Índice de Stems" (ou via `scripts/precompute_embeddings.py`). Radicais muito curtos (`< MIN_STEM_LENGTH`) caem para substring exata para evitar colisões ortográficas.

## 📊 Exemplos de Uso

### Busca Avançada por Educação
1. Na aba 🔍 Explorar Cartas, seção "Busca Avançada"
2. Digite: `+educação -escravatura`
3. Selecione "Variações" (encontra: educação, educador, educativo...)
4. Resultados aparecem filtrados + destaque automático no texto

### Busca Semântica por Tema
1. Aba "Busca Semântica"
2. Digite: "cartas que discutem direitos políticos"
3. Obtenha resultados ordenados por similaridade semântica
4. Painel lateral para adicionar cartas a séries

### Criar Série e Exportar
1. Aba "Séries Temáticas" → "Criar Nova Série"
2. Nome: "Direitos Políticos", Descrição: "Discussões sobre voto e participação"
3. Multiselect cartas (use busca avançada para encontrá-las)
4. Aba "Exportar" → selecione série → CSV/JSON/PDF

### Análise Demográfica
1. Aba "Gráficos e Tabelas"
2. Visualize distribuição por sexo, UF, instrução
3. Identifique padrões (ex: mais cartas de SP do que RJ)
4. Exporte relatório HTML completo

## 🐛 Troubleshooting

### Busca Semântica lenta
- Embeddings são computados na primeira execução
- Depois são cacheados
- Reduza tamanho da base para testes
- Verifique memória disponível

### Sessão não salva
- Verifique permissões na pasta `sessions/`
- Confirme que `sessions/` existe
- Tente fazer backup manual em "Configurações"

### Base de dados não carrega
- Certifique-se que JSON é válido: `python -m json.tool cartas_db.json`
- Verifique encoding (UTF-8)
- Valide estrutura: cada carta deve ter campos esperados

### Gráficos não aparecem
- Verifique se Plotly está instalado: `pip install plotly`
- Cache pode estar obsoleto: `streamlit cache clear`
- Confirme que há dados para exibir

### Erro de memória com PDF grandes
- Gere PDF de séries menores primeiro
- Aumente memória disponível (sistemas com <4GB podem ter problemas)
- Exporte como CSV/JSON e processe com outro tool

## 📝 Comandos Úteis

```bash
# Validar JSON
python -m json.tool cartas_db.json

# Rodar com porta customizada
streamlit run app.py --server.port 8502

# Modo de desenvolvimento
streamlit run app.py --logger.level=debug

# Limpar cache Streamlit
streamlit cache clear
```

## 📚 Dependências

- **Streamlit** ≥1.31: Interface web, tema nativo (`.streamlit/config.toml`)
- **Pandas** ≥2.2: Manipulação de dados, DataFrames, exportação Parquet
- **PyArrow** ≥17: Backend Parquet para pandas
- **Plotly** ≥5.22: Gráficos interativos (HTML)
- **NumPy** ≥1.26: Operações numéricas / embeddings
- **Sentence-Transformers** ≥2.4: Embeddings RoBERTa multilíngue
- **NLTK** ≥3.8: Stemming RSLP (variações lexicais)
- **ReportLab** ≥4.1: Geração de PDF
- **Matplotlib** ≥3.10: Gráficos embutidos no PDF
- **openpyxl** ≥3.1: Leitura de XLSX no conversor XLSX/CSV → JSON
- **tqdm** ≥4.67: Progress bar nos embeddings
- **filelock** ≥3.13: Escrita concorrente segura de `sessions/current_session.json`
- **psutil** ≥5.9: Monitor de memória (debug, `?debug=memory`)
- **requests**: download automático da base e do cache a partir das GitHub Releases
- **re, json, csv, zipfile, datetime, io**: stdlib
- Testes (`requirements-dev.txt`): **pytest** ≥8, **pytest-cov**, **pytest-mock**, **hypothesis**

## 🔐 Segurança

- Arquivos JSON e de sessão são salvos localmente apenas
- Nenhum dado do usuário é enviado a servidores externos
- Embeddings rodam 100% localmente (download único do modelo via Hugging Face Hub, ~420 MB)
- Único tráfego de saída: download da base e do cache a partir das **GitHub Releases** do projeto, na primeira execução

## 📄 Licença

Projeto desenvolvido para análise de documentos históricos democráticos.

## 🤝 Contribuindo

Para adicionar features:
1. Implemente a lógica em um módulo apropriado
2. Adicione UI correspondente no `app.py`
3. Teste completamente
4. Documente mudanças

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte este README
2. Verifique os logs do Streamlit
3. Revise a estrutura em `modules/`
4. Teste com um arquivo JSON simples

---

**Desenvolvido para preservar e analisar correspondências constitucionais brasileiras** 📚
