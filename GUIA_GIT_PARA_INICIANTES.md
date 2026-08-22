# Guia de Git para Iniciantes — Historicidades Democráticas

> Este guia foi escrito para quem **não é programador** e não tem familiaridade com conceitos de computação. Todos os comandos abaixo foram testados considerando que você está no Windows, usando o PowerShell, dentro da pasta do projeto (`C:\Projetos\historicidades_democraticas`).

---

## 1. O que é Git, na prática (sem jargão)

Pense no Git como uma **máquina do tempo** para os arquivos do seu projeto.

- Cada vez que você salva um "ponto de checagem" (isso se chama **commit**), o Git tira uma foto completa de como todos os arquivos estavam naquele momento.
- Essas fotos ficam guardadas para sempre (a não ser que você as apague de propósito), formando uma linha do tempo — o **histórico**.
- Se depois de uma alteração o programa quebrar, piorar, ou você simplesmente mudar de ideia, você pode **voltar para qualquer foto anterior**.
- O **GitHub** é apenas um "cofre" na internet onde uma cópia dessa linha do tempo fica guardada, para o caso do seu computador quebrar, perder o arquivo, etc. Ele não faz nada sozinho — você que manda as fotos (commits) para lá quando quiser, com o comando `git push`.

**Sua intuição está certa.** Sim, é exatamente para isso que serve: te dar a segurança de experimentar mudanças sabendo que sempre existe um "botão de desfazer" para voltar a um estado bom.

### Termos que vão aparecer

| Termo | O que significa |
|---|---|
| **Repositório (repo)** | A pasta do projeto inteira, com todo o histórico do Git dentro dela (numa pasta escondida chamada `.git`) |
| **Commit** | Uma "foto" salva do projeto, com uma mensagem explicando o que mudou |
| **Histórico** | A lista de todos os commits, em ordem cronológica |
| **Branch** | Uma "linha do tempo paralela". Seu projeto usa só uma, chamada `master` |
| **Remoto (remote/origin)** | O endereço do GitHub onde a cópia do histórico fica salva. No seu caso: `origin` |
| **Push** | Enviar seus commits (fotos) do seu computador para o GitHub |
| **Pull** | Trazer commits do GitHub para o seu computador |
| **Status** | Um "raio-X" que mostra o que foi alterado desde a última foto |

---

## 2. Antes de mexer em qualquer coisa: veja o estado atual

Sempre que for começar a trabalhar (ou se algo parecer estranho), rode:

```powershell
git status
```

Isso te diz:
- Se há arquivos alterados que ainda **não** foram salvos como commit
- Se você está "na frente" ou "atrás" do GitHub

Se aparecer `nothing to commit, working tree clean`, significa que tudo que você tem no computador já está salvo e igual ao último commit — ou seja, você está em um "ponto seguro" conhecido.

---

## 3. Fluxo do dia a dia (salvando o trabalho)

Isso é o que você (ou eu, quando mexo no código a seu pedido) faz regularmente:

### Passo 1 — Ver o que mudou
```powershell
git status
```

### Passo 2 — Ver exatamente as linhas que mudaram (opcional, mas recomendado)
```powershell
git diff
```
Isso mostra, arquivo por arquivo, o que foi adicionado (linhas em verde/`+`) e removido (linhas em vermelho/`-`).

### Passo 3 — Escolher o que vai virar "foto" (commit)
```powershell
git add app.py
```
(Troque `app.py` pelo nome do arquivo que mudou. Se quiser adicionar **todos** os arquivos alterados de uma vez, existe `git add -A`, mas use com cuidado — veja a seção 7.)

### Passo 4 — Tirar a foto (criar o commit)
```powershell
git commit -m "Descrição curta do que mudou"
```
Exemplo real do seu projeto: `git commit -m "Fix: corrige navegação Anterior/Próximo"`

### Passo 5 — Mandar a foto para o GitHub (backup na nuvem)
```powershell
git push
```

**Importante:** enquanto você não fizer `git commit`, a alteração só existe "solta" no seu computador — ainda não virou uma foto que pode ser recuperada depois. E enquanto não fizer `git push`, a foto existe só no seu computador, não no GitHub.

---

## 4. "Já bagunçei tudo, quero voltar atrás!" — Guia por situação

Aqui está o coração deste documento. Existem **4 situações diferentes**, dependendo de quanto você já avançou. Identifique a sua situação abaixo antes de rodar qualquer comando.

