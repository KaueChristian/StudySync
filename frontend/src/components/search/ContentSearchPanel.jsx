/**
 * Painel "Buscar Conteúdo de Apoio".
 *
 * Reutilizado no editor de anotações, no modal de agendamento e na página
 * de pesquisa. Dado um tema, chama o motor de busca do backend, mostra os
 * links ranqueados e permite salvá-los no destino informado.
 *
 * Props:
 *   - defaultQuery : tema pré-preenchido (título/tópico do item)
 *   - subjectHint  : nome da matéria, usado para refinar a consulta
 *   - target       : { note_id } | { schedule_id } — onde salvar
 *   - savedLinks   : links já anexados (evita duplicar e permite remover)
 *   - onSaved / onRemoved : callbacks para o componente pai ressincronizar
 */
import { useCallback, useEffect, useState } from 'react'
import {
  BookmarkPlus,
  Check,
  ExternalLink,
  Link2Off,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
} from 'lucide-react'

import Button from '@/components/ui/Button'
import { Badge, EmptyState, Skeleton } from '@/components/ui/Misc'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'
import { searchService } from '@/lib/services'
import { prettyDomain } from '@/lib/format'

/** Traduz a pontuação de relevância em um rótulo legível. */
function relevanceBadge(score) {
  if (score >= 65) return { label: 'Alta relevância', className: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/25' }
  if (score >= 45) return { label: 'Relevante', className: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/25' }
  return { label: 'Complementar', className: '' }
}

export default function ContentSearchPanel({
  defaultQuery = '',
  subjectHint = '',
  target = null,
  savedLinks = [],
  onSaved,
  onRemoved,
  autoSearch = false,
}) {
  const toast = useToast()

  const [query, setQuery] = useState(defaultQuery)
  const [results, setResults] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const [savingUrl, setSavingUrl] = useState(null)
  const [error, setError] = useState('')

  // URLs já salvas — usadas para marcar o botão como "salvo".
  const savedUrls = new Set(savedLinks.map((link) => link.url))

  useEffect(() => {
    setQuery(defaultQuery)
  }, [defaultQuery])

  const runSearch = useCallback(
    async (term, refresh = false) => {
      const value = (term ?? '').trim()
      if (value.length < 2) {
        setError('Digite ao menos 2 caracteres para pesquisar.')
        return
      }

      setLoading(true)
      setError('')
      try {
        const data = await searchService.run(
          { query: value, limit: 5, subject_hint: subjectHint || null },
          refresh,
        )
        setResults(data.results)
        setMeta({ provider: data.provider, cached: data.cached, took: data.took_ms, query: data.query })
        if (!data.results.length) setError('Nenhum resultado encontrado. Tente outros termos.')
      } catch (err) {
        setError(getErrorMessage(err, 'A busca falhou.'))
        setResults([])
      } finally {
        setLoading(false)
      }
    },
    [subjectHint],
  )

  // Busca automática ao abrir (usado quando o item já tem um tópico definido).
  useEffect(() => {
    if (autoSearch && defaultQuery.trim().length >= 2) runSearch(defaultQuery)
    // Intencionalmente só na montagem: buscas seguintes são disparadas pelo usuário.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSave = async (result) => {
    if (!target) {
      toast.info('Salve o item primeiro', {
        description: 'Os links podem ser anexados depois que a anotação ou sessão for criada.',
      })
      return
    }

    setSavingUrl(result.url)
    try {
      const saved = await searchService.save({
        title: result.title,
        url: result.url,
        snippet: result.snippet,
        source: result.source,
        query: meta?.query ?? query,
        ...target,
      })
      onSaved?.(saved)
      toast.success('Link salvo!', { description: prettyDomain(result.url) })
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível salvar o link.'))
    } finally {
      setSavingUrl(null)
    }
  }

  const handleRemove = async (link) => {
    try {
      await searchService.remove(link.id)
      onRemoved?.(link)
      toast.success('Link removido.')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível remover o link.'))
    }
  }

  return (
    <div className="space-y-4">
      {/* ---------------------------------------------------------- busca */}
      <form
        onSubmit={(event) => {
          event.preventDefault()
          runSearch(query)
        }}
        className="flex gap-2"
      >
        <div className="relative flex-1">
          <Search
            className="text-subtle pointer-events-none absolute top-1/2 left-3.5 h-4 w-4 -translate-y-1/2"
            aria-hidden
          />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ex.: partes do corpo humano"
            aria-label="Tema para buscar conteúdo de apoio"
            className="h-11 w-full rounded-xl border border-[var(--border-strong)] bg-[var(--surface)] pr-3.5 pl-10 text-[var(--text)] transition-colors placeholder:text-[var(--text-subtle)] focus:border-brand-500 focus:ring-2 focus:ring-brand-500/40 focus:outline-none"
          />
        </div>

        <Button type="submit" size="lg" icon={Sparkles} loading={loading}>
          <span className="hidden sm:inline">Buscar</span>
        </Button>

        {results.length > 0 && (
          <Button
            type="button"
            variant="secondary"
            size="lg"
            icon={RefreshCw}
            disabled={loading}
            onClick={() => runSearch(query, true)}
            title="Refazer a busca ignorando o cache"
          />
        )}
      </form>

      {subjectHint && (
        <p className="text-subtle text-xs">
          A busca inclui automaticamente o contexto da matéria{' '}
          <strong className="text-[var(--text-muted)]">{subjectHint}</strong> para resultados
          mais precisos.
        </p>
      )}

      {/* -------------------------------------------------------- estados */}
      {loading && (
        <div className="space-y-2.5">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="card space-y-2 p-4">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-2/3" />
            </div>
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-sm text-amber-800 dark:border-amber-500/25 dark:bg-amber-500/10 dark:text-amber-300">
          {error}
        </div>
      )}

      {/* ------------------------------------------------------ resultados */}
      {!loading && results.length > 0 && (
        <>
          <div className="text-subtle flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
            <span>
              <strong className="text-[var(--text-muted)]">{results.length}</strong> resultados
            </span>
            <span aria-hidden>·</span>
            <span>via {meta?.provider}</span>
            <span aria-hidden>·</span>
            <span>{meta?.cached ? 'do cache' : `${meta?.took}ms`}</span>
          </div>

          <ul className="space-y-2.5">
            {results.map((result, index) => {
              const isSaved = savedUrls.has(result.url)
              const relevance = relevanceBadge(result.score)

              return (
                <li key={result.url} className="card card-interactive p-4">
                  <div className="flex items-start gap-3">
                    <span className="bg-brand-50 text-brand-700 dark:bg-brand-500/12 dark:text-brand-300 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-xs font-bold">
                      {index + 1}
                    </span>

                    <div className="min-w-0 flex-1">
                      <a
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer nofollow"
                        className="group flex items-start gap-1.5 text-sm leading-snug font-semibold hover:underline"
                      >
                        <span className="min-w-0">{result.title}</span>
                        <ExternalLink
                          className="text-subtle mt-0.5 h-3.5 w-3.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
                          aria-hidden
                        />
                      </a>

                      {result.snippet && (
                        <p className="text-muted mt-1.5 line-clamp-2 text-sm leading-relaxed">
                          {result.snippet}
                        </p>
                      )}

                      <div className="mt-2.5 flex flex-wrap items-center gap-2">
                        <Badge>{result.source}</Badge>
                        <Badge className={relevance.className}>{relevance.label}</Badge>
                      </div>
                    </div>

                    <Button
                      variant={isSaved ? 'ghost' : 'secondary'}
                      size="sm"
                      icon={isSaved ? Check : BookmarkPlus}
                      disabled={isSaved}
                      loading={savingUrl === result.url}
                      onClick={() => handleSave(result)}
                      title={isSaved ? 'Já salvo neste item' : 'Salvar link'}
                      className={isSaved ? 'text-emerald-600 dark:text-emerald-400' : ''}
                    >
                      <span className="hidden sm:inline">{isSaved ? 'Salvo' : 'Salvar'}</span>
                    </Button>
                  </div>
                </li>
              )
            })}
          </ul>
        </>
      )}

      {!loading && !results.length && !error && (
        <EmptyState
          icon={Search}
          title="Busque conteúdo de apoio"
          description="Digite o tema que você vai estudar e receba os 5 links mais relevantes e confiáveis sobre o assunto."
          className="py-10"
        />
      )}

      {/* -------------------------------------------------- links salvos */}
      {savedLinks.length > 0 && (
        <section className="border-t border-[var(--border)] pt-4">
          <h3 className="mb-2.5 flex items-center gap-2 text-sm font-semibold">
            <BookmarkPlus className="text-brand-500 h-4 w-4" aria-hidden />
            Links salvos ({savedLinks.length})
          </h3>

          <ul className="space-y-2">
            {savedLinks.map((link) => (
              <li
                key={link.id}
                className="flex items-start gap-2.5 rounded-xl bg-[var(--surface-sunken)] p-3"
              >
                <div className="min-w-0 flex-1">
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer nofollow"
                    className="line-clamp-1 text-sm font-medium hover:underline"
                  >
                    {link.title}
                  </a>
                  <p className="text-subtle mt-0.5 truncate text-xs">
                    {link.source || prettyDomain(link.url)}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => handleRemove(link)}
                  aria-label={`Remover ${link.title}`}
                  className="text-subtle rounded-lg p-1.5 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-500/10 dark:hover:text-red-400"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {!target && (
        <p className="text-subtle flex items-center gap-1.5 text-xs">
          <Link2Off className="h-3.5 w-3.5" aria-hidden />
          Salve o item primeiro para poder anexar links a ele.
        </p>
      )}
    </div>
  )
}
