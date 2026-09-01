/** Página 404. */
import { Link } from 'react-router-dom'
import { Compass, Home } from 'lucide-react'

import Button from '@/components/ui/Button'

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <div className="bg-brand-50 dark:bg-brand-500/10 rounded-2xl p-5">
        <Compass className="text-brand-600 dark:text-brand-400 h-10 w-10" aria-hidden />
      </div>

      <p className="text-brand-600 dark:text-brand-400 mt-6 text-sm font-semibold">Erro 404</p>
      <h1 className="font-display mt-1.5 text-3xl">Página não encontrada</h1>
      <p className="text-muted mt-3 max-w-md text-sm leading-relaxed">
        O endereço que você tentou acessar não existe ou foi movido. Verifique o link ou
        volte para o painel.
      </p>

      <Link to="/" className="mt-7">
        <Button icon={Home} size="lg">
          Voltar ao painel
        </Button>
      </Link>
    </div>
  )
}
