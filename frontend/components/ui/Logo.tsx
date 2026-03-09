'use client'

import { useTheme } from '@/components/design-system/theme-provider'

interface LogoProps {
  variant: 'icon' | 'horizontal' | 'stacked'
  className?: string
  alt?: string
}

export function Logo({ variant, className, alt = 'RechnungsWerk' }: LogoProps) {
  const { resolved } = useTheme()
  const suffix = resolved === 'dark' ? '-dark' : ''
  return <img src={`/logo-${variant}${suffix}.png`} alt={alt} className={className} />
}
