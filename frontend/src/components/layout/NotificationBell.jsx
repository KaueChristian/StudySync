/** Sino de notificações com contador e painel suspenso. */
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, BellOff, CheckCheck, Trash2, Wifi, WifiOff } from 'lucide-react'

import { useNotifications } from '@/context/NotificationContext'
import { formatRelative } from '@/lib/format'
import Button from '@/components/ui/Button'

export default function NotificationBell() {
  const { items, unread, connected, markAsRead, markAllAsRead, clearRead, requestPermission, nativePermission } =
    useNotifications()
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)
  const navigate = useNavigate()

  // Fecha ao clicar fora ou pressionar Esc.
  useEffect(() => {
    if (!open) return undefined

    const onPointerDown = (event) => {
      if (!containerRef.current?.contains(event.target)) setOpen(false)
    }
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setOpen(false)
    }

    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  const handleClick = (notification) => {
    if (!notification.is_read) markAsRead(notification.id)
    if (notification.schedule_id) {
      navigate(`/agenda?sessao=${notification.schedule_id}`)
      setOpen(false)
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label={`Notificações${unread ? ` (${unread} não lidas)` : ''}`}
        aria-expanded={open}
        className="relative rounded-xl p-2.5 text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
      >
        <Bell className="h-5 w-5" aria-hidden />
        {unread > 0 && (
          <span className="absolute top-1.5 right-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white ring-2 ring-[var(--surface)]">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="card animate-scale-in absolute right-0 z-50 mt-2 flex max-h-[70vh] w-[min(22rem,calc(100vw-2rem))] origin-top-right flex-col shadow-xl">
          <header className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <div>
              <h2 className="text-sm font-semibold">Notificações</h2>
              <p
                className="text-subtle mt-0.5 flex items-center gap-1 text-[11px]"
                title={connected ? 'Recebendo lembretes em tempo real' : 'Reconectando…'}
              >
                {connected ? (
                  <>
                    <Wifi className="h-3 w-3 text-emerald-500" aria-hidden /> Tempo real ativo
                  </>
                ) : (
                  <>
                    <WifiOff className="h-3 w-3 text-amber-500" aria-hidden /> Reconectando…
                  </>
                )}
              </p>
            </div>

            {items.length > 0 && (
              <div className="flex gap-1">
                {unread > 0 && (
                  <button
                    type="button"
                    onClick={markAllAsRead}
                    title="Marcar todas como lidas"
                    className="text-subtle hover:text-[var(--text)] rounded-lg p-1.5 hover:bg-[var(--surface-hover)]"
                  >
                    <CheckCheck className="h-4 w-4" />
                  </button>
                )}
                <button
                  type="button"
                  onClick={clearRead}
                  title="Limpar as lidas"
                  className="text-subtle rounded-lg p-1.5 hover:bg-[var(--surface-hover)] hover:text-red-500"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            )}
          </header>

          {nativePermission === 'default' && (
            <div className="border-b border-[var(--border)] bg-[var(--surface-sunken)] px-4 py-3">
              <p className="text-muted text-xs leading-relaxed">
                Ative as notificações do sistema para receber lembretes mesmo com a aba em
                segundo plano.
              </p>
              <Button size="xs" className="mt-2" onClick={requestPermission}>
                Ativar notificações
              </Button>
            </div>
          )}

          <div className="min-h-0 flex-1 overflow-y-auto">
            {items.length === 0 ? (
              <div className="flex flex-col items-center gap-2 px-4 py-10 text-center">
                <BellOff className="text-subtle h-7 w-7" aria-hidden />
                <p className="text-muted text-sm">Nenhuma notificação por enquanto.</p>
                <p className="text-subtle text-xs">
                  Os lembretes das suas sessões aparecem aqui.
                </p>
              </div>
            ) : (
              <ul className="divide-y divide-[var(--border)]">
                {items.map((notification) => (
                  <li key={notification.id}>
                    <button
                      type="button"
                      onClick={() => handleClick(notification)}
                      className={`flex w-full gap-3 px-4 py-3 text-left transition-colors hover:bg-[var(--surface-hover)] ${
                        notification.is_read ? '' : 'bg-brand-50/60 dark:bg-brand-500/8'
                      }`}
                    >
                      <span
                        className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                          notification.is_read ? 'bg-[var(--border-strong)]' : 'bg-brand-500'
                        }`}
                        aria-hidden
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm leading-snug font-medium">
                          {notification.title}
                        </span>
                        {notification.message && (
                          <span className="text-muted mt-0.5 block text-xs leading-snug">
                            {notification.message}
                          </span>
                        )}
                        <span className="text-subtle mt-1 block text-[11px]">
                          {formatRelative(notification.created_at)}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
