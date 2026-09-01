/**
 * Entrada de tags com chips.
 *
 * Confirma a tag com Enter, vírgula ou Tab; Backspace em campo vazio remove
 * a última. Sugestões vindas das tags já usadas pelo usuário.
 */
import { useMemo, useState } from 'react'
import { Tag as TagIcon, X } from 'lucide-react'

import { Field } from '@/components/ui/Field'

const MAX_TAGS = 15

export default function TagInput({ value = [], onChange, suggestions = [], label = 'Tags' }) {
  const [draft, setDraft] = useState('')

  const available = useMemo(() => {
    const query = draft.trim().toLowerCase()
    return suggestions
      .filter((tag) => !value.includes(tag.name))
      .filter((tag) => !query || tag.name.includes(query))
      .slice(0, 6)
  }, [suggestions, value, draft])

  const add = (raw) => {
    const tag = raw.trim().toLowerCase()
    if (!tag || value.includes(tag) || value.length >= MAX_TAGS) return
    onChange([...value, tag])
    setDraft('')
  }

  const remove = (tag) => onChange(value.filter((item) => item !== tag))

  const handleKeyDown = (event) => {
    if (['Enter', ',', 'Tab'].includes(event.key) && draft.trim()) {
      event.preventDefault()
      add(draft)
    } else if (event.key === 'Backspace' && !draft && value.length) {
      remove(value[value.length - 1])
    }
  }

  return (
    <Field
      label={label}
      hint={
        value.length >= MAX_TAGS
          ? `Limite de ${MAX_TAGS} tags atingido.`
          : 'Pressione Enter ou vírgula para adicionar.'
      }
    >
      <div className="focus-within:border-brand-500 focus-within:ring-brand-500/40 flex flex-wrap items-center gap-1.5 rounded-xl border border-[var(--border-strong)] bg-[var(--surface)] p-2 transition-colors focus-within:ring-2">
        <TagIcon className="text-subtle ml-1 h-4 w-4 shrink-0" aria-hidden />

        {value.map((tag) => (
          <span
            key={tag}
            className="bg-brand-50 text-brand-700 dark:bg-brand-500/12 dark:text-brand-300 inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium"
          >
            {tag}
            <button
              type="button"
              onClick={() => remove(tag)}
              aria-label={`Remover tag ${tag}`}
              className="hover:text-brand-900 dark:hover:text-brand-100"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}

        <input
          type="text"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => draft.trim() && add(draft)}
          disabled={value.length >= MAX_TAGS}
          placeholder={value.length ? '' : 'anatomia, prova…'}
          aria-label="Adicionar tag"
          maxLength={60}
          className="min-w-24 flex-1 bg-transparent px-1 py-1 text-sm outline-none placeholder:text-[var(--text-subtle)] disabled:cursor-not-allowed"
        />
      </div>

      {available.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          <span className="text-subtle py-1 text-xs">Sugestões:</span>
          {available.map((tag) => (
            <button
              key={tag.id}
              type="button"
              onClick={() => add(tag.name)}
              className="text-muted rounded-lg border border-[var(--border)] px-2 py-0.5 text-xs transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
            >
              + {tag.name}
            </button>
          ))}
        </div>
      )}
    </Field>
  )
}
