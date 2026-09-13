## Download (Windows 10/11, 64 bits)

| Arquivo | Para quem |
|---|---|
| `StudySync-Setup-<versão>.exe` | **Recomendado.** Instala para o seu usuário (sem pedir administrador), cria atalho no Menu Iniciar e desinstalador. |
| `StudySync-<versão>-win64.zip` | Versão portátil: extraia a pasta `StudySync` inteira e abra `StudySync.exe` de dentro dela. |

**Aviso do Windows ("O Windows protegeu o computador"):** o executável ainda não tem
assinatura digital, então o SmartScreen avisa na primeira execução. Clique em
**Mais informações → Executar assim mesmo**. Para conferir que o arquivo é o mesmo gerado
pelo GitHub Actions a partir do código deste repositório, compare o hash com o
`SHA256SUMS.txt` (`Get-FileHash .\arquivo -Algorithm SHA256` no PowerShell).

- Não precisa de conta nem login — o app é local e de um usuário só.
- Seus dados ficam em `%LOCALAPPDATA%\StudySync` e são mantidos ao atualizar ou desinstalar.
- Requer o WebView2 Runtime (já vem no Windows 11 e na maioria das instalações do Windows 10).
- A busca de conteúdo de apoio usa a internet; o restante funciona offline.
