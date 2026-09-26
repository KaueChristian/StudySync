/**
 * Cliente HTTP central da aplicação.
 *
 * Responsabilidades:
 *   - anexar o access token em toda requisição;
 *   - renovar o token automaticamente ao receber 401, enfileirando as
 *     requisições concorrentes para que apenas UMA renovação aconteça;
 *   - normalizar as mensagens de erro para exibição direta na interface.
 */
import axios from 'axios'

import { IS_DESKTOP, requestLocalSession } from './desktop'

const ACCESS_KEY = 'studysync:access_token'
const REFRESH_KEY = 'studysync:refresh_token'

/** Base da API: usa VITE_API_URL quando definido, senão o proxy do Vite. */
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export const apiUrl = (path = '') => `${API_BASE}/api${path}`

/** Retorna a URL absoluta completa (essencial para feeds públicos como o link .ics). */
export const absoluteApiUrl = (path = '') => {
  const url = apiUrl(path)
  if (/^https?:\/\//i.test(url)) return url
  const origin = typeof window !== 'undefined' && window.location?.origin ? window.location.origin : ''
  return `${origin}${url}`
}

// ---------------------------------------------------------------------------
// Armazenamento dos tokens
// ---------------------------------------------------------------------------
export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  save({ access_token, refresh_token }) {
    if (access_token) localStorage.setItem(ACCESS_KEY, access_token)
    if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

// ---------------------------------------------------------------------------
// Instância axios
// ---------------------------------------------------------------------------
const api = axios.create({
  baseURL: apiUrl(),
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = tokenStore.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ---------------------------------------------------------------------------
// Renovação automática do token
// ---------------------------------------------------------------------------
let refreshing = null
/** Callback disparado quando a sessão é definitivamente perdida. */
let onSessionExpired = () => {}

export function setSessionExpiredHandler(handler) {
  onSessionExpired = handler
}

async function renewWithRefreshToken() {
  const refreshToken = tokenStore.refresh
  if (!refreshToken) throw new Error('Sem refresh token.')

  // Cliente separado: evita que este POST passe pelos interceptors e
  // dispare um loop infinito de renovação.
  const { data } = await axios.post(
    apiUrl('/auth/refresh'),
    { refresh_token: refreshToken },
    { headers: { 'Content-Type': 'application/json' }, timeout: 15000 },
  )
  tokenStore.save(data)
  return data.access_token
}

async function refreshAccessToken() {
  try {
    return await renewWithRefreshToken()
  } catch (error) {
    // No desktop não há login para onde mandar o usuário: a ponte emite uma
    // sessão nova (refresh vencido, ou porta diferente com localStorage vazio).
    if (!IS_DESKTOP) throw error
    const data = await requestLocalSession()
    tokenStore.save(data)
    return data.access_token
  }
}

/**
 * Uma renovação por vez para o app inteiro: duas em paralelo reapresentariam
 * o mesmo refresh token, e o backend trata isso como roubo (derruba todas as
 * sessões).
 */
function sharedRefresh() {
  refreshing =
    refreshing ||
    refreshAccessToken().finally(() => {
      refreshing = null
    })
  return refreshing
}

function expireSession() {
  tokenStore.clear()
  onSessionExpired()
}

/**
 * O servidor recusou o refresh (vencido, revogado, conta desativada)? Só
 * isso encerra a sessão. Falha de rede ou 5xx — backend reiniciando, proxy
 * sem upstream — é indisponibilidade: deslogar aí jogaria o usuário na tela
 * de login toda vez que o servidor piscasse.
 */
export function isSessionRejected(error) {
  return axios.isAxiosError(error) && [401, 403].includes(error.response?.status)
}

/** O access token vence em até `marginMs`? Token ilegível conta como vencido. */
function isExpiring(token, marginMs = 60_000) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return !payload.exp || payload.exp * 1000 - marginMs < Date.now()
  } catch {
    return true
  }
}

/**
 * Access token válido para quem não passa pelo axios — o WebSocket, que só
 * apresenta o token na conexão. Sem isso, um socket que cai depois de 30 min
 * (notebook suspenso, servidor reiniciado) tentaria reconectar com o token
 * vencido para sempre.
 *
 * Servidor indisponível só propaga o erro, para tentar de novo depois;
 * refresh recusado encerra a sessão, como no axios.
 */
export async function getFreshAccessToken() {
  const token = tokenStore.access
  if (token && !isExpiring(token)) return token
  try {
    return await sharedRefresh()
  } catch (error) {
    if (isSessionRejected(error)) expireSession()
    throw error
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error

    const canRetry =
      response?.status === 401 &&
      config &&
      !config._retried &&
      !config.url?.includes('/auth/login') &&
      !config.url?.includes('/auth/register') &&
      !config.url?.includes('/auth/refresh')

    if (canRetry) {
      config._retried = true
      let token
      try {
        token = await sharedRefresh()
      } catch (refreshError) {
        if (!isSessionRejected(refreshError)) {
          // Servidor indisponível: quem chamou vê a causa real, não o 401.
          return Promise.reject(refreshError)
        }
        expireSession()
        return Promise.reject(error)
      }
      config.headers.Authorization = `Bearer ${token}`
      return api(config)
    }

    return Promise.reject(error)
  },
)

// ---------------------------------------------------------------------------
// Erros
// ---------------------------------------------------------------------------
/**
 * Extrai uma mensagem legível de qualquer erro vindo da API.
 * @param {unknown} error
 * @param {string} fallback
 * @returns {string}
 */
export function getErrorMessage(error, fallback = 'Algo deu errado. Tente novamente.') {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNABORTED') return 'A requisição demorou demais. Tente novamente.'
    if (!error.response) {
      return IS_DESKTOP
        ? 'Não foi possível falar com o StudySync. Feche e abra o app novamente.'
        : 'Não foi possível falar com o servidor. Ele está rodando em http://localhost:8000?'
    }

    const data = error.response.data
    if (typeof data?.detail === 'string') return data.detail
    if (Array.isArray(data?.errors) && data.errors.length) return data.errors[0].message
    if (Array.isArray(data?.detail) && data.detail.length) {
      return data.detail[0]?.msg ?? fallback
    }

    if (error.response.status === 429) return 'Muitas tentativas. Aguarde um instante.'
    if (error.response.status >= 500) return 'Erro no servidor. Tente novamente em instantes.'
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}

export default api
