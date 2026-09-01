/** Listagem de anotações com filtros, busca e paginação. */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  ChevronLeft,
  ChevronRight,
  Link2,
  Pin,
  Plus,
  Search,
  SlidersHorizontal,
  StickyNote,
  Trash2,
  X,
} from 'lucide-react'

import NoteEditorModal from '@/components/notes/NoteEditorModal'
import Button from '@/components/ui/Button'
import { useConfirm } from '@/components/ui/ConfirmDialog'
import { Badge, CardSkeleton, EmptyState, PageHeading } from '@/components/ui/Misc'
import { SubjectAvatar } from '@/components/ui/SubjectIcon'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'
import { noteService, subjectService, tagService } from '@/lib/services'
import { formatRelative } from '@/lib/format'

const PAGE_SIZE = 12

function NoteCard({ note, onOpen, onDelete }) {
  return (
    <article
      onClick={() => onOpen(note)}
      className="card card-interactive group flex cursor-pointer flex-col p-5"
    >
      <header className="flex items-start gap-3">
        {note.subject ? (
          <SubjectAvatar subject={note.subject} size="sm" />
        ) : (
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--surface-sunken)]">
            <StickyNote className="text-subtle h-4 w-4" aria-hidden />
          </div>
        )}

        <div className="min-w-0 flex-1">
          <h2 className="font-display flex items-start gap-1.5 text-[17px] leading-snug">
            {note.is_pinned && (
              <Pin className="text-brand-500 mt-0.5 h-3.5 w-3.5 shrink-0 fill-current" aria-label="Fixada" />
            )}
            <span className="line-clamp-2">{note.title}</span>
          </h2>
          {note.subject && (
            <p className="text-subtle mt-0.5 truncate text-xs">{note.subject.name}</p>
          )}
        </div>

        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation()
            onDelete(note)
          }}
          aria-label={`Excluir ${note.title}`}
          className="text-subtle -mt-1 -mr-1 rounded-lg p-1.5 opacity-0 transition-all group-hover:opacity-100 hover:bg-red-50 hover:text-red-600 focus:opacity-100 dark:hover:bg-red-500/10 dark:hover:text-red-400"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </header>

      {note.excerpt && (
        <p className="text-muted mt-3 line-clamp-3 flex-1 text-sm leading-relaxed">
          {note.excerpt}
        </p>
      )}

      <footer className="mt-4 flex flex-wrap items-center gap-1.5 border-t border-[var(--border)] pt-3.5">
        {note.category && <Badge>{note.category}</Badge>}
        {note.tags.slice(0, 3).map((tag) => (
          <Badge key={tag.id} className="bg-brand-50 text-brand-700 border-brand-100 dark:bg-brand-500/10 dark:text-brand-300 dark:border-brand-500/20">
            #{tag.name}
          </Badge>
        ))}
        {note.tags.length > 3 && <Badge>+{note.tags.length - 3}</Badge>}

        <span className="text-subtle ml-auto flex items-center gap-2 text-xs">
          {note.links_count > 0 && (
            <span className="flex items-center gap-1" title={`${note.links_count} links salvos`}>
              <Link2 className="h-3 w-3" aria-hidden />
              {note.links_count}
            </span>
          )}
          {formatRelative(note.updated_at)}
        </span>
      </footer>
    </article>
  )
}

