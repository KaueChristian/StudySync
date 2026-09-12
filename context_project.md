# StudySync — Contexto do Projeto

> **Este é o documento de referência único do projeto.** Qualquer agente de IA (Claude, ou
> outro) e qualquer pessoa que assuma trabalho neste repositório deve ler este arquivo antes
> de tocar em qualquer código. Ele descreve o que o StudySync **deveria ser**, o que ele **é
> hoje** (com evidência de teste real, não suposição), e o que falta para fechar essa
> distância.
>
> **Regra de manutenção — não opcional:** toda sessão de trabalho relevante (uma correção,
> uma feature, uma decisão de design/arquitetura) precisa atualizar a seção correspondente
> deste arquivo **antes de a sessão terminar**. Um doc de contexto desatualizado é pior que
> nenhum doc — ele engana em vez de orientar o próximo agente ou o próprio autor. Ver
> [VALIDATION_PROTOCOL.md](VALIDATION_PROTOCOL.md) para como validar antes de marcar algo
> como concluído aqui.

---

## 1. O que o StudySync deve ser

**Contexto:** projeto pessoal/portfólio de Kaue Christian. Desenvolvimento acontece com mais
de uma ferramenta de IA em sessões distintas — é por isso que este arquivo existe: para que
nenhuma delas trabalhe com uma versão desatualizada ou incompleta da realidade do projeto.

**Ideia original (definição do autor):** um agendador de matérias de estudo. O usuário
cadastra uma matéria de interesse, marca o dia e a hora em que quer estudar aquele assunto, e
é notificado quando o horário se aproxima. Ligada a cada matéria/sessão salva, existe uma
opção de busca que devolve de 3 a 5 links sobre o conteúdo — pensada para quem não sabe por
onde começar a estudar um assunto e precisa de um ponto de partida.

**Verificado em 2026-09-01:** essa ideia original já estava **100% implementada e funcional**
antes de qualquer trabalho de correção ou redesign começar — confirmado rodando a aplicação
ao vivo (login, agenda, busca de conteúdo retornando 5 links reais, lembrete disparando pelo
WebSocket). O trabalho desta fase do projeto não foi "completar o MVP", foi: (a) corrigir um
bug real na busca de conteúdo, (b) blindar essa busca contra bloqueio dos provedores, e (c)
dar ao produto uma identidade visual própria em vez do template genérico de dashboard SaaS
que ele tinha.

**Público-alvo:** estudantes organizando a própria rotina de estudo — não é uma ferramenta de
gestão de equipe nem um produto B2B; a UX deve favorecer clareza e baixa fricção para uso
solo, diário.

**Decisões de arquitetura já tomadas (âncoras, não para reabrir sem motivo forte):**
- **Execução local-first:** backend FastAPI + SQLite + Alembic, sem dependência de serviço
  pago de terceiros para nenhuma funcionalidade principal (nem para autenticação, nem para a
  busca de conteúdo, que usa scraping de buscadores públicos em vez de uma API paga).
- **Frontend:** React 19 + Vite 7 + Tailwind CSS v4 (tokens de tema centralizados em
  `frontend/src/index.css`, não Tailwind default nem um design system de terceiros).
- **Identidade visual "Caderno / Editorial"** (decidida em 2026-09-01, ver §7): tema claro
  quente (papel/creme), serifada nos títulos, verde-tinta como cor de destaque, e uma
  linguagem de cantos **retos** (não a bolha arredondada padrão de templates SaaS) — ver
  decisão de 2026-09-01 sobre os botões em §7, que é a correção mais recente dessa
  identidade.

---

## 2. Diferenciais frente a "mais um agendador/calendário"

Um agendador com lembrete, sozinho, não é diferencial — existem dezenas. O que este projeto
tem que um Google Calendar/Todoist genérico não tem pronto:

| # | Diferencial | Por que uma ferramenta genérica não faz isso de graça |
|---|---|---|
| 1 | **Busca de conteúdo de apoio integrada à sessão/matéria**, sem custo de API — cascata de provedores (DuckDuckGo → Bing → Wikipédia) com ranking por relevância **e confiabilidade da fonte** (bônus para `.edu`/`.gov`/portais educacionais, penalidade para redes sociais/e-commerce) | Um calendário genérico não sabe o que você vai estudar, só quando. Aqui a busca nasce do tópico da própria sessão |
| 2 | **Lembrete resiliente por varredura indexada**, não um job por agendamento — sobrevive a reinício do servidor dentro de uma janela de tolerância, sem precisar reconstruir jobs | A alternativa óbvia (um job por sessão) exige sincronizar o agendador a cada criação/edição/exclusão — mais um ponto de falha |
| 3 | **Sessões recorrentes materializadas como linhas reais**, agrupadas por `recurrence_group_id`, não calculadas em tempo de leitura por uma regra RRULE | Cada instância tem seu próprio status, lembrete e links de apoio — uma série recorrente não é um evento fantasma repetido, é N sessões reais que podem divergir entre si depois de criadas |
| 4 | **Timer de foco (Pomodoro) ligado à sessão de estudo**, com um botão de "marcar como concluída" ao final do ciclo | Um app de Pomodoro isolado não sabe que sessão de estudo você está cumprindo; aqui o ciclo de foco fecha o loop com o agendamento |
| 5 | **Interoperabilidade de calendário** — download `.ics` autenticado e URL de assinatura por token para Google/Apple Calendar | Os dados de estudo não ficam presos dentro do app |
| 6 | **Identidade visual própria e deliberada** ("Caderno/Editorial": papel, serifa, cantos retos) em vez do template indigo/dark de dashboard SaaS que qualquer scaffold gera | Diferencia o projeto num portfólio — "mais um CRUD com Tailwind" não sobrevive à primeira olhada; um sistema de design com ponto de vista, sim |

