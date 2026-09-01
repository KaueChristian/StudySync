/**
 * Utilitários de data, hora e texto.
 *
 * Convenção de fuso horário: a API sempre troca datas em **UTC** (ISO-8601
 * com sufixo Z). O navegador converte para o fuso local automaticamente ao
 * construir um `Date`; estas funções cuidam do caminho inverso, necessário
 * para os inputs `datetime-local`, que operam em horário local sem offset.
 */
import {
  differenceInMinutes,
  format,
  formatDistanceToNowStrict,
  isSameDay,
  isToday,
  isTomorrow,
  isYesterday,
  parseISO,
} from 'date-fns'
import { ptBR } from 'date-fns/locale'

const LOCALE = { locale: ptBR }

/** Converte string ISO (ou Date) em objeto Date. */
export function toDate(value) {
  if (!value) return null
  return value instanceof Date ? value : parseISO(value)
}

/** "14 de mar. de 2026" */
export function formatDate(value) {
  const date = toDate(value)
  return date ? format(date, "d 'de' MMM 'de' yyyy", LOCALE) : ''
}

/** "14/03/2026 14:30" */
export function formatDateTime(value) {
  const date = toDate(value)
  return date ? format(date, "dd/MM/yyyy 'às' HH:mm", LOCALE) : ''
}

/** "14:30" */
export function formatTime(value) {
  const date = toDate(value)
  return date ? format(date, 'HH:mm', LOCALE) : ''
}

/** "há 3 minutos" / "em 2 horas" */
export function formatRelative(value) {
  const date = toDate(value)
  if (!date) return ''
  return formatDistanceToNowStrict(date, { addSuffix: true, ...LOCALE })
}

/**
 * Rótulo humanizado de dia: "Hoje", "Amanhã", "Ontem" ou a data completa.
 */
export function formatDayLabel(value) {
  const date = toDate(value)
  if (!date) return ''
  if (isToday(date)) return 'Hoje'
  if (isTomorrow(date)) return 'Amanhã'
  if (isYesterday(date)) return 'Ontem'
  return format(date, "EEEE, d 'de' MMMM", LOCALE)
}

/** "Hoje às 14:30" */
export function formatSmartDateTime(value) {
  const date = toDate(value)
  if (!date) return ''
  const day = formatDayLabel(date)
  return `${day} às ${format(date, 'HH:mm', LOCALE)}`
}

/** Intervalo compacto: "14:30 – 16:00" (ou com data, se cruzar o dia). */
export function formatRange(start, end) {
  const a = toDate(start)
  const b = toDate(end)
  if (!a || !b) return ''
  if (isSameDay(a, b)) return `${format(a, 'HH:mm')} – ${format(b, 'HH:mm')}`
  return `${formatDateTime(a)} – ${formatDateTime(b)}`
}

/** Duração em minutos entre dois instantes, formatada: "1h 30min". */
export function formatDuration(start, end) {
  const a = toDate(start)
  const b = toDate(end)
  if (!a || !b) return ''
  return formatMinutes(differenceInMinutes(b, a))
}

/** 95 → "1h 35min" */
export function formatMinutes(total) {
  const minutes = Math.max(0, Math.round(total))
  if (minutes < 60) return `${minutes}min`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest ? `${hours}h ${rest}min` : `${hours}h`
}

// ---------------------------------------------------------------------------
// Inputs datetime-local
// ---------------------------------------------------------------------------
/**
 * ISO em UTC → valor de `<input type="datetime-local">` (horário local).
 * @param {string|Date|null} value
 * @returns {string} "YYYY-MM-DDTHH:mm"
 */
export function toInputValue(value) {
  const date = toDate(value)
  if (!date || Number.isNaN(date.getTime())) return ''
  return format(date, "yyyy-MM-dd'T'HH:mm")
}

/**
 * Valor de `<input type="datetime-local">` → ISO em UTC.
 * O construtor `Date` interpreta a string como horário local, e `toISOString`
 * converte para UTC — exatamente o que a API espera.
 */
export function fromInputValue(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date.toISOString()
}

/** Data/hora local "agora + N minutos", arredondada para o quarto de hora. */
export function roundedInputValue(minutesAhead = 60) {
  const date = new Date(Date.now() + minutesAhead * 60_000)
  date.setMinutes(Math.ceil(date.getMinutes() / 15) * 15, 0, 0)
  return toInputValue(date)
}

// ---------------------------------------------------------------------------
// Texto
// ---------------------------------------------------------------------------
/** Iniciais do nome, para o avatar: "Ana Souza" → "AS". */
export function initials(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/** Corta o texto preservando palavras inteiras. */
export function truncate(text = '', max = 120) {
  if (text.length <= max) return text
  return `${text.slice(0, text.lastIndexOf(' ', max) || max)}…`
}

/** Domínio legível de uma URL. */
export function prettyDomain(url = '') {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}
