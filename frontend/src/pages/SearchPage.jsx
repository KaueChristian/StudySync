/**
 * Pesquisa avulsa de conteúdo de apoio.
 *
 * Diferente do painel embutido nos modais, aqui o usuário escolhe o destino
 * (uma anotação ou uma sessão) depois de ver os resultados.
 */
import { useCallback, useEffect, useState } from 'react'
import { Search, Sparkles } from 'lucide-react'

import ContentSearchPanel from '@/components/search/ContentSearchPanel'
import { Select } from '@/components/ui/Field'
import { PageHeading } from '@/components/ui/Misc'
import { useToast } from '@/context/ToastContext'
import { getErrorMessage } from '@/lib/api'
import { noteService, scheduleService, searchService, subjectService } from '@/lib/services'
import { formatSmartDateTime } from '@/lib/format'

/** Sugestões exibidas quando o usuário ainda não pesquisou nada. */
const EXAMPLES = [
  'partes do corpo humano',
  'revolução industrial causas e consequências',
  'função do segundo grau',
  'ligações químicas iônica e covalente',
  'interpretação de texto dissertativo',
  'leis de Newton exercícios',
]

export default function SearchPage() {
  const toast = useToast()

  const [subjects, setSubjects] = useState([])
  const [notes, setNotes] = useState([])
  const [schedules, setSchedules] = useState([])
  const [savedLinks, setSavedLinks] = useState([])

  const [subjectHint, setSubjectHint] = useState('')
  // Destino no formato "note:12" ou "schedule:5".
  const [destination, setDestination] = useState('')
  const [seed, setSeed] = useState('')

  const loadOptions = useCallback(async () => {
    try {
      const [subjectList, noteList, scheduleList] = await Promise.all([
        subjectService.list(),
        noteService.list({ page: 1, page_size: 50 }),
        scheduleService.upcoming({ hours: 720, limit: 30 }),
      ])
      setSubjects(subjectList)
      setNotes(noteList.items)
      setSchedules(scheduleList)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível carregar as opções.'))
    }
  }, [toast])

  useEffect(() => {
    loadOptions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Recarrega os links já salvos no destino escolhido, para o painel poder
  // marcar os que já existem e permitir removê-los.
  useEffect(() => {
    if (!destination) {
      setSavedLinks([])
      return
    }
    const [kind, id] = destination.split(':')
    searchService
      .saved(kind === 'note' ? { note_id: Number(id) } : { schedule_id: Number(id) })
      .then(setSavedLinks)
      .catch(() => setSavedLinks([]))
  }, [destination])

  const target = destination
    ? destination.startsWith('note:')
      ? { note_id: Number(destination.split(':')[1]) }
      : { schedule_id: Number(destination.split(':')[1]) }
    : null

  return (
    <>
      <PageHeading
        icon={Search}
        title="Pesquisa de conteúdo"
        description="Encontre material de apoio confiável sobre qualquer tema e salve nas suas anotações ou sessões."
      />

      <div className="grid gap-5 lg:grid-cols-[1fr_minmax(0,280px)]">
        <div className="card p-5">
          <ContentSearchPanel
            key={seed} /* força remontagem ao clicar num exemplo */
            defaultQuery={seed}
            subjectHint={subjectHint}
            target={target}
            savedLinks={savedLinks}
            autoSearch={Boolean(seed)}
            onSaved={(link) => setSavedLinks((current) => [...current, link])}
            onRemoved={(link) =>
              setSavedLinks((current) => current.filter((item) => item.id !== link.id))
            }
          />
        </div>

        <aside className="space-y-4">
          <section className="card p-4">
            <h2 className="mb-3 text-sm font-semibold">Refinar e salvar</h2>

            <div className="space-y-3.5">
              <Select
                label="Contexto da matéria"
                hint="Ajuda a desambiguar termos genéricos."
                value={subjectHint}
                onChange={(event) => setSubjectHint(event.target.value)}
              >
                <option value="">Nenhum</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.name}>
                    {subject.name}
                  </option>
                ))}
              </Select>

              <Select
                label="Salvar os links em"
                hint={destination ? undefined : 'Escolha um destino para habilitar o botão salvar.'}
                value={destination}
                onChange={(event) => setDestination(event.target.value)}
              >
                <option value="">Escolher depois</option>

                {notes.length > 0 && (
                  <optgroup label="Anotações">
                    {notes.map((note) => (
                      <option key={`note-${note.id}`} value={`note:${note.id}`}>
                        {note.title}
                      </option>
                    ))}
                  </optgroup>
                )}

                {schedules.length > 0 && (
                  <optgroup label="Próximas sessões">
                    {schedules.map((schedule) => (
                      <option key={`sch-${schedule.id}`} value={`schedule:${schedule.id}`}>
                        {schedule.title} — {formatSmartDateTime(schedule.start_at)}
                      </option>
                    ))}
                  </optgroup>
                )}
              </Select>
            </div>
          </section>

          <section className="card p-4">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <Sparkles className="text-brand-500 h-4 w-4" aria-hidden />
              Exemplos de busca
            </h2>
            <ul className="space-y-1.5">
              {EXAMPLES.map((example) => (
                <li key={example}>
                  <button
                    type="button"
                    onClick={() => setSeed(example)}
                    className="text-muted w-full rounded-lg px-2.5 py-1.5 text-left text-sm transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
                  >
                    {example}
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section className="card p-4">
            <h2 className="mb-2 text-sm font-semibold">Como funciona</h2>
            <p className="text-muted text-xs leading-relaxed">
              A busca percorre vários provedores públicos (DuckDuckGo, Bing e a API da
              Wikipédia) e ordena os resultados por relevância ao tema e confiabilidade da
              fonte — priorizando domínios acadêmicos, governamentais e portais educacionais
              consolidados.
            </p>
          </section>
        </aside>
      </div>
    </>
  )
}