---

## 3. Estado atual — por item, com evidência

**Legenda de status:** ✅ Concluído e validado ao vivo · 🟡 Parcial/mitigado · ❌ Não
implementado · 🚫 Bug confirmado (corrigido ou não)

### Núcleo funcional (✅ construído antes desta fase de trabalho; revalidado ao vivo em 2026-09-01)

| Item | Status | Evidência |
|---|---|---|
| Auth (registro/login/JWT + refresh rotativo, conta demo) | ✅ | Login com a conta demo (`demo@studysync.dev`) testado ao vivo no navegador; dashboard carregou com dados reais da seed |
| Matérias (CRUD, cor/ícone) | ✅ | Página `/materias` testada ao vivo: 4 matérias da seed renderizadas com contadores de anotações/sessões corretos |
| Anotações (Markdown, tags, categorias) | ✅ | Página `/anotacoes` testada ao vivo: 4 anotações da seed renderizadas com tags e preview de conteúdo |
| Agenda + lembretes (WebSocket + notificação nativa) | ✅ | Calendário mensal testado ao vivo; sino de notificação mostrou "1 não lida" durante o teste — o lembrete da seed disparou de fato pelo APScheduler + WebSocket |
| **Busca de conteúdo (3–5 links por tema)** | ✅ | Em 2026-09-01 funcionou de ponta a ponta. A regressão do cabeçalho `Accept-Encoding: br` (Defeito 1) foi corrigida em 2026-09-12: cabeçalho ajustado para `gzip, deflate` em `_browser_headers()` de `scraper.py`. Revalidado ao vivo contra os provedores reais: Bing devolveu 10 resultados brutos com URLs desembrulhadas, DuckDuckGo devolveu 10 resultados brutos e `search_content` entregou 5 resultados ranqueados de domínios educacionais confiáveis (todamateria.com.br, brasilescola.uol.com.br, pt.wikipedia.org, significados.com.br), com fallback resiliente para Bing e Wikipédia sob bloqueio simulado. |
| Dashboard, Biblioteca, Configurações | ✅ | Todas testadas ao vivo, sem erro de console |

### Features adicionadas nesta fase (2026-08-31, README atualizado no mesmo dia)

| Item | Status | Evidência |
|---|---|---|
| Sessões recorrentes semanais | ✅ | `ScheduleModal.jsx`: toggle "Repetir semanalmente" + campo "até"; backend materializa uma linha por semana com `recurrence_group_id` compartilhado (`schedules.py`, migração `0002`). Exclusão aceita `scope=this\|following\|all` via `RecurrenceScopeDialog.jsx` |
| Timer de foco (Pomodoro) | 🟡 | `FocusTimer.jsx`: presets 25/5, 50/10, 15/5, beep via WebAudio (sem arquivo de áudio), notificação nativa, botão de concluir a sessão ao final — tudo funcionando com a janela em primeiro plano (testado ao vivo). **Correção de 2026-09-12:** a afirmação anterior de que "sobrevive a aba em segundo plano" estava errada. O valor exibido de fato é recalculado a partir de um timestamp-alvo, mas o laço é `requestAnimationFrame`, que **não roda** quando a janela não está sendo desenhada — e o fim do ciclo (beep + notificação) só acontece dentro do tick. Ver defeito 7 da bateria de 2026-09-12 |
| Exportação/assinatura de agenda (.ics) | ✅ | `services/ics.py` gera iCalendar (RFC 5545) manualmente, sem dependência nova. Três rotas: `GET /schedules/export` (autenticado, download), `POST /schedules/export-token` (gera `users.ics_token`), `GET /schedules/export.ics?token=` (pública, para assinatura no Google/Apple Calendar) |

### Redesign visual "Caderno / Editorial" (2026-09-01)

| Item | Status | Evidência |
|---|---|---|
| Paleta/tipografia (papel quente, serifa `Fraunces` nos títulos, verde-tinta `--color-brand-*`) | ✅ | `index.css` reescrito; validado visualmente em várias telas (login, dashboard, matérias, agenda) em modo claro e escuro |
| **Correção da linguagem de forma (2026-09-01, feedback direto do autor)** | ✅ | O autor apontou que os botões arredondados quebravam a estética de "caderno". Causa: todo o app usa as classes padrão do Tailwind (`rounded-lg`/`xl`/`2xl`) — corrigido **no nível do token**, redefinindo `--radius-*` inteiro em `@theme` (de 8–16px para 1–6px), o que se propagou sozinho para botões, inputs, modais e calendário sem editar cada componente. Badges/chips em pílula (`rounded-full`) trocados manualmente para o mesmo raio retangular, já que não são cobertos pela escala numérica do Tailwind. Validado visualmente: dashboard, matérias, agenda (calendário com células quadradas), modal de nova sessão |

### Motor de busca — bug encontrado e corrigido (2026-09-01, relatado pelo autor após uso real)

