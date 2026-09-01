/**
 * Guardas de rota.
 *
 * `ProtectedRoute` exige sessão ativa; `PublicRoute` impede que um usuário
 * já autenticado veja as telas de login/cadastro. Ambos aguardam o fim da
 * restauração da sessão para não redirecionar por engano no primeiro render.
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { GraduationCap } from 'lucide-react'

import { useAuth } from '@/context/AuthContext'
import { Spinner } from '@/components/ui/Misc'

function Splash() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <div className="bg-brand-600 shadow-brand-600/25 flex h-14 w-14 items-center justify-center rounded-2xl shadow-lg">
        <GraduationCap className="h-7 w-7 text-white" aria-hidden />
      </div>
      <Spinner className="h-5 w-5" />
      <p className="text-muted text-sm">Carregando sua área de estudos…</p>
    </div>
  )
}

export function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Splash />
  if (!isAuthenticated) {
    // Guarda o destino para retomar a navegação após o login.
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return <Outlet />
}

export function PublicRoute() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) return <Splash />
  if (isAuthenticated) return <Navigate to="/" replace />
  return <Outlet />
}
