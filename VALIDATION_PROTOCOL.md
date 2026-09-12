# Protocolo de Validação e Comportamento — StudySync

> Referenciado por [context_project.md](context_project.md) (§5, roadmap, e regra de
> manutenção no topo). Tool-agnostic — vale para qualquer agente de IA (Claude ou outro) ou
> pessoa que declare um item concluído no projeto.
>
> Este documento responde a duas perguntas: **como o agente deve se comportar** neste projeto
> (§1) e **o que fazer, passo a passo, antes de considerar qualquer mudança validada** (§2 em
> diante).

---

## 1. Como o agente deve agir neste projeto

1. **Leia [context_project.md](context_project.md) inteiro antes de tocar em qualquer
   código.** Ele é a fonte única de verdade sobre o que já existe, o que já foi corrigido, e
   o que está deliberadamente pendente (ex.: logo/imagens — adiado pelo próprio autor, não
   retomar sem sinal verde explícito).
2. **Não confie em revisão estática para declarar algo correto.** Este projeto já teve um
   caso concreto e documentado (`context_project.md` §3, "bug do Bing") de um defeito que
   passava por leitura de código, mas quebrava sempre que executado contra os provedores
   reais. Se a mudança toca `scraper.py`, agendamento/recorrência, ou qualquer lógica com
   estado (WebSocket, cache, disjuntor de circuito), **rodar de verdade é obrigatório**, não
   opcional — ver §3.
3. **Ações destrutivas ou estruturais (git, banco de dados, remoção de arquivo) pedem
   confirmação antes, mesmo que pareçam óbvias.** Precedente real: a reestruturação do
   repositório Git (`port/.git` → `StudySync/.git` próprio) só aconteceu depois de confirmar
   explicitamente com o autor que a estrutura anterior era, de fato, um erro — não foi
   assumido de antemão. O mesmo vale para: apagar dados de teste, resetar o banco SQLite,
   forçar push, ou remover uma feature que já está em uso.
4. **Ao terminar qualquer mudança de código relevante, atualize `context_project.md`**
   (status em §3, decisão em §7 se foi uma escolha de arquitetura/design, entrada em §8) **na
   mesma sessão**, antes de encerrar. Isso vale mesmo que a mudança pareça pequena — foi
   assim que o "bug lateral" da Wikipédia (achado ao corrigir o Bing) quase passou
   despercebido: registre também o que apareceu no caminho, não só o que foi pedido
   originalmente.
5. **Prefira o token/padrão central já estabelecido a uma correção pontual espalhada.** O
   projeto usa tokens de tema centralizados (`index.css`) precisamente para que uma mudança
   de identidade visual (cor, raio de borda) seja uma edição em um lugar, não em dezenas de
   componentes — foi assim que a correção do raio de borda (`context_project.md` §7,
   2026-09-01) se propagou para o app inteiro numa única mudança. Ao adicionar um componente
   novo, siga esse padrão em vez de introduzir cor/raio fixo.
6. **Quando encontrar algo quebrado fora do escopo pedido, não ignore.** Registre em
   `context_project.md` §3/§6 mesmo que não vá ser corrigido na hora — um "achado fora de
   escopo não registrado" é exatamente o tipo de lacuna que este documento existe para
   fechar.

---

## 2. Princípio central da validação

**Revisão estática de código nunca é suficiente para declarar algo concluído neste
projeto.** Motivo documentado (`context_project.md` §3): a correção do motor de busca
(2026-09-01) envolvia três defeitos — o redirecionador de clique do Bing, o desafio 202 do
DuckDuckGo, e o 403 da Wikipédia por cabeçalho incoerente — e **nenhum dos três seria
detectável lendo o código**. Os três só apareceram chamando os provedores de verdade e
inspecionando a URL/status/corpo da resposta real. **Toda mudança em lógica de negócio (busca,
agendamento/recorrência, lembretes, auth) exige pelo menos um teste de execução real** — sem
mock do provedor externo quando a mudança é justamente sobre como o provedor externo se
comporta.

