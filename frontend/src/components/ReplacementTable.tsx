/**
 * ReplacementTable — Core UI component for the replacement engine.
 *
 * Displays ranked candidates with:
 * - Rank medal / number
 * - Score bar (visual)
 * - Recency indicator
 * - Quality risk badge
 * - Expandable reason explanation
 * - "Affecter" action button
 */
import React, { useState } from 'react'
import type { ReplacementCandidate } from '../types'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'
import { ScoreBar } from './ui/ScoreBar'
import { Spinner } from './ui/Spinner'

interface ReplacementTableProps {
  candidates: ReplacementCandidate[]
  onAssign?: (candidate: ReplacementCandidate) => void
  loading?: boolean
}

function qualityBadge(penalty: number) {
  if (penalty < 1) return <Badge variant="success">✓ Qualité OK</Badge>
  if (penalty < 5) return <Badge variant="warning">⚠ Risque modéré</Badge>
  return <Badge variant="danger">✗ Risque élevé</Badge>
}

function recencyLabel(days: number) {
  if (days <= 7) return <Badge variant="success">Récent ({days}j)</Badge>
  if (days <= 30) return <Badge variant="info">{days}j</Badge>
  return <Badge variant="warning">{days}j</Badge>
}

export function ReplacementTable({ candidates, onAssign, loading }: ReplacementTableProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [assigningId, setAssigningId] = useState<number | null>(null)

  if (loading) {
    return (
      <div className="loading-center">
        <Spinner size="lg" />
        <span>Calcul des remplaçants…</span>
      </div>
    )
  }

  if (candidates.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">👥</div>
        <div className="empty-state__text">Aucun candidat disponible</div>
        <div className="empty-state__sub">Aucun opérateur présent qualifié pour ce poste.</div>
      </div>
    )
  }

  async function handleAssign(candidate: ReplacementCandidate) {
    setAssigningId(candidate.operator_id)
    await onAssign?.(candidate)
    setAssigningId(null)
  }

  return (
    <div className="table-wrapper">
      <table className="replacement-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Opérateur</th>
            <th style={{ minWidth: 160 }}>Score global</th>
            <th>Dernière pratique</th>
            <th>Qualité</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c, idx) => {
            const rank = idx + 1
            const isExpanded = expandedId === c.operator_id
            return (
              <React.Fragment key={c.operator_id}>
                <tr className={isExpanded ? 'expanded' : ''}>
                  <td>
                    <div className={`replacement-row__rank replacement-row__rank--${Math.min(rank, 3)}`}>
                      {rank}
                    </div>
                  </td>
                  <td>
                    <div className="font-medium">{c.full_name}</div>
                    <div className="text-xs text-muted">{c.matricule}</div>
                  </td>
                  <td>
                    <ScoreBar score={c.score} />
                  </td>
                  <td>{recencyLabel(c.days_since_practice)}</td>
                  <td>{qualityBadge(c.quality_penalty)}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setExpandedId(isExpanded ? null : c.operator_id)}
                        aria-expanded={isExpanded}
                      >
                        {isExpanded ? '▲' : '▼'} Détails
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        loading={assigningId === c.operator_id}
                        onClick={() => handleAssign(c)}
                      >
                        Affecter
                      </Button>
                    </div>
                  </td>
                </tr>
                {isExpanded && (
                  <tr className="reason-row">
                    <td colSpan={6}>
                      <strong>Explication :</strong> {c.reason}
                      <div style={{ marginTop: '0.375rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                        <span className="text-xs text-muted">Maîtrise : <strong>{c.mastery_score.toFixed(1)}</strong></span>
                        <span className="text-xs text-muted">Récence : <strong>{c.recency_factor.toFixed(2)}</strong></span>
                        <span className="text-xs text-muted">Pénalité qualité : <strong>{c.quality_penalty.toFixed(2)}</strong></span>
                        <span className="text-xs text-muted">Bonus adjacence : <strong>{c.adjacency_bonus.toFixed(2)}</strong></span>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
