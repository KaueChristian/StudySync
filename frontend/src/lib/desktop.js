/**
 * Integração com o app desktop (pywebview).
 *
 * O build do desktop é marcado com `VITE_DESKTOP=true` (desktop/build.ps1).
 * Nele não existe login: a sessão do usuário local vem da ponte
 * `window.pywebview.api`, injetada pelo launcher logo após a página carregar.
 */

export const IS_DESKTOP = import.meta.env.VITE_DESKTOP === 'true'

const BRIDGE_TIMEOUT_MS = 10_000

function waitForBridge() {
  if (window.pywebview?.api?.local_session) return Promise.resolve(window.pywebview.api)

  return new Promise((resolve, reject) => {
    const onReady = () => {
      clearTimeout(timer)
      resolve(window.pywebview.api)
    }
    const timer = setTimeout(() => {
      window.removeEventListener('pywebviewready', onReady)
      reject(new Error('A ponte do app desktop não respondeu.'))
    }, BRIDGE_TIMEOUT_MS)
    window.addEventListener('pywebviewready', onReady, { once: true })
  })
}

/** Par de tokens + usuário local (mesmo formato da resposta de `/auth/login`). */
export async function requestLocalSession() {
  const bridge = await waitForBridge()
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || null
  return bridge.local_session(timezone)
}
