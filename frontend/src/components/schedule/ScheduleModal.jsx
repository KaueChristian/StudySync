/**
 * Modal de criação/edição de sessão de estudo.
 *
 * Duas abas: os dados da sessão e a busca de conteúdo de apoio. A busca usa
 * o **tópico** como semente da consulta — é ele que descreve o que será
 * estudado (ex.: "partes do corpo humano").
 */
import { useEffect, useState } from 'react'
import { CalendarClock, Sparkles, Timer } from 'lucide-react'

import ContentSearchPanel from '@/components/search/ContentSearchPanel'
import FocusTimer from './FocusTimer'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { Input, Select, Textarea } from '@/components/ui/Field'
import { Badge, Toggle } from '@/components/ui/Misc'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'
import { scheduleService } from '@/lib/services'
import { REMINDER_OPTIONS } from '@/lib/constants'
import { fromInputValue, roundedInputValue, toInputValue } from '@/lib/format'

/** Estado inicial: começa daqui a 1h e dura 1h. */
function emptyForm(defaults = {}) {
  const start = defaults.start ?? roundedInputValue(60)
  const end = toInputValue(new Date(new Date(start).getTime() + 60 * 60_000))
  // "Repetir até" começa sugerindo 8 semanas à frente do início.
  const repeatUntil = toInputValue(
    new Date(new Date(start).getTime() + 8 * 7 * 24 * 60 * 60_000),
  ).slice(0, 10)
  return {
    title: '',
    topic: '',
    description: '',
    location: '',
    subject_id: defaults.subject_id ?? '',
    start_at: start,
    end_at: end,
    remind_minutes: 15,
    reminder_enabled: true,
    repeat_weekly: false,
    repeat_until: repeatUntil,
  }
}

