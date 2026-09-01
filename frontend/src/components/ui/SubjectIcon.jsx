/**
 * Resolve o slug de ícone salvo na matéria para o componente lucide-react.
 *
 * O mapa é explícito (em vez de import dinâmico) para que o bundler consiga
 * fazer tree-shaking e só inclua os ícones realmente usados.
 */
import {
  Atom,
  BookOpen,
  Brain,
  Calculator,
  Code,
  FlaskConical,
  Globe,
  HeartPulse,
  Landmark,
  Languages,
  Leaf,
  Music,
  Palette,
  PenTool,
  Scale,
  TrendingUp,
} from 'lucide-react'

const ICON_MAP = {
  'book-open': BookOpen,
  leaf: Leaf,
  calculator: Calculator,
  'flask-conical': FlaskConical,
  atom: Atom,
  landmark: Landmark,
  globe: Globe,
  languages: Languages,
  'pen-tool': PenTool,
  code: Code,
  palette: Palette,
  music: Music,
  brain: Brain,
  scale: Scale,
  'heart-pulse': HeartPulse,
  'trending-up': TrendingUp,
}

export function getSubjectIcon(slug) {
  return ICON_MAP[slug] ?? BookOpen
}

export default function SubjectIcon({ icon, className = 'h-5 w-5', ...props }) {
  const Icon = getSubjectIcon(icon)
  return <Icon className={className} aria-hidden {...props} />
}

/** Avatar quadrado com a cor e o ícone da matéria. */
export function SubjectAvatar({ subject, size = 'md' }) {
  const sizes = {
    sm: { box: 'h-8 w-8 rounded-lg', icon: 'h-4 w-4' },
    md: { box: 'h-10 w-10 rounded-xl', icon: 'h-5 w-5' },
    lg: { box: 'h-12 w-12 rounded-xl', icon: 'h-6 w-6' },
  }[size]

  return (
    <div
      className={`flex shrink-0 items-center justify-center ${sizes.box}`}
      style={{ backgroundColor: `${subject.color}1f`, color: subject.color }}
    >
      <SubjectIcon icon={subject.icon} className={sizes.icon} />
    </div>
  )
}
