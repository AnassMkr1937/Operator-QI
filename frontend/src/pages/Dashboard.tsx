/**
 * Dashboard — Main overview page for the production supervisor.
 *
 * Displays:
 * - KPI cards: present operators, fragile operations, avg polyvalence
 * - Quick replacement form (select operation → see top 3 candidates)
 * - Alert banner for CRITIQUE fragilities
 */
import { useState } from 'react'
import { useOperators } from '../hooks/useOperators'
import { useOperations } from '../hooks/useOperations'
import { useReplacement } from '../hooks/useReplacement'
import { useInsights } from '../hooks/useInsights'
import { ReplacementTable } from '../components/ReplacementTable'
import { Card } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'
import type { ReplacementCandidate } from '../types'

export default function Dashboard() {
  const [selectedOpId, setSelectedOpId] = useState<number | null>(null)
  const [shift, setShift] = useState('all')

  const { data: operators, isLoading: loadingOps } = useOperators()
  const { data: operations, isLoading: loadingOperations } = useOperations()
  const { data: insights, isLoading: loadingInsights } = useInsights()
  const { data: replacement, isLoading: loadingReplacement } = useReplacement(selectedOpId, shift)

  const presentCount = operators?.filter((o) => o.status === 'present').length ?? 0
  const absentCount  = operators?.filter((o) => o.status === 'absent').length ?? 0
  const criticalOps  = insights?.fragile_operations.filter((op) => op.risk_level === 'CRITIQUE') ?? []
  const polyvalence  = insights?.polyvalence_index ?? 0

  function handleAssign(candidate: ReplacementCandidate) {
    const opName = operations?.find((o) => o.id === selectedOpId)?.name ?? 'ce poste'
    alert(`✅ ${candidate.full_name} affecté(e) à ${opName}`)
  }

  return (
    <div>
      <div className="page-header">
        <h1>Tableau de bord</h1>
        <p>Vue d'ensemble en temps réel de la production</p>
      </div>

      {/* Alert banners */}
      {criticalOps.length > 0 && (
        <div className="alert-banner alert-banner--danger">
          🚨 <strong>{criticalOps.length} opération(s) critique(s)</strong> — couverture insuffisante :{' '}
          {criticalOps.map((op) => op.operation_name).join(', ')}
        </div>
      )}

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-card__label">Opérateurs présents</div>
          {loadingOps ? (
            <Spinner />
          ) : (
            <div className="kpi-card__value kpi-card__value--success">{presentCount}</div>
          )}
          <div className="kpi-card__delta">{absentCount} absent(s)</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-card__label">Opérations critiques</div>
          {loadingInsights ? (
            <Spinner />
          ) : (
            <div className={`kpi-card__value ${criticalOps.length > 0 ? 'kpi-card__value--danger' : 'kpi-card__value--success'}`}>
              {criticalOps.length}
            </div>
          )}
          <div className="kpi-card__delta">Risque de sous-couverture</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-card__label">Index polyvalence</div>
          {loadingInsights ? (
            <Spinner />
          ) : (
            <div className={`kpi-card__value ${polyvalence >= 2.5 ? 'kpi-card__value--success' : 'kpi-card__value--warning'}`}>
              {polyvalence.toFixed(1)}
            </div>
          )}
          <div className="kpi-card__delta">postes moyens / opérateur</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-card__label">Total opérateurs</div>
          {loadingOps ? <Spinner /> : (
            <div className="kpi-card__value">{operators?.length ?? 0}</div>
          )}
          <div className="kpi-card__delta">{operations?.length ?? 0} opérations</div>
        </div>
      </div>

      {/* Quick Replacement */}
      <Card
        title="🔄 Trouver un remplaçant rapide"
        subtitle="Sélectionnez un poste pour voir les meilleurs candidats"
      >
        <div className="filter-row">
          <div className="form-group">
            <label htmlFor="dash-op">Poste à couvrir</label>
            {loadingOperations ? (
              <Spinner size="sm" />
            ) : (
              <select
                id="dash-op"
                value={selectedOpId ?? ''}
                onChange={(e) => setSelectedOpId(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">-- Choisir un poste --</option>
                {operations?.map((op) => (
                  <option key={op.id} value={op.id}>
                    {op.code} — {op.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="dash-shift">Équipe</label>
            <select id="dash-shift" value={shift} onChange={(e) => setShift(e.target.value)}>
              <option value="all">Toutes les équipes</option>
              <option value="matin">Matin</option>
              <option value="aprem">Après-midi</option>
              <option value="nuit">Nuit</option>
            </select>
          </div>
        </div>

        {selectedOpId && (
          <ReplacementTable
            candidates={replacement?.candidates.slice(0, 3) ?? []}
            onAssign={handleAssign}
            loading={loadingReplacement}
          />
        )}

        {!selectedOpId && (
          <div className="empty-state">
            <div className="empty-state__icon">🔍</div>
            <div className="empty-state__text">Sélectionnez un poste ci-dessus</div>
            <div className="empty-state__sub">Les 3 meilleurs remplaçants s'afficheront ici</div>
          </div>
        )}
      </Card>
    </div>
  )
}
