/** Tela de login. */
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AlertCircle, Eye, EyeOff, KeyRound, LogIn, Mail } from 'lucide-react'

import AuthShell from '@/components/auth/AuthShell'
import Button from '@/components/ui/Button'
import { Input } from '@/components/ui/Field'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'

const DEMO = { email: 'demo@studysync.dev', password: 'Estudo2024' }

export default function LoginPage() {
  const { login, sessionExpired } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const [form, setForm] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
    setError('')
  }

  const submit = async (event, credentials = form) => {
    event?.preventDefault()
    setLoading(true)
    setError('')

    try {
      const user = await login(credentials)
      toast.success(`Bem-vindo de volta, ${user.name.split(' ')[0]}!`)
      // Retoma a rota que o usuário tentou acessar antes de ser redirecionado.
      navigate(location.state?.from?.pathname ?? '/', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível entrar.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Entrar na sua conta"
      subtitle="Continue de onde parou nos seus estudos."
      footer={
        <>
          Ainda não tem conta?{' '}
          <Link to="/cadastro" className="text-brand-600 dark:text-brand-400 font-semibold hover:underline">
            Criar conta gratuita
          </Link>
        </>
      }
    >
      {sessionExpired && (
        <div
          role="alert"
          className="mb-5 flex gap-2.5 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-500/25 dark:bg-amber-500/10 dark:text-amber-300"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          Sua sessão expirou. Entre novamente para continuar.
        </div>
      )}

      <form onSubmit={submit} className="space-y-4" noValidate>
        <Input
          label="E-mail"
          type="email"
          icon={Mail}
          autoComplete="email"
          placeholder="voce@exemplo.com"
          value={form.email}
          onChange={update('email')}
          required
          autoFocus
        />

        <div className="relative">
          <Input
            label="Senha"
            type={showPassword ? 'text' : 'password'}
            icon={KeyRound}
            autoComplete="current-password"
            placeholder="••••••••"
            value={form.password}
            onChange={update('password')}
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword((value) => !value)}
            aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
            className="text-subtle hover:text-[var(--text)] absolute top-[38px] right-3 p-1 transition-colors"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>

        {error && (
          <div
            role="alert"
            className="flex gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-500/25 dark:bg-red-500/10 dark:text-red-400"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            {error}
          </div>
        )}

        <Button type="submit" size="lg" icon={LogIn} loading={loading} className="w-full">
          Entrar
        </Button>
      </form>

      <div className="mt-6 rounded-xl border border-dashed border-[var(--border-strong)] p-4">
        <p className="text-muted text-xs leading-relaxed">
          <strong className="text-[var(--text)]">Conta de demonstração</strong> — criada pelo
          script <code className="text-[11px]">python -m app.seed</code>, com matérias,
          anotações e sessões de exemplo.
        </p>
        <Button
          variant="secondary"
          size="sm"
          className="mt-3 w-full"
          disabled={loading}
          onClick={(event) => {
            setForm(DEMO)
            submit(event, DEMO)
          }}
        >
          Entrar com a conta demo
        </Button>
      </div>
    </AuthShell>
  )
}
