/**
 * Diálogo de confirmação para ações destrutivas.
 *
 * Usado via o hook `useConfirm`, que devolve uma função assíncrona:
 *
 *   const confirm = useConfirm()
 *   if (await confirm({ title: 'Excluir?', tone: 'danger' })) { ... }
 */
import { createContext, useCallback, useContext, useRef, useState } from 'react'
import { AlertTriangle } from 'lucide-react'

import Button from './Button'
import Modal from './Modal'

const ConfirmContext = createContext(null)

const DEFAULTS = {
  title: 'Tem certeza?',
  description: 'Esta ação não pode ser desfeita.',
  confirmLabel: 'Confirmar',
  cancelLabel: 'Cancelar',
  tone: 'danger',
}

export function ConfirmProvider({ children }) {
  const [state, setState] = useState(null)
  const resolverRef = useRef(null)

  const confirm = useCallback((options = {}) => {
    setState({ ...DEFAULTS, ...options })
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
    <ConfirmContext.Provider value={confirm}>
      {children}

      <Modal
        open={Boolean(state)}
        onClose={() => close(false)}
        size="sm"
        title={state?.title}
        footer={
          <>
            <Button variant="secondary" onClick={() => close(false)}>
              {state?.cancelLabel}
            </Button>
            <Button
              variant={state?.tone === 'danger' ? 'danger' : 'primary'}
              onClick={() => close(true)}
            >
              {state?.confirmLabel}
            </Button>
          </>
        }
      >
        <div className="flex gap-3.5">
          {state?.tone === 'danger' && (
            <div className="h-fit rounded-xl bg-red-50 p-2.5 dark:bg-red-500/10">
              <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" aria-hidden />
            </div>
          )}
          <p className="text-muted text-sm leading-relaxed">{state?.description}</p>
        </div>
      </Modal>
    </ConfirmContext.Provider>
  )
}

export function useConfirm() {
  const context = useContext(ConfirmContext)
  if (!context) throw new Error('useConfirm precisa estar dentro de <ConfirmProvider>.')
  return context
}
