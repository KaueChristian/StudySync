/**
 * Editor de anotações.
 *
 * Três abas:
 *   Escrever   — textarea Markdown com barra de formatação
 *   Visualizar — pré-visualização renderizada
 *   Conteúdo   — busca de links de apoio (só após a anotação existir)
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Bold,
  Code,
  Eye,
  Heading2,
  Italic,
  Link as LinkIcon,
  List,
  ListChecks,
  PenLine,
  Quote,
  Sparkles,
  Table,
} from 'lucide-react'

import ContentSearchPanel from '@/components/search/ContentSearchPanel'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Field'
import { Badge } from '@/components/ui/Misc'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'
import { noteService } from '@/lib/services'
import { NOTE_CATEGORIES } from '@/lib/constants'
import Markdown from './Markdown'
import TagInput from './TagInput'

const EMPTY = {
  title: '',
  content: '',
  subject_id: '',
  category: '',
  tags: [],
  is_pinned: false,
}

/** Botões da barra de formatação: [ícone, título, prefixo, sufixo, placeholder]. */
const TOOLBAR = [
  { icon: Heading2, title: 'Título', prefix: '## ', suffix: '', sample: 'Título' },
  { icon: Bold, title: 'Negrito', prefix: '**', suffix: '**', sample: 'texto' },
  { icon: Italic, title: 'Itálico', prefix: '_', suffix: '_', sample: 'texto' },
  { icon: List, title: 'Lista', prefix: '- ', suffix: '', sample: 'item' },
  { icon: ListChecks, title: 'Checklist', prefix: '- [ ] ', suffix: '', sample: 'tarefa' },
  { icon: Quote, title: 'Citação', prefix: '> ', suffix: '', sample: 'citação' },
  { icon: Code, title: 'Código', prefix: '`', suffix: '`', sample: 'código' },
  { icon: LinkIcon, title: 'Link', prefix: '[', suffix: '](https://)', sample: 'texto' },
  {
    icon: Table,
    title: 'Tabela',
    prefix: '\n| Coluna A | Coluna B |\n|---|---|\n| ',
    suffix: ' |  |\n',
    sample: 'valor',
  },
]

