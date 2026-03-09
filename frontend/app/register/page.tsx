'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import { Input } from '@/components/ui/input'

const getMainDomainUrl = (path: string) => {
  if (typeof window !== 'undefined' && window.location.hostname.startsWith('app.')) {
    const mainHost = window.location.hostname.replace('app.', '')
    return `${window.location.protocol}//${mainHost}${path}`
  }
  return path
}

export default function RegisterPage() {
  const { register } = useAuth()
  const router = useRouter()
  const [form, setForm] = useState({
    email: '',
    password: '',
    full_name: '',
    organization_name: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form)
      router.push('/dashboard')
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string | Array<{ msg?: string }> } } }
      const detail = apiError?.response?.data?.detail
      if (typeof detail === 'string') {
        setError(detail)
      } else if (Array.isArray(detail) && detail[0]?.msg) {
        setError(detail[0].msg.replace('Value error, ', ''))
      } else {
        setError('Registrierung fehlgeschlagen. Bitte versuche es erneut.')
      }
    } finally {
      setLoading(false)
    }
  }

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }))

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="text-center mb-8">
          <a
            href={getMainDomainUrl('/')}
            className="inline-flex items-center gap-2 mb-6 text-xl font-bold tracking-tight"
            style={{ color: 'rgb(var(--primary))' }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
              <path d="M14 2v6h6" />
              <path d="M16 13H8" />
              <path d="M16 17H8" />
              <path d="M10 9H8" />
            </svg>
            RechnungsWerk
          </a>
          <h1 className="text-2xl font-bold" style={{ color: 'rgb(var(--foreground))' }}>
            Konto erstellen
          </h1>
          <p className="text-sm mt-2" style={{ color: 'rgb(var(--foreground) / 0.5)' }}>
            Starte kostenlos mit RechnungsWerk
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            id="full_name"
            label="Vollstaendiger Name"
            value={form.full_name}
            onChange={update('full_name')}
            required
          />
          <Input
            id="organization_name"
            label="Firmenname"
            value={form.organization_name}
            onChange={update('organization_name')}
            required
          />
          <Input
            id="email"
            type="email"
            label="E-Mail"
            value={form.email}
            onChange={update('email')}
            required
          />
          <Input
            id="password"
            type="password"
            label="Passwort"
            value={form.password}
            onChange={update('password')}
            required
            hint="Mindestens 10 Zeichen, 1 Grossbuchstabe, 1 Kleinbuchstabe, 1 Zahl, 1 Sonderzeichen (!@#$...)"
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="auth-submit-btn"
          >
            {loading ? 'Wird erstellt...' : 'Registrieren'}
          </button>
        </form>

        <p className="text-center text-sm mt-8" style={{ color: 'rgb(var(--foreground) / 0.5)' }}>
          Bereits ein Konto?{' '}
          <Link
            href="/login"
            className="font-medium transition-colors hover:opacity-80"
            style={{ color: 'rgb(var(--primary))' }}
          >
            Anmelden
          </Link>
        </p>
      </div>
    </div>
  )
}