**Corolário sobre o próprio ambiente de teste:** ferramentas de inspeção de processo podem
mentir. Durante a validação de 2026-09-01, `Get-Process`/`taskkill` (PowerShell) e `wmic`
afirmaram consistentemente que um PID não existia, enquanto `Get-NetTCPConnection` e uma
chamada `curl` real confirmavam que a porta seguia respondendo — o processo era real, só
invisível para aquelas ferramentas específicas (raiz provável: namespace de processo diferente
do namespace de rede num ambiente de execução em sandbox/contêiner). **Não conclua "o servidor
parou" só porque uma ferramenta de processo não o encontra** — confirme sempre com uma
chamada real (`curl`/requisição HTTP) contra a porta em questão.

---

## 3. Checklist obrigatório, em ordem

Aplicar todos os passos relevantes para o tipo de mudança — nem toda mudança passa por todos
(ver §4).

### 3.1 Verificação estática
- [ ] O backend importa sem erro (`python -c "import app.main"` dentro do venv) e o frontend
      builda ou ao menos não quebra o dev server (`npm run dev` sobe sem erro no console).
- [ ] Nenhum import quebrado, nenhuma referência a função/variável removida.
- [ ] Se a mudança remove um comportamento (ex.: um cabeçalho, uma validação), confirmar via
      `grep` que ele de fato não existe mais no arquivo final — não confiar só na memória do
      diff aplicado.

### 3.2 Regressão
- [ ] **Não existe suíte automatizada de testes neste projeto ainda** (débito registrado em
      `context_project.md` §6). Na ausência dela, rodar manualmente o roteiro mínimo de fumaça
      abaixo sempre que a mudança tocar código compartilhado (auth, layout, contexto React,
      `api.js`):
      1. Login com a conta demo.
      2. Criar uma matéria.
      3. Criar uma sessão de estudo com lembrete ativado.
      4. Rodar uma busca de conteúdo e salvar um link.
      5. Marcar a sessão como concluída.
      6. Alternar tema claro/escuro.
- [ ] Se a mudança adiciona lógica nova sem cobertura nenhuma (ex.: uma nova heurística de
      ranking, uma nova regra de recorrência), considerar se vale a pena começar a suíte
      automatizada agora em vez de adiar de novo — mas isso é uma decisão a registrar em
      `context_project.md` §7, não a fazer silenciosamente.

### 3.3 Execução real — o passo que não pode ser pulado
- [ ] Backend subido de verdade (`python run.py`), não só importado em processo; frontend
      subido de verdade (`npm run dev`) quando a mudança é visível na UI.
- [ ] **Mudança em `scraper.py`:** chamar os provedores diretamente contra a internet real
      (como em `context_project.md` §3) — imprimir a URL final de cada resultado bruto antes
      do ranking, não só a contagem. Um mock do HTML de um provedor não teria pego nenhum dos
      três bugs de 2026-09-01, porque os três eram sobre *o que o provedor real de fato
      devolve agora*, não sobre a lógica de parsing em si.
- [ ] **Mudança em agendamento/recorrência/lembrete:** criar uma sessão real via API (ou UI),
      conferir o `remind_at` calculado, e — se a mudança afeta o agendador — aguardar o
      intervalo de varredura (`REMINDER_POLL_SECONDS`) e confirmar que a notificação chega de
      fato pelo WebSocket, não só que o registro foi criado no banco.
- [ ] **Mudança visual/tema:** abrir de verdade no navegador (claro e escuro), não confiar só
      na leitura do CSS — tokens compostos (`bg-brand-500/12`, sombras coloridas) podem
      parecer corretos no código e ainda assim ficarem ilegíveis/quebrados quando renderizados.
- [ ] Ler a resposta/tela real, não assumir que "não deu erro" = "está correto". Para o motor
      de busca especificamente: inspecionar a URL final de cada link (não só o título/score),
      já que o próprio bug corrigido em 2026-09-01 produzia respostas com título e snippet
      perfeitamente normais — só a URL estava errada.

### 3.4 Caminho feliz **e** caminho de falha
- [ ] Um cenário onde a mudança deveria funcionar. Exemplos já usados neste projeto: busca
      retornando 5 links reais; sessão recorrente criando as instâncias semanais esperadas.
