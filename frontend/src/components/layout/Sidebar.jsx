/** Navegação lateral — fixa no desktop, gaveta deslizante no mobile. */
import { NavLink } from 'react-router-dom'
import {
  BookMarked,
  CalendarDays,
  GraduationCap,
  LayoutDashboard,
  Search,
  Settings,
  StickyNote,
  X,
} from 'lucide-react'

const LINKS = [
  { to: '/', label: 'Painel', icon: LayoutDashboard, end: true },
  { to: '/materias', label: 'Matérias', icon: GraduationCap },
  { to: '/anotacoes', label: 'Anotações', icon: StickyNote },
  { to: '/agenda', label: 'Agenda', icon: CalendarDays },
  { to: '/pesquisa', label: 'Pesquisa', icon: Search },
  { to: '/biblioteca', label: 'Biblioteca', icon: BookMarked },
]

function NavItem({ link, onNavigate }) {
  const { to, label, icon: Icon, end } = link
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onNavigate}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
          isActive
            ? 'bg-brand-50 text-brand-700 dark:bg-brand-500/12 dark:text-brand-300'
            : 'text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <Icon className={`h-[18px] w-[18px] ${isActive ? '' : 'text-subtle'}`} aria-hidden />
          {label}
        </>
      )}
    </NavLink>
  )
}

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {/* Fundo escurecido no mobile */}
      {open && (
        <div
          className="animate-fade-in fixed inset-0 z-30 bg-slate-900/50 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-[var(--border)] bg-[var(--surface)] transition-transform duration-250 lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 shrink-0 items-center justify-between px-5">
          <div className="flex items-center gap-2.5">
            <div className="bg-brand-600 shadow-brand-600/25 flex h-9 w-9 items-center justify-center rounded-xl shadow-lg">
              <GraduationCap className="h-5 w-5 text-white" aria-hidden />
            </div>
            <div className="leading-tight">
              <p className="font-display text-[17px]">StudySync</p>
              <p className="text-subtle text-[11px]">Estudos organizados</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar menu"
            className="text-subtle hover:text-[var(--text)] -mr-2 rounded-lg p-2 lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2" aria-label="Navegação principal">
          {LINKS.map((link) => (
            <NavItem key={link.to} link={link} onNavigate={onClose} />
          ))}
        </nav>

        <div className="border-t border-[var(--border)] p-3">
          <NavItem
            link={{ to: '/configuracoes', label: 'Configurações', icon: Settings }}
            onNavigate={onClose}
          />
        </div>
      </aside>
    </>
  )
}
