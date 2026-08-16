# 📋 Plano de Melhoria: UX & Funcionalidade
**Históricidades Democráticas** — Foco em 4 Pilares

---

## 1. ⚡ OTIMIZAR PERFORMANCE

### Problemas Identificados:
- 28 `@st.cache` espalhados em app.py — difícil de gerenciar
- Cache de séries invalida frequentemente
- Lazy load de abas não implementado
- Operações PDF longas bloqueiam UI

### Soluções Propostas:

#### 1.1 Consolidar Cache em `cache_manager.py`
```python
# Em vez de:
@st.cache_data(ttl=60)
def load_data():
    return dm.load_db()

# Fazer:
def get_cached_db():
    from modules.cache_manager import build_df_fast
    return build_df_fast()  # Centralizado
```
**Impacto**: Melhor controle, TTL consistente, fácil invalidação

#### 1.2 Lazy Load de Abas
- Abas 1-5: Carregar imediatamente
- Abas 6-9 (Gráficos, Filtros, Semântica, Frequência): Carregar sob demanda
**Impacto**: Primeira carga 3-5x mais rápida

#### 1.3 Cache de Search Results com TTL
```python
# Guardar últimos 5 searches em session_state
st.session_state.search_history = {
    "query": results,
    "timestamp": now,
    "ttl": 3600
}
```
**Impacto**: Sem delay em buscas repetidas

#### 1.4 Async PDFs (Background Task)
- PDF gerado em thread separada
- User pode continuar navegando
- Notificação quando pronto para download
**Impacto**: UI não bloqueia durante export

---

## 2. 🎨 MELHORAR FEEDBACK VISUAL

### Problemas Identificados:
- `st.spinner()` genérico ("Gerando PDF...")
- Sem indicação de progresso em operações longas
- Sem feedback de sucesso/erro claro
- Sem loading state em abas

### Soluções Propostas:

#### 2.1 Usar `st.status()` em vez de `st.spinner()`
```python
# Antes:
with st.spinner("Gerando PDF..."):
    pdf_bytes = export_pdf(...)

# Depois:
with st.status("📄 Gerando PDF...", expanded=True) as status:
    st.write("Processando cartas...")
    pdf_bytes = export_pdf(...)
    st.write("Formatando PDF...")
    status.update(label="✅ PDF pronto!", state="complete")
```
**Impacto**: User vê progresso real

#### 2.2 Progress Bars para Operações Longas
```python
progress_bar = st.progress(0)
for i, carta in enumerate(cartas):
    process(carta)
    progress_bar.progress((i+1) / len(cartas))
```
**Impacto**: Visual feedback, não fica preso

#### 2.3 Toast Notifications (Success/Error)
```python
try:
    save_annotation(...)
    st.success("✅ Anotação salva com sucesso!")
except Exception as e:
    st.error(f"❌ Erro ao salvar: {str(e)}")
```
**Impacto**: Feedback claro de ações

#### 2.4 Skeleton/Loading State nas Abas
```python
if 'tab_6_loaded' not in st.session_state:
    with tab6:
        st.write("⏳ Carregando gráficos...")
else:
    # Mostrar gráficos
```
**Impacto**: User sabe que está loading, não é branco vazio

---

## 3. 🧭 REFATORAR NAVEGAÇÃO

### Problemas Identificados:
- Sidebar confusa (muitos itens espalhados)
- Sem contexto visual (qual aba estou?)
- Difícil voltar para home/explorador
- Sem breadcrumbs ou caminho visual

### Soluções Propostas:

#### 3.1 Reorganizar Sidebar em Seções
```
📚 HISTORICIDADES DEMOCRÁTICAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 BUSCAR & EXPLORAR
  ├─ Explorador de Cartas
  ├─ Busca Avançada
  ├─ Semântica
  └─ [Botão "Limpar contexto"]

📊 ANÁLISE
  ├─ Filtros
  ├─ Frequência
  └─ Gráficos

📝 MEUS DADOS
  ├─ Anotações
  ├─ Séries
  └─ Exportar

⚙️ SISTEMA
  ├─ Configurações
  └─ Carregar Base
```
**Impacto**: Muito mais intuitivo

#### 3.2 Breadcrumb em Abas Secundárias
```python
# Na aba "Explorador de Cartas"
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("← Voltar ao explorador"):
        st.session_state.current_view = "explorer"
        st.rerun()
with col2:
    st.caption("📍 Explorador > Carta #42")
```
**Impacto**: User sempre sabe onde está

