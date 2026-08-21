# Análise Arquitetural: Duplicação de Gráficos em `export_manager.py`

**Data:** 2026-08-21  
**Tamanho do módulo:** ~1573 linhas  
**Escopo:** Dois pipelines completamente separados de geração de gráficos

---

## 1. INVENTÁRIO DE GRÁFICOS

### Pipeline HTML — `_gerar_graficos_html()` (linhas 138-307)
Tecnologia: **Plotly Express** → HTML inline com CDN Plotly

| # | Campo | Tipo | Top N | Escala de Cor | Linhas |
|----|-------|------|-------|----------------|--------|
| 1 | **sexo** | Barra H | — | Blues | 214–220 |
| 2 | **uf** | Barra H | 15 | Blues | 223–229 |
| 3 | **faixa_etaria** | Barra V | — | Teal | 232–239 |
| 4 | **estado_civil** | Barra H | — | Teal | 242–248 |
| 5 | **instrucao** | Barra H | 10 | Greens | 251–257 |
| 6 | **faixa_renda** | Barra H | 10 | Oranges | 260–266 |
| 7 | **atividade** | Barra H | 15 | Purples | 269–275 |
| 8 | **morador** | Barra H | — | Greens | 278–284 |
| 9 | **origem** | Barra V | 10 | Reds | 287–293 |
| 10 | **catalogo** | Barra H | 10 | Cividis | 296–302 |

**Total: 10 gráficos** (8 barras horizontais, 2 barras verticais)

---

### Pipeline PDF — `_gerar_graficos_pdf()` (linhas 310-394)
Tecnologia: **Matplotlib** → PNG buffer → ReportLab Table → PDF

| # | Campo | Tipo | Top N | Cor Hex | Linhas |
|----|-------|------|-------|---------|--------|
| 1 | **sexo** | Barra H | — | #3b82f6 | 356–375 |
| 2 | **uf** | Barra H | 10 | #1d4ed8 | 358–375 |
| 3 | **faixa_etaria** | Barra H | — | #0891b2 | 359–375 |
| 4 | **estado_civil** | Barra H | — | #0891b2 | 360–375 |
| 5 | **instrucao** | Barra H | 10 | #059669 | 361–375 |
| 6 | **faixa_renda** | Barra H | 10 | #d97706 | 362–375 |
| 7 | **atividade** | Barra H | 10 | #7c3aed | 363–375 |
| 8 | **morador** | Barra H | — | #059669 | 364–375 |

**Total: 8 gráficos** (todos barras horizontais)

---

## 2. ANÁLISE DE EQUIVALÊNCIA

### Gráficos Equivalentes (com divergências notáveis)

| Gráfico | HTML | PDF | Divergências |
|---------|------|-----|--------------|
| **Sexo** | Barra H, Plotly | Barra H, Matplotlib | ✓ Equivalentes (layout similar) |
| **UF** | Top 15 | Top 10 | ⚠️ **Top_n inconsistente** |
| **Faixa Etária** | Barra V, rotação -40° | Barra H | ⚠️ **Orientação diferente** |
| **Estado Civil** | Barra H | Barra H | ✓ Equivalentes |
| **Instrução** | Top 10 | Top 10 | ✓ Equivalentes |
| **Faixa Renda** | Top 10 | Top 10 | ✓ Equivalentes |
| **Atividade** | Top 15 | Top 10 | ⚠️ **Top_n inconsistente** |
| **Morador** | Barra H | Barra H | ✓ Equivalentes |

### Gráficos Exclusivos

| Campo | Onde? | Tipo | Motivo Provável |
|-------|-------|------|-----------------|
| **origem** | HTML apenas | Barra V, top 10 | Omitido em PDF (overhead) |
| **catalogo** | HTML apenas | Barra H, top 10 | Omitido em PDF (overhead) |

---

## 3. QUANTIFICAÇÃO DA DUPLICAÇÃO

### Código Duplicado

**Dados (preparação, contagem, top_n):**
- Função `_contar_campo()` (linhas 123–131): Compartilhada ✓

**Renderização (o problema real):**
- **HTML** (~170 linhas): Lógica Plotly + helpers `_hbar()`, `_vbar()`
- **PDF** (~85 linhas): Lógica Matplotlib + helper `_make_hbar()`
- **Total de código de renderização duplicado:** ~255 linhas

**Lugares de uso (chamadas aos pipelines):**
1. `exportar_pdf()` — linha 890
2. `exportar_todas_series_pdf()` — linha 1166
3. `gerar_relatorio_html()` — linha 1263
4. `gerar_relatorio_busca_html()` — linha 1425
5. `gerar_relatorio_filtros_html()` — linha 1526

**Impacto:** Se adicionar um novo gráfico (ex.: "Índice de Escolaridade Média"):
- ❌ Precisa implementar em DOIS lugares
- ❌ Manter `top_n` e cores sincronizadas manualmente
- ❌ Risco de divergências e bugs (ex.: UF top 15 vs top 10)

