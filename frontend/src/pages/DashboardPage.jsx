/** Painel inicial: métricas, próximas sessões, anotações recentes e distribuição. */
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  BookMarked,
  CalendarClock,
  CalendarPlus,
  CheckCircle2,
  Clock,
  GraduationCap,
  Plus,
  Sparkles,
  StickyNote,
  TrendingUp,
} from 'lucide-react'

import ScheduleCard from '@/components/schedule/ScheduleCard'
import Button from '@/components/ui/Button'
import { Badge, EmptyState, PageHeading, Skeleton } from '@/components/ui/Misc'
import { SubjectAvatar } from '@/components/ui/SubjectIcon'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'
import { dashboardService, scheduleService } from '@/lib/services'
import { formatMinutes, formatRelative } from '@/lib/format'

function greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Bom dia'
  if (hour < 18) return 'Boa tarde'
  return 'Boa noite'
}

function StatCard({ icon: Icon, label, value, hint, to, accent }) {
  const content = (
    <>
      <div className="flex items-start justify-between">
        <div className={`rounded-xl p-2.5 ${accent}`}>
          <Icon className="h-[18px] w-[18px]" aria-hidden />
        </div>
        {to && <ArrowRight className="text-subtle h-4 w-4" aria-hidden />}
      </div>
      <p className="mt-3.5 text-2xl font-bold tracking-tight">{value}</p>
      <p className="text-muted text-sm">{label}</p>
      {hint && <p className="text-subtle mt-1 text-xs">{hint}</p>}
    </>
  )

  return to ? (
    <Link to={to} className="card card-interactive block p-4">
      {content}
    </Link>
  ) : (
    <div className="card p-4">{content}</div>
  )
}

