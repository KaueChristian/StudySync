/** CRUD de matérias — grade de cartões com contadores. */
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  CalendarDays,
  GraduationCap,
  MoreVertical,
  Pencil,
  Plus,
  StickyNote,
  Trash2,
} from 'lucide-react'

import SubjectModal from '@/components/subjects/SubjectModal'
import Button from '@/components/ui/Button'
import { useConfirm } from '@/components/ui/ConfirmDialog'
import { CardSkeleton, EmptyState, PageHeading } from '@/components/ui/Misc'
import SubjectIcon from '@/components/ui/SubjectIcon'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'
import { subjectService } from '@/lib/services'

function SubjectCard({ subject, onEdit, onDelete }) {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <article className="card card-interactive relative flex flex-col p-5">
      <div className="flex items-start gap-3.5">
        <div
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
          style={{ backgroundColor: `${subject.color}1f`, color: subject.color }}
        >
          <SubjectIcon icon={subject.icon} className="h-6 w-6" />
        </div>

        <div className="min-w-0 flex-1">
          <h2 className="font-display truncate text-[17px]">{subject.name}</h2>
          <p className="text-muted mt-0.5 line-clamp-2 text-sm leading-snug">
            {subject.description || 'Sem descrição'}
          </p>
        </div>

        {/* Menu de ações */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((value) => !value)}
            onBlur={() => setTimeout(() => setMenuOpen(false), 150)}
            aria-label={`Ações de ${subject.name}`}
            className="text-subtle hover:text-[var(--text)] -mr-1 rounded-lg p-1.5 transition-colors hover:bg-[var(--surface-hover)]"
          >
            <MoreVertical className="h-4 w-4" />
          </button>

          {menuOpen && (
            <div className="card animate-scale-in absolute right-0 z-20 mt-1 w-40 origin-top-right overflow-hidden p-1.5 shadow-lg">
              <button
                type="button"
                onClick={() => onEdit(subject)}
                className="text-muted flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
              >
                <Pencil className="h-4 w-4" aria-hidden />
                Editar
              </button>
              <button
                type="button"
                onClick={() => onDelete(subject)}
                className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10"
              >
                <Trash2 className="h-4 w-4" aria-hidden />
                Excluir
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="mt-5 flex items-center gap-2 border-t border-[var(--border)] pt-4">
        <Link
          to={`/anotacoes?materia=${subject.id}`}
          className="text-muted flex flex-1 items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs font-medium transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
        >
          <StickyNote className="h-3.5 w-3.5" aria-hidden />
          {subject.notes_count} {subject.notes_count === 1 ? 'anotação' : 'anotações'}
        </Link>

        <span className="h-4 w-px bg-[var(--border)]" aria-hidden />

        <Link
          to={`/agenda?materia=${subject.id}`}
          className="text-muted flex flex-1 items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs font-medium transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
        >
          <CalendarDays className="h-3.5 w-3.5" aria-hidden />
          {subject.schedules_count} {subject.schedules_count === 1 ? 'sessão' : 'sessões'}
        </Link>
      </div>
    </article>
  )
}

export default function SubjectsPage() {
  const toast = useToast()
  const confirm = useConfirm()

  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setSubjects(await subjectService.list())
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível carregar as matérias.'))
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const openCreate = () => {
    setEditing(null)
    setModalOpen(true)
  }

  const openEdit = (subject) => {
    setEditing(subject)
    setModalOpen(true)
  }

  const handleDelete = async (subject) => {
    const ok = await confirm({
      title: `Excluir "${subject.name}"?`,
      description: `Todas as ${subject.notes_count} anotações e ${subject.schedules_count} sessões vinculadas a esta matéria também serão excluídas. Esta ação não pode ser desfeita.`,
      confirmLabel: 'Excluir matéria',
    })
    if (!ok) return

    try {
      await subjectService.remove(subject.id)
      setSubjects((current) => current.filter((item) => item.id !== subject.id))
      toast.success('Matéria excluída.')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível excluir a matéria.'))
    }
  }

  return (
    <>
      <PageHeading
        icon={GraduationCap}
        title="Matérias"
        description="Organize seus estudos por disciplina."
        actions={
          <Button icon={Plus} onClick={openCreate}>
            Nova matéria
          </Button>
        }
      />

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <CardSkeleton count={6} />
        </div>
      ) : subjects.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={GraduationCap}
            title="Nenhuma matéria ainda"
            description="Comece criando as disciplinas que você estuda. Depois você poderá anexar anotações e agendar sessões a cada uma delas."
            action={
              <Button icon={Plus} onClick={openCreate}>
                Criar primeira matéria
              </Button>
            }
          />
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {subjects.map((subject) => (
            <SubjectCard
              key={subject.id}
              subject={subject}
              onEdit={openEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      <SubjectModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        subject={editing}
        onSaved={load}
      />
    </>
  )
}
