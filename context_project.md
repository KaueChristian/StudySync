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
| Timer de foco (Pomodoro) | ✅ | `FocusTimer.jsx`: presets 25/5, 50/10, 15/5, beep via WebAudio, notificação nativa, botão de concluir a sessão ao final. Em 2026-09-12 a bateria de validação mostrou que o laço em `requestAnimationFrame` congelava com a janela sem pintar (defeito 7). **Reverificado em 2026-09-12 após a correção (laço em `setInterval` de 250 ms + `visibilitychange`):** na mesma condição que antes congelava o relógio (0 callbacks de rAF em 12 s), o relógio andou `15:00 → 14:48` em 12 s; e adiantando o `Date.now` da página em 15 min, o ciclo encerrou sozinho, disparou "Hora da pausa!" e passou para `Pausa · Ciclo 1 · 05:00` |
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
| 2 | 🚫→✅ **Corrigido** | **A rede de segurança nunca entrega os 3–5 links prometidos.** Todo resultado da Wikipédia é do mesmo domínio, e `dedupe_and_rank` cortava em 2 links por domínio (`scraper.py:634`). Corrigido em 2026-09-12: `dedupe_and_rank` agora aceita `max_per_domain` configurável (definido como `limit` quando o provedor for a Wikipédia) e aplica a restrição após a ordenação por score. | Revalidado ao vivo contra a Wikipédia real em 2026-09-12 com "revolução industrial causas e consequências" e "fotossintese plantas", entregando 5 links ranqueados de alta relevância (Revolução Industrial, Fotossíntese, etc.). |
| 3 | 🚫→✅ **Corrigido** | `normalize_url()` remontava a query string a partir do `parse_qs` **sem re-codificar** (`scraper.py:396`): `?q=a%20b%20c` virava `?q=a b c`, com espaço cru dentro da URL salva/aberta. Corrigido em 2026-09-12 usando `urllib.parse.urlencode(kept, doseq=True)`. | Validado ao vivo: normalização de URLs com múltiplos parâmetros e espaços gera query codificada (`q=a+b+c&x=1`), sem espaços crus nem parâmetros de rastreamento. |
| 4 | 🚫→✅ **Corrigido** (com ressalva) | **Sessão pendente que já passou desaparecia do painel.** O card "Sessões pendentes" exibia `sessions_upcoming` (só futuras) e o docstring de `scheduler.py` prometia um job `mark_overdue_sessions` inexistente. Corrigido em 2026-09-12: `DashboardStats` entrega `sessions_pending` e `sessions_overdue`; o painel mostra o total pendente e "N em atraso"; docstring corrigido. **Ressalva encontrada na reverificação:** `sessions_overdue` usa `start_at < agora`, então uma sessão **em andamento** (começou há 10 min, termina em 50) já aparece como "em atraso" — ver N2 abaixo | Reverificado em 2026-09-12 (API + navegador): conta demo exibe "3 Sessões pendentes · 3 em atraso"; cenário sintético com 5 pendentes (2 futuras, 2 vencidas, 1 em andamento) devolveu `sessions_pending=5`, `sessions_upcoming=2`, `sessions_overdue=3` |
| 5 | 🚫→✅ **Corrigido** | **"Resumo do mês" não é do mês.** O painel somava o array inteiro carregado (`SchedulePage.jsx:236-238`), que vai do mês anterior ao mês seguinte (`SchedulePage.jsx:47-48`). Corrigido em 2026-09-12 filtrando `monthSchedules` com `isSameMonth(toDate(s.start_at), month)`. | Validado no frontend: ao navegar na agenda, os contadores do resumo refletem estritamente as sessões do mês ativo. |
| 6 | 🚫→✅ **Corrigido** | **O link de assinatura da agenda era relativo e não servia para o que foi feito.** `SettingsPage.jsx:145` montava a URL com `apiUrl()`, que devolvia caminho relativo quando `VITE_API_URL` estava vazio (`/api/schedules/export.ics?token=…`). Corrigido em 2026-09-12 adicionando `absoluteApiUrl()` em `api.js` e utilizando-o em `SettingsPage.jsx`. | Validado: o botão "Gerar link de assinatura" produz URL absoluta completa com protocolo e domínio (`http://localhost:5173/api/...` ou domínio configurado). |
| 7 | 🚫→✅ **Corrigido** | **O Pomodoro congelava quando a janela não estava sendo desenhada.** `FocusTimer.jsx` usava só `requestAnimationFrame`, que é pausado pelo navegador em segundo plano / janelas minimizadas, impedindo o alarme e notificação de término de ciclo. Corrigido em 2026-09-12 substituindo rAF por `setInterval` (250ms) contra `targetAtRef.current`, somado a evento `visibilitychange` e atualização de estado apenas ao mudar de segundo. | Validado: timer continua calculando o tempo mesmo em segundo plano e notifica pontualmente ao final do ciclo. |
| 8 | 🚫→✅ **Corrigido** | Disjuntor com `threshold=2` e `cooldown=600s`: com DDG bloqueado e Bing offline, a busca inteira parava por 10 minutos antes de tentar a Wikipédia. Corrigido em 2026-09-12 calibrando os limites por provedor (Wikipédia com threshold 3 e cooldown 60s; buscadores com threshold 2 e cooldown 300s), desarmando penalidade em busca vazia na Wikipédia e adicionando fallback de emergência caso todos estejam em cooldown. | Validado: simulação com provedores principais em cooldown ativa a Wikipédia imediatamente sem silêncio do motor de busca. |
| 9 | 🚫→✅ **Corrigido** | `_escape()` do ICS (`ics.py:19-26`) não escapava `\r`: descrição com CRLF vazava um CR cru para dentro da linha do arquivo. Corrigido em 2026-09-12 normalizando `\r\n` e `\r` para `\n` antes do escape de caracteres. | Validado: `_escape("linha1\r\nlinha2\rlinha3")` devolve `linha1\nlinha2\nlinha3`, em estrita conformidade com a RFC 5545. |
| 10 | 🚫→✅ **Corrigido** | `tokenize()` descartava termos de até 2 caracteres (`scraper.py:326`): "pH", "IA", "3D" sumiam do cálculo de relevância. Corrigido em 2026-09-12 aceitando termos com `len >= 2` e expandindo `STOPWORDS` com preposições e artigos curtos ("is", "at", "by", "an", "it", "me", "te", "eu"). | Validado: `tokenize("escala de ph")` devolve `{'escala', 'ph'}` e `tokenize("estudos de ia e 3d")` preserva `'ia'` e `'3d'`. |
| 11 | 🔵→✅ **Corrigido** | O teto de 2 links por domínio era aplicado **antes** da pontuação: ficavam os 2 primeiros do provedor, não os 2 melhores. Corrigido em 2026-09-12 pontuando e ordenando todos os candidatos antes de aplicar a contagem de `domain_count`. | Validado sinteticamente e ao vivo: o candidato mais aderente de um domínio com múltiplos resultados é selecionado mesmo chegando em 3º ou posterior na lista original do provedor. |
| 12 | 🚫→✅ **Corrigido** | Excluir matéria apagava em cascata anotações e sessões, mas deixava tags órfãs. Corrigido em 2026-09-12 executando `cleanup_orphan_tags(db, current_user.id)` ao excluir matéria e aplicando exclusão direta SQL por ID em conjunto com `passive_deletes=True` nos relacionamentos N:N. | Validado: ao excluir matéria contendo anotação com tag exclusiva, a tag órfã é removida do banco de dados. |
| 13 | 🚫→✅ **Corrigido** (fechado na 2ª rodada) | `notifications.schedule_id` sem integridade referencial. **1ª rodada (commit `135d1c2`):** `delete_schedule` zera `schedule_id`, FK `ON DELETE SET NULL` no modelo, toast em `SchedulePage.jsx` — mas a FK entrou só no modelo, sem migração, e não chegava a bancos existentes (excluir a matéria ainda deixava órfã). **2ª rodada (2026-09-12, noite):** migração `alembic/versions/0003_fk_notificacao_agendamento.py` — zera notificações órfãs e cria a FK via `batch_alter_table`, pulando a alteração se a FK já existir (bancos criados pelo `create_all` depois do `135d1c2`). Ela chega a todo banco porque o boot passou a aplicar as migrations (ver N3 e §7) | Cópia do `studysync.db` de dev, antes com FK só para `users`: no boot o log mostra `Running upgrade 0002 -> 0003`, `PRAGMA foreign_key_list(notifications)` passa a listar `schedules / SET NULL`, e o cenário que falhava — excluir a matéria com sessão notificada — agora deixa `schedule_id=NULL`. Dados preservados (usuários, matérias, anotações, sessões, notificações, links, tags: mesmas contagens), `integrity_check=ok`, `foreign_key_check` vazio; órfã de teste com `schedule_id=999` virou `NULL`. `downgrade -1` + `upgrade head` idempotentes |
| 14 | 🚫→✅ **Corrigido** | `npm run lint` quebrado por falta de dependências e configuração. Corrigido em 2026-09-12 instalando `eslint`, `@eslint/js`, `globals`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh` e criando `eslint.config.js` adaptado para React 19 / Vite. | Validado: `npm run lint` executa e passa com 0 erros. |
| 15 | 🚫→✅ **Corrigido** | Rótulos relativos não se atualizavam sozinhos em `ScheduleCard.jsx:127`. Corrigido em 2026-09-12 adicionando ticker intervalar (`useEffect` com `now`) que recalcula a cada 5s/30s e transiciona automaticamente o status quando o horário de início da sessão é atingido. | Validado: o rótulo "começa em..." atualiza em tempo real e cessa quando a sessão começa. |
| 16 | 🚫→✅ **Corrigido** | `truncate()` (`format.js`) quebrava com palavras sem espaços por usar `-1 || max`. Corrigido em 2026-09-12 utilizando `max` diretamente quando `lastSpace <= 0`. | Validado: `truncate("a".repeat(200), 20)` retorna 20 caracteres + reticências. |
| 17 | 🚫→✅ **Corrigido** | Plurais fixos ("1 sessões", "Todas as 1 anotações"). Corrigido em 2026-09-12 flexibilizando singular e plural no `aria-label` de `CalendarMonth.jsx` e no modal de confirmação de exclusão em `SubjectsPage.jsx`. | Validado na acessibilidade e nos diálogos da interface. |

**Achados novos das reverificações de 2026-09-12** (depois das correções; não faziam parte dos 17). N1–N3 da 1ª reverificação; N4–N11 da validação completa com o app real. Situação em 2026-09-12 (noite, 3): **N3 corrigido; N1, N2 e N4–N11 abertos** (N1 e N2 reconfirmados):

| # | Gravidade | Defeito | Evidência |
|---|---|---|---|
| N1 | 🟡 Médio | **Anúncios pagos do DuckDuckGo entram no resultado como se fossem links de estudo.** O seletor `div.result` do provedor HTML também captura os blocos de anúncio, cuja URL é um redirecionador de clique `https://duckduckgo.com/y.js?ad_domain=...`. O domínio vira `duckduckgo.com` (então nem a penalidade de e-commerce se aplica) e o link é de rastreamento. Era invisível antes porque o DuckDuckGo HTML nunca funcionava (defeito 1); a correção do brotli o expôs | Contra o DuckDuckGo real: "curso de ingles online" → 12 resultados brutos, 2 anúncios, e **os 2 anúncios entraram no top 5** (scores 62,1 e 61,8: "Aulas de Idiomas Online - Curso De Inglês", "Maior Curso de Inglês Online - English Live"). Consultas didáticas ("partes do corpo humano") não trouxeram anúncio |
| N2 | 🔵 Baixo | `sessions_overdue` conta sessão em andamento como "em atraso" (`dashboard.py`, filtro `start_at < now`). Durante toda sessão que o usuário está cumprindo agora, o painel acusa 1 atraso. `end_at < now` expressaria "já passou e não foi concluída" | Cenário sintético: sessão iniciada há 10 min e terminando em 50 contou em `sessions_overdue` |
| N3 | 🚫→✅ **Corrigido** (2026-09-12, noite) | **O Alembic não gravava a versão aplicada.** Causa confirmada em reprodução isolada: `connection.exec_driver_sql("PRAGMA foreign_keys=ON")` em `alembic/env.py` dispara o autobegin do SQLAlchemy 2.0; `context.begin_transaction()` vê a transação já aberta e não assume o commit; ao fechar a conexão, o `INSERT` em `alembic_version` é desfeito — o `CREATE TABLE` sobrevive porque o SQLite confirma DDL sozinho. Corrigido com `connection.commit()` logo após o PRAGMA. **Problema maior encontrado no caminho:** o boot da aplicação criava o banco com `Base.metadata.create_all`, que também não registra versão — todo banco nascido de `python run.py` ficava fora do Alembic, e o `alembic upgrade head` seguinte quebrava com `table users already exists`. `app/db/init_db.py` reescrito para aplicar as migrations no boot (ver §7) | Banco vazio → `upgrade head` → `alembic current` = `0003 (head)` (antes: vazio). `alembic check` → "No new upgrade operations detected" (modelos e migrations batem). `init_database()` testado em 4 cenários: banco vazio (0001→0003), banco do `create_all` antigo sem versão (carimba `0002`, aplica `0003`), cópia do dev (`0002`→`0003`) e `--reset`; segunda chamada é no-op em todos. `python -m app.seed` e `python -m app.db.init_db` OK |
| N4 | 🟡 Médio | **"Hoje" do painel é o dia UTC, não o do usuário.** `dashboard.py` calcula `today_start` a partir de `datetime.now(timezone.utc)`; o mesmo vale para `minutes_scheduled_week` e o gráfico de 7 dias. Em Brasília, das 21h à meia-noite o painel já considera o dia seguinte | Reproduzido na UI real às 21h15 de sábado 12/09: sessão criada para **domingo 13/09 às 09:00** → painel exibiu "Você tem 1 sessão hoje", e o gráfico de 7 dias passou a terminar em "D". Via API: 4 sessões no dia local (01h, 10h, 22h e 23h BRT) → `sessions_today=2`; sessão de amanhã 00h30 BRT entrou na contagem de hoje |
| N5 | 🟡 Médio | **`PATCH` com `null` explícito derruba a API com 500.** `update_schedule` e `update_note` usam `model_dump(exclude_unset=True)`, que deixa `null` passar para colunas `NOT NULL`. `subjects` e `auth/me` usam `exclude_none` e não têm o problema. A UI atual sempre envia valores, então o erro só aparece para quem chama a API direto | `PATCH /schedules/{id}` com `title: null` → 500 (`IntegrityError: NOT NULL constraint failed: schedules.title`); `start_at: null` → 500 (`AssertionError` em `compute_remind_at`); `remind_minutes: null` → 500; `PATCH /notes/{id}` com `title: null` → 500 |
| N6 | 🟡 Médio | **A busca de anotações não ignora acento nem maiúscula acentuada.** O `ILIKE` do SQLite só dobra maiúsculas ASCII. Os curingas `%` e `_` digitados pelo usuário também não são escapados, e a ordenação por título (`func.lower`) põe palavras acentuadas no fim | Na UI real: "química" acha a anotação; "QUÍMICA" e "quimica" não acham nada. Via API: "HISTÓRIA", "historia", "IMPÉRIO" e "periodo" → 0 resultados para "História do Brasil / Período colonial e Império"; busca por `_` casou uma anotação sem sublinhado; ordem alfabética `abacate, História, zebra, Árvore` |
| N7 | 🔵 Baixo | **A configuração "Fuso horário" é gravada e ignorada.** Nenhum trecho do backend ou do frontend lê `user.timezone` (a tela diz "Usado para exibir os horários das sessões"), e a API aceita qualquer texto | Na UI: fuso trocado para `UTC` e salvo (`PATCH /auth/me` 200), mas o cartão continuou `09:00 – 10:00` (em UTC seria 12:00). Via API: `timezone: "Marte/Base_Alfa"` → 200 e gravado |
| N8 | 🔵 Baixo | `PATCH` de sessão não aplica o limite de 24 h que a criação aplica (`ScheduleUpdate` não repete a regra) | Sessão de 1 h editada com `end_at` 2 dias depois → 200 |
| N9 | 🔵 Baixo | `POST /search/save` não normaliza a URL antes do teste de duplicidade: o mesmo link com e sem barra final vira dois registros | Resultado real do DuckDuckGo salvo duas vezes numa sessão (`…/fotossintese` e `…/fotossintese/`) → 2 links |
| N10 | 🔵 Baixo | A unicidade do nome de matéria diferencia maiúsculas (`UniqueConstraint(owner_id, name)` no SQLite): "Biologia" e "biologia" coexistem e aparecem duplicadas no filtro da agenda. Renomear para um nome exatamente igual dá 409 corretamente | Criada "biologia" pela UI com "Biologia" já existente → "Matéria criada!" |
| N11 | 🔵 Baixo | Arestas de UI: (a) **colar** `fisica, quimica, biologia` no campo de tags cria uma única tag com vírgulas, embora o placeholder sugira separação por vírgula (digitar a vírgula funciona); (b) o resumo de anotação com tabela Markdown mostra `\| a \| b \| \| \|` (o `_MARKDOWN_NOISE` não remove `\|`); (c) o `aria-label` do sino diz "Notificações (1 não lidas)" — o mesmo problema de plural do #17, num ponto que a correção não cobriu | Observado no navegador real durante o fluxo de anotações e do sino |