/** Gráfico de barras horizontais da distribuição por matéria. */
function DistributionChart({ data }) {
  const max = Math.max(1, ...data.map((item) => item.notes + item.sessions))

  return (
    <ul className="space-y-3">
      {data.map((item) => {
        const total = item.notes + item.sessions
        return (
          <li key={item.subject_id}>
            <div className="mb-1.5 flex items-center justify-between text-sm">
              <span className="flex items-center gap-2 truncate font-medium">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: item.color }}
                  aria-hidden
                />
                {item.name}
              </span>
              <span className="text-muted shrink-0 text-xs">
                {item.notes} {item.notes === 1 ? 'nota' : 'notas'} · {item.sessions}{' '}
                {item.sessions === 1 ? 'sessão' : 'sessões'}
              </span>
            </div>
            <div
              className="h-2 overflow-hidden rounded-full bg-[var(--surface-sunken)]"
              role="img"
              aria-label={`${item.name}: ${total} itens`}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${(total / max) * 100}%`, backgroundColor: item.color }}
              />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      setData(await dashboardService.get())
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível carregar o painel.'))
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleStatusChange = async (schedule, status) => {
    try {
      await scheduleService.setStatus(schedule.id, status)
      toast.success(status === 'completed' ? 'Sessão concluída! 🎉' : 'Status atualizado.')
      load()
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível alterar o status.'))
    }
  }

  if (loading) {
    return (
      <>
        <Skeleton className="mb-6 h-9 w-64" />
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="card space-y-3 p-4">
              <Skeleton className="h-10 w-10 rounded-xl" />
              <Skeleton className="h-7 w-16" />
              <Skeleton className="h-3 w-24" />
            </div>
          ))}
        </div>
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="card h-72 lg:col-span-2" />
          <div className="card h-72" />
        </div>
      </>
    )
  }

  if (!data) return null

  const { stats, upcoming, recent_notes: recentNotes, distribution, weekly_activity: weekly } = data
  const isEmpty = stats.subjects === 0 && stats.notes === 0 && stats.sessions_upcoming === 0
  const weeklyMax = Math.max(1, ...weekly.map((day) => day.count))

  return (
    <>
      <PageHeading
        title={`${greeting()}, ${user?.name?.split(' ')[0] ?? 'estudante'}!`}
        description={
          stats.sessions_today > 0
            ? `Você tem ${stats.sessions_today} ${stats.sessions_today === 1 ? 'sessão' : 'sessões'} hoje. Bons estudos!`
            : 'Nenhuma sessão para hoje — bom momento para planejar a semana.'
        }
        actions={
          <>
            <Button variant="secondary" icon={Plus} onClick={() => navigate('/anotacoes')}>
              Anotação
            </Button>
            <Button icon={CalendarPlus} onClick={() => navigate('/agenda')}>
              Agendar sessão
            </Button>
          </>
        }
      />

      {isEmpty ? (
        <div className="card">
          <EmptyState
            icon={GraduationCap}
            title="Vamos começar?"
            description="Cadastre suas matérias, escreva anotações em Markdown e agende sessões de estudo. O StudySync avisa você antes de cada uma e ainda busca conteúdo de apoio na web."
            action={
              <Button icon={GraduationCap} onClick={() => navigate('/materias')}>
                Criar minha primeira matéria
              </Button>
            }
          />
        </div>
      ) : (
        <>
          {/* ------------------------------------------------------ métricas */}
          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              icon={CalendarClock}
              label="Sessões pendentes"
              value={stats.sessions_upcoming}
              hint={
                stats.minutes_scheduled_week
                  ? `${formatMinutes(stats.minutes_scheduled_week)} planejados nos próximos 7 dias`
                  : undefined
              }
              to="/agenda"
              accent="bg-brand-50 text-brand-600 dark:bg-brand-500/12 dark:text-brand-400"
            />
            <StatCard
              icon={CheckCircle2}
              label="Sessões concluídas"
              value={stats.sessions_completed}
              to="/agenda"
              accent="bg-emerald-50 text-emerald-600 dark:bg-emerald-500/12 dark:text-emerald-400"
            />
            <StatCard
              icon={StickyNote}
              label="Anotações"
              value={stats.notes}
              hint={`em ${stats.subjects} ${stats.subjects === 1 ? 'matéria' : 'matérias'}`}
              to="/anotacoes"
              accent="bg-amber-50 text-amber-600 dark:bg-amber-500/12 dark:text-amber-400"
            />
            <StatCard
              icon={BookMarked}
              label="Links salvos"
              value={stats.saved_links}
              to="/biblioteca"
              accent="bg-purple-50 text-purple-600 dark:bg-purple-500/12 dark:text-purple-400"
            />
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            {/* -------------------------------------------- próximas sessões */}
            <section className="lg:col-span-2">
              <header className="mb-3.5 flex items-center justify-between">
                <h2 className="flex items-center gap-2 font-semibold">
                  <CalendarClock className="text-brand-500 h-[18px] w-[18px]" aria-hidden />
                  Próximas sessões
                </h2>
                <Link
                  to="/agenda"
                  className="text-brand-600 dark:text-brand-400 text-sm font-medium hover:underline"
                >
                  Ver agenda
                </Link>
              </header>

              {upcoming.length === 0 ? (
                <div className="card">
                  <EmptyState
                    icon={CalendarPlus}
                    title="Nada agendado"
                    description="Planeje sua próxima sessão de estudo e receba um lembrete antes dela começar."
                    className="py-10"
                    action={
                      <Button size="sm" icon={CalendarPlus} onClick={() => navigate('/agenda')}>
                        Agendar sessão
                      </Button>
                    }
                  />
                </div>
              ) : (
                <div className="space-y-3">
                  {upcoming.map((schedule) => (
                    <ScheduleCard
                      key={schedule.id}
                      schedule={schedule}
                      compact
                      onStatusChange={handleStatusChange}
                      onEdit={() => navigate(`/agenda?sessao=${schedule.id}`)}
                    />
                  ))}
                </div>
              )}
            </section>

            {/* --------------------------------------------------- coluna lateral */}
            <div className="space-y-5">
              {/* Atividade da semana */}
              <section className="card p-5">
                <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold">
                  <TrendingUp className="text-brand-500 h-4 w-4" aria-hidden />
                  Sessões concluídas (7 dias)
                </h2>

                <div className="flex h-24 items-end justify-between gap-1.5">
                  {weekly.map((day) => {
                    const date = new Date(`${day.date}T12:00:00`)
                    return (
                      <div key={day.date} className="flex flex-1 flex-col items-center gap-1.5">
                        <div
                          className="bg-brand-500 hover:bg-brand-600 w-full rounded-t-md transition-all"
                          style={{ height: `${Math.max(4, (day.count / weeklyMax) * 72)}px` }}
                          title={`${day.count} sessão(ões)`}
                        />
                        <span className="text-subtle text-[10px]">
                          {date.toLocaleDateString('pt-BR', { weekday: 'narrow' })}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </section>

              {/* Distribuição por matéria */}
              {distribution.length > 0 && (
                <section className="card p-5">
                  <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold">
                    <GraduationCap className="text-brand-500 h-4 w-4" aria-hidden />
                    Distribuição por matéria
                  </h2>
                  <DistributionChart data={distribution} />
                </section>
              )}

              {/* Atalho para a pesquisa */}
              <section className="card from-brand-600 to-brand-800 border-0 bg-gradient-to-br p-5 text-white">
                <Sparkles className="h-6 w-6" aria-hidden />
                <h2 className="mt-3 font-semibold">Precisa de material?</h2>
                <p className="text-brand-100 mt-1 text-sm leading-relaxed">
                  Pesquise qualquer tema e receba os 5 links mais relevantes e confiáveis
                  para estudar.
                </p>
                <Button
                  variant="secondary"
                  size="sm"
                  className="mt-4 w-full !text-brand-700 !border-transparent"
                  onClick={() => navigate('/pesquisa')}
                >
                  Buscar conteúdo
                </Button>
              </section>
            </div>
          </div>

          {/* ------------------------------------------------ notas recentes */}
          {recentNotes.length > 0 && (
            <section className="mt-6">
              <header className="mb-3.5 flex items-center justify-between">
                <h2 className="flex items-center gap-2 font-semibold">
                  <StickyNote className="text-brand-500 h-[18px] w-[18px]" aria-hidden />
                  Anotações recentes
                </h2>
                <Link
                  to="/anotacoes"
                  className="text-brand-600 dark:text-brand-400 text-sm font-medium hover:underline"
                >
                  Ver todas
                </Link>
              </header>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {recentNotes.map((note) => (
                  <Link
                    key={note.id}
                    to={`/anotacoes?q=${encodeURIComponent(note.title)}`}
                    className="card card-interactive flex flex-col p-4"
                  >
                    <div className="flex items-start gap-2.5">
                      {note.subject ? (
                        <SubjectAvatar subject={note.subject} size="sm" />
                      ) : (
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--surface-sunken)]">
                          <StickyNote className="text-subtle h-4 w-4" aria-hidden />
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        <h3 className="font-display line-clamp-1 text-[15px]">{note.title}</h3>
                        <p className="text-subtle text-xs">
                          {note.subject?.name ?? 'Sem matéria'}
                        </p>
                      </div>
                    </div>

                    {note.excerpt && (
                      <p className="text-muted mt-2.5 line-clamp-2 flex-1 text-sm">
                        {note.excerpt}
                      </p>
                    )}

                    <div className="mt-3 flex items-center gap-1.5">
                      {note.category && <Badge>{note.category}</Badge>}
                      <span className="text-subtle ml-auto flex items-center gap-1 text-xs">
                        <Clock className="h-3 w-3" aria-hidden />
                        {formatRelative(note.updated_at)}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </>
  )
}