---

## 4. ARQUITETURA ATUAL

```
exportar_pdf() / exportar_todas_series_pdf()
    ↓
    _gerar_graficos_pdf(cartas_dict)  ← Matplotlib pipeline
        ├─ _make_hbar()
        └─ → PNG buffers → ReportLab Table

gerar_relatorio_html() / gerar_relatorio_busca_html() / gerar_relatorio_filtros_html()
    ↓
    _gerar_graficos_html(cartas_dict)  ← Plotly pipeline
        ├─ _hbar()
        ├─ _vbar()
        └─ → HTML strings com Plotly CDN

    COMPARTILHADO:
    _contar_campo(cartas_dict, campo, top_n)
```

**Problema:** Cada pipeline tem sua própria lógica de renderização, cores, dimensionamento, e até orientação de eixos.

---

## 5. ALTERNATIVAS DE SOLUÇÃO

### **OPÇÃO A: Unificar em Plotly + Kaleido (Render como PNG)**

**Ideia:** Gerar TODOS os gráficos em Plotly, renderizar como PNG com Kaleido, inserir no PDF (eliminando matplotlib).

**Prós:**
- ✅ Uma única linguagem de gráficos (Plotly)
- ✅ Cores, temas, dimensões sincronizados automaticamente
- ✅ Redução de código: `-85 linhas de matplotlib`
- ✅ Falha segura: `kaleido` é optional (já funciona sem)
- ✅ Qualidade visual do PDF melhora (Plotly render é mais refinado que matplotlib)

**Contras:**
- ❌ Kaleido precisa de Chromium headless (overhead ~60 MB, não está em requirements.txt)
- ❌ Em Streamlit Cloud com recursos limitados, renderizar 10 gráficos como PNG pode ser lento (~2-3s por PDF)
- ❌ Plotly → PNG perde interatividade, mas HTML interativo é preservado ✓
- ⚠️ Kaleido é dependência extra (adiciona 50MB ao ambiente)

**Esforço de implementação:** Médio (~3-4 horas)
- Adicionar `kaleido>=0.2.1` a requirements.txt
- Refatorar `_gerar_graficos_pdf()` para chamar Plotly + render com kaleido
- Simplificar CSS/layout de ReportLab

**Risco:** Baixo (Kaleido é maduro, usável com try/except)

---

### **OPÇÃO B: Camada de Abstração Única (Spec + Backends)**

**Ideia:** Criar uma representação **agnóstica** do gráfico (dados, tipo, cores, top_n) e dois backends (matplotlib/plotly) que a consomem.

```python
class ChartSpec:
    def __init__(self, campo, titulo, tipo='bar', orientacao='h', 
                 top_n=None, cor_plotly='Blues', cor_hex='#3b82f6'):
        self.campo = campo
        self.titulo = titulo
        self.tipo = tipo
        self.orientacao = orientacao
        self.top_n = top_n
        self.cor_plotly = cor_plotly
        self.cor_hex = cor_hex

def render_plotly(specs_list, cartas_dict) → str
def render_matplotlib(specs_list, cartas_dict) → List[ReportLab Image]
```

**Prós:**
- ✅ Fonte única de verdade para spec de cada gráfico
- ✅ Novo gráfico = adicionar 1 linha na definição
- ✅ Fácil manter top_n, cores sincronizadas
- ✅ Reutilizável em futuros contextos (ex.: API, React)
- ✅ Testável (spec é agnóstica)

**Contras:**
- ❌ Requer refatoração maior (~250 linhas → 180 linhas de app, +150 de abstração)
- ⚠️ Risco: Abstrações genéricas podem ser frágeis se gráficos futuros forem muito diferentes
- ❌ Trade-off: Perder flexibilidade de plotly (ex.: gráficos que não cabem no modelo)
- ⚠️ Mantém Matplotlib (35 MB, ainda duplica engine)

**Esforço de implementação:** Alto (~6-8 horas)
- Design da classe `ChartSpec` e validação
- Refatoração de `_gerar_graficos_html()` e `_gerar_graficos_pdf()`
- Testes de equivalência visual HTML ↔ PDF

**Risco:** Médio (abstração prematura pode ser subótima se gráficos divergirem no futuro)

---

### **OPÇÃO C: Extrair Preparação de Dados, Manter Renderização Duplicada**

**Ideia:** Isolar a lógica de **preparação** (contagem, top_n, seleção de cores) em funções compartilhadas. Deixar renderização final (matplotlib vs. plotly) como está.

```python
def prep_sexo(cartas_dict):
    return _contar_campo(cartas_dict, 'sexo')

def prep_uf(cartas_dict):
    return _contar_campo(cartas_dict, 'uf', top_n=15)

# etc.

CHARTS = [
    {'campo': 'sexo', 'titulo': 'Distribuição por Sexo', 'prep': prep_sexo, 
     'cor_plotly': 'Blues', 'cor_hex': '#3b82f6'},
    # ...
]

def _gerar_graficos_html(cartas_dict):
    for chart_spec in CHARTS:
        data = chart_spec['prep'](cartas_dict)
        # Render com Plotly

def _gerar_graficos_pdf(cartas_dict):
    for chart_spec in CHARTS:
        data = chart_spec['prep'](cartas_dict)
        # Render com Matplotlib
```