Efeitos colaterais conhecidos das correções (aceitáveis, só registrados): `tokenize` agora conta termos de 2 letras que não são stopword ("já", "lá", "só", "vs"); `normalize_url` transforma `?flag` em `?flag=`; e, pelo desenho do #8, quando **todos** os provedores estão em cooldown a Wikipédia é tentada em toda busca (o disjuntor deixa de protegê-la nesse cenário — escolha consciente, já que é API oficial).

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
    0003_fk_notificacao_agendamento.py — FK notifications.schedule_id → schedules.id (SET NULL)
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
| 2026-09-12 | **O boot da aplicação passa a aplicar as migrations do Alembic** (`init_database()` em `app/db/init_db.py`), em vez de `Base.metadata.create_all`. Banco vazio recebe todas as migrations; banco antigo sem versão é carimbado com a revisão equivalente (detectada pelas colunas de `0002`) e recebe o restante; banco versionado recebe só o que falta. `create_all` deixa de ser usado para criar esquema | Com dois caminhos (Alembic na documentação, `create_all` no boot), todo banco criado ao rodar `python run.py` ficava sem versão e nenhuma migration nova chegava a ele — foi exatamente por isso que a FK do defeito #13 nunca alcançou bancos existentes. Um caminho só também é o que o empacotamento desktop (roadmap item 3) exige: cada usuário terá um banco local com dados reais, que precisa ser atualizado no lugar a cada versão nova. Regra daqui em diante: **toda mudança de esquema em modelo vem com migration** (`alembic revision --autogenerate`), conferida com `alembic check` |
| 2026-09-12 | Criado este documento (`context_project.md`) + [VALIDATION_PROTOCOL.md](VALIDATION_PROTOCOL.md) | O autor usa mais de uma ferramenta de IA para testar/validar/criar as etapas do projeto — precisa de uma fonte de verdade comum entre sessões e ferramentas, no mesmo padrão já usado com sucesso em outro projeto do autor |
| 2026-09-12 | Limite por domínio pós-pontuação e flexibilizado para Wikipédia em `dedupe_and_rank` | Resolve os defeitos 2 e 11: permite que a Wikipédia entregue até `limit` links (3–5) em fallback, e garante que nos buscadores gerais os melhores links de cada domínio sejam selecionados em vez dos primeiros da listagem bruta |
| 2026-09-12 | Resolução simultânea de todos os defeitos de prioridade média (Defeitos 3, 4, 5, 6, 7 e 8) | Normalização de URL com `urlencode` (evita espaços crus); `DashboardStats` com `sessions_pending` e `sessions_overdue`; resumo do mês isolado por `isSameMonth`; URLs públicas absolutas via `absoluteApiUrl`; Pomodoro resiliente a abas inativas via `setInterval` + `visibilitychange`; disjuntor de busca calibrado com parâmetros por provedor e fallback seguro contra blackouts |
| 2026-09-12 | Resolução simultânea de todos os defeitos de prioridade baixa (Defeitos 9, 10, 12, 13, 14, 15, 16 e 17) | Escape seguro de quebras de linha em ICS; preservação de termos de 2 caracteres em `tokenize()`; limpeza de tags órfãs em cascata na exclusão de matérias; integridade de `schedule_id` e fallback informativo em notificações; ESLint flat config configurado no frontend; ticker intervalar dinâmico em `ScheduleCard`; correção em `truncate()`; flexão singular/plural correta em calendário e diálogos |

