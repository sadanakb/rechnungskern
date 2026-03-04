'use client'

import { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  actionLabel?: string
  actionHref?: string
  onAction?: () => void
}

export default function EmptyState({ icon: Icon, title, description, actionLabel, actionHref, onAction }: EmptyStateProps) {
  const button = actionLabel ? (
    actionHref ? (
      <a href={actionHref} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors" style={{ background: 'rgb(var(--primary))' }}>
        {actionLabel}
      </a>
    ) : (
      <button onClick={onAction} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors" style={{ background: 'rgb(var(--primary))' }}>
        {actionLabel}
      </button>
    )
  ) : null

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4" style={{ background: 'rgb(var(--muted))' }}>
        <Icon size={28} style={{ color: 'rgb(var(--foreground-muted))' }} />
      </div>
      <h3 className="text-lg font-semibold mb-2" style={{ color: 'rgb(var(--foreground))' }}>{title}</h3>
      <p className="text-sm max-w-sm mb-6" style={{ color: 'rgb(var(--foreground-muted))' }}>{description}</p>
      {button}
    </div>
  )
}