| Item | Status | Evidência |
|---|---|---|
| 🚫→✅ **Bug do Bing:** todo link orgânico vinha embrulhado em redirecionador de clique (`bing.com/ck/a?...&u=<base64>`), nunca desembrulhado. Efeito: todo resultado "virava" o domínio `bing.com`, disparando a regra de máximo 2 links por domínio — a busca sempre devolvia exatamente 2 links, e eram links de rastreamento que não abrem direito fora de uma sessão do Bing | ✅ Corrigido | Reproduzido chamando os provedores diretamente: Bing devolveu 10 resultados brutos, todos com `url` começando em `https://www.bing.com/ck/a?...`. `clean_bing_redirect()` decodifica o parâmetro `u=` (base64, prefixo `a1`) e recupera a URL real. Testado após a correção: 5 resultados, 5 domínios distintos reais (dicio.com.br, todadisciplina.com.br, dicionariojuridico.com, escreva.ai, partes.com.br) |
| 🚫→✅ **Por que só vinha Bing:** o DuckDuckGo (HTML e Lite), quando desconfia de tráfego automatizado, devolve **HTTP 202** com uma página de "verificação" vazia em vez de um erro — isso não disparava `raise_for_status()`, então o provedor parecia "sem resultados" em vez de "bloqueado", e a cascata caía sempre no Bing | ✅ Corrigido | `_raise_if_blocked()` detecta o 202 explicitamente e levanta `BlockedByProviderError`, alimentando o disjuntor de circuito (abaixo) em vez de falhar silenciosamente |
| ✅ Anti-bloqueio: User-Agent rotativo (5 navegadores/SOs), cabeçalhos `Sec-Fetch-*`/`Accept-Encoding` coerentes, `Referer` correspondendo ao site de destino | ✅ | `_browser_headers()` em `scraper.py` |
| ✅ Disjuntor de circuito por provedor (`ProviderHealth`) — após 2 falhas seguidas, cooldown de 10 min, sem insistir num provedor já bloqueado | ✅ | Reproduzido ao vivo: bateria de testes derrubou DuckDuckGo **e** Bing simultaneamente (bloqueio real, não simulado); o disjuntor pulou ambos e a cascata caiu para a Wikipédia com resultados reais — prova prática de que a resiliência funciona sob a mesma condição relatada pelo autor |
| 🚫→✅ **Bug lateral encontrado durante a correção:** a Wikipédia (rede de segurança final) tomava `403 Forbidden` porque os mesmos cabeçalhos de "navegador" (`Sec-Fetch-Dest: document`) estavam sendo aplicados numa chamada de API JSON — sinal inconsistente que pesa contra o pedido, já que a própria Wikimedia recomenda um User-Agent honesto para chamadas de API, não simulação de navegador | ✅ Corrigido | `_wikipedia_headers()` separado, com User-Agent descritivo (`StudySync/1.0 (...)`). Testado: 200 OK, resultados reais |

**Nota de estado (atualizada em 2026-09-12):** as correções acima continuam válidas e a
regressão do cabeçalho `Accept-Encoding: br` (Defeito 1) foi corrigida (`scraper.py` agora envia
apenas `gzip, deflate`). Revalidado ao vivo com sucesso contra os três provedores reais e cascata
de fallback completa (DDG → Bing → Wikipédia), confirmando URLs desembrulhadas e ranking de
fontes educacionais confiáveis. O item 1 do roadmap está liberado e concluído.

### Infraestrutura de repositório (2026-09-01)

| Item | Status | Evidência |
|---|---|---|
| 🚫→✅ **`git init` acidental na pasta `port/`** (pasta geral do portfólio, continha StudySync e outros projetos irmãos como pastas dentro do mesmo repositório) | ✅ Corrigido | Detectado via `git rev-parse --show-toplevel` apontando para `port/`, não para `StudySync/`. Confirmado com o autor que isso era "comportamento errado". Corrigido: `port/.git` removido inteiramente (nenhum outro projeto tinha commit ali — verificado com `git log --all`, `git branch -a`, `git stash list` antes de apagar); `StudySync/` inicializado como repositório próprio, independente, com um único commit inicial limpo |
| Publicado no GitHub | ✅ | `origin` → `https://github.com/KaueChristian/StudySync.git`, branch `main` publicada e rastreando `origin/main`. Commit `34bf4f7` |

### Bateria de validação massiva (2026-09-12) — o que passou e o que quebrou

Sessão dedicada só a testar (nenhuma linha de código de produção alterada). Execução real:
backend isolado em porta e banco descartáveis (387 verificações automatizadas), provedores de
busca chamados contra a internet real, e o app completo aberto no navegador com a conta demo.
Detalhe do método e dos números em §8.

**O que foi confirmado funcionando** (não repetir esse trabalho sem motivo):

