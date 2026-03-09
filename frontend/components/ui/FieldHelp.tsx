'use client'
import { useState, useEffect, useRef } from 'react'
import { HelpCircle, X } from 'lucide-react'

interface FieldHelpProps {
  title: string
  description: string
  example?: string
}

export function FieldHelp({ title, description, example }: FieldHelpProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLSpanElement>(null)

  // Click outside schließt das Panel
  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  // Escape schließt das Panel
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open])

  return (
    <span className="relative inline-flex items-center ml-1.5" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="inline-flex items-center justify-center w-5 h-5 rounded-full transition-colors"
        style={{
          color: open ? 'rgb(var(--primary))' : 'rgb(var(--foreground-muted))',
        }}
        aria-label={`Hilfe: ${title}`}
        aria-expanded={open}
      >
        <HelpCircle size={15} />
      </button>

      {open && (
        <div
          role="dialog"
          aria-label={title}
          className="absolute z-50 w-72 rounded-xl p-4 shadow-lg border sm:left-8 sm:top-0 left-0 top-8"
          style={{
            backgroundColor: 'rgb(var(--card))',
            borderColor: 'rgb(var(--border))',
          }}
        >
          <div className="flex items-start justify-between mb-2">
            <h4 className="text-sm font-semibold" style={{ color: 'rgb(var(--foreground))' }}>
              {title}
            </h4>
            <button onClick={() => setOpen(false)} style={{ color: 'rgb(var(--foreground-muted))' }}>
              <X size={14} />
            </button>
          </div>
          <p className="text-xs leading-relaxed" style={{ color: 'rgb(var(--foreground-muted))' }}>
            {description}
          </p>
          {example && (
            <div
              className="mt-2 px-2.5 py-1.5 rounded-lg text-xs font-mono"
              style={{
                backgroundColor: 'rgb(var(--secondary))',
                color: 'rgb(var(--foreground))',
              }}
            >
              Beispiel: {example}
            </div>
          )}
        </div>
      )}
    </span>
  )
}
