/**
 * Campos de formulário: Input, Textarea e Select.
 *
 * Todos compartilham o mesmo invólucro (`Field`), que cuida do rótulo,
 * da mensagem de erro e da associação acessível entre eles.
 */
import { useId } from 'react'
import { AlertCircle } from 'lucide-react'

const CONTROL_BASE =
  'w-full rounded-xl border bg-[var(--surface)] px-3.5 text-[var(--text)] transition-colors ' +
  'placeholder:text-[var(--text-subtle)] focus:outline-none focus:ring-2 focus:ring-brand-500/40 ' +
  'focus:border-brand-500 disabled:opacity-60 disabled:cursor-not-allowed'

const errorBorder = (error) =>
  error ? 'border-red-400 focus:border-red-500 focus:ring-red-500/30' : 'border-[var(--border-strong)]'

export function Field({ label, error, hint, required, htmlFor, children, className = '' }) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label htmlFor={htmlFor} className="text-sm font-medium">
          {label}
          {required && (
            <span className="ml-0.5 text-red-500" aria-label="obrigatório">
              *
            </span>
          )}
        </label>
      )}

      {children}

      {error ? (
        <p role="alert" className="flex items-center gap-1.5 text-sm text-red-600 dark:text-red-400">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden />
          {error}
        </p>
      ) : (
        hint && <p className="text-subtle text-xs">{hint}</p>
      )}
    </div>
  )
}

export function Input({ label, error, hint, icon: Icon, className = '', id, ...props }) {
  const generatedId = useId()
  const inputId = id ?? generatedId

  return (
    <Field
      label={label}
      error={error}
      hint={hint}
      required={props.required}
      htmlFor={inputId}
      className={className}
    >
      <div className="relative">
        {Icon && (
          <Icon
            className="text-subtle pointer-events-none absolute top-1/2 left-3.5 h-4 w-4 -translate-y-1/2"
            aria-hidden
          />
        )}
        <input
          id={inputId}
          aria-invalid={Boolean(error) || undefined}
          className={`${CONTROL_BASE} ${errorBorder(error)} h-11 ${Icon ? 'pl-10' : ''}`}
          {...props}
        />
      </div>
    </Field>
  )
}

export function Textarea({ label, error, hint, className = '', id, rows = 4, ...props }) {
  const generatedId = useId()
  const inputId = id ?? generatedId

  return (
    <Field
      label={label}
      error={error}
      hint={hint}
      required={props.required}
      htmlFor={inputId}
      className={className}
    >
      <textarea
        id={inputId}
        rows={rows}
        aria-invalid={Boolean(error) || undefined}
        className={`${CONTROL_BASE} ${errorBorder(error)} resize-y py-2.5 leading-relaxed`}
        {...props}
      />
    </Field>
  )
}

export function Select({ label, error, hint, options = [], className = '', id, children, ...props }) {
  const generatedId = useId()
  const inputId = id ?? generatedId

  return (
    <Field
      label={label}
      error={error}
      hint={hint}
      required={props.required}
      htmlFor={inputId}
      className={className}
    >
      <select
        id={inputId}
        aria-invalid={Boolean(error) || undefined}
        className={`${CONTROL_BASE} ${errorBorder(error)} h-11 cursor-pointer pr-9`}
        {...props}
      >
        {children ??
          options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
      </select>
    </Field>
  )
}