| Área | Evidência |
|---|---|
| Isolamento entre usuários (IDOR) | 12 tentativas de ler/editar/excluir recurso de outro usuário (matéria, anotação, sessão, link, tag, `/notes/{id}/links`) → **404 em todas**, nunca 403 (não vaza existência de id) |
| JWT | `alg=none`, assinatura adulterada, token sem `exp`, refresh usado como access, header sem `Bearer` → todos rejeitados com 401 |
| Rotação de refresh | Reuso de token rotacionado derruba **todas** as sessões do usuário (detecção de vazamento), confirmado ao vivo |
| XSS (2 camadas) | `<script>`, `<img onerror>`, `<svg onload>`, `javascript:`, `data:text/html` — neutralizados no backend (`bleach`) **e** no render (`react-markdown` sem `rehype-raw`): no preview real, `javascript:`/`data:` viram `href=""` e as tags viram texto |
| Lembrete ponta a ponta | Sessão criada pela UI → lembrete disparou em 20 s pela varredura, chegou pelo WebSocket, apareceu no sino, persistiu no banco, **não** repetiu no ciclo seguinte, e chegou simultaneamente em 2 abas |
| Janela de tolerância | Lembrete atrasado 30 min (dentro dos 120) dispara; atrasado 200 min é descartado — testado inserindo as linhas direto no banco (cenário "servidor esteve fora do ar") |
| Recorrência | 5 instâncias exatas de 7 em 7 dias, mesmo horário; teto de 52 respeitado; `scope=this/following/all` excluem 1 / 3 / a série inteira; diálogo de escopo funciona na UI |
| Fuso horário | `05:07 -03:00` digitado na UI → `08:07Z` no banco → `05:07` de volta na tela |
| Concorrência (SQLite/WAL) | 20 criações simultâneas + leituras concorrentes: 0 erro de `database is locked` |
| Rate limit | Login trava na 11ª tentativa (limite 10/60 s) e libera após a janela; busca trava na 21ª (20/60 s), com `Retry-After` |
| Renovação de token no frontend | Dois 401 simultâneos dispararam **um único** `POST /auth/refresh` (a fila de `api.js` funciona — se disparasse dois, a detecção de reuso derrubaria a sessão do usuário) |
| Exportação `.ics` | Arquivo válido com dados reais: CRLF coerente, nenhuma linha acima de 75 octetos, acentos e emoji preservados; token de assinatura estável entre chamadas; token inválido → 404 |

**Defeitos encontrados** (nenhum corrigido nesta sessão — decisão do autor sobre o que atacar
primeiro):

| # | Gravidade | Defeito | Evidência |
|---|---|---|---|
| 1 | 🚫→✅ **Corrigido** | **A blindagem anti-bloqueio quebrou a busca que ela deveria proteger.** `_browser_headers()` anunciava `Accept-Encoding: gzip, deflate, br` (`scraper.py:78`), mas o `httpx` deste venv não tem decodificador brotli (`SUPPORTED_DECODERS` = gzip/deflate/identity). Quando o buscador respondia em brotli, o httpx devolvia bytes crus sem levantar exceção → o BeautifulSoup não encontrava resultados → o disjuntor colocava o provedor em cooldown de 10 min. Corrigido em 2026-09-12 removendo o `br` indevido do cabeçalho em `scraper.py:80`. | Revalidado ao vivo contra a internet real: Bing retornou 10 resultados brutos (`li.b_algo`), DuckDuckGo retornou 10 (`div.result`), e `search_content` entregou 5 links ranqueados de fontes educacionais reais (todamateria, brasilescola, uol, wikipedia), com fallback resiliente funcional. |
| 2 | 🚫 **Alto** | **A rede de segurança nunca entrega os 3–5 links prometidos.** Todo resultado da Wikipédia é do mesmo domínio, e `dedupe_and_rank` corta em 2 links por domínio (`scraper.py:634`) — então, sempre que a cascata cai na Wikipédia, o usuário recebe **no máximo 2 links**. É o mesmo sintoma "só vêm 2 links" que o autor relatou antes, por um caminho diferente do bug do Bing | Reproduzido no app real (backend de dev, conta demo): busca "revolução industrial causas e consequências" → **"2 resultados · via wikipedia"**, sendo o 2º "Revolução Gloriosa" (irrelevante). Log do servidor na mesma requisição: `duckduckgo` 202, `duckduckgo-lite` sem resultados úteis, `bing` sem resultados úteis, `wikipedia` 2 resultados |
| 3 | 🟡 Médio | `normalize_url()` remonta a query string a partir do `parse_qs` **sem re-codificar** (`scraper.py:396`): `?q=a%20b%20c` vira `?q=a b c`, com espaço cru dentro da URL salva/aberta | `normalize_url("https://a.com/p?q=a+b%20c&x=1")` → `https://a.com/p?q=a b c&x=1` |
| 4 | 🟡 Médio | **Sessão pendente que já passou desaparece do painel.** O card rotulado "Sessões pendentes" (`DashboardPage.jsx:200`) exibe `sessions_upcoming`, que só conta `start_at >= agora` (`dashboard.py`). Não existe nenhum contador de "atrasada" — e o docstring de `scheduler.py:9` ainda promete um job `mark_overdue_sessions` **que não existe no arquivo** | Conta demo: 3 sessões pendentes de agosto, painel mostrando "Sessões pendentes 0". No teste automatizado: 31 pendentes reais x `sessions_upcoming=30` |
| 5 | 🟡 Médio | **"Resumo do mês" não é do mês.** O painel soma o array inteiro carregado (`SchedulePage.jsx:236-238`), que vai do mês anterior ao mês seguinte (`SchedulePage.jsx:47-48`) | Setembro/2026 tinha **1** sessão e o painel exibia "Total 6 · Pendentes 4 · Concluídas 2" (números de agosto) |
| 6 | 🟡 Médio | **O link de assinatura da agenda é relativo e não serve para o que foi feito.** `SettingsPage.jsx:145` monta a URL com `apiUrl()`, que devolve caminho relativo quando `VITE_API_URL` está vazio (a configuração recomendada, via proxy do Vite) | Botão "Gerar link de assinatura" produziu `/api/schedules/export.ics?token=…`. Colado no Google/Apple Calendar, como a própria instrução ao lado manda fazer, não funciona |
| 7 | 🟡 Médio | **O Pomodoro congela quando a janela não está sendo desenhada.** `FocusTimer.jsx` usa só `requestAnimationFrame` (linhas 113-145) — e o `advancePhase()` (beep + notificação de fim de ciclo) só roda dentro do tick. Com a janela atrás de outra / minimizada, o rAF simplesmente não roda: **o aviso de "hora da pausa" nunca chega** até o usuário voltar. O comentário no topo do arquivo afirma justamente o contrário | Medido na própria página: `requestAnimationFrame` → **0 callbacks em 3 s**, `setInterval` → 30, relógio parado em `50:00` (com `document.visibilityState === "visible"`). Efeito colateral: `setRemaining` a 60 fps re-renderiza o modal inteiro a cada quadro |
| 8 | 🟡 Médio | Disjuntor com `threshold=2` e `cooldown=600s`: com DDG e Bing já em cooldown, **duas** falhas da Wikipédia deixam a busca 10 minutos inteiramente fora do ar (503) | Reproduzido na bateria: consulta seguinte devolveu `SearchEngineError` com os 4 provedores pulados |
| 9 | 🔵 Baixo | `_escape()` do ICS (`ics.py:19-26`) não escapa `\r`: descrição com CRLF vaza um CR cru para dentro da linha do arquivo (inválido pelo RFC 5545) | `build_ics` com `description="linha1\r\nlinha2"` → `'DESCRIPTION:linha1\r\\nlinha2'` |
| 10 | 🔵 Baixo | `tokenize()` descarta termos de até 2 caracteres (`scraper.py:326`): "pH", "IA", "3D" somem do cálculo de relevância | `tokenize("escala de ph")` → `{'escala'}` |
| 11 | 🔵 Baixo | O teto de 2 links por domínio é aplicado **antes** da pontuação: ficam os 2 primeiros do provedor, não os 2 melhores | Caso sintético: a página mais aderente ao tema foi descartada por ter chegado em 3º no mesmo domínio |
| 12 | 🔵 Baixo | Excluir matéria apaga em cascata anotações e sessões (bem avisado no diálogo da UI ✅), mas **deixa tags órfãs** — a limpeza (`cleanup_orphan_tags`) só roda no caminho de edição/exclusão de anotação | Após excluir a matéria, `GET /tags` ainda listava a tag com `notes_count: 0` |
| 13 | 🔵 Baixo | `notifications.schedule_id` não tem chave estrangeira: excluir a sessão deixa a notificação apontando para um id inexistente, e clicar nela (`/agenda?sessao=…`) não faz nada nem avisa (`SchedulePage.jsx:67-84`) | Verificado no banco após excluir a sessão de teste |
| 14 | 🔵 Baixo | `npm run lint` está quebrado: o script chama `eslint .`, mas o eslint não está em `devDependencies` e não há arquivo de configuração | `node_modules/.bin` sem eslint; nenhum `eslint.config.*` |
| 15 | 🔵 Baixo | Rótulos relativos não se atualizam sozinhos (`ScheduleCard.jsx:127`): o card continuou exibindo "começa em 42 segundos" depois de a sessão já ter começado | Observado na UI durante o teste do lembrete |
| 16 | 🔵 Baixo | `truncate()` (`format.js`) usa `lastIndexOf(' ', max) || max` → `-1` quando não há espaço, e `slice(0, -1)` devolve o texto quase inteiro em vez de truncar. Hoje é **código morto** (nenhum componente usa) | `truncate("a".repeat(200), 20)` → 200 caracteres |
| 17 | 🔵 Baixo | Plurais fixos: `aria-label` do calendário diz "1 sessões"; a confirmação de exclusão diz "Todas as 1 anotações" | Lido direto da árvore de acessibilidade e do diálogo |

