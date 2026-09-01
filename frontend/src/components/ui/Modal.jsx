/**
 * Diálogo modal acessível.
 *
 * Cuida de: fechar com Esc, travar o scroll do fundo, prender o foco dentro
 * do diálogo (focus trap) e devolver o foco ao elemento de origem ao fechar.
 */
import { useCallback, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

const SIZES = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-6xl',
}

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

export default function Modal({
  open,
  onClose,
  title,
  description,
  size = 'md',
  footer,
  children,
  closeOnOverlay = true,
}) {
  const panelRef = useRef(null)
  const previouslyFocused = useRef(null)

  const handleKeyDown = useCallback(
    (event) => {
      if (event.key === 'Escape') {
        event.stopPropagation()
        onClose()
        return
      }

      if (event.key !== 'Tab' || !panelRef.current) return

      const focusable = Array.from(panelRef.current.querySelectorAll(FOCUSABLE)).filter(
        (el) => el.offsetParent !== null,
      )
      if (!focusable.length) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    },
    [onClose],
  )

  useEffect(() => {
    if (!open) return undefined

    previouslyFocused.current = document.activeElement

    // Trava o scroll do body compensando a largura da barra de rolagem,
    // para o conteúdo não "pular" ao abrir o modal.
    const scrollbar = window.innerWidth - document.documentElement.clientWidth
    const { overflow, paddingRight } = document.body.style
    document.body.style.overflow = 'hidden'
    if (scrollbar > 0) document.body.style.paddingRight = `${scrollbar}px`

    // Foca o primeiro controle útil do diálogo.
    const timer = setTimeout(() => {
      const target = panelRef.current?.querySelector(FOCUSABLE)
      target?.focus()
    }, 50)

    return () => {
      clearTimeout(timer)
      document.body.style.overflow = overflow
      document.body.style.paddingRight = paddingRight
      previouslyFocused.current?.focus?.()
    }
  }, [open])

  if (!open) return null

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-end justify-center overflow-y-auto p-0 sm:items-center sm:p-4"
      onKeyDown={handleKeyDown}
      role="presentation"
    >
      <div
        className="animate-fade-in fixed inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={closeOnOverlay ? onClose : undefined}
        aria-hidden
      />

      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        className={`card animate-slide-up relative z-10 flex max-h-[92vh] w-full flex-col rounded-b-none sm:rounded-2xl ${SIZES[size]}`}
      >
        {title && (
          <header className="flex items-start gap-4 border-b border-[var(--border)] px-5 py-4">
            <div className="min-w-0 flex-1">
              <h2 id="modal-title" className="font-display truncate text-lg">
                {title}
              </h2>
              {description && <p className="text-muted mt-0.5 text-sm">{description}</p>}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Fechar"
              className="text-subtle hover:text-[var(--text)] -mr-1 rounded-lg p-1.5 transition-colors hover:bg-[var(--surface-hover)]"
            >
              <X className="h-5 w-5" />
            </button>
          </header>
        )}

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">{children}</div>

        {footer && (
          <footer className="flex flex-wrap items-center justify-end gap-2 border-t border-[var(--border)] px-5 py-3.5">
            {footer}
          </footer>
        )}
      </div>
    </div>,
    document.body,
  )
}
