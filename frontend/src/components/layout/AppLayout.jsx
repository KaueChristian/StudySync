/** Casca da aplicação autenticada: sidebar + topbar + área de conteúdo. */
import { useEffect, useRef, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { ChevronDown, LogOut, Menu, Moon, Settings, Sun, User } from 'lucide-react'

import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/context/ThemeContext'
import { initials } from '@/lib/format'
import NotificationBell from './NotificationBell'
import Sidebar from './Sidebar'

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!open) return undefined
    const onPointerDown = (event) => {
      if (!containerRef.current?.contains(event.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [open])

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-label="Menu do usuário"
        className="flex items-center gap-2 rounded-xl p-1.5 transition-colors hover:bg-[var(--surface-hover)]"
      >
        <span className="from-brand-500 to-brand-700 flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br text-xs font-bold text-white">
          {initials(user?.name)}
        </span>
        <span className="hidden max-w-32 truncate text-sm font-medium sm:block">
          {user?.name}
        </span>
        <ChevronDown className="text-subtle hidden h-4 w-4 sm:block" aria-hidden />
      </button>

      {open && (
        <div className="card animate-scale-in absolute right-0 z-50 mt-2 w-60 origin-top-right overflow-hidden shadow-xl">
          <div className="border-b border-[var(--border)] px-4 py-3">
            <p className="truncate text-sm font-semibold">{user?.name}</p>
            <p className="text-muted truncate text-xs">{user?.email}</p>
          </div>

          <div className="p-1.5">
            <Link
              to="/configuracoes"
              onClick={() => setOpen(false)}
              className="text-muted flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
            >
              <Settings className="h-4 w-4" aria-hidden />
              Configurações
            </Link>
            <button
              type="button"
              onClick={handleLogout}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10"
            >
              <LogOut className="h-4 w-4" aria-hidden />
              Sair da conta
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { theme, toggle } = useTheme()
  const location = useLocation()

  // Fecha a gaveta ao navegar (relevante no mobile).
  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname])

  return (
    <div className="min-h-screen">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-[var(--border)] bg-[var(--surface)]/85 backdrop-blur-md">
          <div className="flex h-16 items-center gap-2 px-4 sm:px-6">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              aria-label="Abrir menu"
              className="text-muted -ml-1 rounded-xl p-2.5 transition-colors hover:bg-[var(--surface-hover)] lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </button>

            <div className="flex-1" />

            <button
              type="button"
              onClick={toggle}
              aria-label={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'}
              className="rounded-xl p-2.5 text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
            >
              {theme === 'dark' ? (
                <Sun className="h-5 w-5" aria-hidden />
              ) : (
                <Moon className="h-5 w-5" aria-hidden />
              )}
            </button>

            <NotificationBell />
            <UserMenu />
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
