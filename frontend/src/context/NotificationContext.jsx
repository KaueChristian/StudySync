/**
 * Notificações em tempo real via WebSocket.
 *
 * Mantém a lista de avisos, o contador de não lidas e a conexão persistente
 * com o backend. Ao receber um lembrete:
 *   1. adiciona à lista (badge do sino);
 *   2. exibe um toast;
 *   3. dispara uma notificação nativa do sistema, se autorizada.
 *
 * A conexão reconecta sozinha com backoff exponencial e um heartbeat de 25s
 * mantém proxies intermediários de fecharem o socket por inatividade.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

import { tokenStore } from '@/lib/api'
import { notificationService } from '@/lib/services'
import { useAuth } from './AuthContext'
import { useToast } from './ToastContext'

const NotificationContext = createContext(null)

const HEARTBEAT_MS = 25_000
const MAX_RECONNECT_DELAY = 30_000

/** Monta a URL do WebSocket a partir do ambiente ou da origem atual. */
function buildSocketUrl(token) {
  const explicit = import.meta.env.VITE_WS_URL
  if (explicit) return `${explicit}?token=${encodeURIComponent(token)}`

  const apiBase = import.meta.env.VITE_API_URL
  const origin = apiBase || window.location.origin
  const wsOrigin = origin.replace(/^http/, 'ws').replace(/\/$/, '')
  return `${wsOrigin}/api/ws/notifications?token=${encodeURIComponent(token)}`
}

export function NotificationProvider({ children }) {
  const { isAuthenticated } = useAuth()
  const toast = useToast()

  const [items, setItems] = useState([])
  const [unread, setUnread] = useState(0)
  const [connected, setConnected] = useState(false)

  const socketRef = useRef(null)
  const heartbeatRef = useRef(null)
  const reconnectRef = useRef(null)
  const attemptsRef = useRef(0)
  // Evita que o efeito de conexão seja reexecutado a cada novo toast.
  const toastRef = useRef(toast)
  toastRef.current = toast

  // -------------------------------------------------------- carga inicial
  const refresh = useCallback(async () => {
    try {
      const data = await notificationService.list({ limit: 30 })
      setItems(data.items)
      setUnread(data.unread)
    } catch {
      // Silencioso: o sino simplesmente fica vazio se a API falhar.
    }
  }, [])

  useEffect(() => {
    if (!isAuthenticated) {
      setItems([])
      setUnread(0)
      return
    }
    refresh()
  }, [isAuthenticated, refresh])

  // -------------------------------------------------- notificação nativa
  const requestPermission = useCallback(async () => {
    if (!('Notification' in window)) return 'unsupported'
    if (Notification.permission !== 'default') return Notification.permission
    return Notification.requestPermission()
  }, [])

  const showNativeNotification = useCallback((notification) => {
    if (!('Notification' in window) || Notification.permission !== 'granted') return
    try {
      const native = new Notification(notification.title, {
        body: notification.message ?? '',
        tag: `studysync-${notification.id}`,
        icon: '/vite.svg',
      })
      native.onclick = () => {
        window.focus()
        native.close()
      }
    } catch {
      // Alguns navegadores bloqueiam o construtor fora de um service worker.
    }
  }, [])

  // ------------------------------------------------- recepção de mensagem
  const handleIncoming = useCallback(
    (notification) => {
      setItems((current) => {
        if (current.some((item) => item.id === notification.id)) return current
        return [notification, ...current].slice(0, 50)
      })
      setUnread((count) => count + 1)

      toastRef.current.reminder(notification.title, {
        description: notification.message,
      })
      showNativeNotification(notification)
    },
    [showNativeNotification],
  )

  // -------------------------------------------------------- ciclo do socket
  useEffect(() => {
    if (!isAuthenticated) return undefined

    let disposed = false

    const clearTimers = () => {
      if (heartbeatRef.current) clearInterval(heartbeatRef.current)
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      heartbeatRef.current = null
      reconnectRef.current = null
    }

    const connect = () => {
      if (disposed) return

      const token = tokenStore.access
      if (!token) return

      let socket
      try {
        socket = new WebSocket(buildSocketUrl(token))
      } catch {
        scheduleReconnect()
        return
      }
      socketRef.current = socket

      socket.onopen = () => {
        if (disposed) return
        setConnected(true)
        attemptsRef.current = 0

        heartbeatRef.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ event: 'ping' }))
          }
        }, HEARTBEAT_MS)
      }

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data)
          if (payload.event === 'notification') handleIncoming(payload.data)
        } catch {
          // Mensagem malformada é ignorada.
        }
      }

      socket.onclose = () => {
        if (disposed) return
        setConnected(false)
        clearTimers()
        scheduleReconnect()
      }

      socket.onerror = () => {
        // `onclose` sempre dispara em seguida e cuida da reconexão.
        socket.close()
      }
    }

    const scheduleReconnect = () => {
      if (disposed) return
      attemptsRef.current += 1
      // Backoff exponencial com teto: 1s, 2s, 4s, 8s… até 30s.
      const delay = Math.min(1000 * 2 ** (attemptsRef.current - 1), MAX_RECONNECT_DELAY)
      reconnectRef.current = setTimeout(connect, delay)
    }

    connect()

    return () => {
      disposed = true
      clearTimers()
      setConnected(false)
      const socket = socketRef.current
      if (socket && socket.readyState <= WebSocket.OPEN) {
        socket.onclose = null // impede o agendamento de reconexão na desmontagem
        socket.close(1000, 'Componente desmontado')
      }
      socketRef.current = null
    }
  }, [isAuthenticated, handleIncoming])

  // ------------------------------------------------------------- ações
  // Referência estável para `refresh`, usada como fallback quando uma
  // atualização otimista falha e o estado precisa ser ressincronizado.
  const refreshRef = useRef(refresh)
  refreshRef.current = refresh

  const markAsRead = useCallback(async (id) => {
    setItems((current) =>
      current.map((item) => (item.id === id ? { ...item, is_read: true } : item)),
    )
    setUnread((count) => Math.max(0, count - 1))
    try {
      await notificationService.markRead(id)
    } catch {
      refreshRef.current?.()
    }
  }, [])

  const markAllAsRead = useCallback(async () => {
    setItems((current) => current.map((item) => ({ ...item, is_read: true })))
    setUnread(0)
    try {
      await notificationService.markAllRead()
    } catch {
      refreshRef.current?.()
    }
  }, [])

  const clearRead = useCallback(async () => {
    setItems((current) => current.filter((item) => !item.is_read))
    try {
      await notificationService.clearRead()
    } catch {
      refreshRef.current?.()
    }
  }, [])

  const value = useMemo(
    () => ({
      items,
      unread,
      connected,
      refresh,
      markAsRead,
      markAllAsRead,
      clearRead,
      requestPermission,
      nativePermission:
        typeof Notification !== 'undefined' ? Notification.permission : 'unsupported',
    }),
    [items, unread, connected, refresh, markAsRead, markAllAsRead, clearRead, requestPermission],
  )

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>
}

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications precisa estar dentro de <NotificationProvider>.')
  }
  return context
}
