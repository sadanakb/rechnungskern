import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Marketing routes that should be on the main domain
const MARKETING_ROUTES = ['/', '/features', '/pricing', '/impressum', '/datenschutz', '/agb', '/kontakt']

// Auth routes accessible on app subdomain
const AUTH_ROUTES = ['/login', '/register', '/passwort-zuruecksetzen', '/email-verifizieren']

// Dashboard routes only on app subdomain
const DASHBOARD_PREFIXES = ['/dashboard', '/invoices', '/angebote', '/manual', '/ocr', '/import', '/contacts', '/suppliers', '/settings', '/analytics', '/audit', '/reports', '/recurring', '/onboarding', '/templates', '/team', '/webhooks', '/api-docs']

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || ''
  const pathname = request.nextUrl.pathname

  // Skip API routes and static assets
  if (pathname.startsWith('/api') || pathname.startsWith('/_next') || pathname.startsWith('/static') || pathname.includes('.')) {
    return NextResponse.next()
  }

  const isAppSubdomain = hostname.startsWith('app.')

  // In development, don't redirect between subdomains (app.localhost may not resolve)
  const isDev = hostname.includes('localhost') || hostname.includes('127.0.0.1')
  if (isDev) {
    // Only redirect app subdomain root to dashboard
    if (isAppSubdomain && pathname === '/') {
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
    return NextResponse.next()
  }

  // On app subdomain
  if (isAppSubdomain) {
    // Root of app subdomain → redirect to dashboard
    if (pathname === '/') {
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
    // Marketing routes on app subdomain → redirect to main domain
    if (MARKETING_ROUTES.includes(pathname)) {
      const mainDomain = hostname.replace('app.', '')
      return NextResponse.redirect(new URL(pathname, `${request.nextUrl.protocol}//${mainDomain}`))
    }
    return NextResponse.next()
  }

  // On main domain
  // Dashboard routes on main domain → redirect to app subdomain
  if (DASHBOARD_PREFIXES.some(prefix => pathname.startsWith(prefix))) {
    const appDomain = `app.${hostname}`
    return NextResponse.redirect(new URL(pathname, `${request.nextUrl.protocol}//${appDomain}`))
  }
  // Auth routes on main domain → redirect to app subdomain
  if (AUTH_ROUTES.some(route => pathname === route || pathname.startsWith(route + '/'))) {
    const appDomain = `app.${hostname}`
    return NextResponse.redirect(new URL(pathname, `${request.nextUrl.protocol}//${appDomain}`))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|icon-.*\\.png).*)'],
}
