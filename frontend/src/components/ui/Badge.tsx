/**
 * Badge component for status indicators and risk levels.
 * Supports variants: success, warning, danger, info, neutral
 */
import React from 'react'

type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral'

interface BadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  size?: 'sm' | 'md'
}

export function Badge({ children, variant = 'neutral', size = 'md' }: BadgeProps) {
  return (
    <span className={`badge badge--${size} badge--${variant}`}>
      {children}
    </span>
  )
}
