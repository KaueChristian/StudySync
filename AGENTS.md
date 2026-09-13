# Instruções para agentes de IA neste repositório

> Nota: este arquivo segue a convenção emergente `AGENTS.md`, adotada por várias ferramentas
> agênticas de código. Se a ferramenta que você está usando espera outro nome de arquivo,
> duplique este ponteiro com o nome correto — o conteúdo deve ser idêntico.

**Leia `context_project.md` inteiro antes de qualquer trabalho neste projeto.** É a fonte
única de verdade sobre o que o StudySync é, o que já está implementado (com evidência de
teste real), e o que falta implementar ou está deliberadamente pendente (ex.: logo/imagens —
adiado pelo próprio autor, não retomar sem sinal verde explícito).

Antes de declarar qualquer mudança como concluída, siga o checklist e as diretrizes de
comportamento em `VALIDATION_PROTOCOL.md`. Revisão estática de código não é suficiente neste
projeto — os três bugs mais recentes do motor de busca (`context_project.md` §3) só
apareceram rodando o sistema de verdade contra os provedores reais, nunca por leitura de
código.

**Regra que não é opcional:** ao terminar qualquer mudança de código relevante, atualize
`context_project.md` (status em §3, decisão em §7 se for arquitetural/de design, entrada em
§8) antes de encerrar a sessão. Este projeto é desenvolvido em paralelo por mais de uma
ferramenta de IA — um documento de contexto desatualizado engana a próxima sessão que ler.
