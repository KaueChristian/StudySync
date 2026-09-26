/**
 * Logo do StudySync: monograma "S" com o bojo de cima curvo (o ciclo de foco)
 * e o de baixo reto (a célula da agenda).
 *
 * O contorno vem de `brand/build.py`, que também gera o favicon e o ícone do
 * app desktop — mudou lá, mude aqui.
 */
const MARK_PATH = 'M24 4H13A7 7 0 0 0 13 18H22V24H8V28H26V14H13A3 3 0 0 1 13 8H24Z'

/** Só o "S", na cor do texto em volta (`currentColor`). */
export function BrandMark({ className = '' }) {
  return (
    <svg viewBox="0 0 32 32" fill="currentColor" className={className} aria-hidden focusable="false">
      <path d={MARK_PATH} />
    </svg>
  )
}

/**
 * O ícone do app: "S" em papel sobre o bloco verde-tinta. `inverse` troca as
 * cores, para usar sobre fundo verde.
 */
export function BrandIcon({ className = 'h-9 w-9', inverse = false }) {
  const colors = inverse ? 'bg-paper text-brand-700' : 'bg-brand-600 text-paper'
  return (
    <span className={`inline-flex shrink-0 rounded-md ${colors} ${className}`}>
      <BrandMark className="h-full w-full" />
    </span>
  )
}
