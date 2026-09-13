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
import { IS_DESKTOP } from '@/lib/desktop'

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

/** Desktop sem sessão: não há tela de login para onde mandar o usuário. */
function DesktopSessionError() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-6 text-center">
      <div className="bg-brand-600 flex h-14 w-14 items-center justify-center rounded-2xl">
        <GraduationCap className="h-7 w-7 text-white" aria-hidden />
      </div>
      <p className="font-semibold">Não foi possível abrir sua área de estudos.</p>
      <p className="text-muted text-sm">Feche e abra o StudySync novamente.</p>
    </div>
  )
}

export function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Splash />
  if (!isAuthenticated) {
    if (IS_DESKTOP) return <DesktopSessionError />
    // Guarda o destino para retomar a navegação após o login.
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return <Outlet />
}

export function PublicRoute() {
  const { isAuthenticated, loading } = useAuth()

  // No desktop, login e cadastro não existem.
  if (IS_DESKTOP) return <Navigate to="/" replace />
  if (loading) return <Splash />
  if (isAuthenticated) return <Navigate to="/" replace />
  return <Outlet />
}
