## Download (Windows 10/11, 64 bits)

| Arquivo | Para quem |
|---|---|
| `StudySync-Setup-<versão>.exe` | **Recomendado.** Instala para o seu usuário (sem pedir administrador), cria atalho no Menu Iniciar e desinstalador. |
| `StudySync-<versão>-win64.zip` | Versão portátil: extraia a pasta `StudySync` inteira e abra `StudySync.exe` de dentro dela. |

### Avisos esperados

O executável ainda **não tem assinatura digital**, então o navegador e o Windows tratam cada
versão nova como "incomum". Não é detecção de vírus — é falta de reputação.

1. **O navegador bloqueia o download** ("pode ser perigoso" / "não é baixado com frequência"):
   - **Edge:** painel de downloads → `…` → **Manter** → **Mostrar mais** → **Manter mesmo assim**.
   - **Chrome:** painel de downloads → **Baixar arquivo suspeito** (ou **Manter** em `chrome://downloads`).
   - **Firefox:** clique no download bloqueado → **Permitir download**.
2. **(Opcional) Confira o arquivo:** no PowerShell,
   `(Get-FileHash .\arquivo -Algorithm SHA256).Hash.ToLower()` tem que ser igual à linha
   correspondente do `SHA256SUMS.txt` abaixo. Os arquivos foram gerados pelo GitHub Actions a
   partir do código deste repositório.
3. **"O Windows protegeu o computador"** ao abrir: **Mais informações → Executar assim mesmo**.

### Bom saber

- Não precisa de conta nem login — o app é local e de um usuário só.
- Seus dados ficam em `%LOCALAPPDATA%\StudySync` e são mantidos ao atualizar ou desinstalar.
- Requer o WebView2 Runtime (já vem no Windows 11 e na maioria das instalações do Windows 10).
- A busca de conteúdo de apoio usa a internet; o restante funciona offline.
