/**
 * Calendário mensal.
 *
 * Monta a grade de 6 semanas (42 células) que cobre qualquer mês, marca o dia
 * atual e o selecionado, e mostra até 3 sessões por dia como pontos coloridos
 * na cor da matéria.
 */
import { useMemo } from 'react'
import {
  addDays,
  eachDayOfInterval,
  endOfMonth,
  format,
  isSameDay,
  isSameMonth,
  isToday,
  startOfMonth,
  startOfWeek,
} from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { ChevronLeft, ChevronRight } from 'lucide-react'

import { WEEKDAYS_SHORT } from '@/lib/constants'
import { toDate } from '@/lib/format'

export default function CalendarMonth({
  month,
  onMonthChange,
  selectedDate,
  onSelectDate,
  schedules = [],
}) {
  // 42 dias a partir do domingo da semana em que o mês começa.
  const days = useMemo(() => {
    const gridStart = startOfWeek(startOfMonth(month), { weekStartsOn: 0 })
    return eachDayOfInterval({ start: gridStart, end: addDays(gridStart, 41) })
  }, [month])

  // Índice dia → sessões, para evitar varrer a lista inteira em cada célula.
  const byDay = useMemo(() => {
    const map = new Map()
    schedules.forEach((schedule) => {
      const date = toDate(schedule.start_at)
      if (!date) return
      const key = format(date, 'yyyy-MM-dd')
      if (!map.has(key)) map.set(key, [])
      map.get(key).push(schedule)
    })
    return map
  }, [schedules])

  const monthLabel = format(month, "MMMM 'de' yyyy", { locale: ptBR })

  return (
    <div className="card p-4">
      <header className="mb-4 flex items-center justify-between">
        {/* `first-letter` em vez de `capitalize`: o Tailwind capitalizaria
            todas as palavras ("Agosto De 2026"). */}
        <h2 className="font-semibold first-letter:uppercase">{monthLabel}</h2>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => onMonthChange(-1)}
            aria-label="Mês anterior"
            className="text-muted rounded-lg p-1.5 transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => onSelectDate(new Date())}
            className="text-muted rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
          >
            Hoje
          </button>
          <button
            type="button"
            onClick={() => onMonthChange(1)}
            aria-label="Próximo mês"
            className="text-muted rounded-lg p-1.5 transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </header>

      <div className="grid grid-cols-7 gap-1">
        {WEEKDAYS_SHORT.map((weekday) => (
          <div key={weekday} className="text-subtle pb-2 text-center text-[11px] font-semibold">
            {weekday}
          </div>
        ))}

        {days.map((day) => {
          const key = format(day, 'yyyy-MM-dd')
          const dayItems = byDay.get(key) ?? []
          const inMonth = isSameMonth(day, month)
          const selected = selectedDate && isSameDay(day, selectedDate)
          const today = isToday(day)

          return (
            <button
              key={key}
              type="button"
              onClick={() => onSelectDate(day)}
              aria-label={`${format(day, "d 'de' MMMM", { locale: ptBR })}${
                dayItems.length ? `, ${dayItems.length} sessões` : ''
              }`}
              aria-pressed={selected}
              className={`relative flex aspect-square flex-col items-center justify-center rounded-lg text-sm transition-colors ${
                selected
                  ? 'bg-brand-600 font-semibold text-white'
                  : today
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-500/12 dark:text-brand-300 font-semibold'
                    : inMonth
                      ? 'hover:bg-[var(--surface-hover)]'
                      : 'text-subtle hover:bg-[var(--surface-hover)]'
              }`}
            >
              {format(day, 'd')}

              {dayItems.length > 0 && (
                <span className="absolute bottom-1 flex gap-0.5">
                  {dayItems.slice(0, 3).map((schedule) => (
                    <span
                      key={schedule.id}
                      className="h-1 w-1 rounded-full"
                      style={{
                        backgroundColor: selected
                          ? '#fff'
                          : (schedule.subject?.color ?? 'var(--text-subtle)'),
                      }}
                    />
                  ))}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