---

## 8. Changelog

> Toda entrada de trabalho relevante entra aqui, mais recente no topo. Formato: `data — o que
> mudou — arquivo(s) — por quê`.

- **2026-09-12 (noite, 3)** — **Validação completa do sistema com o app real, após fechar #13
  e N3. Nenhum código de produção alterado nesta etapa.** Backend subido sobre o `studysync.db`
  de desenvolvimento: o boot aplicou `0002 → 0003` sozinho, dados preservados (mesmas contagens,
  `integrity_check=ok`, `foreign_key_check` vazio) e `alembic check` sem divergência. Regressão
  sem mudança: API 162 ok, reverificação de banco 22+22, WebSocket/lembretes 32, rotas 28,
  limites/concorrência 23, unitários 27, motor de busca contra provedores reais 53 ok (as 3
  falhas de sempre são artefatos do próprio teste), `npm run lint` 0 erros, build OK. Nova bateria
  em áreas nunca testadas (fuso, acentos, IDOR de notificações, tokens expirados/nbf/conta
  desativada, WebSocket, tags hostis, edição de instância recorrente, `PATCH` com nulls, busca +
  salvar pela API, purge de tokens): 37 ok, 15 falhas → **N4–N11** em §3. Navegador com a conta
  demo: anotações (criar com tags e Markdown, filtro por tag, busca, editar, barra de formatação,
  salvar link pela aba Conteúdo de apoio, excluir), matérias (criar, 409 ao renomear, excluir),
  troca de senha (validação de confirmação e 400 de senha atual), sino (marcar lidas, Esc),
  sair, rota protegida, cadastro (validações e e-mail existente), menu mobile e download `.ics`
  — tudo funcionando, exceto o que está em N4, N6, N7, N10 e N11. Dados de teste removidos; a
  notificação da seed voltou a não lida; ficaram 2 refresh tokens a mais (os logins do teste),
  que são registros normais de sessão. Portas 8000/5173/8010/8011/8012 conferidas com HTTP real.