export default function ScheduleModal({
  open,
  onClose,
  schedule,
  subjects = [],
  defaultDate,
  defaultSubjectId,
  onSaved,
}) {
  const toast = useToast()

  const [form, setForm] = useState(() => emptyForm())
  const [tab, setTab] = useState('details')
  const [scheduleId, setScheduleId] = useState(null)
  const [timerOpen, setTimerOpen] = useState(false)
  const [savedLinks, setSavedLinks] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return

    if (schedule) {
      setForm({
        title: schedule.title,
        topic: schedule.topic ?? '',
        description: schedule.description ?? '',
        location: schedule.location ?? '',
        subject_id: schedule.subject_id ?? '',
        start_at: toInputValue(schedule.start_at),
        end_at: toInputValue(schedule.end_at),
        remind_minutes: schedule.remind_minutes,
        reminder_enabled: schedule.reminder_enabled,
      })
      setScheduleId(schedule.id)
      setSavedLinks(schedule.search_results ?? [])
    } else {
      // Ao criar a partir de um dia clicado no calendário, mantém a data
      // escolhida e usa 19:00 como horário padrão.
      let start
      if (defaultDate) {
        const date = new Date(defaultDate)
        date.setHours(19, 0, 0, 0)
        start = toInputValue(date)
      }
      setForm(emptyForm({ start, subject_id: defaultSubjectId ?? '' }))
      setScheduleId(null)
      setSavedLinks([])
    }
    setTab('details')
    setError('')
  }, [open, schedule, defaultDate, defaultSubjectId])

  const update = (field, value) => {
    setForm((current) => {
      const next = { ...current, [field]: value }
      // Mover o início arrasta o fim, preservando a duração da sessão.
      if (field === 'start_at' && current.start_at && current.end_at) {
        const duration = new Date(current.end_at) - new Date(current.start_at)
        if (duration > 0) {
          next.end_at = toInputValue(new Date(new Date(value).getTime() + duration))
        }
      }
      return next
    })
    setError('')
  }

  const persist = async ({ closeAfter = true } = {}) => {
    if (!form.title.trim()) {
      setError('Informe um título para a sessão.')
      setTab('details')
      return null
    }

    const start = fromInputValue(form.start_at)
    const end = fromInputValue(form.end_at)
    if (!start || !end) {
      setError('Preencha a data e a hora de início e término.')
      setTab('details')
      return null
    }
    if (new Date(end) <= new Date(start)) {
      setError('O horário de término deve ser posterior ao de início.')
      setTab('details')
      return null
    }

    if (!scheduleId && form.repeat_weekly && !form.repeat_until) {
      setError('Informe até quando a sessão deve se repetir.')
      setTab('details')
      return null
    }

    setSaving(true)
    try {
      const payload = {
        title: form.title.trim(),
        topic: form.topic.trim() || null,
        description: form.description.trim() || null,
        location: form.location.trim() || null,
        subject_id: form.subject_id ? Number(form.subject_id) : null,
        start_at: start,
        end_at: end,
        remind_minutes: Number(form.remind_minutes),
        reminder_enabled: form.reminder_enabled,
      }

      // Repetição só se aplica à criação — editar uma instância existente
      // não recria a série.
      if (!scheduleId && form.repeat_weekly) {
        payload.repeat_weekly = true
        payload.repeat_until = fromInputValue(`${form.repeat_until}T23:59`)
      }

      const saved = scheduleId
        ? await scheduleService.update(scheduleId, payload)
        : await scheduleService.create(payload)

      setScheduleId(saved.id)
      setSavedLinks(saved.search_results ?? [])
      onSaved?.(saved)

      toast.success(scheduleId ? 'Sessão atualizada!' : 'Sessão agendada!', {
        description:
          saved.reminder_enabled && !saved.reminder_sent
            ? `Você será avisado ${saved.remind_minutes} minutos antes.`
            : undefined,
      })
      if (closeAfter) onClose()
      return saved
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível salvar a sessão.'))
      return null
    } finally {
      setSaving(false)
    }
  }

  const goToSearch = async () => {
    if (!scheduleId) {
      const saved = await persist({ closeAfter: false })
      if (!saved) return
    }
    setTab('search')
  }

  const subjectName = subjects.find((s) => String(s.id) === String(form.subject_id))?.name ?? ''
  const searchSeed = form.topic.trim() || form.title.trim()

  return (
    <>
    <Modal
      open={open}
      onClose={onClose}
      size="lg"
      title={scheduleId ? 'Editar sessão de estudo' : 'Nova sessão de estudo'}
      description="Defina o que estudar, quando e com quanta antecedência ser lembrado."
      footer={
        <>
          {scheduleId && schedule?.status === 'pending' && (
            <Button variant="secondary" icon={Timer} onClick={() => setTimerOpen(true)}>
              Iniciar foco
            </Button>
          )}
          <div className="flex-1" />
          <Button variant="secondary" onClick={onClose}>
            Fechar
          </Button>
          <Button onClick={() => persist()} loading={saving}>
            {scheduleId ? 'Salvar alterações' : 'Agendar sessão'}
          </Button>
        </>
      }
    >
      <div className="mb-4 flex gap-1 border-b border-[var(--border)]">
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'details'}
          onClick={() => setTab('details')}
          className={`-mb-px flex items-center gap-1.5 border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors ${
            tab === 'details'
              ? 'border-brand-500 text-brand-600 dark:text-brand-400'
              : 'text-muted border-transparent hover:text-[var(--text)]'
          }`}
        >
          <CalendarClock className="h-4 w-4" aria-hidden />
          Detalhes
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={tab === 'search'}
          onClick={goToSearch}
          className={`-mb-px flex items-center gap-1.5 border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors ${
            tab === 'search'
              ? 'border-brand-500 text-brand-600 dark:text-brand-400'
              : 'text-muted border-transparent hover:text-[var(--text)]'
          }`}
        >
          <Sparkles className="h-4 w-4" aria-hidden />
          Conteúdo de apoio
          {savedLinks.length > 0 && (
            <Badge className="ml-0.5 px-1.5 py-0 text-[10px]">{savedLinks.length}</Badge>
          )}
        </button>
      </div>

      {tab === 'details' ? (
        <form onSubmit={(event) => event.preventDefault()} className="space-y-4" noValidate>
          <Input
            label="Título da sessão"
            placeholder="Ex.: Revisão de anatomia"
            value={form.title}
            onChange={(event) => update('title', event.target.value)}
            maxLength={200}
            required
          />

          <Input
            label="Tópico específico"
            placeholder="Ex.: partes do corpo humano"
            hint="Usado como base para a busca de conteúdo de apoio."
            value={form.topic}
            onChange={(event) => update('topic', event.target.value)}
            maxLength={255}
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Matéria"
              value={form.subject_id}
              onChange={(event) => update('subject_id', event.target.value)}
            >
              <option value="">Sem matéria</option>
              {subjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </Select>

            <Input
              label="Local"
              placeholder="Biblioteca, em casa…"
              value={form.location}
              onChange={(event) => update('location', event.target.value)}
              maxLength={160}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Início"
              type="datetime-local"
              value={form.start_at}
              onChange={(event) => update('start_at', event.target.value)}
              required
            />
            <Input
              label="Término"
              type="datetime-local"
              value={form.end_at}
              onChange={(event) => update('end_at', event.target.value)}
              required
            />
          </div>

          <Textarea
            label="Observações"
            placeholder="O que você pretende cobrir nesta sessão?"
            value={form.description}
            onChange={(event) => update('description', event.target.value)}
            maxLength={5000}
            rows={3}
          />

          <div className="space-y-3 rounded-xl bg-[var(--surface-sunken)] p-3.5">
            <Toggle
              id="reminder-enabled"
              checked={form.reminder_enabled}
              onChange={(value) => update('reminder_enabled', value)}
              label="Receber lembrete"
              description="Um aviso aparece na tela e, se autorizado, no sistema."
            />

            {form.reminder_enabled && (
              <Select
                label="Antecedência"
                value={form.remind_minutes}
                onChange={(event) => update('remind_minutes', Number(event.target.value))}
                options={REMINDER_OPTIONS}
              />
            )}
          </div>

          {!scheduleId && (
            <div className="space-y-3 rounded-xl bg-[var(--surface-sunken)] p-3.5">
              <Toggle
                id="repeat-weekly"
                checked={form.repeat_weekly}
                onChange={(value) => update('repeat_weekly', value)}
                label="Repetir semanalmente"
                description="Cria uma sessão no mesmo dia e horário toda semana."
              />

              {form.repeat_weekly && (
                <Input
                  label="Repetir até"
                  type="date"
                  value={form.repeat_until}
                  onChange={(event) => update('repeat_until', event.target.value)}
                  required
                />
              )}
            </div>
          )}

          {error && (
            <p role="alert" className="text-sm text-red-600 dark:text-red-400">
              {error}
            </p>
          )}
        </form>
      ) : (
        <ContentSearchPanel
          defaultQuery={searchSeed}
          subjectHint={subjectName}
          target={scheduleId ? { schedule_id: scheduleId } : null}
          savedLinks={savedLinks}
          autoSearch={Boolean(searchSeed)}
          onSaved={(link) => setSavedLinks((current) => [...current, link])}
          onRemoved={(link) =>
            setSavedLinks((current) => current.filter((item) => item.id !== link.id))
          }
        />
      )}
    </Modal>

    {scheduleId && (
      <FocusTimer
        open={timerOpen}
        onClose={() => setTimerOpen(false)}
        schedule={schedule}
        onComplete={async () => {
          try {
            const updated = await scheduleService.setStatus(scheduleId, 'completed')
            toast.success('Sessão concluída! 🎉')
            setTimerOpen(false)
            onSaved?.(updated)
            onClose()
          } catch (err) {
            toast.error(getErrorMessage(err, 'Não foi possível concluir a sessão.'))
          }
        }}
      />
    )}
    </>
  )
}
