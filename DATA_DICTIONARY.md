# Dicionário de Dados — Base SAIC e a base interna do software

Este documento explica a relação entre a **Base SAIC original** (planilha
distribuída pelo Senado Federal, formato `.xlsx`, 72.719 linhas) e a **base
interna do software Historicidades Democráticas** (`cartas_db.json`).

## 1. Princípio geral

**Nenhum valor de célula da planilha original foi alterado, editado ou
corrigido.** A conversão de `.xlsx` para `.json` (feita pelo conversor
integrado na aba ⚙️ Configurações) preserva o conteúdo textual e os
metadados sociodemográficos exatamente como constam na fonte primária.

O que muda é a **estrutura**: (a) os nomes das colunas foram normalizados
para facilitar o processamento em Python, e (b) três campos novos foram
adicionados pelo software para dar suporte às atividades de pesquisa —
esses três campos **não fazem parte da Base SAIC original** e não devem
ser confundidos com dado produzido pelo cidadão-autor da carta ou pelo
Senado/PRODASEN.

## 2. Tabela de correspondência (crosswalk)

| Coluna na Base SAIC original (`.xlsx`) | Campo na base do software (`.json`) | Observação |
|---|---|---|
| `NOME` | `nome` | idêntico, só minúsculo |
| `DESTINATARIO` | `destinatario` | idêntico |
| `CATALOGO` | `catalogo` | idêntico |
| `INDEXACAO` | `indexacao` | idêntico |
| `SUGESTAO.TEXTO` | `texto` | renomeado (conteúdo idêntico) |
| `ORIGEM` | `origem` | idêntico |
| `DATA` | `data` | idêntico |
| `FORMUL` | `formul` | idêntico |
| `DV` | `dv` | idêntico |
| `DATA2` | `data2` | idêntico |
| `MUNICIPIO` | `municipio` | idêntico |
| `UF` | `uf` | idêntico |
| `CEP` | `cep` | idêntico |
| `SEXO` | `sexo` | idêntico |
| `MORADOR` | `morador` | idêntico |
| `INSTRUCAO` | `instrucao` | idêntico |
| `ESTADO CIVIL` | `estado_civil` | renomeado (espaço → underscore) |
| `FAIXA ETÁRIA` | `faixa_etaria` | renomeado (sem acento/espaço) |
| `FAIXA RENDA` | `faixa_renda` | renomeado (sem espaço) |
| `ATIVIDADE` | `atividade` | idêntico |
| — (não existe na fonte) | `linha` | **campo novo**: número da linha correspondente na planilha original, para rastreabilidade/auditoria |
| — (não existe na fonte) | `anotacoes` | **campo novo**: anotações de pesquisa feitas pelo(a) pesquisador(a) dentro do software |
| — (não existe na fonte) | `series` | **campo novo**: lista de séries temáticas às quais a carta foi vinculada pelo(a) pesquisador(a) |

## 3. Por que isso importa para a publicação

- **Reprodutibilidade**: qualquer pessoa que confira a base do software
  contra a planilha original do Senado (disponível publicamente) deve
  encontrar os mesmos 72.719 registros e os mesmos valores em todos os
  19 campos originais.
- **Transparência**: os campos `linha`, `anotacoes` e `series` são
  produção analítica do projeto de pesquisa, não da fonte primária. Isso
  deve estar claro para qualquer usuário externo do software (revisor,
  outro pesquisador, orientador de banca) que venha a explorar a base.
- **Citação**: ao citar a fonte primária em textos acadêmicos, a
  referência correta continua sendo a Base SAIC/Senado Federal (ver
  `sumula.md`), não o arquivo `cartas_db.json` — este último é uma
  ferramenta de trabalho derivada da fonte, não uma fonte nova.

## 4. Recomendação prática

Ao exportar dados pela aba "📥 Exportar", existe a opção de exportar
**somente os campos originais** (excluindo `linha`, `anotacoes`, `series`)
sempre que o objetivo for compartilhar um recorte da base equivalente à
fonte primária (por exemplo, para verificação por terceiros ou para
publicação de material suplementar em um artigo).
