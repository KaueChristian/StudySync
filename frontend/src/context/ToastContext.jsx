/**
 * Sistema de toasts (avisos flutuantes).
 *
 * Exposto via `useToast()`, que devolve helpers semânticos:
 *   toast.success('Salvo!')
 *   toast.error('Falhou.')
 *   toast.reminder('Lembrete', { description, action })
 */
import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'
import { AlertTriangle, Bell, CheckCircle2, Info, X, XCircle } from 'lucide-react'

const ToastContext = createContext(null)

const VARIANTS = {
  success: {
    Icon: CheckCircle2,
    accent: 'text-emerald-500',
    ring: 'border-l-emerald-500',
  },
  error: { Icon: XCircle, accent: 'text-red-500', ring: 'border-l-red-500' },
  warning: { Icon: AlertTriangle, accent: 'text-amber-500', ring: 'border-l-amber-500' },
  info: { Icon: Info, accent: 'text-blue-500', ring: 'border-l-blue-500' },
  reminder: { Icon: Bell, accent: 'text-brand-500', ring: 'border-l-brand-500' },
}

const DEFAULT_DURATION = 4500

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const timers = useRef(new Map())

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((t) => t.id !== id))
    const timer = timers.current.get(id)
    if (timer) {
      clearTimeout(timer)
      timers.current.delete(id)
    }
  }, [])

  const push = useCallback(
    (variant, title, options = {}) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
      const duration = options.duration ?? DEFAULT_DURATION

      setToasts((current) => {
        // No máximo 4 simultâneos: o mais antigo cede lugar.
        const next = [...current, { id, variant, title, ...options }]
        return next.slice(-4)
      })

      // duration === 0 mantém o toast até o usuário fechar.
      if (duration > 0) {
        timers.current.set(id, setTimeout(() => dismiss(id), duration))
      }
      return id
    },
    [dismiss],
  )

  const toast = useMemo(
    () => ({
      success: (title, options) => push('success', title, options),
      error: (title, options) => push('error', title, options),
      warning: (title, options) => push('warning', title, options),
      info: (title, options) => push('info', title, options),
      reminder: (title, options) => push('reminder', title, { duration: 12000, ...options }),
      dismiss,
    }),
    [push, dismiss],
  )

  return (
    <ToastContext.Provider value={toast}>
      {children}

      {/* Região viva: leitores de tela anunciam os toasts que chegam. */}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="pointer-events-none fixed top-4 right-4 z-[100] flex w-[calc(100vw-2rem)] max-w-sm flex-col gap-2.5"
      >
        {toasts.map((item) => {
          const { Icon, accent, ring } = VARIANTS[item.variant] ?? VARIANTS.info
          return (
            <div
              key={item.id}
              role="status"
              className={`card animate-slide-in-right pointer-events-auto flex gap-3 border-l-4 p-3.5 shadow-lg ${ring}`}
            >
              <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${accent}`} aria-hidden />

              <div className="min-w-0 flex-1">
                <p className="text-sm leading-snug font-semibold">{item.title}</p>
                {item.description && (
                  <p className="text-muted mt-1 text-sm leading-snug">{item.description}</p>
                )}
                {item.action && (
                  <button
                    type="button"
                    onClick={() => {
                      item.action.onClick()
                      dismiss(item.id)
                    }}
                    className="text-brand-600 dark:text-brand-400 mt-2 text-sm font-semibold hover:underline"
                  >
                    {item.action.label}
                  </button>
                )}
              </div>

              <button
                type="button"
                onClick={() => dismiss(item.id)}
                aria-label="Fechar aviso"
                className="text-subtle hover:text-muted h-fit rounded-md p-1 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast precisa estar dentro de <ToastProvider>.')
  return context
}
