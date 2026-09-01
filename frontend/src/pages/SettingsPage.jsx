/** Configurações: perfil, preferências de lembrete, notificações e senha. */
import { useEffect, useState } from 'react'
import {
  Bell,
  CalendarSync,
  Check,
  Copy,
  KeyRound,
  Moon,
  Settings,
  Sun,
  User,
  Wifi,
  WifiOff,
} from 'lucide-react'

import Button from '@/components/ui/Button'
import { Input, Select } from '@/components/ui/Field'
import { Badge, PageHeading } from '@/components/ui/Misc'
import { useAuth } from '@/context/AuthContext'
import { useNotifications } from '@/context/NotificationContext'
import { useTheme } from '@/context/ThemeContext'
import { useToast } from '@/context/ToastContext'
import { apiUrl, getErrorMessage } from '@/lib/api'
import { authService, scheduleService } from '@/lib/services'
import { REMINDER_OPTIONS } from '@/lib/constants'
import { formatDate } from '@/lib/format'

/** Fusos mais comuns no Brasil + o do navegador, se for diferente. */
const TIMEZONES = [
  'America/Sao_Paulo',
  'America/Manaus',
  'America/Belem',
  'America/Fortaleza',
  'America/Recife',
  'America/Bahia',
  'America/Cuiaba',
  'America/Campo_Grande',
  'America/Rio_Branco',
  'America/Noronha',
  'UTC',
]

function Section({ icon: Icon, title, description, children }) {
  return (
    <section className="card p-5">
      <header className="mb-4 flex items-start gap-3">
        <div className="bg-brand-50 dark:bg-brand-500/10 rounded-xl p-2.5">
          <Icon className="text-brand-600 dark:text-brand-400 h-[18px] w-[18px]" aria-hidden />
        </div>
        <div>
          <h2 className="font-semibold">{title}</h2>
          {description && <p className="text-muted mt-0.5 text-sm">{description}</p>}
        </div>
      </header>
      {children}
    </section>
  )
}

