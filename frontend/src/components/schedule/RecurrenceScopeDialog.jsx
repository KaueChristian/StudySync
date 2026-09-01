/**
 * Escolha de alcance ao excluir uma sessão que faz parte de uma série
 * recorrente — análogo ao `useConfirm`, mas resolve para um `scope`
 * ('this' | 'following' | 'all') em vez de um booleano.
 */
import { createContext, useCallback, useContext, useRef, useState } from 'react'
import { CalendarRange, Repeat } from 'lucide-react'

import Button from '../ui/Button'
import Modal from '../ui/Modal'

const RecurrenceScopeContext = createContext(null)

export function RecurrenceScopeProvider({ children }) {
  const [state, setState] = useState(null)
  const resolverRef = useRef(null)

  const askScope = useCallback((options = {}) => {
    setState(options)
    return new Promise((resolve) => {
      resolverRef.current = resolve
    })
  }, [])

  const close = useCallback((result) => {
    resolverRef.current?.(result)
    resolverRef.current = null
    setState(null)
  }, [])

  return (
    <RecurrenceScopeContext.Provider value={askScope}>
      {children}

      <Modal
        open={Boolean(state)}
        onClose={() => close(null)}
        size="sm"
        title={`Excluir "${state?.title ?? ''}"?`}
        description="Esta sessão faz parte de uma série recorrente. O que você quer excluir?"
      >
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => close('this')}
            className="card card-interactive flex w-full items-start gap-3 p-3.5 text-left"
          >
            <div className="bg-brand-50 dark:bg-brand-500/10 rounded-lg p-2">
              <CalendarRange className="text-brand-600 dark:text-brand-400 h-4 w-4" aria-hidden />
            </div>
            <div>
              <p className="text-sm font-semibold">Somente esta sessão</p>
              <p className="text-muted text-xs">As demais ocorrências da série continuam agendadas.</p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => close('following')}
            className="card card-interactive flex w-full items-start gap-3 p-3.5 text-left"
          >
            <div className="bg-brand-50 dark:bg-brand-500/10 rounded-lg p-2">
              <Repeat className="text-brand-600 dark:text-brand-400 h-4 w-4" aria-hidden />
            </div>
            <div>
              <p className="text-sm font-semibold">Esta e as próximas</p>
              <p className="text-muted text-xs">Remove esta ocorrência e todas as futuras da série.</p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => close('all')}
            className="card card-interactive flex w-full items-start gap-3 p-3.5 text-left"
          >
            <div className="rounded-lg bg-red-50 p-2 dark:bg-red-500/10">
              <Repeat className="h-4 w-4 text-red-600 dark:text-red-400" aria-hidden />
            </div>
            <div>
              <p className="text-sm font-semibold">Toda a série</p>
              <p className="text-muted text-xs">Remove todas as ocorrências, passadas e futuras.</p>
            </div>
          </button>
        </div>

        <div className="mt-4 flex justify-end border-t border-[var(--border)] pt-4">
          <Button variant="secondary" onClick={() => close(null)}>
            Cancelar
          </Button>
        </div>
      </Modal>
    </RecurrenceScopeContext.Provider>
  )
}

export function useRecurrenceScope() {
  const context = useContext(RecurrenceScopeContext)
  if (!context) {
    throw new Error('useRecurrenceScope precisa estar dentro de <RecurrenceScopeProvider>.')
  }
  return context
}