export default function NotesPage() {
  const toast = useToast()
  const confirm = useConfirm()
  const [searchParams, setSearchParams] = useSearchParams()

  const [notes, setNotes] = useState([])
  const [pagination, setPagination] = useState({ total: 0, pages: 0 })
  const [subjects, setSubjects] = useState([])
  const [tags, setTags] = useState([])
  const [loading, setLoading] = useState(true)

  const [editorOpen, setEditorOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [showFilters, setShowFilters] = useState(false)

  // Os filtros vivem na URL: recarregar ou compartilhar o link preserva a visão.
  const filters = useMemo(
    () => ({
      subject_id: searchParams.get('materia') ?? '',
      tag: searchParams.get('tag') ?? '',
      search: searchParams.get('q') ?? '',
      sort: searchParams.get('ordem') ?? 'updated_at',
      page: Number(searchParams.get('pagina') ?? 1),
    }),
    [searchParams],
  )

  const [searchDraft, setSearchDraft] = useState(filters.search)

  const setFilter = useCallback(
    (patch) => {
      setSearchParams((current) => {
        const next = new URLSearchParams(current)
        Object.entries(patch).forEach(([key, value]) => {
          if (value === '' || value === null || value === undefined) next.delete(key)
          else next.set(key, String(value))
        })
        // Qualquer mudança de filtro reinicia a paginação.
        if (!('pagina' in patch)) next.delete('pagina')
        return next
      })
    },
    [setSearchParams],
  )

  // ----------------------------------------------------------------- carga
  const loadNotes = useCallback(async () => {
    setLoading(true)
    try {
      const data = await noteService.list({
        page: filters.page,
        page_size: PAGE_SIZE,
        subject_id: filters.subject_id || undefined,
        tag: filters.tag || undefined,
        search: filters.search || undefined,
        sort: filters.sort,
      })
      setNotes(data.items)
      setPagination({ total: data.total, pages: data.pages })
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível carregar as anotações.'))
    } finally {
      setLoading(false)
    }
  }, [filters, toast])

  const loadAux = useCallback(async () => {
    try {
      const [subjectList, tagList] = await Promise.all([
        subjectService.list(),
        tagService.list(),
      ])
      setSubjects(subjectList)
      setTags(tagList)
    } catch {
      // Filtros auxiliares são opcionais — falha silenciosa é aceitável.
    }
  }, [])

  useEffect(() => {
    loadNotes()
  }, [loadNotes])

  useEffect(() => {
    loadAux()
  }, [loadAux])

  // Debounce da busca textual para não disparar uma requisição por tecla.
  useEffect(() => {
    if (searchDraft === filters.search) return undefined
    const timer = setTimeout(() => setFilter({ q: searchDraft }), 400)
    return () => clearTimeout(timer)
  }, [searchDraft, filters.search, setFilter])

  // ---------------------------------------------------------------- ações
  const openNote = async (note) => {
    try {
      // A listagem devolve só o resumo; buscamos a anotação completa.
      setEditing(await noteService.get(note.id))
      setEditorOpen(true)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível abrir a anotação.'))
    }
  }

  const handleDelete = async (note) => {
    const ok = await confirm({
      title: `Excluir "${note.title}"?`,
      description: 'A anotação e os links de apoio salvos nela serão removidos permanentemente.',
      confirmLabel: 'Excluir anotação',
    })
    if (!ok) return

    try {
      await noteService.remove(note.id)
      toast.success('Anotação excluída.')
      loadNotes()
      loadAux()
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível excluir a anotação.'))
    }
  }

  const activeFilterCount = [filters.subject_id, filters.tag, filters.search].filter(Boolean).length

  return (
    <>
      <PageHeading
        icon={StickyNote}
        title="Anotações"
        description={
          pagination.total
            ? `${pagination.total} ${pagination.total === 1 ? 'anotação' : 'anotações'}`
            : 'Escreva em Markdown e anexe conteúdo de apoio.'
        }
        actions={
          <Button
            icon={Plus}
            onClick={() => {
              setEditing(null)
              setEditorOpen(true)
            }}
          >
            Nova anotação
          </Button>
        }
      />

      {/* ------------------------------------------------------- filtros */}
      <div className="card mb-5 p-3.5">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative min-w-48 flex-1">
            <Search
              className="text-subtle pointer-events-none absolute top-1/2 left-3.5 h-4 w-4 -translate-y-1/2"
              aria-hidden
            />
            <input
              type="search"
              value={searchDraft}
              onChange={(event) => setSearchDraft(event.target.value)}
              placeholder="Buscar no título e no conteúdo…"
              aria-label="Buscar anotações"
              className="focus:border-brand-500 focus:ring-brand-500/40 h-10 w-full rounded-xl border border-[var(--border-strong)] bg-[var(--surface)] pr-3.5 pl-10 text-sm transition-colors placeholder:text-[var(--text-subtle)] focus:ring-2 focus:outline-none"
            />
          </div>

          <Button
            variant={showFilters || activeFilterCount ? 'primary' : 'secondary'}
            icon={SlidersHorizontal}
            onClick={() => setShowFilters((value) => !value)}
          >
            Filtros
            {activeFilterCount > 0 && (
              <span className="ml-0.5 rounded-lg bg-white/25 px-1.5 text-xs">
                {activeFilterCount}
              </span>
            )}
          </Button>
        </div>

        {showFilters && (
          <div className="animate-fade-in mt-3.5 grid gap-3 border-t border-[var(--border)] pt-3.5 sm:grid-cols-3">
            <select
              value={filters.subject_id}
              onChange={(event) => setFilter({ materia: event.target.value })}
              aria-label="Filtrar por matéria"
              className="h-10 rounded-xl border border-[var(--border-strong)] bg-[var(--surface)] px-3 text-sm"
            >
              <option value="">Todas as matérias</option>
              {subjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </select>

            <select
              value={filters.tag}
              onChange={(event) => setFilter({ tag: event.target.value })}
              aria-label="Filtrar por tag"
              className="h-10 rounded-xl border border-[var(--border-strong)] bg-[var(--surface)] px-3 text-sm"
            >
              <option value="">Todas as tags</option>
              {tags.map((tag) => (
                <option key={tag.id} value={tag.name}>
                  #{tag.name} ({tag.notes_count})
                </option>
              ))}
            </select>

            <select
              value={filters.sort}
              onChange={(event) => setFilter({ ordem: event.target.value })}
              aria-label="Ordenar anotações"
              className="h-10 rounded-xl border border-[var(--border-strong)] bg-[var(--surface)] px-3 text-sm"
            >
              <option value="updated_at">Editadas recentemente</option>
              <option value="created_at">Criadas recentemente</option>
              <option value="title">Ordem alfabética</option>
            </select>

            {activeFilterCount > 0 && (
              <button
                type="button"
                onClick={() => {
                  setSearchDraft('')
                  setSearchParams({})
                }}
                className="text-muted flex items-center justify-center gap-1.5 rounded-xl border border-dashed border-[var(--border-strong)] px-3 py-2 text-sm transition-colors hover:text-[var(--text)] sm:col-span-3"
              >
                <X className="h-3.5 w-3.5" aria-hidden />
                Limpar filtros
              </button>
            )}
          </div>
        )}
      </div>

      {/* -------------------------------------------------------- listagem */}
      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <CardSkeleton count={6} />
        </div>
      ) : notes.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={StickyNote}
            title={activeFilterCount ? 'Nenhum resultado' : 'Nenhuma anotação ainda'}
            description={
              activeFilterCount
                ? 'Tente ajustar ou limpar os filtros aplicados.'
                : 'Crie sua primeira anotação em Markdown e anexe links de apoio pesquisados na web.'
            }
            action={
              activeFilterCount ? (
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSearchDraft('')
                    setSearchParams({})
                  }}
                >
                  Limpar filtros
                </Button>
              ) : (
                <Button
                  icon={Plus}
                  onClick={() => {
                    setEditing(null)
                    setEditorOpen(true)
                  }}
                >
                  Criar primeira anotação
                </Button>
              )
            }
          />
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {notes.map((note) => (
              <NoteCard key={note.id} note={note} onOpen={openNote} onDelete={handleDelete} />
            ))}
          </div>

          {pagination.pages > 1 && (
            <nav className="mt-6 flex items-center justify-center gap-2" aria-label="Paginação">
              <Button
                variant="secondary"
                size="sm"
                icon={ChevronLeft}
                disabled={filters.page <= 1}
                onClick={() => setFilter({ pagina: filters.page - 1 })}
              >
                Anterior
              </Button>
              <span className="text-muted px-3 text-sm">
                Página {filters.page} de {pagination.pages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={filters.page >= pagination.pages}
                onClick={() => setFilter({ pagina: filters.page + 1 })}
              >
                Próxima
                <ChevronRight className="h-4 w-4" aria-hidden />
              </Button>
            </nav>
          )}
        </>
      )}

      <NoteEditorModal
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        note={editing}
        subjects={subjects}
        tagSuggestions={tags}
        defaultSubjectId={filters.subject_id}
        onSaved={() => {
          loadNotes()
          loadAux()
        }}
      />
    </>
  )
}