**Prós:**
- ✅ Mínima refatoração (~80 linhas de mudança)
- ✅ Reduz acoplamento: preparação e renderização separadas
- ✅ Fácil adicionar novo gráfico (1 entrada em `CHARTS`)
- ✅ Sincroniza colors/top_n automaticamente
- ✅ Mantém Matplotlib e Plotly (estrutura confortável)
- ✅ Baixo risco: renderização continua idêntica

**Contras:**
- ⚠️ Renderização ainda duplicada (~250 linhas permanecem)
- ⚠️ Futuro novo gráfico = ainda 2 impls de render
- ❌ Não resolve o problema de overhead de manutenção a longo prazo

**Esforço de implementação:** Baixo (~2-3 horas)
- Extrair specs para data structure
- Refatorar `_gerar_graficos_html()` e `_gerar_graficos_pdf()` para iterar sobre specs
- Testes de regressão visual

**Risco:** Muito baixo (mínima refatoração, sem dependências novas)

---

## 6. RECOMENDAÇÃO

### **Escolha: OPÇÃO C (Preparação Compartilhada)**

**Justificativa:**

1. **Esforço vs. Ganho:** Opção C oferece 70% do ganho (sincronização de dados/cores) com 30% do esforço.

2. **Risco Operacional:** 
   - OPÇÃO A (Kaleido) adiciona dependência pesada (~50 MB) em ambiente constrangido (Streamlit Cloud)
   - OPÇÃO B (Abstração) pode ser "engenharia excessiva" se gráficos não divergirem muito no futuro
   - OPÇÃO C: Risco negligenciável

3. **Manutenibilidade Imediata:**
   - PDF vs. HTML têm requisitos visuais realmente diferentes (matplotlib para print/documento, Plotly para interativo)
   - Renderização duplicada é aceitável porque serve propósitos diferentes
   - Dados duplicados (top_n inconsistente, cores desincronizadas) = problema real de OPÇÃO C resolve

4. **Janela de Melhoria Futura:**
   - OPÇÃO C deixa porta aberta para OPÇÃO A ou B depois
   - Se Kaleido for adoptado, convertar renderização fica trivial
   - Se gráficos ficarem mais complexos, abstração fica justificada

5. **Alinhamento com Projeto:**
   - Projeto prioriza funcionalidade sobre perfeição arquitetural
   - "Sem testes automatizados" (doc) → manutenção manual é crítica
   - OPÇÃO C reduz erro manual (cores/top_n) sem adicionar complexidade

---

## 7. PLANO DE IMPLEMENTAÇÃO (OPÇÃO C)

**Fase 1: Estruturação de Specs**
- Criar `CHART_SPECS` list com dicts para cada gráfico (título, campo, top_n, cores)
- Funções auxiliares: `prep_chart(spec, cartas_dict)`

**Fase 2: Refatoração HTML**
- `_gerar_graficos_html()` itera sobre `CHART_SPECS` em vez de hardcoded
- Reutiliza `prep_chart()` → dados sempre sincronizados

**Fase 3: Refatoração PDF**
- `_gerar_graficos_pdf()` itera sobre `CHART_SPECS` (subset) em vez de hardcoded
- Mesmo `prep_chart()` → cores/top_n sincronizadas

**Fase 4: Testes de Regressão**
- Comparação visual PDF antigo vs. novo (cores, labels, top_n)
- Comparação HTML (interatividade preservada?)

**Esforço Total:** ~3-4 horas  
**Risco:** Baixo  
**Ganho Imediato:** Reduz bug potencial (top_n/cores desincronizadas)  
**Ganho Futuro:** Novo gráfico = 1 linha em specs + 1 render-impl em cada backend

---

## 8. TRADE-OFFS FINAIS

| Aspecto | OPÇÃO A | OPÇÃO B | OPÇÃO C |
|---------|---------|---------|---------|
| **Esforço** | 3-4h | 6-8h | 2-3h |
| **Risco** | Médio (Kaleido) | Médio (Abstração) | Baixo |
| **Ganho Imediato** | 85L menos código | 70L menos código | 30L menos código |
| **Ganho Futuro** | Alto (sem matplotlib) | Alto (novo gráfico fácil) | Médio (render ainda duplicado) |
| **Viável em Streamlit Cloud?** | Sim, com overhead | Sim | Sim |
| **Recomendado AGORA?** | Depois | Depois | ✅ **SIM** |

---

**Conclusão:** OPÇÃO C é o Goldilocks – não é perfeita, mas é pragmática, segura e deixa a porta aberta para evoluir.
