# 📚 StudySync

Aplicação web completa para **gerenciar matérias, anotações e sessões de estudo**, com
lembretes em tempo real e um motor de **busca de conteúdo de apoio na web** — sem custo
de API externa.

```
┌──────────────────────┐   REST + WebSocket   ┌───────────────────────────┐
│  Frontend (React)    │ ───────────────────► │  Backend (FastAPI)        │
│  Vite · Tailwind v4  │ ◄─────────────────── │  SQLAlchemy · APScheduler │
└──────────────────────┘   lembretes push     └────────────┬──────────────┘
                                                           │
                                          ┌────────────────┴────────────────┐
                                          │                                 │
                                    ┌─────▼─────┐              ┌────────────▼────────────┐
                                    │  SQLite   │              │  Scraper (BeautifulSoup)│
                                    │ + Alembic │              │  DDG → Bing → Wikipédia │
                                    └───────────┘              └─────────────────────────┘
```

---

## ✨ Funcionalidades

| Área | O que faz |
|---|---|
| **Autenticação** | Cadastro e login com **bcrypt** (salt por senha), **JWT** de acesso (30 min) + refresh rotativo (7 dias) revogável em banco, detecção de reuso de token, rate limiting anti-brute-force |
| **Matérias** | CRUD completo com cor e ícone personalizados, contadores de anotações e sessões |
| **Anotações** | CRUD com **Markdown** (GFM: tabelas, checklists, código), tags, categorias, fixar no topo, busca textual, filtros e paginação |
| **Agenda** | Calendário mensal interativo, sessões com matéria/tópico/local, status (pendente, concluída, cancelada), **repetição semanal** (uma série inteira materializada de uma vez, com exclusão por "somente esta", "esta e as próximas" ou "toda a série") |
| **Lembretes** | **APScheduler** varre os lembretes vencidos a cada 30s → persiste a notificação → empurra por **WebSocket** → toast na tela + notificação nativa do sistema |
| **Timer de foco** | Pomodoro embutido na sessão (presets 25/5, 50/10, 15/5, pausa longa a cada 4 ciclos), contagem por timestamp para não perder precisão em segundo plano, e atalho para marcar a sessão como concluída ao final |
| **Exportar agenda** | Download `.ics` sob demanda ou **link de assinatura** (token opaco por usuário) para Google Calendar/Apple Calendar acompanharem a agenda automaticamente, com `VALARM` refletindo o lembrete de cada sessão |
| **Busca de conteúdo** | Scraping em cascata (DuckDuckGo HTML → Lite → Bing → API da Wikipédia) com **ranking de relevância e confiabilidade**, retornando os 5 melhores links (título, snippet e URL) para salvar em anotações ou sessões |
| **Biblioteca** | Todos os links salvos em um só lugar, com filtro por origem |
| **Interface** | Identidade visual própria ("Caderno" — papel creme/tinta escura, tipografia serif Fraunces nos títulos), SPA responsiva, tema claro/escuro, acessibilidade (focus trap, ARIA, `prefers-reduced-motion`) |

---

## 🚀 Instalação e execução

**Pré-requisitos:** Python ≥ 3.11 · Node.js ≥ 18 · Git

```bash
git clone <url-do-repositorio>
cd StudySync
```

### 1️⃣ Backend

