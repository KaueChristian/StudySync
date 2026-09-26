# Marca do StudySync

<img src="studysync-icon.svg" width="96" alt="Ícone do StudySync">

Monograma **S** desenhado numa grade de 32 unidades com traço de 4. O bojo de cima é
curvo: é o ciclo de foco (Pomodoro). O de baixo é reto: é a célula da agenda. Numa letra só
estão as duas coisas que o app junta, a sessão agendada e o tempo de foco dentro dela. O
desenho segue a mesma "linguagem de caderno" do resto da interface: geometria reta, cantos de
1–6 px, sem gradiente nem sombra.

Os três conceitos avaliados antes deste estão registrados em `context_project.md` §7
(2026-09-25).

## Arquivos

| Arquivo | Uso |
|---|---|
| `studysync-icon.svg` | Ícone do app: S em papel sobre o bloco verde-tinta |
| `studysync-mark.svg` | Só o S, em tinta — para fundos claros sem o bloco |
| `build.py` | Gera tudo a partir de uma única geometria (ver abaixo) |

Gerados por `build.py` fora desta pasta: `frontend/public/favicon.svg`, `favicon.ico`,
`icon-192.png` (ícone das notificações) e `desktop/StudySync.ico` (o `.exe`, a janela e o
instalador). Na interface, o logo é o componente `BrandIcon` / `BrandMark` em
`frontend/src/components/ui/Brand.jsx`.

```bash
backend/venv/Scripts/python.exe brand/build.py
```

Só biblioteca padrão. Rode de novo apenas se a geometria ou as cores mudarem, e mude o
contorno em `Brand.jsx` junto.

## Cores

| Nome | Hex | Token |
|---|---|---|
| Verde-tinta (bloco) | `#3a6334` | `--color-brand-600` |
| Papel (o S sobre o bloco) | `#fffdf8` | `--color-paper` |
| Tinta (o S sozinho) | `#2b2420` | `--text` do tema claro |

Sobre fundo verde (o painel da tela de login), use a versão invertida: bloco em papel e S em
verde (`<BrandIcon inverse />`).

## Regras

- **Monocromia primeiro.** O S funciona em uma cor só, sem gradiente, sombra ou contorno
  extra. Não adicione nenhum deles.
- **Tamanho mínimo: 16 px.** Nesse tamanho, 1 unidade da grade é meio pixel, e todas as
  bordas retas caem em pixel inteiro. Por isso os terminais param em x=24 e x=8. Não mova
  esses pontos sem conferir o ícone a 16 px.
- **O bloco é quadrado.** Cantos de 2 px na interface (`rounded-md`) e 1,5 de 32 unidades no
  ícone. Nada de círculo nem de "squircle".
- **Nome ao lado, nunca embaixo.** "StudySync" em Fraunces 600, alinhado ao centro do
  bloco, com espaço de ~¼ do bloco entre os dois.
