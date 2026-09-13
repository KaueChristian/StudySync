/** Cartão de uma sessão de estudo, usado na agenda e no painel. */
import { useEffect, useState } from 'react'
import {
  Bell,
  BellOff,
  CheckCircle2,
  Clock,
  ExternalLink,
  Link2,
  MapPin,
  Pencil,
  Repeat,
  RotateCcw,
  Timer,
  Trash2,
  XCircle,
} from 'lucide-react'

import Button from '@/components/ui/Button'
import { Badge } from '@/components/ui/Misc'
import { SubjectAvatar } from '@/components/ui/SubjectIcon'
import { SCHEDULE_STATUS } from '@/lib/constants'
import { formatDuration, formatRange, formatRelative, toDate } from '@/lib/format'
import FocusTimer from './FocusTimer'

export default function ScheduleCard({
  schedule,
  onEdit,
  onDelete,
  onStatusChange,
  compact = false,
}) {
  const [timerOpen, setTimerOpen] = useState(false)
  const [now, setNow] = useState(() => Date.now())

  const status = SCHEDULE_STATUS[schedule.status] ?? SCHEDULE_STATUS.pending
  const start = toDate(schedule.start_at)
  const isPast = start ? start.getTime() <= now : false
  const isPending = schedule.status === 'pending'
  const linksCount = schedule.search_results?.length ?? 0

  useEffect(() => {
    if (!isPending || isPast || !start) return
    const diff = start.getTime() - now
    const intervalMs = diff < 120_000 ? 5_000 : 30_000
    const timer = setInterval(() => setNow(Date.now()), intervalMs)
    return () => clearInterval(timer)
  }, [isPending, isPast, start, now])

  const completeFromTimer = () => {
    setTimerOpen(false)
    onStatusChange?.(schedule, 'completed')
  }

  return (
    <article
      className={`card ${compact ? 'p-4' : 'p-5'} relative overflow-hidden`}
      style={
        schedule.subject
          ? { borderLeft: `3px solid ${schedule.subject.color}` }
          : undefined
      }
    >
      <div className="flex items-start gap-3">
        {schedule.subject && !compact && (
          <SubjectAvatar subject={schedule.subject} size="sm" />
        )}

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3
              className={`font-display text-[17px] leading-snug ${
                schedule.status === 'canceled' ? 'text-muted line-through' : ''
              }`}
            >
              {schedule.title}
            </h3>
            <Badge className={status.className}>{status.label}</Badge>
            {schedule.recurrence_group_id && (
              <Badge title="Faz parte de uma série recorrente">
                <Repeat className="h-3 w-3" aria-hidden />
                Recorrente
              </Badge>
            )}
          </div>

          {schedule.topic && (
            <p className="text-muted mt-1 text-sm">
              <span className="text-subtle">Tópico:</span> {schedule.topic}
            </p>
          )}

          <div className="text-muted mt-2.5 flex flex-wrap items-center gap-x-3.5 gap-y-1.5 text-xs">
            <span className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" aria-hidden />
              {formatRange(schedule.start_at, schedule.end_at)}
              <span className="text-subtle">({formatDuration(schedule.start_at, schedule.end_at)})</span>
            </span>

            {schedule.subject && (
              <Badge color={schedule.subject.color}>{schedule.subject.name}</Badge>
            )}

            {schedule.location && (
              <span className="flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5" aria-hidden />
                {schedule.location}
              </span>
            )}

            {isPending && (
              <span
                className="flex items-center gap-1.5"
                title={
                  schedule.reminder_enabled
                    ? `Lembrete ${schedule.remind_minutes} min antes`
                    : 'Lembrete desativado'
                }
              >
                {schedule.reminder_enabled ? (
                  <>
                    <Bell className="h-3.5 w-3.5" aria-hidden />
                    {schedule.reminder_sent ? 'Lembrete enviado' : `${schedule.remind_minutes} min antes`}
                  </>
                ) : (
                  <>
                    <BellOff className="h-3.5 w-3.5" aria-hidden />
                    Sem lembrete
                  </>
                )}
              </span>
            )}

            {isPending && !isPast && (
              <span className="text-brand-600 dark:text-brand-400 font-medium">
                começa {formatRelative(schedule.start_at)}
              </span>
            )}
          </div>

          {schedule.description && !compact && (
            <p className="text-muted mt-2.5 line-clamp-2 text-sm leading-relaxed">
              {schedule.description}
            </p>
          )}

          {/* Links de apoio salvos nesta sessão */}
          {linksCount > 0 && (
            <div className="mt-3 rounded-lg bg-[var(--surface-sunken)] p-2.5">
              <p className="text-subtle mb-1.5 flex items-center gap-1.5 text-xs font-medium">
                <Link2 className="h-3.5 w-3.5" aria-hidden />
                {linksCount} {linksCount === 1 ? 'link de apoio' : 'links de apoio'}
              </p>
              <ul className="space-y-1">
                {schedule.search_results.slice(0, compact ? 2 : 3).map((link) => (
                  <li key={link.id}>
                    <a
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer nofollow"
                      className="text-brand-600 dark:text-brand-400 flex items-center gap-1.5 truncate text-xs hover:underline"
                    >
                      <ExternalLink className="h-3 w-3 shrink-0" aria-hidden />
                      <span className="truncate">{link.title}</span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------ ações */}
      {(onEdit || onDelete || onStatusChange) && (
        <div className="mt-3.5 flex flex-wrap items-center gap-1.5 border-t border-[var(--border)] pt-3">
          {isPending && (
            <Button size="xs" variant="ghost" icon={Timer} onClick={() => setTimerOpen(true)}>
              Iniciar foco
            </Button>
          )}

          {onStatusChange && isPending && (
            <>
              <Button
                size="xs"
                variant="ghost"
                icon={CheckCircle2}
                onClick={() => onStatusChange(schedule, 'completed')}
                className="text-emerald-600 dark:text-emerald-400"
              >
                Concluir
              </Button>
              <Button
                size="xs"
                variant="ghost"
                icon={XCircle}
                onClick={() => onStatusChange(schedule, 'canceled')}
              >
                Cancelar
              </Button>
            </>
          )}

          {onStatusChange && !isPending && (
            <Button
              size="xs"
              variant="ghost"
              icon={RotateCcw}
              onClick={() => onStatusChange(schedule, 'pending')}
            >
              Reabrir
            </Button>
          )}

          <div className="flex-1" />

          {onEdit && (
            <Button size="xs" variant="ghost" icon={Pencil} onClick={() => onEdit(schedule)}>
              Editar
            </Button>
          )}
          {onDelete && (
            <Button
              size="xs"
              variant="danger-ghost"
              icon={Trash2}
              onClick={() => onDelete(schedule)}
              aria-label={`Excluir ${schedule.title}`}
            />
          )}
        </div>
      )}

      <FocusTimer
        open={timerOpen}
        onClose={() => setTimerOpen(false)}
        schedule={schedule}
        onComplete={completeFromTimer}
      />
    </article>
  )
}