```
Você alterou um arquivo
        │
        ▼
Situação A: Ainda não rodou "git add" nem "git commit"
        │  (a mudança está "solta", nenhuma foto foi tirada)
        ▼
Situação B: Rodou "git add" mas ainda não "git commit"
        │
        ▼
Situação C: Já rodou "git commit" (a foto foi tirada), mas ainda não "git push"
        │
        ▼
Situação D: Já rodou "git commit" E "git push" (a foto já está no GitHub também)
```

### Situação A — Alterei um arquivo, não gostei, quero descartar (ainda não fiz `add` nem `commit`)

Isso é o caso mais simples: **desfazer a edição e voltar exatamente ao último commit salvo.**

```powershell
git status
```
Confira o nome do arquivo alterado (vai aparecer em vermelho, algo como `modified: app.py`).

```powershell
git restore app.py
```

Isso apaga a alteração e o arquivo volta a ficar idêntico ao do último commit. **Atenção: isso é definitivo, não tem como recuperar a versão "ruim" depois.**

Se você alterou **vários arquivos** e quer descartar tudo:
```powershell
git restore .
```

### Situação B — Já rodei `git add`, mas não `git commit`

Primeiro "desmarque" o arquivo, depois descarte a alteração:
```powershell
git restore --staged app.py
git restore app.py
```

### Situação C — Já fiz o `git commit`, mas ainda **não** fiz `git push` (a foto ruim ainda não foi para o GitHub)

Aqui você já tem uma "foto ruim" no histórico local. Duas opções:

**Opção 1 — Desfazer o último commit, mas manter as alterações nos arquivos** (útil se você quer corrigir algo e tentar de novo):
```powershell
git reset --soft HEAD~1
```
Isso "desfaz a foto" mas mantém tudo escrito nos arquivos, como se você tivesse acabado de editar (ainda não commitado).

**Opção 2 — Desfazer o último commit E jogar fora as alterações também** (apaga tudo, volta ao estado de antes de mexer):
```powershell
git reset --hard HEAD~1
```
⚠️ **Cuidado**: este comando apaga as mudanças de verdade, sem possibilidade fácil de recuperação. Só use se tiver certeza que quer jogar fora aquela mudança específica.

`HEAD~1` significa "um commit antes do atual". Se quiser voltar 2 commits, use `HEAD~2`, e assim por diante.

### Situação D — Já fiz `git commit` **e** `git push` (a foto ruim já está no GitHub também)

Esta é a situação mais comum quando você percebe o problema um tempo depois (ex: "a busca semântica parou de funcionar e eu já mandei pro GitHub ontem").

Aqui existem duas estratégias bem diferentes — **use a primeira, quase sempre**:

#### Opção 1 (recomendada e segura): `git revert` — cria uma foto nova que desfaz a anterior

Isso **não apaga** nada do histórico. Em vez disso, cria um commit novo que "cancela" as alterações do commit ruim, mantendo a linha do tempo completa e honesta (você consegue ver depois "isso foi feito, e depois foi desfeito").

Passo a passo:

1. Veja o histórico de commits para achar o "código" (hash) do commit problemático:
   ```powershell
   git log --oneline -15
   ```
   Isso mostra algo assim:
   ```
   8520357 Fix: Solução definitiva para navegação Anterior/Próximo e desync com sidebar
   9e999c9 Fix: Adicionar st.rerun() em botoes de navegacao para sincronizar sidebar
   e7ba9df UX: Remover paginacao duplicada e Filtros Rapidos da busca
   ```
   O código de 7 letras/números no início (ex: `8520357`) identifica aquele commit.

2. Reverta o commit problemático (troque `8520357` pelo código do commit que você quer desfazer):
   ```powershell
   git revert 8520357
   ```
   Uma janela de texto pode abrir pedindo a mensagem do commit de reversão — pode simplesmente salvar e fechar (já vem preenchida automaticamente).

3. Mande essa correção para o GitHub:
   ```powershell
   git push
   ```

Pronto — o efeito daquele commit ruim foi anulado, e o histórico continua íntegro e rastreável.

#### Opção 2 (arriscada, evite se possível): `git reset --hard` + envio forçado

Isso **reescreve o histórico**, como se o commit ruim nunca tivesse existido. Só considere isso se:
- Tem certeza absoluta que ninguém mais depende daquele histórico (nem você, em outro computador)
- Entende que é uma operação destrutiva

