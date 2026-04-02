/**
 * InsightsPage — Strategic view of workforce skill gaps and recommendations.
 */
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { useInsights } from '../hooks/useInsights'
import { InsightPanel } from '../components/InsightPanel'
import { Card } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'

const RISK_COLORS: Record<string, string> = {
  CRITIQUE: '#c81e1e',
  'ÉLEVÉ': '#c27803',
  MOYEN: '#1c64f2',
  OK: '#057a55',
}

export default function InsightsPage() {
  const { data: insights, isLoading, error } = useInsights()

  if (isLoading) {
    return (
      <div className="loading-center" style={{ height: '60vh' }}>
        <Spinner size="lg" />
        <span>Analyse en cours…</span>
      </div>
    )
  }

  if (error || !insights) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">⚠️</div>
        <div className="empty-state__text">Impossible de charger les insights</div>
        <div className="empty-state__sub">Vérifiez que le backend est démarré</div>
      </div>
    )
  }

  const chartData = insights.fragile_operations
    .slice(0, 12)
    .map((op) => ({
      name: op.operation_name.length > 15 ? op.operation_name.slice(0, 12) + '…' : op.operation_name,
      fullName: op.operation_name,
      count: op.qualified_operators_count,
      risk: op.risk_level,
    }))

  return (
    <div>
      <div className="page-header">
        <h1>Insights RH</h1>
        <p>Analyse proactive des risques de compétences</p>
      </div>

      {/* Summary KPIs */}
      <div className="kpi-grid" style={{ marginBottom: '1.5rem' }}>
        <div className="kpi-card">
          <div className="kpi-card__label">Total opérateurs</div>
          <div className="kpi-card__value">{insights.total_operators}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card__label">Index polyvalence</div>
          <div className={`kpi-card__value ${insights.polyvalence_index >= 2.5 ? 'kpi-card__value--success' : 'kpi-card__value--warning'}`}>
            {insights.polyvalence_index.toFixed(2)}
          </div>
          <div className="kpi-card__delta">postes / opérateur (cible ≥ 2.5)</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card__label">Opérations fragiles</div>
          <div className="kpi-card__value kpi-card__value--warning">
            {insights.fragile_operations.filter((op) => op.risk_level !== 'OK').length}
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card__label">Parcours recommandés</div>
          <div className="kpi-card__value kpi-card__value--success">{insights.learning_paths.length}</div>
        </div>
      </div>

      {/* Fragility bar chart */}
      {chartData.length > 0 && (
        <Card title="📊 Opérateurs qualifiés par poste" className="mb-6" subtitle="Nombre d'opérateurs au-dessus du seuil par opération">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                formatter={(value, _name, props) => [value, (props.payload as { fullName?: string } | undefined)?.fullName ?? '']}
                contentStyle={{ fontSize: 12 }}
              />
              <Bar dataKey="count" name="Opérateurs qualifiés" radius={[3, 3, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={RISK_COLORS[entry.risk] ?? '#6b7280'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', fontSize: '0.75rem', flexWrap: 'wrap' }}>
            {Object.entries(RISK_COLORS).map(([risk, color]) => (
              <span key={risk} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <span style={{ display: 'inline-block', width: 12, height: 12, background: color, borderRadius: 2 }} />
                {risk}
              </span>
            ))}
          </div>
        </Card>
      )}

      {/* Insight panel: fragilities + learning paths */}
      <InsightPanel data={insights} />
    </div>
  )
}
