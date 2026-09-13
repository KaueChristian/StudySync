/**
 * Estado global de autenticação.
 *
 * Mantém o usuário atual, expõe as ações de login/cadastro/logout e restaura
 * a sessão ao recarregar a página (validando o token contra `/auth/me`).
 * No app desktop não há login: sem token, a sessão vem da ponte do pywebview.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { getErrorMessage, setSessionExpiredHandler, tokenStore } from '@/lib/api'
import { IS_DESKTOP, requestLocalSession } from '@/lib/desktop'
import { authService } from '@/lib/services'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // `loading` cobre apenas a restauração inicial da sessão — enquanto for
  // true, as rotas protegidas exibem o splash em vez de redirecionar ao login.
  const [loading, setLoading] = useState(true)
  const [sessionExpired, setSessionExpired] = useState(false)

  // ------------------------------------------------------------- restauração
  useEffect(() => {
    let active = true

    async function restore() {
      try {
        if (tokenStore.access) {
          // Com token vencido, o interceptor renova (no desktop, até pela ponte).
          const profile = await authService.me()
          if (active) setUser(profile)
        } else if (IS_DESKTOP) {
          const data = await requestLocalSession()
          tokenStore.save(data)
          if (active) setUser(data.user)
        }
      } catch {
        // O interceptor já tentou renovar; chegar aqui significa sessão morta.
        tokenStore.clear()
      } finally {
        if (active) setLoading(false)
      }
    }

    restore()
    return () => {
      active = false
    }
  }, [])

  // Reage à expiração detectada pelo interceptor do axios.
  useEffect(() => {
    setSessionExpiredHandler(() => {
      setUser(null)
      setSessionExpired(true)
    })
  }, [])

  // Mantém as abas sincronizadas: sair em uma desloga as demais.
  useEffect(() => {
    function onStorage(event) {
      if (event.key === 'studysync:access_token' && !event.newValue) setUser(null)
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  // ----------------------------------------------------------------- ações
  const login = useCallback(async (credentials) => {
    const data = await authService.login(credentials)
    tokenStore.save(data)
    setUser(data.user)
    setSessionExpired(false)
    return data.user
  }, [])

  const register = useCallback(async (payload) => {
    const data = await authService.register({
      ...payload,
      // Envia o fuso do navegador para humanizar as mensagens de lembrete.
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/Sao_Paulo',
    })
    tokenStore.save(data)
    setUser(data.user)
    setSessionExpired(false)
    return data.user
  }, [])

  const logout = useCallback(async () => {
    const refresh = tokenStore.refresh
    try {
      if (refresh) await authService.logout(refresh)
    } catch {
      // Falha de rede não deve impedir o logout local.
    } finally {
      tokenStore.clear()
      setUser(null)
      setSessionExpired(false)
    }
  }, [])

  const updateProfile = useCallback(async (payload) => {
    const updated = await authService.updateProfile(payload)
    setUser(updated)
    return updated
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      sessionExpired,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      updateProfile,
      getErrorMessage,
    }),
    [user, loading, sessionExpired, login, register, logout, updateProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth precisa estar dentro de <AuthProvider>.')
  return context
}
