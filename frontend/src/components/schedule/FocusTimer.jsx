/**
 * Timer de foco (Pomodoro), opcionalmente ligado a uma sessão de estudo.
 *
 * A contagem é baseada em timestamp (`Date.now()` - `targetAt`), não em
 * decremento ingênuo por `setInterval` — assim ela continua correta mesmo se
 * a aba ficar em segundo plano e o navegador atrasar os timers.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { CheckCircle2, Coffee, Pause, Play, RotateCcw, Timer } from 'lucide-react'

import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { useToast } from '@/context/ToastContext'

/** Mesmo padrão de `NotificationContext`: só notifica se já autorizado. */
function notifyNative(title, body) {
  if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return
  try {
    new Notification(title, { body, tag: 'studysync-focus-timer' })
  } catch {
    // Alguns navegadores bloqueiam o construtor fora de um service worker.
  }
}

const PRESETS = [
  { label: '25 / 5', focus: 25, break: 5 },
  { label: '50 / 10', focus: 50, break: 10 },
  { label: '15 / 5', focus: 15, break: 5 },
]

const CYCLES_BEFORE_LONG_BREAK = 4
const LONG_BREAK_MINUTES = 15

/** Beep curto via WebAudio — sem precisar de nenhum arquivo de áudio. */
function playBeep() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()
    const oscillator = ctx.createOscillator()
    const gain = ctx.createGain()
    oscillator.type = 'sine'
    oscillator.frequency.value = 880
    gain.gain.setValueAtTime(0.001, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.25, ctx.currentTime + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6)
    oscillator.connect(gain)
    gain.connect(ctx.destination)
    oscillator.start()
    oscillator.stop(ctx.currentTime + 0.6)
    oscillator.onended = () => ctx.close()
  } catch {
    // Navegador sem suporte a WebAudio, ou bloqueado por política de
    // autoplay — silenciosamente ignorado, o toast já avisa visualmente.
  }
}

