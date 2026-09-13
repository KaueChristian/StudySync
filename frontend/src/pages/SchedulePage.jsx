/** Agenda: calendário mensal + lista de sessões do dia selecionado. */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { addMonths, endOfMonth, isSameDay, isSameMonth, startOfMonth } from 'date-fns'
import { CalendarDays, CalendarPlus, Download, ListFilter } from 'lucide-react'

import CalendarMonth from '@/components/schedule/CalendarMonth'
import ScheduleCard from '@/components/schedule/ScheduleCard'
import ScheduleModal from '@/components/schedule/ScheduleModal'
import { useRecurrenceScope } from '@/components/schedule/RecurrenceScopeDialog'
import Button from '@/components/ui/Button'
import { useConfirm } from '@/components/ui/ConfirmDialog'
import { EmptyState, PageHeading, Skeleton } from '@/components/ui/Misc'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'
import { scheduleService, subjectService } from '@/lib/services'
import { formatDayLabel, toDate } from '@/lib/format'

export default function SchedulePage() {
  const toast = useToast()
  const confirm = useConfirm()
  const askRecurrenceScope = useRecurrenceScope()
  const [searchParams, setSearchParams] = useSearchParams()
  const [exporting, setExporting] = useState(false)

  const [month, setMonth] = useState(() => startOfMonth(new Date()))
  const [selectedDate, setSelectedDate] = useState(() => new Date())
  const [schedules, setSchedules] = useState([])
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)

  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)

  const subjectFilter = searchParams.get('materia') ?? ''
  // Id vindo do clique em uma notificação (`/agenda?sessao=12`).
  const focusId = searchParams.get('sessao')

  // ----------------------------------------------------------------- carga
  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [scheduleList, subjectList] = await Promise.all([
        scheduleService.list({
          // Margem de um mês para cada lado cobre as células do calendário
          // que pertencem aos meses vizinhos.
          start: addMonths(startOfMonth(month), -1).toISOString(),
          end: addMonths(endOfMonth(month), 1).toISOString(),
          subject_id: subjectFilter || undefined,
        }),
        subjectService.list(),
      ])
      setSchedules(scheduleList)
      setSubjects(subjectList)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível carregar a agenda.'))
    } finally {
      setLoading(false)
    }
  }, [month, subjectFilter, toast])

  useEffect(() => {
    load()
  }, [load])

  // Abre automaticamente a sessão indicada por uma notificação.
  useEffect(() => {
    if (!focusId) return
    if (loading) return

    const target = schedules.find((item) => String(item.id) === focusId)
    if (target) {
      const date = toDate(target.start_at)
      if (date) {
        setSelectedDate(date)
        setMonth(startOfMonth(date))
      }
      setEditing(target)
      setModalOpen(true)
    } else {
      scheduleService
        .get(focusId)
        .then((fetched) => {
          const date = toDate(fetched.start_at)
          if (date) {
            setSelectedDate(date)
            setMonth(startOfMonth(date))
          }
          setEditing(fetched)
          setModalOpen(true)
        })
        .catch(() => {
          toast.warning('A sessão associada a este lembrete não foi encontrada ou foi excluída.')
        })
    }

    setSearchParams((current) => {
      const next = new URLSearchParams(current)
      next.delete('sessao')
      return next
    })
  }, [focusId, schedules, loading, setSearchParams, toast])

  // ------------------------------------------------------------- derivados
  const monthSchedules = useMemo(
    () =>
      schedules.filter((schedule) => {
        const date = toDate(schedule.start_at)
        return date && isSameMonth(date, month)
      }),
    [schedules, month],
  )

  const daySchedules = useMemo(
    () =>
      schedules
        .filter((schedule) => {
          const date = toDate(schedule.start_at)
          return date && isSameDay(date, selectedDate)
        })
        .sort((a, b) => new Date(a.start_at) - new Date(b.start_at)),
    [schedules, selectedDate],
  )

  // ---------------------------------------------------------------- ações
  const openCreate = () => {
    setEditing(null)
    setModalOpen(true)
  }

  const handleStatusChange = async (schedule, status) => {
    try {
      const updated = await scheduleService.setStatus(schedule.id, status)
      setSchedules((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      )
      const labels = {
        completed: 'Sessão concluída! 🎉',
        canceled: 'Sessão cancelada.',
        pending: 'Sessão reaberta.',
      }
      toast.success(labels[status])
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível alterar o status.'))
    }
  }

  const handleDelete = async (schedule) => {
    let scope = 'this'

    if (schedule.recurrence_group_id) {
      const chosen = await askRecurrenceScope({ title: schedule.title })
      if (!chosen) return
      scope = chosen
    } else {
      const ok = await confirm({
        title: `Excluir "${schedule.title}"?`,
        description: 'A sessão e os links de apoio anexados a ela serão removidos.',
        confirmLabel: 'Excluir sessão',
      })
      if (!ok) return
    }

    try {
      await scheduleService.remove(schedule.id, scope)
      if (scope === 'this') {
        setSchedules((current) => current.filter((item) => item.id !== schedule.id))
      } else {
        // 'following'/'all' podem remover outras instâncias da série —
        // mais simples recarregar a agenda do que calcular o subconjunto.
        load()
      }
      toast.success('Sessão excluída.')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível excluir a sessão.'))
    }
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const blob = await scheduleService.exportIcs()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'studysync-agenda.ics'
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível exportar a agenda.'))
    } finally {
      setExporting(false)
    }
  }

  return (
    <>
      <PageHeading
        icon={CalendarDays}
        title="Agenda de estudos"
        description="Planeje suas sessões e receba lembretes antes de cada uma."
        actions={
          <>
            <div className="relative">
              <ListFilter
                className="text-subtle pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
                aria-hidden
              />
              <select
                value={subjectFilter}
                onChange={(event) =>
                  setSearchParams(event.target.value ? { materia: event.target.value } : {})
                }
                aria-label="Filtrar por matéria"
                className="h-10 rounded-xl border border-[var(--border-strong)] bg-[var(--surface)] pr-3 pl-9 text-sm"
              >
                <option value="">Todas as matérias</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>
            </div>

            <Button
              variant="secondary"
              icon={Download}
              onClick={handleExport}
              loading={exporting}
              title="Baixar a agenda em .ics"
            >
              <span className="hidden sm:inline">Exportar</span>
            </Button>

            <Button icon={CalendarPlus} onClick={openCreate}>
              Nova sessão
            </Button>
          </>
        }
      />

      <div className="grid gap-5 lg:grid-cols-[minmax(0,340px)_1fr]">
        {/* ------------------------------------------------------ calendário */}
        <div className="lg:sticky lg:top-24 lg:self-start">
          <CalendarMonth
            month={month}
            onMonthChange={(delta) => setMonth((current) => addMonths(current, delta))}
            selectedDate={selectedDate}
            onSelectDate={(date) => {
              setSelectedDate(date)
              setMonth(startOfMonth(date))
            }}
            schedules={schedules}
          />

          <div className="card mt-4 p-4">
            <h3 className="mb-2.5 text-sm font-semibold">Resumo do mês</h3>
            <dl className="space-y-2 text-sm">
              {[
                ['Total de sessões', monthSchedules.length],
                ['Pendentes', monthSchedules.filter((s) => s.status === 'pending').length],
                ['Concluídas', monthSchedules.filter((s) => s.status === 'completed').length],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between">
                  <dt className="text-muted">{label}</dt>
                  <dd className="font-semibold">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>

        {/* ---------------------------------------------------- lista do dia */}
        <section>
          <header className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold first-letter:uppercase">
                {formatDayLabel(selectedDate)}
              </h2>
              <p className="text-muted text-sm">
                {daySchedules.length === 0
                  ? 'Nenhuma sessão agendada'
                  : `${daySchedules.length} ${daySchedules.length === 1 ? 'sessão' : 'sessões'}`}
              </p>
            </div>
          </header>

          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="card space-y-2.5 p-5">
                  <Skeleton className="h-5 w-1/2" />
                  <Skeleton className="h-3 w-3/4" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
              ))}
            </div>
          ) : daySchedules.length === 0 ? (
            <div className="card">
              <EmptyState
                icon={CalendarDays}
                title="Dia livre"
                description="Nenhuma sessão de estudo agendada para esta data. Que tal planejar uma agora?"
                action={
                  <Button icon={CalendarPlus} onClick={openCreate}>
                    Agendar sessão
                  </Button>
                }
              />
            </div>
          ) : (
            <div className="space-y-3">
              {daySchedules.map((schedule) => (
                <ScheduleCard
                  key={schedule.id}
                  schedule={schedule}
                  onEdit={(item) => {
                    setEditing(item)
                    setModalOpen(true)
                  }}
                  onDelete={handleDelete}
                  onStatusChange={handleStatusChange}
                />
              ))}
            </div>
          )}
        </section>
      </div>

      <ScheduleModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        schedule={editing}
        subjects={subjects}
        defaultDate={selectedDate}
        defaultSubjectId={subjectFilter}
        onSaved={load}
      />
    </>
  )
}