```powershell
git reset --hard 9e999c9
git push --force
```
(troque `9e999c9` pelo código do último commit **bom**, antes do problema)

⚠️ **Eu (Claude) não vou executar `git push --force` sem confirmar explicitamente com você antes**, porque pode sobrescrever histórico no GitHub de forma irreversível. Prefira sempre a Opção 1 (`git revert`).

---

## 5. Como saber qual versão era a "boa"?

### Ver a lista de commits (o histórico)
```powershell
git log --oneline -20
```
Mostra os últimos 20 commits, do mais recente para o mais antigo.

### Ver exatamente o que um commit específico mudou
```powershell
git show 8520357
```
(troque pelo código do commit que quer inspecionar)

### Comparar o estado atual com uma versão antiga, sem mudar nada ainda
```powershell
git diff 9e999c9 HEAD
```
Isso é só para **olhar**, sem alterar nada — útil pra confirmar "foi essa mudança mesmo que quebrou algo?" antes de reverter.

### Testar temporariamente uma versão antiga, sem se comprometer

Se quiser só **olhar/testar** como o programa era numa versão antiga, sem perder o trabalho atual:
```powershell
git stash
git checkout 9e999c9
```
Depois de testar e quiser voltar ao normal:
```powershell
git checkout master
git stash pop
```
(`git stash` "guarda numa gaveta" qualquer alteração não commitada, para não se perder durante o teste)

---

## 6. Rede de segurança extra: crie um "ponto de restauração" antes de mudanças arriscadas

Antes de pedir uma alteração grande ou arriscada, é uma boa prática marcar o estado atual com uma **tag** (uma etiqueta fixa num commit, fácil de achar depois):

```powershell
git tag versao-estavel-2026-08-22
git push origin versao-estavel-2026-08-22
```

Se algo der muito errado depois, dá pra voltar direto para essa etiqueta:
```powershell
git checkout versao-estavel-2026-08-22
```

---

## 7. Erros comuns e cuidados

- **`git add -A` ou `git add .`** adiciona *todos* os arquivos alterados de uma vez, inclusive arquivos que talvez você não quisesse (ex: arquivos temporários, dados sensíveis). Prefira adicionar arquivo por arquivo (`git add app.py`) quando não tiver certeza do que mudou. Rode `git status` antes para conferir.
- **`git reset --hard`** e **`git push --force`** são os únicos comandos deste guia que **apagam informação de verdade, sem chance fácil de recuperação**. Todo o resto (`git revert`, `git restore` antes de commit, `git reset --soft`) é seguro ou reversível.
- **Nunca rode um comando de "resetar" ou "forçar" sem antes rodar `git status` e `git log`** para confirmar exatamente onde você está e para onde vai voltar.
- Se tiver qualquer dúvida sobre qual comando usar numa situação real, é mais seguro **parar e perguntar** (a mim ou em uma busca) do que arriscar um comando destrutivo.

---

## 8. Resumo rápido (cola de emergência)

| Eu quero... | Comando |
|---|---|
| Ver o que mudou desde o último commit | `git status` |
| Ver o histórico de commits | `git log --oneline -20` |
| Descartar uma edição que ainda não virou commit | `git restore <arquivo>` |
| Salvar uma alteração como "foto" | `git add <arquivo>` seguido de `git commit -m "mensagem"` |
| Mandar para o GitHub | `git push` |
| Desfazer o último commit (mantendo as edições) | `git reset --soft HEAD~1` |
| Desfazer o último commit (jogando tudo fora) | `git reset --hard HEAD~1` |
| Desfazer um commit que **já foi** pro GitHub, com segurança | `git revert <código-do-commit>` seguido de `git push` |
| Ver o que um commit específico mudou | `git show <código-do-commit>` |
| Criar um ponto de restauração nomeado | `git tag <nome>` seguido de `git push origin <nome>` |

---

## 9. Seu projeto especificamente

- Repositório remoto (GitHub): `https://github.com/walderezsimoescostaramalho-ship-it/historicidades-democraticas`
- Branch única em uso: `master` (não há outras linhas paralelas de desenvolvimento)
- Sempre que eu (Claude) fizer uma alteração significativa a seu pedido, o ideal é: você testar o app, e só then me pedir para fazer o commit — assim cada "foto" no histórico corresponde a uma versão que você já viu funcionando (ou já sabe o que está testando).
