import type { Metadata } from 'next'
import type { ReactNode } from 'react'

export const metadata: Metadata = {
  title: 'FAQ – RechnungsKern | Haeufig gestellte Fragen',
  description:
    'Antworten auf alle Fragen zu E-Rechnungspflicht, XRechnung, ZUGFeRD, Peppol, GoBD-Konformitaet, Datenschutz und RechnungsKern. Jetzt informieren.',
  openGraph: {
    title: 'FAQ – RechnungsKern',
    description: 'Antworten zu E-Rechnungspflicht, XRechnung, ZUGFeRD und mehr.',
    type: 'website',
    locale: 'de_DE',
  },
}

export default function FAQLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}
