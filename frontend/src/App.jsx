/** Definição das rotas da SPA. */
import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import AppLayout from '@/components/layout/AppLayout'
import { ProtectedRoute, PublicRoute } from '@/components/auth/RouteGuards'
import { LoadingState } from '@/components/ui/Misc'

// Páginas de entrada são carregadas de imediato (primeira tela do usuário).
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'

// As demais entram por code-splitting, reduzindo o bundle inicial.
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const SubjectsPage = lazy(() => import('@/pages/SubjectsPage'))
const NotesPage = lazy(() => import('@/pages/NotesPage'))
const SchedulePage = lazy(() => import('@/pages/SchedulePage'))
const SearchPage = lazy(() => import('@/pages/SearchPage'))
const LibraryPage = lazy(() => import('@/pages/LibraryPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

export default function App() {
  return (
    <Suspense fallback={<LoadingState className="min-h-screen" />}>
      <Routes>
        {/* Rotas públicas — inacessíveis para quem já está logado */}
        <Route element={<PublicRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/cadastro" element={<RegisterPage />} />
        </Route>

        {/* Rotas protegidas */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="/materias" element={<SubjectsPage />} />
            <Route path="/anotacoes" element={<NotesPage />} />
            <Route path="/agenda" element={<SchedulePage />} />
            <Route path="/pesquisa" element={<SearchPage />} />
            <Route path="/biblioteca" element={<LibraryPage />} />
            <Route path="/configuracoes" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="/registro" element={<Navigate to="/cadastro" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  )
}
