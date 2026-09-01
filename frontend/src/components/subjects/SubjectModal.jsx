/** Modal de criação/edição de matéria. */
import { useEffect, useState } from 'react'
import { Check } from 'lucide-react'

import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { Field, Input, Textarea } from '@/components/ui/Field'
import SubjectIcon from '@/components/ui/SubjectIcon'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'
import { subjectService } from '@/lib/services'
import { SUBJECT_COLORS, SUBJECT_ICONS } from '@/lib/constants'

const EMPTY = { name: '', description: '', color: SUBJECT_COLORS[0], icon: 'book-open' }

export default function SubjectModal({ open, onClose, subject, onSaved }) {
  const toast = useToast()
  const isEditing = Boolean(subject)

  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Recarrega o formulário sempre que o modal abre.
  useEffect(() => {
    if (!open) return
    setForm(
      subject
        ? {
            name: subject.name,
            description: subject.description ?? '',
            color: subject.color,
            icon: subject.icon,
          }
        : EMPTY,
    )
    setError('')
  }, [open, subject])

  const update = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
    setError('')
  }

  const submit = async (event) => {
    event.preventDefault()
    if (!form.name.trim()) return setError('Informe o nome da matéria.')

    setLoading(true)
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim() || null,
        color: form.color,
        icon: form.icon,
      }
      const saved = isEditing
        ? await subjectService.update(subject.id, payload)
        : await subjectService.create(payload)

      toast.success(isEditing ? 'Matéria atualizada!' : 'Matéria criada!')
      onSaved?.(saved)
      onClose()
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível salvar a matéria.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEditing ? 'Editar matéria' : 'Nova matéria'}
      description="Agrupe suas anotações e sessões de estudo por disciplina."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={submit} loading={loading}>
            {isEditing ? 'Salvar alterações' : 'Criar matéria'}
          </Button>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-5" noValidate>
        {/* Pré-visualização ao vivo */}
        <div className="flex items-center gap-3 rounded-xl bg-[var(--surface-sunken)] p-3.5">
          <div
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
            style={{ backgroundColor: `${form.color}1f`, color: form.color }}
          >
            <SubjectIcon icon={form.icon} className="h-6 w-6" />
          </div>
          <div className="min-w-0">
            <p className="truncate font-semibold">{form.name || 'Nome da matéria'}</p>
            <p className="text-muted truncate text-sm">
              {form.description || 'Descrição opcional'}
            </p>
          </div>
        </div>

        <Input
          label="Nome"
          placeholder="Ex.: Biologia"
          value={form.name}
          onChange={(event) => update('name', event.target.value)}
          maxLength={120}
          required
        />

        <Textarea
          label="Descrição"
          placeholder="Quais assuntos essa matéria cobre?"
          value={form.description}
          onChange={(event) => update('description', event.target.value)}
          maxLength={2000}
          rows={3}
        />

        <Field label="Cor">
          <div className="flex flex-wrap gap-2">
            {SUBJECT_COLORS.map((color) => (
              <button
                key={color}
                type="button"
                onClick={() => update('color', color)}
                aria-label={`Selecionar cor ${color}`}
                aria-pressed={form.color === color}
                className="flex h-8 w-8 items-center justify-center rounded-lg transition-transform hover:scale-110"
                style={{ backgroundColor: color }}
              >
                {form.color === color && (
                  <Check className="h-4 w-4 text-white" strokeWidth={3} aria-hidden />
                )}
              </button>
            ))}
          </div>
        </Field>

        <Field label="Ícone">
          <div className="grid grid-cols-8 gap-2">
            {SUBJECT_ICONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => update('icon', option.value)}
                title={option.label}
                aria-label={option.label}
                aria-pressed={form.icon === option.value}
                className={`flex aspect-square items-center justify-center rounded-lg border transition-colors ${
                  form.icon === option.value
                    ? 'border-brand-500 bg-brand-50 text-brand-600 dark:bg-brand-500/12 dark:text-brand-400'
                    : 'border-[var(--border)] text-[var(--text-muted)] hover:bg-[var(--surface-hover)]'
                }`}
              >
                <SubjectIcon icon={option.value} className="h-[18px] w-[18px]" />
              </button>
            ))}
          </div>
        </Field>

        {error && (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}
      </form>
    </Modal>
  )
}