<details open>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```
</details>

<details>
<summary><strong>Linux / macOS</strong></summary>

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
</details>

**Gere a chave secreta** e cole em `SECRET_KEY=` dentro do `.env`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

> Em desenvolvimento a chave é opcional (uma temporária é gerada a cada boot, invalidando
> os tokens no restart). Em `ENV=production` ela é **obrigatória**.

**Crie o banco de dados** — via migrations (recomendado):

```bash
alembic upgrade head
```

<details>
<summary>Alternativa sem Alembic</summary>

```bash
python -m app.db.init_db          # cria as tabelas
python -m app.db.init_db --reset  # apaga e recria (destrutivo)
```
</details>

**Popule com dados de demonstração** (opcional, mas recomendado):

```bash
python -m app.seed
```

Cria o usuário **`demo@studysync.dev`** / senha **`Estudo2024`** com 4 matérias,
4 anotações, 5 sessões e links de apoio. Uma das sessões começa em ~18 minutos, então o
**lembrete dispara em cerca de 3 minutos** — deixe a aplicação aberta para vê-lo chegar.

**Suba o servidor:**

```bash
python run.py
```

| Endereço | Descrição |
|---|---|
| http://localhost:8000/api | Base da API |
| http://localhost:8000/docs | Documentação interativa (Swagger UI) |
| http://localhost:8000/health | Health check |

### 2️⃣ Frontend

Em **outro terminal**:

```bash
cd frontend
npm install
cp .env.example .env      # Windows: copy .env.example .env
npm run dev
```

Abra **http://localhost:5173** 🎉

> O `.env` do frontend pode ficar com os valores vazios: o Vite faz proxy de `/api`
> (incluindo o WebSocket) para `http://127.0.0.1:8000`, evitando qualquer questão de CORS
> em desenvolvimento.

---

## 📁 Estrutura do projeto

```
StudySync/
├── backend/
│   ├── alembic/                    # migrations versionadas
│   │   └── versions/0001_esquema_inicial.py
│   ├── app/
│   │   ├── api/routes/             # auth, subjects, notes, tags, schedules,
│   │   │                           # search, notifications, dashboard, ws
│   │   ├── core/                   # config, security, deps, rate_limit, sanitize
│   │   ├── db/                     # engine, sessão, base declarativa, init_db
│   │   ├── models/                 # User, RefreshToken, Subject, Tag, Note,
│   │   │                           # Schedule, SearchResult, Notification
│   │   ├── schemas/                # contratos Pydantic de entrada/saída
│   │   ├── services/               # scraper, notifier (WS), scheduler, tags
│   │   ├── main.py                 # app FastAPI, CORS, middlewares, lifespan
│   │   └── seed.py                 # dados de demonstração
│   ├── alembic.ini
│   ├── requirements.txt
│   └── run.py                      # servidor de desenvolvimento
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── auth/               # AuthShell, RouteGuards
    │   │   ├── layout/             # AppLayout, Sidebar, NotificationBell
    │   │   ├── notes/              # NoteEditorModal, Markdown, TagInput
    │   │   ├── schedule/           # CalendarMonth, ScheduleModal, ScheduleCard
    │   │   ├── search/             # ContentSearchPanel
    │   │   ├── subjects/           # SubjectModal
    │   │   └── ui/                 # Button, Field, Modal, ConfirmDialog, Misc
    │   ├── context/                # Auth, Theme, Toast, Notification (WebSocket)
    │   ├── lib/                    # api (axios), services, format, constants
    │   ├── pages/                  # Login, Register, Dashboard, Subjects, Notes,
    │   │                           # Schedule, Search, Library, Settings, NotFound
    │   ├── App.jsx                 # rotas
    │   └── main.jsx                # provedores
    └── vite.config.js
```

---

## 🔌 API

Documentação completa e testável em **http://localhost:8000/docs**.

<details>
<summary><strong>Ver todos os endpoints</strong></summary>

### Autenticação — `/api/auth`
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/register` | Cria a conta e devolve os tokens |
| `POST` | `/login` | Autentica |
| `POST` | `/refresh` | Renova o access token (com rotação do refresh) |
| `POST` | `/logout` | Revoga o refresh token atual |
| `POST` | `/logout-all` | Revoga todas as sessões |
| `GET` `PATCH` | `/me` | Consulta / atualiza o perfil |
| `POST` | `/change-password` | Troca a senha |

### Matérias — `/api/subjects`
`GET` · `POST` · `GET /{id}` · `PATCH /{id}` · `DELETE /{id}`

### Anotações — `/api/notes`
`GET` (filtros: `subject_id`, `tag`, `category`, `search`, `sort`, `page`) · `POST` ·
`GET /{id}` · `PATCH /{id}` · `DELETE /{id}` · `GET /categories` · `GET /{id}/links`

### Tags — `/api/tags`
`GET` (com contagem de uso) · `DELETE /{id}`

### Agendamentos — `/api/schedules`
`GET` (filtros: `start`, `end`, `subject_id`, `status`) · `GET /upcoming` · `POST`
(aceita `repeat_weekly` + `repeat_until` para criar uma série semanal) ·
`GET /{id}` · `PATCH /{id}` · `PATCH /{id}/status` ·
`DELETE /{id}` (query `scope=this|following|all` para séries recorrentes) ·
`GET /export` (baixa a agenda em `.ics`) · `POST /export-token` (gera o token de
assinatura) · `GET /export.ics?token=…` (assinatura pública, sem JWT)

### Busca de conteúdo — `/api/search`
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/` | Busca os N links mais relevantes sobre um tema |
| `POST` | `/save` | Anexa um link a uma anotação **ou** a uma sessão |
| `GET` | `/saved` | Lista os links salvos |
| `DELETE` | `/saved/{id}` | Remove um link |