**Registrado, mas provavelmente aceitável por ora:** o rate limit de login é por IP+rota, então
10 tentativas erradas bloqueiam também o login legítimo daquele IP por 60 s; e
`verify_password` trunca em 72 bytes (inalcançável hoje, porque o cadastro rejeita senha maior
que isso).

---

## 4. Arquitetura real

```
backend/
  alembic/versions/
    0001_esquema_inicial.py       — schema base
    0002_recorrencia_e_ics.py     — + schedules.recurrence_group_id, users.ics_token
  app/
    api/routes/
      auth.py, subjects.py, notes.py, tags.py, dashboard.py, notifications.py, ws.py
      schedules.py                — CRUD + /export, /export-token, /export.ics, /{id}?scope=
      search.py                   — busca de conteúdo + salvar/listar/remover links
    core/                         — config, security (JWT/bcrypt), deps, rate_limit, sanitize
    db/                           — engine, sessão, base declarativa (TimestampTZ/ensure_utc)
    models/                       — User (+ics_token), Subject, Note, Tag, Schedule
                                    (+recurrence_group_id), SearchResult, Notification, RefreshToken
    schemas/                      — contratos Pydantic de entrada/saída
    services/
      scraper.py                 — motor de busca (cascata + ranking + disjuntor de circuito)
      scheduler.py                — APScheduler: varredura de lembretes, purga de tokens
      notifier.py                 — gerenciador de conexões WebSocket
      ics.py                      — gerador manual de iCalendar (RFC 5545)
      tags.py
    seed.py                       — dados de demonstração (conta demo@studysync.dev)
  requirements.txt
  run.py

frontend/
  src/
    components/
      auth/       — AuthShell (moldura de login/cadastro), RouteGuards
      layout/      — AppLayout, Sidebar, NotificationBell
      notes/       — NoteEditorModal, Markdown, TagInput
      schedule/    — CalendarMonth, ScheduleCard, ScheduleModal, FocusTimer,
                     RecurrenceScopeDialog
      search/      — ContentSearchPanel (reutilizado em notas, sessões e na página de busca)
      subjects/    — SubjectModal
      ui/          — Button, Field, Modal, ConfirmDialog, Misc (Badge/EmptyState/Toggle/...),
                     SubjectIcon
    context/       — Auth, Theme, Toast, Notification (WebSocket + notificação nativa)
    lib/           — api.js (axios + refresh automático), services.js, format.js, constants.js
    pages/         — Dashboard, Subjects, Notes, Schedule, Search, Library, Settings, Login,
                     Register, NotFound
    index.css      — TODOS os tokens de tema: cores (`--color-brand-*`), raio (`--radius-*`),
                     tipografia (`--font-sans`/`--font-display`), superfícies (`.card`)
  vite.config.js   — proxy `/api` → `http://127.0.0.1:8000` em dev

