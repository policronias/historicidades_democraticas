# 📚 Historicidades Democráticas

Plataforma completa de análise de documentos históricos construída com **Streamlit**. Oferece navegação, **busca avançada** (com operadores), **busca semântica**, **análise visual**, anotações, categorização temática e exportação em múltiplos formatos de correspondência histórica brasileira.

## 🎯 Características Principais

### 0. **Página Inicial (aba 🏠 Início)**
- Logomarca do projeto **Policronias do presente** (símbolo dos três círculos) em destaque
- Cartão para cada funcionalidade, com descrição curta e botão que abre a aba correspondente

### 1. **Navegação e Busca Avançada**
- Busca por texto com operadores: `"frase exata"`, `+obrigatório`, `-exclusão`, `termo*` (wildcard)
- Busca Simples ou com Variações Lexicais
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
- ⚙️ **Configurações**: gerenciar bases, backup/restore, conversor XLSX/CSV
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
├── app.py                          # Aplicação principal Streamlit (~3509 linhas)
├── requirements.txt                # Dependências Python
├── cartas_db.json                  # Base de dados JSON (~72k cartas)
├── CLAUDE.md                       # Referência de arquitetura
├── README.md                       # Este arquivo
├── .streamlit/
│   └── config.toml                 # Tema nativo (claro/escuro), fontes, raio de borda
├── modules/
│   ├── __init__.py                # Exports de todos os módulos
│   ├── data_manager.py            # CRUD, índices, load/upload de bases
│   ├── search_engine.py           # Busca avançada, variações, wildcard
│   ├── semantic_engine.py         # Embeddings RoBERTa + busca semântica
│   ├── series_manager.py          # Séries temáticas, índice invertido O(1)
│   ├── annotation_manager.py      # Anotações por carta, caderno de pesquisa
│   ├── export_manager.py          # Exportação: CSV, JSON, Parquet, HTML, PDF, ZIP
│   ├── frequency_analyzer.py      # Análise comparativa de frequência de termos
│   ├── stemming_engine.py         # Processamento de stemming (suporta highlight)
│   ├── cache_manager.py           # Cache consolidado: DataFrames, gráficos, CSV
│   ├── ui_manager.py              # CSS mínimo, cores via tema nativo (.streamlit/config.toml)
│   ├── config_manager.py          # Constantes, paths, paleta, grupos de campos
│   └── memory_monitor.py          # Monitor de memória (debug, ?debug=true na URL)
├── scripts/
│   ├── backup_sessao.py           # Script: backup manual da sessão
│   ├── consolidar_buscas.py       # Script: consolidar múltiplos CSVs de busca
│   └── precompute_embeddings.py   # Script: pré-computar embeddings (CLI)
└── sessions/
    └── current_session.json       # Sessão atual (anotações, séries, caderno)
```

## 🔧 Arquitetura Técnica

### Data Manager (`modules/data_manager.py`)
- Load/upload de bases JSON
- Múltiplas bases simultâneas
- Índices: nome_index, series_index
- CRUD cartas, contadores

### Search Engine (`modules/search_engine.py`)
- Busca simples, regex, wildcard
- Variações lexicais automáticas
- Destaque HTML com regex
- Case-sensitive/insensitive

### Semantic Engine (`modules/semantic_engine.py`)
- Embeddings (modelo padrão)
- Busca por similaridade
- Scoring de relevância
- Cache de resultados

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
- @st.cache_data para DataFrames
- Pré-computa gráficos (Plotly)
- CSV builder cached

### UI Manager (`modules/ui_manager.py`)
- CSS mínimo (tipografia serif do texto da carta) — cores vêm do tema nativo Streamlit
- Helpers de cor/tema para Plotly (`get_accent_color`, `get_plotly_color_palette`, `apply_plotly_theme`), já que gráficos não herdam o tema nativo automaticamente

### Config Manager (`modules/config_manager.py`)
- Paths (PROJECT_DIR, DATABASE_PATH)
- Campos por categoria
- Paleta de cores
- Mensagens padrão

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
primaryColor = "#9c6b3f"
backgroundColor = "#f7f3ea"
secondaryBackgroundColor = "#efe9dc"
textColor = "#2b2621"
# ... demais cores em .streamlit/config.toml
```

Gráficos Plotly não herdam esse tema automaticamente — as mesmas cores estão replicadas em `_CHART_THEME`, em `modules/ui_manager.py`. Ao mudar uma cor no `config.toml`, atualize também `_CHART_THEME` para os gráficos acompanharem:

```python
from modules.ui_manager import get_accent_color, get_plotly_color_palette
accent = get_accent_color()             # cor de destaque do tema ativo (claro/escuro)
paleta = get_plotly_color_palette()      # paleta categórica para gráficos Plotly
```

### Adicionar Variações Lexicais
Em `modules/search_engine.py`, adicione ao dicionário `LEXICAL_VARIATIONS`:

```python
'democracia': r'\b(?:democracia|democrático|democrática)\b',
```

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
- **tqdm** ≥4.67: Progress bar nos embeddings
- **filelock** ≥3.13: Escrita concorrente segura de `sessions/current_session.json`
- **psutil** ≥5.9: Monitor de memória (debug, `?debug=true`)
- **re, json, csv, zipfile, datetime, io**: stdlib

## 🔐 Segurança

- Arquivos JSON são salvos localmente apenas
- Nenhuma chamada a API externa
- Nenhum envio de dados para servidores
- Dados de sessão em arquivo local

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
