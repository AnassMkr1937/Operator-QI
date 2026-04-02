/**
 * Replacement Page — "Le bon opérateur en 10 secondes"
 *
 * Full workflow:
 * 1. Select absent operation (dropdown with operation list)
 * 2. Filter by shift (optional)
 * 3. See ranked candidates with scores and explanations
 * 4. Click "Affecter" → confirmation → updates DB
 */
import { useState } from 'react'
import { useOperations } from '../hooks/useOperations'
import { useReplacement } from '../hooks/useReplacement'
import { ReplacementTable } from '../components/ReplacementTable'
import { Card } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import type { ReplacementCandidate } from '../types'

export default function ReplacementPage() {
  const [selectedOpId, setSelectedOpId] = useState<number | null>(null)
  const [shift, setShift] = useState('all')
  const [assigned, setAssigned] = useState<{ candidate: ReplacementCandidate; operationName: string } | null>(null)

  const { data: operations, isLoading: loadingOperations } = useOperations()
  const { data: replacement, isLoading, isFetching } = useReplacement(selectedOpId, shift)

  const selectedOp = operations?.find((o) => o.id === selectedOpId)

  function handleAssign(candidate: ReplacementCandidate) {
    setAssigned({ candidate, operationName: replacement?.operation_name ?? '' })
  }

  return (
    <div>
      <div className="page-header">
        <h1>Remplacement</h1>
        <p>Trouvez le bon opérateur en moins de 10 secondes</p>
      </div>

      {assigned && (
        <div className="alert-banner alert-banner--info">
          ✅ <strong>{assigned.candidate.full_name}</strong> ({assigned.candidate.matricule}) affecté(e) à{' '}
          <strong>{assigned.operationName}</strong> — score {assigned.candidate.score.toFixed(1)}
          <button
            style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
            onClick={() => setAssigned(null)}
          >
            ✕
          </button>
        </div>
      )}

      <Card title="Paramètres de recherche">
        <div className="filter-row">
          <div className="form-group">
            <label htmlFor="rp-op">Poste absent / à couvrir</label>
            {loadingOperations ? (
              <Spinner size="sm" />
            ) : (
              <select
                id="rp-op"
                value={selectedOpId ?? ''}
                onChange={(e) => {
                  setSelectedOpId(e.target.value ? Number(e.target.value) : null)
                  setAssigned(null)
                }}
              >
                <option value="">-- Sélectionner un poste --</option>
                {operations?.map((op) => (
                  <option key={op.id} value={op.id}>
                    {op.code} — {op.name} (Ligne {op.line})
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="rp-shift">Équipe disponible</label>
            <select id="rp-shift" value={shift} onChange={(e) => setShift(e.target.value)}>
              <option value="all">Toutes les équipes</option>
              <option value="matin">Matin</option>
              <option value="aprem">Après-midi</option>
              <option value="nuit">Nuit</option>
            </select>
          </div>

          {selectedOp && (
            <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: '0.125rem' }}>
              <Badge variant={selectedOp.criticality >= 4 ? 'danger' : selectedOp.criticality >= 3 ? 'warning' : 'info'}>
                Criticité {selectedOp.criticality}/5
              </Badge>
            </div>
          )}
        </div>
      </Card>

      {selectedOpId ? (
        <div style={{ marginTop: '1.5rem' }}>
          <Card
            title={`Candidats pour "${replacement?.operation_name ?? '…'}"`}
            subtitle={
              replacement
                ? `${replacement.candidates.length} opérateur(s) éligible(s) · calculé en ${replacement.computation_time_ms}ms`
                : isFetching ? 'Calcul en cours…' : undefined
            }
          >
            <ReplacementTable
              candidates={replacement?.candidates ?? []}
              onAssign={handleAssign}
              loading={isLoading || isFetching}
            />
          </Card>
        </div>
      ) : (
        <div className="empty-state" style={{ marginTop: '2rem' }}>
          <div className="empty-state__icon">🎯</div>
          <div className="empty-state__text">Choisissez un poste à couvrir</div>
          <div className="empty-state__sub">L'algorithme calculera instantanément les meilleurs candidats</div>
        </div>
      )}
    </div>
  )
}
