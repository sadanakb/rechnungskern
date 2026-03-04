'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { ChevronRight, Home } from 'lucide-react'

const LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  invoices: 'Rechnungen',
  angebote: 'Angebote',
  neu: 'Neu erstellen',
  manual: 'Manuelle Eingabe',
  ocr: 'OCR Upload',
  import: 'Import',
  contacts: 'Kontakte',
  suppliers: 'Lieferanten',
  settings: 'Einstellungen',
  analytics: 'Auswertungen',
  audit: 'Audit-Log',
  berichte: 'Berichte',
  recurring: 'Wiederkehrend',
  onboarding: 'Einrichtung',
  templates: 'Vorlagen',
  team: 'Team',
  webhooks: 'Webhooks',
  'api-docs': 'API-Dokumentation',
  validator: 'Validator',
  mahnwesen: 'Mahnwesen',
}

export default function Breadcrumbs() {
  const pathname = usePathname()
  const segments = pathname.split('/').filter(Boolean)

  if (segments.length <= 1) return null // Don't show on top-level pages like /dashboard

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm mb-4" style={{ color: 'rgb(var(--foreground-muted))' }}>
      <Link href="/dashboard" className="hover:underline flex items-center gap-1">
        <Home size={14} />
        <span>Dashboard</span>
      </Link>
      {segments.slice(1).map((segment, i) => {
        const href = '/' + segments.slice(0, i + 2).join('/')
        const label = LABELS[segment] || segment
        const isLast = i === segments.length - 2

        return (
          <span key={href} className="flex items-center gap-1.5">
            <ChevronRight size={14} />
            {isLast ? (
              <span style={{ color: 'rgb(var(--foreground))' }} className="font-medium">{label}</span>
            ) : (
              <Link href={href} className="hover:underline">{label}</Link>
            )}
          </span>
        )
      })}
    </nav>
  )
}
