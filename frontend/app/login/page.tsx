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

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login({ email, password })
      router.push('/dashboard')
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string } } }
      const detail = apiError?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Ungueltige Anmeldedaten')
    } finally {
      setLoading(false)
    }
  }

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
            Willkommen zurück
          </h1>
          <p className="text-sm mt-2" style={{ color: 'rgb(var(--foreground) / 0.5)' }}>
            Melden Sie sich bei Ihrem Konto an
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            id="email"
            type="email"
            label="E-Mail"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            id="password"
            type="password"
            label="Passwort"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex justify-end">
            <Link
              href="/passwort-vergessen"
              className="text-sm font-medium transition-colors hover:opacity-80"
              style={{ color: 'rgb(var(--primary))' }}
            >
              Passwort vergessen?
            </Link>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="auth-submit-btn"
          >
            {loading ? 'Wird angemeldet...' : 'Anmelden'}
          </button>
        </form>

        <p className="text-center text-sm mt-8" style={{ color: 'rgb(var(--foreground) / 0.5)' }}>
          Noch kein Konto?{' '}
          <Link
            href="/register"
            className="font-medium transition-colors hover:opacity-80"
            style={{ color: 'rgb(var(--primary))' }}
          >
            Kostenlos registrieren
          </Link>
        </p>
      </div>
    </div>
  )
}
