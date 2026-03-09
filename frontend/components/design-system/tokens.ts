/**
 * RechnungsKern Design Tokens
 *
 * Brand colors, spacing, typography, and component styles
 * for a premium German B2B SaaS look.
 */

export const colors = {
  // Primary — Lime (fresh, modern, energetic)
  primary: {
    50: '#f7fee7',
    100: '#ecfccb',
    200: '#d9f99d',
    300: '#bef264',
    400: '#a3e635',
    500: '#84cc16',
    600: '#65a30d',
    700: '#4d7c0f',
    800: '#3f6212',
    900: '#365314',
    950: '#1a2e05',
  },
  // Accent — Green (success, money, invoices)
  accent: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
  // Neutral — Stone (warm-based)
  gray: {
    50: '#fafaf9',
    100: '#f5f5f4',
    200: '#e7e5e4',
    300: '#d6d3d1',
    400: '#a8a29e',
    500: '#78716c',
    600: '#57534e',
    700: '#44403c',
    800: '#292524',
    900: '#1c1917',
    950: '#0c0a09',
  },
  // Status
  success: '#16a34a',
  warning: '#f59e0b',
  error: '#f43f5e',
  info: '#84cc16',
} as const

export const spacing = {
  page: 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',
  section: 'py-6 sm:py-8',
  card: 'p-5 sm:p-6',
} as const

export const typography = {
  h1: 'text-2xl sm:text-3xl font-bold tracking-tight',
  h2: 'text-xl sm:text-2xl font-semibold',
  h3: 'text-lg font-semibold',
  body: 'text-sm text-gray-600 dark:text-gray-400',
  caption: 'text-xs text-gray-500 dark:text-gray-500',
  mono: 'font-mono text-xs',
} as const

export const shadows = {
  card: 'shadow-sm hover:shadow-md transition-shadow',
  elevated: 'shadow-md',
  modal: 'shadow-xl',
} as const

// Confidence level colors for OCR fields
export const confidenceLevels = {
  high: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', dot: 'bg-green-500' },
  medium: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', dot: 'bg-yellow-500' },
  low: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', dot: 'bg-red-500' },
} as const