function formatClock(seconds) {
  const m = Math.floor(Math.max(0, seconds) / 60)
  const s = Math.max(0, seconds) % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function FocusTimer({ open, onClose, schedule, onComplete }) {
  const toast = useToast()

  const [presetIndex, setPresetIndex] = useState(0)
  const [phase, setPhase] = useState('focus') // 'focus' | 'break'
  const [cycle, setCycle] = useState(1)
  const [running, setRunning] = useState(false)
  const [remaining, setRemaining] = useState(PRESETS[0].focus * 60)

  const targetAtRef = useRef(null)
  const rafRef = useRef(null)

  const preset = PRESETS[presetIndex]
  const phaseMinutes = useMemo(() => {
    if (phase !== 'break') return preset.focus
    const isLongBreak = cycle % CYCLES_BEFORE_LONG_BREAK === 0
    return isLongBreak ? LONG_BREAK_MINUTES : preset.break
  }, [phase, cycle, preset])

  // Reinicia a contagem sempre que a fase/ciclo/preset muda (não durante o
  // próprio tick).
  const resetClock = useCallback((minutes) => {
    setRunning(false)
    setRemaining(minutes * 60)
    targetAtRef.current = null
  }, [])

  useEffect(() => {
    if (!open) return
    resetClock(phaseMinutes)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, presetIndex])

  const advancePhase = useCallback(() => {
    playBeep()
    if (phase === 'focus') {
      toast.reminder('Hora da pausa!', {
        description: 'Levante, alongue e descanse os olhos um pouco.',
      })
      notifyNative('Hora da pausa!', 'Seu ciclo de foco terminou.')
      setPhase('break')
      resetClock(cycle % CYCLES_BEFORE_LONG_BREAK === 0 ? LONG_BREAK_MINUTES : preset.break)
    } else {
      toast.success('Pausa terminada — de volta ao foco!')
      notifyNative('De volta ao foco!', 'A pausa terminou.')
      setCycle((c) => c + 1)
      setPhase('focus')
      resetClock(preset.focus)
    }
  }, [phase, cycle, preset, resetClock, toast])

  // Laço de contagem: recalcula a partir do timestamp-alvo a cada quadro,
  // então atrasos do navegador (aba em segundo plano) não desalinham o
  // relógio exibido.
  useEffect(() => {
    if (!running) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      return undefined
    }

    if (targetAtRef.current === null) {
      targetAtRef.current = Date.now() + remaining * 1000
    }

    const tick = () => {
      const secondsLeft = Math.ceil((targetAtRef.current - Date.now()) / 1000)
      if (secondsLeft <= 0) {
        setRemaining(0)
        setRunning(false)
        targetAtRef.current = null
        advancePhase()
        return
      }
      setRemaining(secondsLeft)
      rafRef.current = requestAnimationFrame(tick)
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running])

  const toggleRunning = () => {
    if (!running) targetAtRef.current = Date.now() + remaining * 1000
    setRunning((value) => !value)
  }

  const resetAll = () => {
    setPhase('focus')
    setCycle(1)
    resetClock(preset.focus)
  }

  const totalSeconds = phaseMinutes * 60
  const progress = totalSeconds > 0 ? 1 - remaining / totalSeconds : 0
  const isLongBreak = phase === 'break' && cycle % CYCLES_BEFORE_LONG_BREAK === 0

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="sm"
      title="Timer de foco"
      description={schedule?.title ? `Sessão: ${schedule.title}` : 'Ciclos de foco e pausa no estilo Pomodoro.'}
    >
      <div className="flex flex-col items-center gap-5 py-2">
        {!running && remaining === phaseMinutes * 60 && phase === 'focus' && cycle === 1 && (
          <div className="flex flex-wrap justify-center gap-1.5">
            {PRESETS.map((item, index) => (
              <button
                key={item.label}
                type="button"
                onClick={() => setPresetIndex(index)}
                className={`rounded-lg border px-3 py-1 text-xs font-medium transition-colors ${
                  index === presetIndex
                    ? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-500/12 dark:text-brand-300'
                    : 'text-muted border-[var(--border)] hover:bg-[var(--surface-hover)]'
                }`}
              >
                {item.label} min
              </button>
            ))}
          </div>
        )}

        <div className="relative flex h-48 w-48 items-center justify-center">
          <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
            <circle cx="50" cy="50" r="45" fill="none" stroke="var(--border)" strokeWidth="6" />
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke={phase === 'focus' ? 'var(--color-brand-500)' : 'var(--color-brand-300)'}
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={2 * Math.PI * 45}
              strokeDashoffset={2 * Math.PI * 45 * (1 - progress)}
              style={{ transition: 'stroke-dashoffset 250ms linear' }}
            />
          </svg>
          <div className="absolute flex flex-col items-center">
            {phase === 'focus' ? (
              <Timer className="text-brand-500 mb-1 h-5 w-5" aria-hidden />
            ) : (
              <Coffee className="text-brand-400 mb-1 h-5 w-5" aria-hidden />
            )}
            <span className="font-display text-4xl font-semibold tabular-nums">
              {formatClock(remaining)}
            </span>
            <span className="text-muted mt-1 text-xs">
              {phase === 'focus' ? 'Foco' : isLongBreak ? 'Pausa longa' : 'Pausa'} · Ciclo {cycle}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="secondary" size="icon" icon={RotateCcw} onClick={resetAll} title="Reiniciar" />
          <Button size="lg" icon={running ? Pause : Play} onClick={toggleRunning}>
            {running ? 'Pausar' : remaining === phaseMinutes * 60 ? 'Iniciar' : 'Continuar'}
          </Button>
        </div>

        {schedule && (
          <Button
            variant="secondary"
            size="sm"
            icon={CheckCircle2}
            className="w-full text-emerald-600 dark:text-emerald-400"
            onClick={() => onComplete?.(schedule)}
          >
            Marcar sessão como concluída
          </Button>
        )}
      </div>
    </Modal>
  )
}
