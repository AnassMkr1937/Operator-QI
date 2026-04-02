/**
 * SkillMatrix — Visual competency matrix.
 *
 * Renders a grid of (operator × operation) cells colored by mastery score:
 * - Dark green  ≥ 85 (expert)
 * - Light green 70–84 (qualified)
 * - Yellow      50–69 (in progress)
 * - Orange      30–49 (beginner)
 * - Gray        < 30  (not qualified)
 *
 * Clicking a cell shows the SkillSnapshot detail tooltip.
 */
import { useState } from 'react'
import type { Operator, Operation, SkillSnapshot } from '../types'
import { Spinner } from './ui/Spinner'

interface SkillMatrixProps {
  operators: Operator[]
  operations: Operation[]
  snapshots: SkillSnapshot[]
  loading?: boolean
}

function scoreClass(score: number | undefined): string {
  if (score === undefined || score < 30) return 'skill-cell--none'
  if (score < 50) return 'skill-cell--beginner'
  if (score < 70) return 'skill-cell--progress'
  if (score < 85) return 'skill-cell--qualified'
  return 'skill-cell--expert'
}

function scoreLabel(score: number | undefined): string {
  if (score === undefined || score < 30) return '–'
  return score.toFixed(0)
}

interface CellTooltip {
  operatorName: string
  operationName: string
  snapshot: SkillSnapshot | undefined
}

export function SkillMatrix({ operators, operations, snapshots, loading }: SkillMatrixProps) {
  const [tooltip, setTooltip] = useState<CellTooltip | null>(null)

  if (loading) {
    return (
      <div className="loading-center">
        <Spinner size="lg" />
        <span>Chargement de la matrice…</span>
      </div>
    )
  }

  if (operators.length === 0 || operations.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">📊</div>
        <div className="empty-state__text">Aucune donnée disponible</div>
      </div>
    )
  }

  // Build lookup: operatorId → operationId → snapshot
  const lookup = new Map<number, Map<number, SkillSnapshot>>()
  for (const snap of snapshots) {
    if (!lookup.has(snap.operator_id)) lookup.set(snap.operator_id, new Map())
    lookup.get(snap.operator_id)!.set(snap.operation_id, snap)
  }

  return (
    <div>
      {tooltip && (
        <div
          style={{
            background: 'white',
            border: '1px solid var(--color-neutral-200)',
            borderRadius: 'var(--radius)',
            padding: '0.75rem',
            marginBottom: '0.75rem',
            boxShadow: 'var(--shadow-md)',
            fontSize: '0.875rem',
          }}
        >
          <strong>{tooltip.operatorName}</strong> → <strong>{tooltip.operationName}</strong>
          {tooltip.snapshot ? (
            <div style={{ marginTop: '0.25rem', color: 'var(--color-neutral-600)', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <span>Score: <strong>{tooltip.snapshot.mastery_score.toFixed(1)}</strong></span>
              <span>Heures: <strong>{tooltip.snapshot.total_hours.toFixed(0)}</strong></span>
              <span>Dernière pratique: <strong>{new Date(tooltip.snapshot.last_practice).toLocaleDateString('fr-FR')}</strong></span>
            </div>
          ) : (
            <div style={{ color: 'var(--color-neutral-400)', marginTop: '0.25rem' }}>Non qualifié</div>
          )}
        </div>
      )}

      <div className="skill-matrix">
        <table>
          <thead>
            <tr>
              <th>Opérateur</th>
              {operations.map((op) => (
                <th key={op.id} title={op.name}>
                  {op.code}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {operators.map((operator) => {
              const opSnaps = lookup.get(operator.id)
              return (
                <tr key={operator.id}>
                  <td>{operator.full_name}</td>
                  {operations.map((operation) => {
                    const snap = opSnaps?.get(operation.id)
                    const score = snap?.mastery_score
                    return (
                      <td key={operation.id}>
                        <div
                          className={`skill-cell ${scoreClass(score)}`}
                          onClick={() =>
                            setTooltip(
                              tooltip?.operatorName === operator.full_name &&
                                tooltip.operationName === operation.name
                                ? null
                                : { operatorName: operator.full_name, operationName: operation.name, snapshot: snap }
                            )
                          }
                          title={`${operator.full_name} – ${operation.name}: ${scoreLabel(score)}`}
                        >
                          {scoreLabel(score)}
                        </div>
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', fontSize: '0.75rem', color: 'var(--color-neutral-600)' }}>
        {[
          { cls: 'skill-cell--expert',    label: '≥ 85 Expert' },
          { cls: 'skill-cell--qualified', label: '70–84 Qualifié' },
          { cls: 'skill-cell--progress',  label: '50–69 En cours' },
          { cls: 'skill-cell--beginner',  label: '30–49 Débutant' },
          { cls: 'skill-cell--none',      label: '< 30 Non qualifié' },
        ].map(({ cls, label }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <div className={`skill-cell ${cls}`} style={{ width: 20, height: 16, borderRadius: 3, fontSize: 0 }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}
