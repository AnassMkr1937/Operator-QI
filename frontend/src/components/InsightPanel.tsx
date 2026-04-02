/**
 * InsightPanel — Proactive alerting component.
 *
 * Shows:
 * 1. Fragile operations (sorted by risk level)
 * 2. Learning path recommendations
 *
 * Visual design: card-based, traffic light icons, priority badges
 */
import type { InsightsResponse, OperationFragility } from '../types'
import { Badge } from './ui/Badge'
import { Card } from './ui/Card'

interface InsightPanelProps {
  data: InsightsResponse
}

const RISK_ORDER: Record<string, number> = { CRITIQUE: 0, 'ÉLEVÉ': 1, MOYEN: 2, OK: 3 }
const RISK_ICON: Record<string, string>  = { CRITIQUE: '🔴', 'ÉLEVÉ': '🟠', MOYEN: '🟡', OK: '🟢' }
const RISK_VARIANT: Record<string, 'danger' | 'warning' | 'info' | 'success'> = {
  CRITIQUE: 'danger',
  'ÉLEVÉ': 'warning',
  MOYEN: 'info',
  OK: 'success',
}

function FragilityItem({ op }: { op: OperationFragility }) {
  return (
    <div className="fragility-item">
      <div>
        <div className="fragility-item__name">
          {RISK_ICON[op.risk_level]} {op.operation_name}
        </div>
        <div className="fragility-item__meta">
          Ligne {op.line} · Criticité {op.criticality}/5 · {op.qualified_operators_count} opérateur(s)
        </div>
      </div>
      <Badge variant={RISK_VARIANT[op.risk_level]}>{op.risk_level}</Badge>
    </div>
  )
}

export function InsightPanel({ data }: InsightPanelProps) {
  const sorted = [...data.fragile_operations].sort(
    (a, b) => (RISK_ORDER[a.risk_level] ?? 99) - (RISK_ORDER[b.risk_level] ?? 99)
  )

  const critical = sorted.filter((op) => op.risk_level === 'CRITIQUE')
  const paths = data.learning_paths.slice(0, 8)

  return (
    <div className="insight-grid">
      <Card
        title="⚠ Opérations à risque"
        subtitle={`${critical.length} critique(s) — ${sorted.length} total`}
      >
        {sorted.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__text">✅ Aucune fragilité détectée</div>
          </div>
        ) : (
          sorted.map((op) => <FragilityItem key={op.operation_id} op={op} />)
        )}
      </Card>

      <Card
        title="📈 Parcours d'apprentissage"
        subtitle={`${paths.length} recommandations prioritaires`}
      >
        {paths.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__text">Aucune recommandation</div>
          </div>
        ) : (
          paths.map((path) => (
            <div key={`${path.operator_id}-${path.target_operation_id}`} className="learning-path-item">
              <div className="learning-path-item__header">
                <span className="font-medium text-sm">{path.operator_name}</span>
                <Badge variant={path.recommended_priority === 'HIGH' ? 'danger' : path.recommended_priority === 'MEDIUM' ? 'warning' : 'info'}>
                  {path.recommended_priority}
                </Badge>
              </div>
              <span className="text-xs text-muted">
                → {path.target_operation_name} · {path.estimated_weeks_to_qualify}sem · score adj.: {path.current_adjacent_score.toFixed(0)}
              </span>
            </div>
          ))
        )}
      </Card>
    </div>
  )
}
