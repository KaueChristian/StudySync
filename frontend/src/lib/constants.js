/** Constantes compartilhadas pela interface. */

/** Paleta oferecida no seletor de cor das matérias. */
export const SUBJECT_COLORS = [
  '#6366f1', // índigo
  '#3b82f6', // azul
  '#06b6d4', // ciano
  '#10b981', // esmeralda
  '#22c55e', // verde
  '#eab308', // amarelo
  '#f59e0b', // âmbar
  '#f97316', // laranja
  '#ef4444', // vermelho
  '#ec4899', // rosa
  '#a855f7', // roxo
  '#64748b', // ardósia
]

/**
 * Ícones disponíveis para as matérias.
 * O `value` é o slug persistido; o `label` é exibido no seletor.
 * Os componentes correspondentes ficam em `components/ui/SubjectIcon.jsx`.
 */
export const SUBJECT_ICONS = [
  { value: 'book-open', label: 'Livro' },
  { value: 'leaf', label: 'Biologia' },
  { value: 'calculator', label: 'Matemática' },
  { value: 'flask-conical', label: 'Química' },
  { value: 'atom', label: 'Física' },
  { value: 'landmark', label: 'História' },
  { value: 'globe', label: 'Geografia' },
  { value: 'languages', label: 'Idiomas' },
  { value: 'pen-tool', label: 'Redação' },
  { value: 'code', label: 'Programação' },
  { value: 'palette', label: 'Artes' },
  { value: 'music', label: 'Música' },
  { value: 'brain', label: 'Filosofia' },
  { value: 'scale', label: 'Direito' },
  { value: 'heart-pulse', label: 'Saúde' },
  { value: 'trending-up', label: 'Economia' },
]

/** Opções de antecedência do lembrete. */
export const REMINDER_OPTIONS = [
  { value: 0, label: 'Na hora exata' },
  { value: 5, label: '5 minutos antes' },
  { value: 10, label: '10 minutos antes' },
  { value: 15, label: '15 minutos antes' },
  { value: 30, label: '30 minutos antes' },
  { value: 60, label: '1 hora antes' },
  { value: 120, label: '2 horas antes' },
  { value: 1440, label: '1 dia antes' },
]

/** Rótulos e estilos por status de agendamento. */
export const SCHEDULE_STATUS = {
  pending: {
    label: 'Pendente',
    className:
      'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/25',
  },
  completed: {
    label: 'Concluída',
    className:
      'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/25',
  },
  canceled: {
    label: 'Cancelada',
    className:
      'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-500/10 dark:text-slate-400 dark:border-slate-500/25',
  },
}

/** Sugestões de categoria exibidas no editor de anotações. */
export const NOTE_CATEGORIES = [
  'Resumo',
  'Exercícios',
  'Revisão',
  'Fórmulas',
  'Mapa mental',
  'Dúvidas',
  'Trabalho',
]

export const WEEKDAYS_SHORT = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