export default function NoteEditorModal({
  open,
  onClose,
  note,
  subjects = [],
  tagSuggestions = [],
  defaultSubjectId = '',
  onSaved,
}) {
  const toast = useToast()
  const textareaRef = useRef(null)

  const [form, setForm] = useState(EMPTY)
  const [tab, setTab] = useState('write')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  // Id da anotação persistida — permite anexar links já na primeira criação.
  const [noteId, setNoteId] = useState(null)
  const [savedLinks, setSavedLinks] = useState([])

  useEffect(() => {
    if (!open) return

    if (note) {
      setForm({
        title: note.title,
        content: note.content ?? '',
        subject_id: note.subject_id ?? '',
        category: note.category ?? '',
        tags: note.tags?.map((tag) => tag.name) ?? [],
        is_pinned: note.is_pinned,
      })
      setNoteId(note.id)
      setSavedLinks(note.search_results ?? [])
    } else {
      setForm({ ...EMPTY, subject_id: defaultSubjectId || '' })
      setNoteId(null)
      setSavedLinks([])
    }
    setTab('write')
    setError('')
  }, [open, note, defaultSubjectId])

  const update = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
    setError('')
  }

  /** Envolve a seleção atual do textarea com a marcação escolhida. */
  const applyFormat = useCallback(({ prefix, suffix, sample }) => {
    const textarea = textareaRef.current
    if (!textarea) return

    const { selectionStart: start, selectionEnd: end, value } = textarea
    const selected = value.slice(start, end) || sample
    const next = `${value.slice(0, start)}${prefix}${selected}${suffix}${value.slice(end)}`

    update('content', next)

    // Reposiciona o cursor sobre o trecho inserido.
    requestAnimationFrame(() => {
      textarea.focus()
      textarea.setSelectionRange(start + prefix.length, start + prefix.length + selected.length)
    })
  }, [])

  const buildPayload = () => ({
    title: form.title.trim(),
    content: form.content,
    subject_id: form.subject_id ? Number(form.subject_id) : null,
    category: form.category.trim() || null,
    tags: form.tags,
    is_pinned: form.is_pinned,
  })

  const persist = async ({ closeAfter = true } = {}) => {
    if (!form.title.trim()) {
      setError('Informe um título para a anotação.')
      setTab('write')
      return null
    }

    setSaving(true)
    try {
      const payload = buildPayload()
      const saved = noteId
        ? await noteService.update(noteId, payload)
        : await noteService.create(payload)

      setNoteId(saved.id)
      setSavedLinks(saved.search_results ?? [])
      onSaved?.(saved)

      toast.success(noteId ? 'Anotação atualizada!' : 'Anotação criada!')
      if (closeAfter) onClose()
      return saved
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível salvar a anotação.'))
      return null
    } finally {
      setSaving(false)
    }
  }

  /** Abre a aba de busca, salvando antes se a anotação ainda não existir. */
  const goToSearch = async () => {
    if (!noteId) {
      const saved = await persist({ closeAfter: false })
      if (!saved) return
    }
    setTab('search')
  }

  const subjectName = subjects.find((s) => String(s.id) === String(form.subject_id))?.name ?? ''
  const searchSeed = form.title.trim() || form.category || ''

  const TABS = [
    { id: 'write', label: 'Escrever', icon: PenLine },
    { id: 'preview', label: 'Visualizar', icon: Eye },
    { id: 'search', label: 'Conteúdo de apoio', icon: Sparkles, badge: savedLinks.length },
  ]

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="xl"
      title={noteId ? 'Editar anotação' : 'Nova anotação'}
      description="Markdown é suportado — use a barra de formatação abaixo."
      footer={
        <>
          <label className="text-muted mr-auto flex cursor-pointer items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.is_pinned}
              onChange={(event) => update('is_pinned', event.target.checked)}
              className="accent-brand-600 h-4 w-4 rounded"
            />
            Fixar no topo
          </label>
          <Button variant="secondary" onClick={onClose}>
            Fechar
          </Button>
          <Button onClick={() => persist()} loading={saving}>
            {noteId ? 'Salvar alterações' : 'Criar anotação'}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {/* ------------------------------------------------------ metadados */}
        <Input
          label="Título"
          placeholder="Ex.: Sistema circulatório"
          value={form.title}
          onChange={(event) => update('title', event.target.value)}
          maxLength={200}
          required
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

          <div>
            <Input
              label="Categoria"
              placeholder="Resumo, Exercícios…"
              value={form.category}
              onChange={(event) => update('category', event.target.value)}
              maxLength={60}
              list="note-categories"
            />
            <datalist id="note-categories">
              {NOTE_CATEGORIES.map((category) => (
                <option key={category} value={category} />
              ))}
            </datalist>
          </div>
        </div>

        <TagInput
          value={form.tags}
          onChange={(tags) => update('tags', tags)}
          suggestions={tagSuggestions}
        />

        {/* ----------------------------------------------------------- abas */}
        <div className="flex gap-1 border-b border-[var(--border)]">
          {TABS.map(({ id, label, icon: Icon, badge }) => (
            <button
              key={id}
              type="button"
              onClick={() => (id === 'search' ? goToSearch() : setTab(id))}
              aria-selected={tab === id}
              role="tab"
              className={`-mb-px flex items-center gap-1.5 border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors ${
                tab === id
                  ? 'border-brand-500 text-brand-600 dark:text-brand-400'
                  : 'text-muted border-transparent hover:text-[var(--text)]'
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden />
              <span className="hidden sm:inline">{label}</span>
              {badge > 0 && (
                <Badge className="ml-0.5 px-1.5 py-0 text-[10px]">{badge}</Badge>
              )}
            </button>
          ))}
        </div>

        {/* ------------------------------------------------------- conteúdo */}
        {tab === 'write' && (
          <div>
            <div className="mb-2 flex flex-wrap gap-0.5 rounded-lg bg-[var(--surface-sunken)] p-1">
              {TOOLBAR.map(({ icon: Icon, title, ...format }) => (
                <button
                  key={title}
                  type="button"
                  title={title}
                  aria-label={title}
                  onClick={() => applyFormat(format)}
                  className="text-muted rounded-md p-1.5 transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
                >
                  <Icon className="h-4 w-4" />
                </button>
              ))}
            </div>

            <textarea
              ref={textareaRef}
              value={form.content}
              onChange={(event) => update('content', event.target.value)}
              rows={14}
              placeholder={'# Título\n\nEscreva aqui suas anotações em **Markdown**…'}
              aria-label="Conteúdo da anotação"
              maxLength={100000}
              className="focus:border-brand-500 focus:ring-brand-500/40 w-full resize-y rounded-xl border border-[var(--border-strong)] bg-[var(--surface)] p-3.5 font-mono text-sm leading-relaxed text-[var(--text)] transition-colors placeholder:text-[var(--text-subtle)] focus:ring-2 focus:outline-none"
            />

            <p className="text-subtle mt-1.5 text-right text-xs">
              {form.content.length.toLocaleString('pt-BR')} caracteres
            </p>
          </div>
        )}

        {tab === 'preview' && (
          <div className="min-h-64 rounded-xl border border-[var(--border)] bg-[var(--surface-sunken)] p-5">
            <Markdown>{form.content}</Markdown>
          </div>
        )}

        {tab === 'search' && (
          <ContentSearchPanel
            defaultQuery={searchSeed}
            subjectHint={subjectName}
            target={noteId ? { note_id: noteId } : null}
            savedLinks={savedLinks}
            autoSearch={Boolean(searchSeed)}
            onSaved={(link) => setSavedLinks((current) => [...current, link])}
            onRemoved={(link) =>
              setSavedLinks((current) => current.filter((item) => item.id !== link.id))
            }
          />
        )}

        {error && (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}
      </div>
    </Modal>
  )
}