export default function SettingsPage() {
  const { user, updateProfile } = useAuth()
  const { theme, toggle } = useTheme()
  const { connected, requestPermission, nativePermission } = useNotifications()
  const toast = useToast()

  const [profile, setProfile] = useState({
    name: '',
    timezone: 'America/Sao_Paulo',
    default_reminder_minutes: 15,
  })
  const [savingProfile, setSavingProfile] = useState(false)

  const [passwords, setPasswords] = useState({ current: '', next: '', confirm: '' })
  const [savingPassword, setSavingPassword] = useState(false)
  const [passwordError, setPasswordError] = useState('')

  const [permission, setPermission] = useState(nativePermission)

  const [subscribeUrl, setSubscribeUrl] = useState('')
  const [loadingLink, setLoadingLink] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!user) return
    setProfile({
      name: user.name,
      timezone: user.timezone,
      default_reminder_minutes: user.default_reminder_minutes,
    })
  }, [user])

  const browserTz = Intl.DateTimeFormat().resolvedOptions().timeZone
  const timezoneOptions = TIMEZONES.includes(browserTz) ? TIMEZONES : [browserTz, ...TIMEZONES]

  const saveProfile = async (event) => {
    event.preventDefault()
    setSavingProfile(true)
    try {
      await updateProfile({
        name: profile.name.trim(),
        timezone: profile.timezone,
        default_reminder_minutes: Number(profile.default_reminder_minutes),
      })
      toast.success('Perfil atualizado!')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível salvar o perfil.'))
    } finally {
      setSavingProfile(false)
    }
  }

  const changePassword = async (event) => {
    event.preventDefault()
    setPasswordError('')

    if (passwords.next !== passwords.confirm) {
      setPasswordError('A confirmação não confere com a nova senha.')
      return
    }
    if (passwords.next.length < 8 || !/[A-Za-z]/.test(passwords.next) || !/\d/.test(passwords.next)) {
      setPasswordError('A nova senha precisa ter ao menos 8 caracteres, uma letra e um número.')
      return
    }

    setSavingPassword(true)
    try {
      const result = await authService.changePassword({
        current_password: passwords.current,
        new_password: passwords.next,
      })
      setPasswords({ current: '', next: '', confirm: '' })
      toast.success('Senha alterada!', { description: result.detail })
    } catch (err) {
      setPasswordError(getErrorMessage(err, 'Não foi possível alterar a senha.'))
    } finally {
      setSavingPassword(false)
    }
  }

  const generateSubscribeLink = async () => {
    setLoadingLink(true)
    try {
      const { token } = await scheduleService.getExportToken()
      setSubscribeUrl(`${apiUrl('/schedules/export.ics')}?token=${token}`)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível gerar o link.'))
    } finally {
      setLoadingLink(false)
    }
  }

  const copySubscribeLink = async () => {
    try {
      await navigator.clipboard.writeText(subscribeUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      toast.error('Não foi possível copiar o link.')
    }
  }

  const askPermission = async () => {
    const result = await requestPermission()
    setPermission(result)
    if (result === 'granted') toast.success('Notificações do sistema ativadas!')
    else if (result === 'denied') {
      toast.warning('Permissão negada.', {
        description: 'Você pode reativar nas configurações do navegador.',
      })
    }
  }

  return (
    <>
      <PageHeading
        icon={Settings}
        title="Configurações"
        description="Ajuste seu perfil, preferências e segurança."
      />

      <div className="grid max-w-3xl gap-5">
        {/* -------------------------------------------------------- perfil */}
        <Section icon={User} title="Perfil" description="Suas informações básicas.">
          <form onSubmit={saveProfile} className="space-y-4">
            <Input
              label="Nome"
              value={profile.name}
              onChange={(event) => setProfile((c) => ({ ...c, name: event.target.value }))}
              minLength={2}
              maxLength={120}
              required
            />

            <Input
              label="E-mail"
              value={user?.email ?? ''}
              hint="O e-mail de acesso não pode ser alterado."
              disabled
              readOnly
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <Select
                label="Fuso horário"
                hint="Usado para exibir os horários das sessões."
                value={profile.timezone}
                onChange={(event) => setProfile((c) => ({ ...c, timezone: event.target.value }))}
              >
                {timezoneOptions.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz.replace('_', ' ')}
                    {tz === browserTz ? ' (deste navegador)' : ''}
                  </option>
                ))}
              </Select>

              <Select
                label="Lembrete padrão"
                hint="Antecedência sugerida ao criar uma sessão."
                value={profile.default_reminder_minutes}
                onChange={(event) =>
                  setProfile((c) => ({ ...c, default_reminder_minutes: event.target.value }))
                }
                options={REMINDER_OPTIONS}
              />
            </div>

            <div className="flex items-center justify-between border-t border-[var(--border)] pt-4">
              <p className="text-subtle text-xs">
                Conta criada em {formatDate(user?.created_at)}
              </p>
              <Button type="submit" loading={savingProfile}>
                Salvar perfil
              </Button>
            </div>
          </form>
        </Section>

        {/* ------------------------------------------------------ aparência */}
        <Section
          icon={theme === 'dark' ? Moon : Sun}
          title="Aparência"
          description="Escolha o tema da interface."
        >
          <div className="flex items-center justify-between rounded-xl bg-[var(--surface-sunken)] p-3.5">
            <div>
              <p className="text-sm font-medium">
                Tema {theme === 'dark' ? 'escuro' : 'claro'}
              </p>
              <p className="text-muted text-xs">
                A preferência fica salva neste navegador.
              </p>
            </div>
            <Button variant="secondary" size="sm" icon={theme === 'dark' ? Sun : Moon} onClick={toggle}>
              Mudar para {theme === 'dark' ? 'claro' : 'escuro'}
            </Button>
          </div>
        </Section>

        {/* --------------------------------------------------- notificações */}
        <Section
          icon={Bell}
          title="Notificações"
          description="Como você recebe os lembretes das sessões."
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-xl bg-[var(--surface-sunken)] p-3.5">
              <div className="flex items-center gap-2.5">
                {connected ? (
                  <Wifi className="h-4 w-4 text-emerald-500" aria-hidden />
                ) : (
                  <WifiOff className="h-4 w-4 text-amber-500" aria-hidden />
                )}
                <div>
                  <p className="text-sm font-medium">Conexão em tempo real</p>
                  <p className="text-muted text-xs">
                    {connected
                      ? 'Os lembretes chegam instantaneamente pelo WebSocket.'
                      : 'Reconectando ao servidor de notificações…'}
                  </p>
                </div>
              </div>
              <Badge
                className={
                  connected
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/25 dark:bg-emerald-500/10 dark:text-emerald-400'
                    : 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/25 dark:bg-amber-500/10 dark:text-amber-400'
                }
              >
                {connected ? 'Conectado' : 'Offline'}
              </Badge>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-[var(--surface-sunken)] p-3.5">
              <div>
                <p className="text-sm font-medium">Notificações do sistema</p>
                <p className="text-muted text-xs">
                  Receba os avisos mesmo com a aba em segundo plano.
                </p>
              </div>

              {permission === 'granted' ? (
                <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/25 dark:bg-emerald-500/10 dark:text-emerald-400">
                  Ativadas
                </Badge>
              ) : permission === 'denied' ? (
                <Badge className="border-red-200 bg-red-50 text-red-700 dark:border-red-500/25 dark:bg-red-500/10 dark:text-red-400">
                  Bloqueadas no navegador
                </Badge>
              ) : permission === 'unsupported' ? (
                <Badge>Não suportadas</Badge>
              ) : (
                <Button variant="secondary" size="sm" onClick={askPermission}>
                  Ativar
                </Button>
              )}
            </div>
          </div>
        </Section>

        {/* ---------------------------------------------- exportar calendário */}
        <Section
          icon={CalendarSync}
          title="Exportar para outro calendário"
          description="Assine sua agenda de estudos no Google Calendar, Apple Calendar ou similar."
        >
          <div className="space-y-3">
            {subscribeUrl ? (
              <div className="flex items-center gap-2">
                <Input readOnly value={subscribeUrl} onFocus={(event) => event.target.select()} />
                <Button
                  variant="secondary"
                  size="icon"
                  icon={copied ? Check : Copy}
                  onClick={copySubscribeLink}
                  aria-label="Copiar link"
                  className={copied ? 'text-emerald-600 dark:text-emerald-400' : ''}
                />
              </div>
            ) : (
              <Button variant="secondary" onClick={generateSubscribeLink} loading={loadingLink}>
                Gerar link de assinatura
              </Button>
            )}
            <p className="text-muted text-xs leading-relaxed">
              No Google Calendar: <strong>Outras agendas → +  → A partir da URL</strong> e cole o
              link acima. A agenda é atualizada automaticamente pelo próprio Google/Apple, com a
              frequência que cada um define.
            </p>
          </div>
        </Section>

        {/* ---------------------------------------------------------- senha */}
        <Section
          icon={KeyRound}
          title="Segurança"
          description="Alterar a senha encerra as sessões nos outros dispositivos."
        >
          <form onSubmit={changePassword} className="space-y-4">
            <Input
              label="Senha atual"
              type="password"
              autoComplete="current-password"
              value={passwords.current}
              onChange={(event) => setPasswords((c) => ({ ...c, current: event.target.value }))}
              required
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <Input
                label="Nova senha"
                type="password"
                autoComplete="new-password"
                hint="Mínimo de 8 caracteres, com letra e número."
                value={passwords.next}
                onChange={(event) => setPasswords((c) => ({ ...c, next: event.target.value }))}
                required
              />
              <Input
                label="Confirmar nova senha"
                type="password"
                autoComplete="new-password"
                value={passwords.confirm}
                onChange={(event) => setPasswords((c) => ({ ...c, confirm: event.target.value }))}
                required
              />
            </div>

            {passwordError && (
              <p role="alert" className="text-sm text-red-600 dark:text-red-400">
                {passwordError}
              </p>
            )}

            <div className="flex justify-end border-t border-[var(--border)] pt-4">
              <Button type="submit" loading={savingPassword}>
                Alterar senha
              </Button>
            </div>
          </form>
        </Section>
      </div>
    </>
  )
}