.claude/launch.json — configs de preview: "backend" (venv/Scripts/python.exe run.py
                      --no-reload, porta 8000) e "frontend" (npm run dev, porta 5173)
```

**Princípio de theming a preservar:** quase toda cor/raio de borda do app vem de tokens
centralizados em `index.css` (`@theme { --color-brand-*; --radius-* }`), não de valores fixos
espalhados pelos componentes — foi isso que tornou o redesign de 2026-09-01 (paleta inteira +
correção do raio de borda) uma mudança de poucas linhas em um arquivo, em vez de uma edição
manual em dezenas de componentes. **Qualquer novo componente deve seguir esse padrão** — usar
`var(--surface)`, `text-muted`/`text-subtle`, `bg-brand-*`, `rounded-lg`/`xl` em vez de cor ou
raio fixo, para que futuras mudanças de identidade visual continuem sendo de baixo custo.

---

## 5. Roadmap ativo — próximos passos

| # | Item | Depende de | Status | Nota |
|---|---|---|---|---|
| 0 | **Corrigir o `Accept-Encoding: br` antes de qualquer outra coisa** (`scraper.py:78`) | Nada | ✅ Concluído | Removido `br` do cabeçalho em `scraper.py:80`. Revalidado ao vivo contra Bing (10/10 com URLs limpas), DDG (10/10) e pipeline completo (5 links ranqueados). |
| 1 | Commitar a correção do `scraper.py` (bug do Bing + anti-bloqueio) | Item 0 | ✅ Concluído | Validado de acordo com o `VALIDATION_PROTOCOL.md` §3.3 e commitado. |
| 2 | Logo e imagens próprias por seção/opção do menu | Nada | ❌ Adiado pelo autor | O autor pediu explicitamente para não avançar nisso ainda ("preciso refinar mais algumas coisas") — não iniciar sem sinal verde |
| 3 | Empacotamento desktop (dados 100% locais, sem depender de hospedagem) | Redesign visual (✅) | ❌ Discutido, não implementado | Duas rotas avaliadas com o autor: **(a)** PyInstaller (backend inteiro + frontend buildado servido pelo FastAPI) + `pywebview` (janela nativa via WebView2, sem Chromium embutido) — caminho mais simples, recomendado; **(b)** Tauri com o mesmo `.exe` do PyInstaller como sidecar — instalador mais "profissional", mais setup (toolchain Rust). Eletron foi descartado — exigiria ou reescrever o backend em Node ou rodar o mesmo sidecar Python com ~150MB+ de Chromium embutido, sem ganho real sobre as outras duas opções |
| 4 | Suíte de testes automatizados (backend e frontend) | Nada | ❌ Não existe | Ver débito técnico em §6 — toda validação até agora foi manual/ao vivo, não há rede de segurança automatizada |

---

## 6. Débitos técnicos conhecidos

- **Nenhuma suíte de testes automatizados.** Não há `pytest` no backend nem testes de
  componente/e2e no frontend. Toda a validação registrada neste documento veio de execução
  manual ao vivo (navegador real, chamadas diretas aos provedores de busca). Isso é aceitável
  para o estágio atual, mas significa que **qualquer regressão só será pega manualmente** —
  relevante sobretudo para `scraper.py` (dedupe/ranking) e para o cálculo de recorrência de
  sessões, que têm lógica não trivial o suficiente para valer um teste unitário.
- **O motor de busca depende inerentemente de scraping de buscadores públicos.** Mesmo com o
  disjuntor de circuito e os cabeçalhos mais realistas (§3), DuckDuckGo/Bing podem mudar o
  HTML a qualquer momento e quebrar os seletores CSS (`div.result`, `li.b_algo` etc.) sem
  aviso — é uma fragilidade estrutural da abordagem "sem custo de API", não um bug pontual.
  A Wikipédia como último recurso mitiga, mas não substitui os outros dois em cobertura.
- **Histórico de git muito raso para o volume de trabalho.** Um único commit inicial contém
  praticamente todo o projeto (110 arquivos, ~18,5k linhas) — as features de recorrência,
  timer de foco, exportação `.ics` e o redesign visual completo entraram todas juntas, sem
  granularidade. Não é um problema funcional, mas dificulta rastrear quando/por que uma
  decisão específica mudou olhando só para `git log` — este documento (§7) existe em parte
  para compensar essa lacuna.
- **`ics_token` não é revogável pela UI.** *(Pendência parcialmente resolvida em 2026-09-12:
  a seção "Exportar para outro calendário" **existe** nas Configurações e o botão "Gerar link
  de assinatura" funciona — testado ao vivo. O que falta mesmo é (a) o botão de
  revogar/renovar, já que `POST /schedules/export-token` devolve sempre o mesmo token, e (b)
  a correção do link relativo, defeito 6 em §3.)*
- **O silêncio é o modo de falha do motor de busca, e isso é estrutural.** Os três bugs de
  2026-09-01 e o defeito 1 de 2026-09-12 têm a mesma forma: HTTP 200, nenhuma exceção, e zero
  resultado — indistinguível de "o buscador não achou nada". A cascata trata "0 resultados"
  como falha do provedor, o que é razoável, mas **nada distingue "a consulta é obscura" de "o
  parser/decodificador quebrou"**. Uma checagem barata de sanidade (o corpo é HTML legível? o
  seletor principal existe na página?) transformaria a próxima quebra silenciosa em log
  explícito, em vez de num usuário recebendo 2 links sem saber por quê.
- **Nenhuma proteção contra regressão no que já foi corrigido.** Os defeitos de `scraper.py`
  já custaram duas rodadas de diagnóstico. Os testes que os pegaram (bateria de 2026-09-12)
  rodaram em scripts descartáveis, fora do repositório — ou seja, **não existem mais**. Vale
  transformar pelo menos os casos de regressão (desembrulho de redirecionador, corpo
  decodificado legível, ranking/dedupe, cálculo de `remind_at`, escopos de recorrência) em
  `pytest` de verdade dentro de `backend/tests/` — é a forma mais barata de o item 4 do
  roadmap começar a existir.

---

## 7. Log de decisões

| Data | Decisão | Motivo |
|---|---|---|
| ~2026-08-17 | Stack e arquitetura original: FastAPI + SQLAlchemy + SQLite + Alembic no backend; React + Vite + Tailwind v4 no frontend; autenticação JWT com refresh rotativo; lembretes por varredura indexada (não job por agendamento); busca de conteúdo por scraping em cascata (DuckDuckGo → Bing → Wikipédia) | Execução 100% local, sem custo de API de terceiros, alinhado ao objetivo original do autor de um agendador de estudos com busca de apoio embutida |
| 2026-08-31 | Sessões recorrentes materializadas como linhas reais agrupadas por `recurrence_group_id`, em vez de uma regra RRULE calculada em tempo de leitura | Mantém o mesmo princípio já usado pra lembretes ("materializar em vez de calcular na hora") e permite que cada instância da série tenha status/lembrete/links próprios, divergentes das demais |
| 2026-08-31 | Exportação de calendário com **duas** rotas (download autenticado `+` assinatura por token público), não só uma | Download resolve "levar os dados para fora"; a URL de assinatura por token resolve "manter sincronizado" em apps como Google/Apple Calendar, que exigem uma URL pública pollável — as duas necessidades são diferentes e não se substituem |
| 2026-09-01 | Identidade visual redefinida para "Caderno / Editorial" (papel quente, serifa `Fraunces`, verde-tinta), escolhida entre 3 direções apresentadas com preview visual (a alternativa era manter/evoluir o dashboard indigo/dark genérico) | O visual anterior era um template de dashboard SaaS competente, mas sem identidade própria — o autor pediu algo "mais único e linear, intuitivo" |
| 2026-09-01 | **Correção da linguagem de forma:** toda a escala de `--radius-*` do Tailwind redefinida de ~8–16px para 1–6px, no nível do token, em vez de editar cada componente | Feedback direto do autor: "esses botões arredondados... quebram muito a estética do projeto de parecer um caderno". Como praticamente todo componente usa as classes padrão (`rounded-lg`/`xl`/`2xl`) em vez de valor fixo, a correção no token se propagou para o app inteiro numa única edição — decisão que reforça o princípio de theming centralizado registrado em §4 |
| 2026-09-01 | Guarda-corpo determinístico (`ProviderHealth`, disjuntor de circuito) adotado para lidar com bloqueio de provedor de busca, em vez de só melhorar os cabeçalhos e torcer | Reproduzido ao vivo que DuckDuckGo **e** Bing podem ficar bloqueados ao mesmo tempo sob uso repetido; sem o disjuntor, cada busca nova insistiria do zero num provedor já bloqueado, desperdiçando tempo de resposta e mantendo o padrão de tráfego que causou o bloqueio |
| 2026-09-01 | Cabeçalhos da Wikipédia separados dos cabeçalhos de scraping dos buscadores (`_wikipedia_headers()` vs. `_browser_headers()`) | Aplicar sinais de "navegação de página" (`Sec-Fetch-Dest: document`) numa chamada de API JSON é, na prática, mais suspeito que menos — a própria Wikimedia recomenda um User-Agent honesto para chamadas de API. Confirmado experimentalmente: o mesmo header set que ajudava contra os buscadores causava 403 na Wikipédia; corrigido separando os dois |
| 2026-09-01 | `StudySync/` desvinculado do repositório Git que existia em `port/` (pasta geral do portfólio) e reinicializado como repositório independente | O `git init` em `port/` foi identificado como acidental/incorreto (confirmado com o autor) — qualquer commit futuro em outro projeto do portfólio poderia ir parar, sem querer, no repositório público do StudySync se a estrutura antiga fosse mantida |
| 2026-09-12 | Criado este documento (`context_project.md`) + [VALIDATION_PROTOCOL.md](VALIDATION_PROTOCOL.md) | O autor usa mais de uma ferramenta de IA para testar/validar/criar as etapas do projeto — precisa de uma fonte de verdade comum entre sessões e ferramentas, no mesmo padrão já usado com sucesso em outro projeto do autor |

---

## 8. Changelog

> Toda entrada de trabalho relevante entra aqui, mais recente no topo. Formato: `data — o que
> mudou — arquivo(s) — por quê`.

- **2026-09-12** — **Correção do cabeçalho `Accept-Encoding` no motor de busca (`backend/app/services/scraper.py`).**
  Removido `br` indevido de `_browser_headers()` (Defeito 1 / Item 0 do roadmap) que causava falha
  silenciosa no parsing de Bing e DuckDuckGo por ausência do decodificador brotli no `httpx` local.
  Validado ao vivo contra a internet real conforme `VALIDATION_PROTOCOL.md` §3.3: Bing retornou 10
  resultados brutos com URLs de rastreamento desembrulhadas; DuckDuckGo retornou 10 resultados;
  `search_content` ranqueou 5 links de domínios educacionais confiáveis e a cascata de fallback
  respondeu perfeitamente sob bloqueio simulado de DDG e Bing. Itens 0 e 1 do roadmap concluídos.
- **2026-09-12** — **Bateria de validação massiva. 17 defeitos encontrados, nenhum corrigido
  (decisão de prioridade fica com o autor); nenhuma linha de código de produção alterada.**
  Método: (a) 387 verificações automatizadas em 7 baterias — lógica pura (scraper, ICS,
  sanitização, JWT, datas), API HTTP contra um backend isolado em porta e banco descartáveis,
  WebSocket/lembretes com espera real pela varredura do APScheduler, limites, concorrência e
  rotas restantes; (b) os 4 provedores de busca chamados contra a internet real, imprimindo a
  URL final de cada resultado bruto antes do ranking, como manda o `VALIDATION_PROTOCOL` §3.3;
  (c) o app inteiro percorrido no navegador com a conta demo (8 páginas, claro e escuro,
  desktop e 375 px), incluindo criar sessão → receber o lembrete pelo sino → excluir.
  Resultado em §3: o núcleo (auth, isolamento entre usuários, XSS, lembretes, recorrência,
  fuso, concorrência, `.ics`) passou inteiro; **o motor de busca está quebrado na prática** —
  o cabeçalho `Accept-Encoding: br` adicionado na blindagem anti-bloqueio ainda não commitada
  faz DuckDuckGo e Bing devolverem corpo brotli que o `httpx` deste ambiente não decodifica,
  em silêncio, e a Wikipédia (rede de segurança) nunca entrega mais de 2 links por causa do
  teto de 2 por domínio. Reproduzido no app real: "revolução industrial causas e
  consequências" → 2 resultados, sendo 1 irrelevante. Dados de teste criados durante a
  validação removidos do banco de desenvolvimento; servidores de preview encerrados e portas
  conferidas com chamada HTTP real.
- **2026-09-12** — Criados os documentos de governança do projeto: `context_project.md` (este
  arquivo) e `VALIDATION_PROTOCOL.md`. Nenhum código alterado.
- **2026-09-01** — **Repositório Git corrigido.** `port/.git` (acidental, continha StudySync e
  projetos irmãos) removido; `StudySync/` inicializado como repositório próprio, commit
  inicial limpo (`34bf4f7`, 110 arquivos), publicado em
  `https://github.com/KaueChristian/StudySync.git` (branch `main`).
