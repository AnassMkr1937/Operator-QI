import React from 'react'

interface CardProps {
  title?: string
  subtitle?: string
  children: React.ReactNode
  className?: string
  actions?: React.ReactNode
}

export function Card({ title, subtitle, children, className = '', actions }: CardProps) {
  return (
    <div className={`card ${className}`}>
      {(title || subtitle || actions) && (
        <div className="card__header">
          <div>
            {title && <div className="card__title">{title}</div>}
            {subtitle && <div className="card__subtitle">{subtitle}</div>}
          </div>
          {actions && <div>{actions}</div>}
        </div>
      )}
      <div className="card__body">{children}</div>
    </div>
  )
}
