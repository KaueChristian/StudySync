/** Componentes visuais pequenos, reutilizados em toda a interface. */
import { Loader2 } from 'lucide-react'

// ---------------------------------------------------------------- Badge
export function Badge({ children, className = '', color, style, ...props }) {
  // Quando uma cor da matéria é passada, geramos o estilo inline a partir
  // dela (fundo translúcido + texto e borda na cor cheia).
  const dynamicStyle = color
    ? { backgroundColor: `${color}1a`, color, borderColor: `${color}40`, ...style }
    : style

  return (
    <span
      style={dynamicStyle}
      className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${
        color ? '' : 'border-[var(--border)] bg-[var(--surface-sunken)] text-[var(--text-muted)]'
      } ${className}`}
      {...props}
    >
      {children}
    </span>
  )
}

// -------------------------------------------------------------- Spinner
export function Spinner({ className = 'h-5 w-5' }) {
  return <Loader2 className={`text-brand-500 animate-spin ${className}`} aria-hidden />
}

export function LoadingState({ label = 'Carregando…', className = 'py-16' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`} role="status">
      <Spinner className="h-7 w-7" />
      <p className="text-muted text-sm">{label}</p>
    </div>
  )
}

// ------------------------------------------------------------- Skeleton
export function Skeleton({ className = 'h-4 w-full' }) {
  return <div className={`skeleton ${className}`} aria-hidden />
}

export function CardSkeleton({ count = 3 }) {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="card space-y-3 p-5">
          <Skeleton className="h-5 w-2/3" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-4/5" />
          <div className="flex gap-2 pt-1">
            <Skeleton className="h-5 w-16 rounded-lg" />
            <Skeleton className="h-5 w-20 rounded-lg" />
          </div>
        </div>
      ))}
    </>
  )
}

// ----------------------------------------------------------- EmptyState
export function EmptyState({ icon: Icon, title, description, action, className = '' }) {
  return (
    <div
      className={`flex flex-col items-center justify-center px-6 py-16 text-center ${className}`}
    >
      {Icon && (
        <div className="mb-4 rounded-2xl bg-[var(--surface-sunken)] p-4">
          <Icon className="text-subtle h-8 w-8" aria-hidden />
        </div>
      )}
      <h3 className="text-base font-semibold">{title}</h3>
      {description && (
        <p className="text-muted mt-1.5 max-w-sm text-sm leading-relaxed">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

// --------------------------------------------------------- PageHeading
export function PageHeading({ title, description, actions, icon: Icon }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="bg-brand-50 dark:bg-brand-500/10 mt-0.5 rounded-xl p-2.5">
            <Icon className="text-brand-600 dark:text-brand-400 h-5 w-5" aria-hidden />
          </div>
        )}
        <div>
          <h1 className="font-display text-2xl">{title}</h1>
          {description && <p className="text-muted mt-1 text-sm">{description}</p>}
        </div>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}

// ---------------------------------------------------------------- Toggle
export function Toggle({ checked, onChange, label, description, id }) {
  return (
    <label htmlFor={id} className="flex cursor-pointer items-start gap-3">
      <button
        type="button"
        role="switch"
        id={id}
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative mt-0.5 h-6 w-11 shrink-0 rounded-full transition-colors ${
          checked ? 'bg-brand-600' : 'bg-[var(--border-strong)]'
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
      <span className="min-w-0">
        <span className="block text-sm font-medium">{label}</span>
        {description && <span className="text-muted block text-xs">{description}</span>}
      </span>
    </label>
  )
}