- **2026-09-12 (noite, 2)** — **Defeitos #13 e N3 fechados.** Arquivos: `backend/alembic/env.py`
  (commit após o PRAGMA — a versão aplicada passa a ser gravada), nova
  `backend/alembic/versions/0003_fk_notificacao_agendamento.py` (FK `SET NULL` + limpeza de
  órfãs, idempotente), `backend/app/db/init_db.py` reescrito (boot aplica migrations, migra
  bancos antigos sem versão, `--reset` recria pelas migrations), comentário em
  `backend/app/main.py`, seção de banco do `README.md`. Decisão registrada em §7. Validação:
  migração pela CLI (upgrade/downgrade/check) e pelo `init_database()` em 4 cenários de banco;
  backend real subido com banco novo e com cópia do `studysync.db` (log de boot mostrou a
  migração); cenário do #13 que falhava agora passa nos dois; regressão completa sem mudança de
  números (API 162 ok, rotas 28 ok, limites/concorrência 23 ok, WebSocket/lembretes 32 ok).
  Única falha remanescente nas baterias é a já conhecida N2. **O `studysync.db` de
  desenvolvimento ainda não foi migrado** — acontece no próximo boot do backend; cópia de
  segurança em `backend/studysync.backup-pre-0003.db` (ignorada pelo git).
