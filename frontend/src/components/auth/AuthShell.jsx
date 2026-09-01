/** Moldura compartilhada pelas telas de login e cadastro. */
import { Link } from 'react-router-dom'
import { BellRing, CalendarCheck, GraduationCap, Search } from 'lucide-react'

const HIGHLIGHTS = [
  {
    icon: CalendarCheck,
    title: 'Agenda inteligente',
    text: 'Planeje sessões de estudo por matéria e tópico específico.',
  },
  {
    icon: BellRing,
    title: 'Lembretes em tempo real',
    text: 'Receba o aviso minutos antes de cada sessão começar.',
  },
  {
    icon: Search,
    title: 'Conteúdo de apoio',
    text: 'Busque os melhores links sobre o tema e salve na anotação.',
  },
]

export default function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="flex min-h-screen">
      {/* Painel de apresentação — escondido em telas pequenas */}
      <aside className="from-brand-700 via-brand-600 to-brand-800 relative hidden w-1/2 flex-col justify-between overflow-hidden bg-gradient-to-br p-12 lg:flex xl:w-[55%]">
        {/* Textura decorativa */}
        <div
          className="pointer-events-none absolute inset-0 opacity-25"
          style={{
            backgroundImage:
              'radial-gradient(circle at 20% 20%, rgba(255,255,255,.35) 0, transparent 45%), radial-gradient(circle at 80% 75%, rgba(255,255,255,.25) 0, transparent 40%)',
          }}
          aria-hidden
        />

        <div className="relative flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
            <GraduationCap className="h-6 w-6 text-white" aria-hidden />
          </div>
          <span className="font-display text-xl text-white">StudySync</span>
        </div>

        <div className="relative">
          <h2 className="font-display max-w-md text-4xl leading-tight text-white">
            Tudo que você estuda, em um só lugar.
          </h2>
          <p className="text-brand-100 mt-4 max-w-md text-[15px] leading-relaxed">
            Organize matérias, escreva anotações em Markdown, agende sessões e receba
            lembretes — com pesquisa de conteúdo integrada.
          </p>

          <ul className="mt-10 space-y-5">
            {HIGHLIGHTS.map(({ icon: Icon, title: t, text }) => (
              <li key={t} className="flex gap-3.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
                  <Icon className="h-[18px] w-[18px] text-white" aria-hidden />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">{t}</p>
                  <p className="text-brand-100 mt-0.5 text-sm">{text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="text-brand-200 relative text-xs">
          FastAPI · SQLAlchemy · React · Tailwind CSS
        </p>
      </aside>

      {/* Formulário */}
      <main className="flex w-full flex-col justify-center px-6 py-12 sm:px-12 lg:w-1/2 xl:w-[45%]">
        <div className="mx-auto w-full max-w-sm">
          <Link to="/login" className="mb-8 flex items-center gap-2.5 lg:hidden">
            <div className="bg-brand-600 flex h-10 w-10 items-center justify-center rounded-xl">
              <GraduationCap className="h-5 w-5 text-white" aria-hidden />
            </div>
            <span className="font-display text-lg">StudySync</span>
          </Link>

          <h1 className="font-display text-2xl">{title}</h1>
          <p className="text-muted mt-1.5 text-sm">{subtitle}</p>

          <div className="mt-8">{children}</div>

          {footer && <div className="text-muted mt-6 text-center text-sm">{footer}</div>}
        </div>
      </main>
    </div>
  )
}
