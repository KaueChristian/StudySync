/** Tela de cadastro, com validação de senha em tempo real. */
import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AlertCircle, Check, Eye, EyeOff, KeyRound, Mail, User, UserPlus } from 'lucide-react'

import AuthShell from '@/components/auth/AuthShell'
import Button from '@/components/ui/Button'
import { Input } from '@/components/ui/Field'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'

/** Espelha as regras validadas no backend (`schemas/user.py`). */
const RULES = [
  { id: 'length', label: 'Pelo menos 8 caracteres', test: (v) => v.length >= 8 },
  { id: 'letter', label: 'Ao menos uma letra', test: (v) => /[A-Za-z]/.test(v) },
  { id: 'digit', label: 'Ao menos um número', test: (v) => /\d/.test(v) },
]

export default function RegisterPage() {
  const { register } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const checks = useMemo(
    () => RULES.map((rule) => ({ ...rule, ok: rule.test(form.password) })),
    [form.password],
  )
  const passwordValid = checks.every((check) => check.ok)
  const passwordsMatch = form.password === form.confirm

  const update = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
    setError('')
  }

  const submit = async (event) => {
    event.preventDefault()

    if (!passwordValid) return setError('A senha não atende aos requisitos mínimos.')
    if (!passwordsMatch) return setError('As senhas não coincidem.')

    setLoading(true)
    setError('')
    try {
      const user = await register({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
      })
      toast.success(`Conta criada! Bem-vindo, ${user.name.split(' ')[0]}.`, {
        description: 'Comece cadastrando suas matérias.',
      })
      navigate('/materias', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível criar a conta.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Criar sua conta"
      subtitle="Leva menos de um minuto e é totalmente gratuito."
      footer={
        <>
          Já tem uma conta?{' '}
          <Link to="/login" className="text-brand-600 dark:text-brand-400 font-semibold hover:underline">
            Fazer login
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4" noValidate>
        <Input
          label="Nome completo"
          icon={User}
          autoComplete="name"
          placeholder="Ana Souza"
          value={form.name}
          onChange={update('name')}
          minLength={2}
          required
          autoFocus
        />

        <Input
          label="E-mail"
          type="email"
          icon={Mail}
          autoComplete="email"
          placeholder="voce@exemplo.com"
          value={form.email}
          onChange={update('email')}
          required
        />

        <div className="relative">
          <Input
            label="Senha"
            type={showPassword ? 'text' : 'password'}
            icon={KeyRound}
            autoComplete="new-password"
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

        {form.password && (
          <ul className="space-y-1.5 rounded-xl bg-[var(--surface-sunken)] p-3">
            {checks.map((check) => (
              <li
                key={check.id}
                className={`flex items-center gap-2 text-xs transition-colors ${
                  check.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-[var(--text-muted)]'
                }`}
              >
                <span
                  className={`flex h-4 w-4 items-center justify-center rounded-full border ${
                    check.ok
                      ? 'border-emerald-500 bg-emerald-500 text-white'
                      : 'border-[var(--border-strong)]'
                  }`}
                >
                  {check.ok && <Check className="h-2.5 w-2.5" strokeWidth={3} />}
                </span>
                {check.label}
              </li>
            ))}
          </ul>
        )}

        <Input
          label="Confirmar senha"
          type={showPassword ? 'text' : 'password'}
          icon={KeyRound}
          autoComplete="new-password"
          placeholder="••••••••"
          value={form.confirm}
          onChange={update('confirm')}
          error={form.confirm && !passwordsMatch ? 'As senhas não coincidem.' : ''}
          required
        />

        {error && (
          <div
            role="alert"
            className="flex gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-500/25 dark:bg-red-500/10 dark:text-red-400"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            {error}
          </div>
        )}

        <Button
          type="submit"
          size="lg"
          icon={UserPlus}
          loading={loading}
          disabled={!passwordValid || !passwordsMatch}
          className="w-full"
        >
          Criar conta
        </Button>
      </form>
    </AuthShell>
  )
}