#### 3.3 "Home" Button na Sidebar
```python
if st.sidebar.button("🏠 Ir para Home"):
    st.session_state.clear()
    st.session_state.initialization_done = False
    st.rerun()
```
**Impacto**: Fácil reset e voltar ao início

#### 3.4 Context Preservation
- Quando volta do "Detalhes da Carta" → Manter filtros anteriores
- Quando troca aba → Manter estado (scroll, seleção)
**Impacto**: Fluxo mais natural

---

## 4. 🔍 MELHORAR SEARCH

### Problemas Identificados:
- Sem autocomplete
- Sem histórico de buscas
- Search delay (computa tudo)
- Sem filtros pré-aplicados

### Soluções Propostas:

#### 4.1 Autocomplete/Suggestions
```python
# Manter cache de termos frequentes
if 'termo_cache' not in st.session_state:
    st.session_state.termo_cache = [
        "brasil", "constituição", "senado", 
        "deputados", "cidadão", "direito"
    ]

termo = st.selectbox(
    "Termo a buscar:",
    st.session_state.termo_cache,
    key="search_termo"
)
```
**Impacto**: Search mais rápido, descoberta melhor

#### 4.2 Histórico de Buscas
```python
# Sidebar
with st.sidebar.expander("📜 Últimas Buscas"):
    if 'search_history' in st.session_state:
        for i, h in enumerate(st.session_state.search_history[-10:]):
            if st.button(f"{h['termo']} ({h['count']} resultados)"):
                # Restaurar busca
                st.session_state.search_termo = h['termo']
                st.rerun()
```
**Impacto**: Rápido acesso a buscas anteriores

#### 4.3 Search Results Melhorados
```python
# Em vez de listar 100 linhas:
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total encontrado", len(results))
with col2:
    st.metric("Cartas com termo", len(set(r['id'] for r in results)))
with col3:
    st.metric("Documentos", dm.get_total_docs())

# Pagination
page = st.number_input("Página", 1, max(1, len(results)//10))
start, end = (page-1)*10, page*10
for r in results[start:end]:
    with st.expander(f"📄 Carta #{r['id']} - {r['data']}", expanded=False):
        st.write(r['texto'][:300] + "...")
        if st.button("Ver Completo", key=r['id']):
            st.session_state.current_view = "detail"
            st.session_state.current_id = r['id']
            st.rerun()
```
**Impacto**: Mais escaneável, melhor UX

#### 4.4 Filtros Pré-aplicados
```python
# Sidebar - Quick Filters
with st.sidebar.expander("⚡ Filtros Rápidos"):
    if st.checkbox("Apenas século XX"):
        # Aplicar filtro
        resultados = [r for r in resultados if 1900 <= r['ano'] <= 2000]
    
    if st.checkbox("Senadores apenas"):
        resultados = [r for r in resultados if r['tipo'] == 'senador']
```
**Impacto**: Search mais preciso, menos resultados noise

---

## 📊 Impacto Estimado

| Pilar | Antes | Depois | Ganho |
|-------|-------|--------|-------|
| **Performance** | ~5s carga | ~1.5s carga | **3.3x** |
| **Feedback** | Opaco | Claro | Satisfação ↑↑ |
| **Navegação** | Confusa | Intuitiva | Curva aprendizado ↓ |
| **Search** | Genérico | Refinado | Precisão ↑↑ |

---

## 🚀 Roadmap Sugerido

### Fase 1 (Semana 1): Performance + Feedback
- [ ] Consolidar cache em `cache_manager.py`
- [ ] Lazy load de abas 6-9
- [ ] Substituir `st.spinner()` por `st.status()`
- [ ] Adicionar progress bars

### Fase 2 (Semana 2): Navegação
- [ ] Reorganizar sidebar em seções
- [ ] Adicionar breadcrumbs
- [ ] Home button
- [ ] Context preservation

### Fase 3 (Semana 3): Search
- [ ] Autocomplete
- [ ] Histórico de buscas
- [ ] Melhorar resultado view
- [ ] Filtros pré-aplicados

---

## 📌 Notas Importantes

- **Manter simplicidade**: Streamlit é limitado; não tentar fazer React
- **Testar com usuários**: Mostrar melhorias para alguém usando realmente
- **Priorizar o que dói mais**: Performance > Feedback > Navegação > Search
- **Commits pequenos**: Um feature por commit

---

**Próximo passo?** Qual dessas fases você quer começar? 🚀