- **2026-09-01** — **Bug do motor de busca corrigido + blindagem anti-bloqueio.**
  `clean_bing_redirect()` desembrulha o redirecionador de clique do Bing (causa raiz de "só
  vem Bing e são 2 links quebrados"); `_raise_if_blocked()` detecta o desafio 202 do
  DuckDuckGo; `ProviderHealth` (disjuntor de circuito) evita insistir num provedor bloqueado;
  `_browser_headers()`/`_wikipedia_headers()` separam cabeçalhos de scraping de navegador dos
  de chamada de API (corrige 403 na Wikipédia). Arquivo: `backend/app/services/scraper.py`.
  **Ainda não commitado** — ver §3/§5.
- **2026-09-01** — **Redesign visual "Caderno/Editorial" + correção da linguagem de forma.**
  Paleta, tipografia e raio de borda redefinidos em `frontend/src/index.css` (tokens
  `--color-brand-*`, `--font-display`, `--radius-*`); badges/chips em pílula corrigidos
  manualmente para o mesmo raio retangular do resto do app (`Misc.jsx`, `FocusTimer.jsx`,
  `NotesPage.jsx`). Validado visualmente em várias telas, claro e escuro.
- **2026-08-31** — **Três features novas adicionadas** (fora do escopo original, a pedido do
  autor): sessões recorrentes semanais (`ScheduleModal.jsx`, `RecurrenceScopeDialog.jsx`,
  `schedules.py`, migração `0002`), timer de foco/Pomodoro (`FocusTimer.jsx`), exportação e
  assinatura de agenda em `.ics` (`services/ics.py`, rotas `/export`, `/export-token`,
  `/export.ics`). `README.md` atualizado no mesmo dia.
- **~2026-08-17** — Build original do projeto: autenticação, matérias, anotações (Markdown),
  agenda com lembretes (WebSocket + notificação nativa), motor de busca de conteúdo em
  cascata, dashboard, biblioteca de links, configurações. Não documentado em detalhe por não
  ter passado por uma sessão orientada a este protocolo — reconstruído aqui a partir de
  evidência de teste ao vivo em 2026-09-01 (ver §3).
