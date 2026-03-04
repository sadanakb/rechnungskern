'use client'

import { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { SidebarNav } from '@/components/layout/SidebarNav'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import { CommandPalette } from '@/components/CommandPalette'
import { NotificationBell } from '@/components/layout/NotificationBell'
import { WebSocketProvider } from '@/contexts/WebSocketContext'
import { ChatWidget } from '@/components/ai/ChatWidget'
import { useAuth } from '@/lib/auth'
import { getOnboardingStatus } from '@/lib/api'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [cmdkOpen, setCmdkOpen] = useState(false)
  const { user, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login')
    }
  }, [loading, user, router])

  // Check onboarding status after user loads
  useEffect(() => {
    if (!user || pathname.startsWith('/onboarding')) return
    let cancelled = false
    getOnboardingStatus()
      .then((status) => {
        if (!cancelled && !status.completed) {
          router.replace('/onboarding')
        }
      })
      .catch(() => {
        // Silently ignore — onboarding endpoint may not exist yet
      })
    return () => { cancelled = true }
  }, [user, pathname, router])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCmdkOpen((prev) => !prev)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  if (loading) {
    return (
      <div className="flex h-screen" style={{ background: 'rgb(var(--background))' }}>
        {/* Sidebar skeleton */}
        <div className="hidden md:flex w-64 flex-col border-r p-4 space-y-4" style={{ borderColor: 'rgb(var(--border))' }}>
          <div className="h-8 w-32 rounded animate-pulse" style={{ background: 'rgb(var(--muted))' }} />
          <div className="space-y-2 mt-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-9 rounded animate-pulse" style={{ background: 'rgb(var(--muted))', opacity: 1 - i * 0.08 }} />
            ))}
          </div>
        </div>
        {/* Content skeleton */}
        <div className="flex-1 p-8 space-y-6">
          <div className="h-8 w-48 rounded animate-pulse" style={{ background: 'rgb(var(--muted))' }} />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-32 rounded-lg animate-pulse" style={{ background: 'rgb(var(--muted))' }} />
            ))}
          </div>
          <div className="h-64 rounded-lg animate-pulse" style={{ background: 'rgb(var(--muted))' }} />
        </div>
      </div>
    )
  }

  if (!user) {
    return null // Will redirect via useEffect
  }

  return (
    <WebSocketProvider>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar — desktop only */}
        <SidebarNav />

        {/* Main content area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Topbar */}
          <div
            className="flex items-center justify-end h-14 px-6 border-b shrink-0"
            style={{ borderColor: 'rgb(var(--border))' }}
          >
            <NotificationBell />
          </div>

          <main className="flex-1 overflow-y-auto">
            <div className="px-4 sm:px-6 lg:px-8 pt-4">
              <Breadcrumbs />
            </div>
            {children}
          </main>
        </div>

        <CommandPalette open={cmdkOpen} onOpenChange={setCmdkOpen} />
        <ChatWidget />
      </div>
    </WebSocketProvider>
  )
}