- [ ] Um cenário onde o sistema deveria degradar graciosamente, não quebrar. Exemplos já
      comprovados neste projeto: **todos** os provedores de busca bloqueados ao mesmo tempo →
      o disjuntor de circuito pula os bloqueados e a Wikipédia ainda responde com links reais
      (validado ao vivo em 2026-09-01, não é hipotético); requisição sem token/cookie válido
      → 401, não 500; sessão sem matéria vinculada → busca de conteúdo ainda funciona sem
      `subject_hint`.

### 3.5 Limpeza
- [ ] Remover dados de teste criados durante a validação (matérias/sessões/anotações de teste
      no `studysync.db`, se a validação rodou contra o banco de desenvolvimento em vez de um
      descartável).
- [ ] Parar servidores de preview que não devem continuar rodando. **Atenção ao Windows:**
      confirmar de verdade que a porta foi liberada com uma nova tentativa de conexão
      (`curl`/`Get-NetTCPConnection`), não só que o comando de kill "teve sucesso" — ver o
      corolário em §2. Se o processo resistir a `Stop-Process`/`taskkill`/WMI simultaneamente,
      é provável que ele esteja fora do namespace de processo acessível à sessão atual; não
      vale insistir indefinidamente — documentar o impasse e seguir.

### 3.6 Atualização de documentação
- [ ] Atualizar `context_project.md` §3 (status do item), §7 (log de decisões, se foi
      escolha de arquitetura/design) e §8 (changelog) — no mesmo momento em que a mudança é
      fechada, não depois.

---

## 4. Checklist por tipo de mudança

| Tipo de mudança | Passos obrigatórios além do básico (3.1–3.2) |
|---|---|
| Correção pontual isolada (ex.: bug de scraping, ajuste de badge) | 3.3 (cenário específico do bug, contra dados/provedores reais) + 3.5 |
| Mudança no motor de busca (`scraper.py`: ranking, dedupe, provedores, cabeçalhos) | 3.3 completo contra os 3 provedores reais + 3.4 (incluir o cenário de bloqueio simultâneo) + 3.5 |
| Mudança em agendamento/recorrência/lembrete | 3.3 (criar sessão real + conferir `remind_at`/disparo real) + 3.4 (sessão recorrente: criar, editar uma instância, excluir com cada `scope`) |
| Mudança visual/tema (cores, tipografia, raio de borda) | 3.3 no navegador real, claro **e** escuro + checar pelo menos 3 telas com densidade de UI diferente (uma lista de cards, um modal, uma página com badges) — foi assim que a inconsistência de `rounded-full` nos badges só apareceu depois da correção do token de raio |
| Feature nova (ex.: próxima recorrência avançada, notificação por e-mail) | 3.3 + 3.4 com um cenário sintético onde o resultado correto é conhecido de antemão + decisão de arquitetura registrada em `context_project.md` §7 antes de implementar, não depois |
| Autenticação/segurança/JWT | 3.3 com teste explícito de acesso negado (cookie/token ausente ou inválido → 401), não só o caminho autenticado |
| Estrutura de repositório (git, `.gitignore`, CI) | **Confirmar com o autor antes de executar** (ver §1.3) + `git status`/`git log --all` para levantar o estado atual sem suposição + verificar que nada de outro projeto/pasta irmã foi afetado, se o repositório não for isolado |

---

## 5. Formato de relatório ao encerrar uma sessão

Ao final da validação, reportar (para o autor, e para `context_project.md`):
1. O que foi implementado/corrigido, arquivo por arquivo.
2. Como foi validado — comando/cenário real usado (URL testada, query de busca usada, tela
   aberta no navegador), não "deveria funcionar porque o código está correto".
3. Resultado observado — citar o resultado real (ex.: as 5 URLs devolvidas, o status HTTP
   recebido), não parafrasear.
4. Qualquer coisa nova encontrada durante a validação que não estava no escopo original
   (como o 403 da Wikipédia ao corrigir o Bing) — nunca omitir, mesmo que pareça fora de
   escopo. Registrar em `context_project.md` mesmo que não seja corrigida na hora.
5. Regressões confirmadas ausentes (resultado do roteiro de fumaça em 3.2).
