/** Biblioteca: todos os links de apoio salvos pelo usuário. */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { BookMarked, ExternalLink, Search, Trash2 } from 'lucide-react'

import Button from '@/components/ui/Button'
import { useConfirm } from '@/components/ui/ConfirmDialog'
import { Badge, EmptyState, PageHeading, Skeleton } from '@/components/ui/Misc'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'
import { searchService } from '@/lib/services'
import { formatDate, prettyDomain } from '@/lib/format'

export default function LibraryPage() {
  const toast = useToast()
  const confirm = useConfirm()

  const [links, setLinks] = useState([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [origin, setOrigin] = useState('all')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setLinks(await searchService.saved({ limit: 200 }))
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível carregar a biblioteca.'))
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase()
    return links.filter((link) => {
      if (origin === 'notes' && !link.note_id) return false
      if (origin === 'schedules' && !link.schedule_id) return false
      if (!term) return true
      return (
        link.title.toLowerCase().includes(term) ||
        link.snippet?.toLowerCase().includes(term) ||
        link.source?.toLowerCase().includes(term)
      )
    })
  }, [links, query, origin])

  const handleDelete = async (link) => {
    const ok = await confirm({
      title: 'Remover este link?',
      description: link.title,
      confirmLabel: 'Remover',
    })
    if (!ok) return

    try {
      await searchService.remove(link.id)
      setLinks((current) => current.filter((item) => item.id !== link.id))
      toast.success('Link removido.')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível remover o link.'))
    }
  }

  const FILTERS = [
    { id: 'all', label: 'Todos', count: links.length },
    { id: 'notes', label: 'Em anotações', count: links.filter((l) => l.note_id).length },
    { id: 'schedules', label: 'Em sessões', count: links.filter((l) => l.schedule_id).length },
  ]

  return (
    <>
      <PageHeading
        icon={BookMarked}
        title="Biblioteca de links"
        description="Todo o conteúdo de apoio que você salvou, em um só lugar."
      />

      <div className="card mb-5 flex flex-wrap items-center gap-3 p-3.5">
        <div className="relative min-w-48 flex-1">
          <Search
            className="text-subtle pointer-events-none absolute top-1/2 left-3.5 h-4 w-4 -translate-y-1/2"
            aria-hidden
          />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Buscar nos links salvos…"
            aria-label="Buscar links salvos"
            className="focus:border-brand-500 focus:ring-brand-500/40 h-10 w-full rounded-xl border border-[var(--border-strong)] bg-[var(--surface)] pr-3.5 pl-10 text-sm transition-colors focus:ring-2 focus:outline-none"
          />
        </div>

        <div className="flex gap-1 rounded-xl bg-[var(--surface-sunken)] p-1">
          {FILTERS.map((filter) => (
            <button
              key={filter.id}
              type="button"
              onClick={() => setOrigin(filter.id)}
              aria-pressed={origin === filter.id}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                origin === filter.id
                  ? 'bg-[var(--surface)] text-[var(--text)] shadow-sm'
                  : 'text-muted hover:text-[var(--text)]'
              }`}
            >
              {filter.label} ({filter.count})
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="card space-y-2 p-4">
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-3 w-full" />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={BookMarked}
            title={links.length ? 'Nenhum link encontrado' : 'Biblioteca vazia'}
            description={
              links.length
                ? 'Tente outros termos ou mude o filtro de origem.'
                : 'Use a pesquisa de conteúdo para encontrar material de apoio e salvá-lo nas suas anotações e sessões.'
            }
          />
        </div>
      ) : (
        <ul className="space-y-3">
          {filtered.map((link) => (
            <li key={link.id} className="card card-interactive p-4">
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer nofollow"
                    className="font-display group flex items-start gap-1.5 text-[15px] leading-snug hover:underline"
                  >
                    <span className="min-w-0">{link.title}</span>
                    <ExternalLink
                      className="text-subtle mt-1 h-3.5 w-3.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
                      aria-hidden
                    />
                  </a>

                  {link.snippet && (
                    <p className="text-muted mt-1.5 line-clamp-2 text-sm leading-relaxed">
                      {link.snippet}
                    </p>
                  )}

                  <div className="mt-2.5 flex flex-wrap items-center gap-2">
                    <Badge>{link.source || prettyDomain(link.url)}</Badge>
                    <Badge>{link.note_id ? 'Anotação' : 'Sessão'}</Badge>
                    {link.query && (
                      <span className="text-subtle text-xs">busca: “{link.query}”</span>
                    )}
                    <span className="text-subtle ml-auto text-xs">
                      {formatDate(link.created_at)}
                    </span>
                  </div>
                </div>

                <Button
                  variant="danger-ghost"
                  size="icon-sm"
                  icon={Trash2}
                  onClick={() => handleDelete(link)}
                  aria-label={`Remover ${link.title}`}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
