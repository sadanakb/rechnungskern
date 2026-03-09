'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Check, X, ArrowRight } from 'lucide-react'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface OnboardingStep {
  key: string
  done: boolean
  label: string
  description: string
  href: string
}

interface OnboardingChecklistData {
  completed: number
  total: number
  all_done: boolean
  steps: OnboardingStep[]
}

interface OnboardingChecklistProps {
  data: OnboardingChecklistData | null
  loading: boolean
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const LS_KEY = 'rw-checklist-dismissed-completed'
const LS_KEY_HIDDEN = 'rw-checklist-hidden-forever'

const CONFETTI_COLORS = [
  '#84cc16', '#65a30d', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#10b981', '#f97316', '#06b6d4', '#a3e635',
]

/* ------------------------------------------------------------------ */
/*  Confetti (CSS-only)                                                */
/* ------------------------------------------------------------------ */

function Confetti() {
  return (
    <>
      <style>{`
        @keyframes confetti-fall {
          0%   { transform: translateY(-20px) rotate(0deg); opacity: 1; }
          100% { transform: translateY(180px) rotate(720deg); opacity: 0; }
        }
        .confetti-piece {
          position: absolute;
          top: 0;
          width: 8px;
          height: 8px;
          border-radius: 2px;
          animation: confetti-fall 2.4s ease-out forwards;
        }
      `}</style>
      <div className="pointer-events-none absolute inset-x-0 top-0 overflow-hidden" style={{ height: 200 }}>
        {CONFETTI_COLORS.map((color, i) => (
          <div
            key={i}
            className="confetti-piece"
            style={{
              left: `${8 + i * 9}%`,
              backgroundColor: color,
              animationDelay: `${i * 0.12}s`,
            }}
          />
        ))}
      </div>
    </>
  )
}

/* ------------------------------------------------------------------ */
/*  Step circle                                                        */
/* ------------------------------------------------------------------ */

function StepCircle({ done, highlighted }: { done: boolean; highlighted: boolean }) {
  if (done) {
    return (
      <span
        className="flex shrink-0 items-center justify-center rounded-full"
        style={{
          width: 16,
          height: 16,
          backgroundColor: 'rgb(var(--primary))',
        }}
      >
        <Check size={10} color="#fff" strokeWidth={3} />
      </span>
    )
  }

  return (
    <span
      className="flex shrink-0 items-center justify-center rounded-full"
      style={{
        width: 16,
        height: 16,
        border: `2px solid ${highlighted ? 'rgb(var(--primary))' : 'rgb(var(--border))'}`,
      }}
    />
  )
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

export default function OnboardingChecklist({ data, loading }: OnboardingChecklistProps) {
  const [dismissed, setDismissed] = useState(false)
  const [hiddenForever, setHiddenForever] = useState(false)
  const [mounted, setMounted] = useState(false)

  // Read localStorage on mount
  useEffect(() => {
    setMounted(true)
    if (localStorage.getItem(LS_KEY_HIDDEN) === '1') {
      setHiddenForever(true)
    }
    const saved = localStorage.getItem(LS_KEY)
    if (saved !== null) {
      setDismissed(true)
    }
  }, [])

  // Re-show if new progress was made
  useEffect(() => {
    if (!mounted || !data) return
    const saved = localStorage.getItem(LS_KEY)
    if (saved !== null && data.completed > Number(saved)) {
      localStorage.removeItem(LS_KEY)
      setDismissed(false)
    }
  }, [data, mounted])

  const firstOpenIndex = useMemo(
    () => data?.steps.findIndex((s) => !s.done) ?? -1,
    [data],
  )

  // ---- Early returns ----
  if (!mounted) return null
  if (!data && !loading) return null
  if (dismissed) return null
  if (hiddenForever) return null

  // ---- Loading skeleton ----
  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="rounded-xl border p-5"
        style={{
          backgroundColor: 'rgb(var(--card))',
          borderColor: 'rgb(var(--border))',
        }}
      >
        <div className="skeleton mb-4 h-5 w-40 rounded" />
        <div className="skeleton mb-3 h-2 w-full rounded-full" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="skeleton h-4 w-4 rounded-full" />
              <div className="skeleton h-4 flex-1 rounded" />
            </div>
          ))}
        </div>
      </motion.div>
    )
  }

  if (!data) return null

  const { completed, total, all_done, steps } = data

  // ---- Dismiss handler ----
  function handleDismiss() {
    localStorage.setItem(LS_KEY, String(completed))
    setDismissed(true)
  }

  function handleHideForever() {
    localStorage.setItem(LS_KEY_HIDDEN, '1')
    setHiddenForever(true)
  }

  // ---- All done state ----
  if (all_done) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="relative overflow-hidden rounded-xl border p-5"
        style={{
          backgroundColor: 'rgb(var(--card))',
          borderColor: 'rgb(var(--border))',
        }}
      >
        <Confetti />
        <div className="relative flex flex-col items-center py-4 text-center">
          <span className="mb-2 text-3xl">🎉</span>
          <p
            className="text-lg font-semibold"
            style={{ color: 'rgb(var(--foreground))' }}
          >
            Alles erledigt! Sie sind startklar.
          </p>
          <button
            onClick={handleHideForever}
            className="mt-4 cursor-pointer rounded-lg px-4 py-2 text-sm font-medium transition-colors"
            style={{
              backgroundColor: 'rgb(var(--muted))',
              color: 'rgb(var(--foreground-muted))',
            }}
          >
            Ausblenden
          </button>
        </div>
      </motion.div>
    )
  }

  // ---- Normal state ----
  const progressPct = total > 0 ? (completed / total) * 100 : 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="relative rounded-xl border p-5"
      style={{
        backgroundColor: 'rgb(var(--card))',
        borderColor: 'rgb(var(--border))',
      }}
    >
      {/* Dismiss button */}
      <button
        onClick={handleDismiss}
        className="absolute right-3 top-3 cursor-pointer rounded-md p-1 transition-colors hover:opacity-70"
        style={{ color: 'rgb(var(--foreground-muted))' }}
        aria-label="Schließen"
      >
        <X size={16} />
      </button>

      {/* Header */}
      <div className="mb-3 flex items-center justify-between pr-6">
        <h3
          className="text-sm font-semibold"
          style={{ color: 'rgb(var(--foreground))' }}
        >
          Erste Schritte
        </h3>
        <span
          className="text-xs"
          style={{ color: 'rgb(var(--foreground-muted))' }}
        >
          {completed} von {total} erledigt
        </span>
      </div>

      {/* Progress bar */}
      <div
        className="mb-4 h-2 w-full overflow-hidden rounded-full"
        style={{ backgroundColor: 'rgb(var(--muted))' }}
      >
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${progressPct}%`,
            backgroundColor: 'rgb(var(--primary))',
          }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-1">
        {steps.map((step, idx) => {
          const isNextOpen = idx === firstOpenIndex

          if (isNextOpen) {
            return (
              <Link
                key={step.key}
                href={step.href}
                className="flex items-center justify-between gap-3 rounded-lg p-3 transition-colors"
                style={{ backgroundColor: 'rgb(var(--primary-light))' }}
              >
                <div className="flex items-center gap-3">
                  <StepCircle done={false} highlighted />
                  <div>
                    <span
                      className="block text-sm font-medium"
                      style={{ color: 'rgb(var(--foreground))' }}
                    >
                      {step.label}
                    </span>
                    <span
                      className="block text-xs"
                      style={{ color: 'rgb(var(--foreground-muted))' }}
                    >
                      {step.description}
                    </span>
                  </div>
                </div>
                <span
                  className="flex shrink-0 items-center gap-1 text-xs font-medium whitespace-nowrap"
                  style={{ color: 'rgb(var(--primary))' }}
                >
                  Jetzt erledigen <ArrowRight size={14} />
                </span>
              </Link>
            )
          }

          if (step.done) {
            return (
              <div
                key={step.key}
                className="flex items-center gap-3 rounded-lg px-3 py-2"
              >
                <StepCircle done highlighted={false} />
                <span
                  className="text-sm"
                  style={{ color: 'rgb(var(--foreground))' }}
                >
                  {step.label}
                </span>
              </div>
            )
          }

          // Other open (not the next one)
          return (
            <Link
              key={step.key}
              href={step.href}
              className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:opacity-80"
            >
              <StepCircle done={false} highlighted={false} />
              <span
                className="text-sm"
                style={{ color: 'rgb(var(--foreground-muted))' }}
              >
                {step.label}
              </span>
            </Link>
          )
        })}
      </div>
    </motion.div>
  )
}