### Notificações — `/api/notifications`
`GET` · `POST /{id}/read` · `POST /read-all` · `DELETE`

### Dashboard — `/api/dashboard`
`GET` — métricas, próximas sessões, anotações recentes, distribuição e atividade semanal

### WebSocket — `/api/ws/notifications?token=<access_token>`
```jsonc
{ "event": "connected",    "data": { "user_id": 1, "server_time": "…" } }
{ "event": "notification", "data": { "title": "Lembrete: …", "schedule": { … } } }
{ "event": "pong",         "data": { "server_time": "…" } }
```
</details>

**Exemplo — buscar conteúdo de apoio:**

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "partes do corpo humano", "limit": 5, "subject_hint": "Biologia"}'
```

---

## 🔐 Segurança

| Ameaça | Mitigação |
|---|---|
| **Vazamento de senhas** | `bcrypt` com custo 12 e salt por senha; o hash nunca sai da camada de dados (nenhum schema de resposta o expõe) |
| **Roubo de token** | Access de vida curta (30 min); refresh persistido apenas como digest SHA-256, com **rotação** — reapresentar um token já revogado derruba todas as sessões do usuário |
| **Força bruta** | Rate limiting por IP nas rotas de autenticação (janela deslizante, HTTP 429 + `Retry-After`) |
| **Enumeração de contas** | Login devolve mensagem genérica e sempre executa a verificação de hash, mesmo com e-mail inexistente |
| **SQL Injection** | 100% das consultas usam o ORM do SQLAlchemy com parâmetros vinculados — não há concatenação de SQL em nenhum ponto |
| **XSS armazenado** | Defesa em profundidade: `bleach` remove tags/atributos/protocolos perigosos na escrita, e `react-markdown` não interpreta HTML bruto na leitura |
| **IDOR** | Toda consulta filtra por `owner_id`; recursos de terceiros retornam **404** (não 403), sem revelar a existência de IDs alheios |
| **CORS** | Origens declaradas explicitamente no `.env` — nunca `*`, já que a API usa credenciais |
| **Clickjacking / MIME sniffing** | `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` e HSTS em produção |
| **Vazamento de detalhes internos** | Erros de banco são registrados no log e devolvem mensagem genérica ao cliente |

---

## 🧠 Como funciona o motor de busca

1. **Cascata de provedores** — a consulta tenta, em ordem: DuckDuckGo HTML → DuckDuckGo
   Lite → Bing → API da Wikipédia. O primeiro que devolver resultados úteis vence, então
   uma mudança de layout ou bloqueio em um provedor não derruba a funcionalidade.
2. **Normalização** — resolve os redirecionamentos do DuckDuckGo, remove parâmetros de
   rastreamento (`utm_*`, `fbclid`…) e descarta o fragmento.
3. **Deduplicação** — por URL canônica, com no máximo 2 links por domínio para garantir
   diversidade de fontes.
4. **Ranking (0–100)** — soma: posição original no buscador (até 20 pts), aderência dos
   termos no título (30) e no snippet (20), **confiabilidade do domínio** (−35 a +22:
   bônus para `.edu`, `.gov`, SciELO, PubMed, Wikipédia, Khan Academy, Mundo Educação…;
   penalidade para redes sociais, agregadores e e-commerce) e qualidade do snippet (8).
5. **Cache TTL** em memória (15 min) e semáforo de concorrência evitam saturar os
   provedores.

O parâmetro opcional `subject_hint` acrescenta o nome da matéria à consulta para
desambiguar termos genéricos — *"célula"* em Biologia é diferente de *"célula"* em Química.

---

## ⏰ Como funcionam os lembretes

Ao criar uma sessão, o backend materializa a coluna indexada
`remind_at = start_at − remind_minutes`. O APScheduler varre a cada 30 segundos as
sessões pendentes cujo `remind_at` já venceu (índice `ix_schedules_reminder_scan`),
grava uma `Notification` e a empurra pelo WebSocket.

Por que polling e não um job por agendamento? Um job por sessão exigiria reconstruir todos
os jobs a cada reinício e sincronizá-los em cada edição. A varredura por índice custa
microssegundos e é resiliente: um lembrete perdido enquanto o servidor estava fora ainda
dispara, desde que dentro da janela de tolerância (`REMINDER_GRACE_MINUTES`).

Se o usuário estiver offline no momento do disparo, a notificação continua persistida e
aparece no sino assim que ele voltar.

---

## 🗄️ Modelo de dados

```
User ──┬─< Subject ──┬─< Note ──┬──< SearchResult
       │             │          └──> Tag (N:N via note_tags)
       │             └─< Schedule ─< SearchResult
       ├─< Notification
       └─< RefreshToken
