# Instruções para o Claude Code neste repositório

**Leia `context_project.md` inteiro antes de qualquer trabalho neste projeto.** Ele é a fonte
única de verdade sobre o que o StudySync é, o que já está implementado (com evidência de
teste real, não suposição), e o que falta ou está deliberadamente pendente. Este arquivo aqui
só existe porque o Claude Code lê `CLAUDE.md` automaticamente — todo o conteúdo real está em
`context_project.md`, não duplique nada aqui.

Antes de declarar qualquer mudança como concluída, siga `VALIDATION_PROTOCOL.md` — ele também
define como o agente deve se comportar neste projeto (quando pedir confirmação antes de agir,
quando registrar um achado fora de escopo, etc.), não só o checklist de teste.

**Regra que não é opcional:** ao terminar qualquer mudança de código relevante, atualize
`context_project.md` (status em §3, decisão em §7 se for arquitetural/de design, entrada em
§8) na mesma sessão. Este projeto é desenvolvido em sessões distintas com mais de uma
ferramenta de IA — um documento de contexto desatualizado engana a próxima sessão, humana ou
não.