- **2026-09-12 (noite)** — **Reverificação independente dos 17 defeitos após os commits
  `c6d1132`, `80153c0` e `135d1c2`. Nenhum código de produção alterado nesta sessão.**
  Resultado: **15 corrigidos e confirmados por execução real**, **1 corrigido com ressalva** (#4,
  sessão em andamento contada como atraso) e **1 parcial** (#13, FK sem migração — falha em
  bancos existentes pelo caminho da cascata de matéria). 3 achados novos (N1–N3 em §3), sendo
  N1 exposto pela própria correção do brotli. Método: backend isolado em **dois esquemas** (banco
  novo via `create_all` e cópia do `studysync.db` de dev), regressão completa das baterias
  anteriores (API 162 ok / WebSocket+lembretes 32 ok / limites e concorrência 23 ok / rotas
  restantes 28 ok — mesmos números de antes, sem regressão), 27 verificações unitárias novas
  por defeito, 22 verificações de banco por esquema, provedores reais (os 5 User-Agents do
  pool agora recebem gzip do Bing e 10 resultados cada; "fotossíntese" e "segunda guerra
  mundial" voltaram a 5 links via DuckDuckGo) e navegador com a conta demo (#4, #5, #6, #7,
  #13, #15, #17). `npm run lint`: 0 erros, 8 avisos; `npm run build` OK. Dados de teste
  removidos, portas 8000/5173/8010/8011 conferidas com HTTP real, `git status` limpo.

- **2026-09-12** — **Correção simultânea de todos os 8 defeitos de prioridade baixa (Defeitos 9, 10, 12, 13, 14, 15, 16 e 17).**
  - **Defeito 9 (`ics.py`):** `_escape()` normaliza quebras `\r\n` e `\r` para `\n` antes do escape, evitando caracteres `\r` crus no formato RFC 5545.
  - **Defeito 10 (`scraper.py`):** `tokenize()` preserva termos com `len >= 2` ("pH", "IA", "3D"), com `STOPWORDS` expandido para preposições e artigos curtos.
  - **Defeito 12 (`subjects.py`, `tags.py`, `note.py`, `tag.py`):** `delete_subject` agora executa `cleanup_orphan_tags()`; `tags.py` usa exclusão SQL direta por ID para não conflitar com a cascata do SQLite; relacionamentos configurados com `passive_deletes=True`.
  - **Defeito 13 (`schedules.py`, `notification.py`, `SchedulePage.jsx`):** `delete_schedule` anula `schedule_id` nas notificações; `notification.py` mapeia FK com `SET NULL`; `SchedulePage.jsx` busca a sessão diretamente ou avisa o usuário com toast informativo em caso de exclusão.
  - **Defeito 14 (`package.json`, `eslint.config.js`):** Instalado ESLint e plugins; configurado `eslint.config.js` moderno com 0 erros no lint.
  - **Defeito 15 (`ScheduleCard.jsx`):** Ticker intervalar atualiza `now` em sessões pendentes futuras, atualizando dinamicamente "começa em..." e transitando quando a sessão começa.
  - **Defeito 16 (`format.js`):** `truncate()` usa `max` quando não há espaços dentro do limite, prevenindo que strings contínuas fiquem quase intactas.
  - **Defeito 17 (`CalendarMonth.jsx`, `SubjectsPage.jsx`):** Singular e plural flexionados corretamente na acessibilidade do calendário e diálogos de confirmação.
  - **Validação:** Todos os testes unitários e de integração com banco de dados em Python passaram; `npm run lint` passou com 0 erros; `npm run build` gerou bundle de produção com sucesso em 2.95s.
- **2026-09-12** — **Correção simultânea de todos os 6 defeitos de prioridade média (Defeitos 3, 4, 5, 6, 7 e 8).**
  - **Defeito 3 (`scraper.py`):** `normalize_url` agora usa `urlencode(kept, doseq=True)`, codificando espaços e caracteres especiais em query strings.
  - **Defeito 4 (`dashboard.py`, `schemas/dashboard.py`, `DashboardPage.jsx`, `scheduler.py`):** Adicionados `sessions_pending` e `sessions_overdue` ao backend e exibição no card de sessões pendentes no frontend; corrigida docstring do agendador.
  - **Defeito 5 (`SchedulePage.jsx`):** Resumo do mês agora usa `monthSchedules` filtrado com `isSameMonth`, ignorando sessões dos meses vizinhos.
  - **Defeito 6 (`api.js`, `SettingsPage.jsx`):** Criada a função `absoluteApiUrl()` para gerar URLs absolutas públicas no link de assinatura `.ics`.
  - **Defeito 7 (`FocusTimer.jsx`):** Substituído `requestAnimationFrame` por `setInterval` (250ms) baseado em timestamp-alvo absoluto com listener de `visibilitychange`, mantendo a contagem e notificações mesmo em abas em segundo plano.
  - **Defeito 8 (`scraper.py`):** `ProviderHealth` agora suporta parâmetros por provedor (Wikipédia: 3 falhas, cooldown 60s; buscadores: 2 falhas, 300s); buscas vazias na Wikipédia não penalizam o disjuntor; busca implementa fallback de emergência quando todos os provedores estão em cooldown.
  - **Validação:** Todos os testes unitários em Python passaram; build do frontend (`npm run build`) concluído com sucesso; chamadas ao vivo aos provedores e à API de dashboard executadas com sucesso.
- **2026-09-12** — **Correção do teto de links por domínio no motor de busca (`backend/app/services/scraper.py`).**
  `dedupe_and_rank` passou a ordenar todos os candidatos por score antes de aplicar o filtro por
  domínio (corrigindo o Defeito 11) e agora aceita `max_per_domain` configurável, definido como
  `limit` quando o provedor for a Wikipédia (corrigindo o Defeito 2). Validado ao vivo contra a
  Wikipédia real com as consultas "revolução industrial causas e consequências" e "fotossintese plantas",
  retornando 5 links ranqueados de alta relevância (anteriormente travada em 2 links).
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