```

Todas as chaves estrangeiras usam `ON DELETE CASCADE` (com `PRAGMA foreign_keys=ON`
habilitado na conexão), então excluir uma matéria remove suas anotações, sessões e links.

**Datas:** persistidas e trafegadas sempre em **UTC**. Um `TypeDecorator`
(`app/db/base.py`) reanexa o fuso na leitura — sem ele, o SQLite devolveria datetimes
ingênuos e o navegador os interpretaria como horário local, deslocando todos os horários.

---

## 🛠️ Comandos úteis

```bash
# Backend (dentro de backend/, com o venv ativo)
python run.py --port 9000 --host 0.0.0.0   # outra porta / acessível na rede
python -m app.seed                          # repopula os dados de demonstração
alembic revision --autogenerate -m "msg"    # nova migration após alterar os modelos
alembic upgrade head                        # aplica as migrations pendentes
alembic downgrade -1                        # reverte uma revisão

# Frontend (dentro de frontend/)
npm run dev        # servidor de desenvolvimento
npm run build      # build de produção em dist/
npm run preview    # serve o build localmente
```

---

## 🐛 Solução de problemas

| Sintoma | Causa provável e correção |
|---|---|
| `Não foi possível falar com o servidor` | O backend não está rodando. Suba-o com `python run.py` em `backend/`. |
| Sino mostra **"Reconectando…"** | O WebSocket caiu (backend reiniciado). Ele reconecta sozinho com backoff exponencial; confirme em http://localhost:8000/health. |
| Busca retorna **503** | Sem acesso à internet ou todos os provedores bloquearam a requisição. Verifique a conexão e tente novamente. |
| Todos os tokens caem após reiniciar o backend | `SECRET_KEY` vazia no `.env` — uma chave temporária é gerada a cada boot. Defina uma chave fixa. |
| `no such table: users` | Banco não inicializado. Rode `alembic upgrade head` em `backend/`. |
| Lembretes não disparam | O agendador não subiu. Cheque `scheduler_running` em `/health` e evite `--reload` em produção (ele duplicaria o processo e o agendador). |
| Porta 5173 ou 8000 ocupada | Use `python run.py --port 9000` ou ajuste `server.port` em `frontend/vite.config.js`. |

---

## 📦 Stack

**Backend** — FastAPI · Uvicorn · SQLAlchemy 2.0 · Alembic · SQLite · Pydantic v2 ·
PyJWT · bcrypt · bleach · APScheduler · httpx · BeautifulSoup4

**Frontend** — React 19 · Vite 7 · Tailwind CSS 4 · React Router 7 · Axios ·
react-markdown + remark-gfm · date-fns · lucide-react

---

## 📄 Licença

MIT
