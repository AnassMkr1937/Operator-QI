/**
 * SkillMatrixPage — Visual competency matrix with filters and export.
 */
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useOperators } from '../hooks/useOperators'
import { useOperations } from '../hooks/useOperations'
import { SkillMatrix } from '../components/SkillMatrix'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { apiClient } from '../api/client'
import type { SkillSnapshot } from '../types'

function useSkillSnapshots() {
  return useQuery({
    queryKey: ['skill-snapshots'],
    queryFn: async () => {
      const { data } = await apiClient.get<SkillSnapshot[]>('/skills/snapshots')
      return data
    },
    staleTime: 60_000,
  })
}

export default function SkillMatrixPage() {
  const [teamFilter, setTeamFilter] = useState('')
  const [lineFilter, setLineFilter] = useState('')

  const { data: operators = [], isLoading: loadingOps } = useOperators()
  const { data: operations = [], isLoading: loadingOperations } = useOperations()
  const { data: snapshots = [], isLoading: loadingSnaps } = useSkillSnapshots()

  const teams = useMemo(() => [...new Set(operators.map((o) => o.team))].sort(), [operators])
  const lines = useMemo(() => [...new Set(operations.map((o) => o.line))].sort(), [operations])

  const filteredOperators = useMemo(
    () => (teamFilter ? operators.filter((o) => o.team === teamFilter) : operators),
    [operators, teamFilter]
  )

  const filteredOperations = useMemo(
    () => (lineFilter ? operations.filter((o) => o.line === lineFilter) : operations),
    [operations, lineFilter]
  )

  const loading = loadingOps || loadingOperations || loadingSnaps

  function handleExport() {
    const header = ['Opérateur', ...filteredOperations.map((op) => op.code)].join(',')
    const lookup = new Map<number, Map<number, number>>()
    for (const snap of snapshots) {
      if (!lookup.has(snap.operator_id)) lookup.set(snap.operator_id, new Map())
      lookup.get(snap.operator_id)!.set(snap.operation_id, snap.mastery_score)
    }
    const rows = filteredOperators.map((op) =>
      [op.full_name, ...filteredOperations.map((operation) => lookup.get(op.id)?.get(operation.id)?.toFixed(0) ?? '0')].join(',')
    )
    const csv = [header, ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'skill-matrix.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div className="page-header">
        <h1>Matrice de compétences</h1>
        <p>Vue complète des qualifications par opérateur et poste</p>
      </div>

      <Card
        title="Skill Matrix"
        subtitle={`${filteredOperators.length} opérateurs × ${filteredOperations.length} opérations`}
        actions={
          <Button variant="secondary" size="sm" onClick={handleExport} disabled={loading}>
            ⬇ Exporter CSV
          </Button>
        }
      >
        <div className="filter-row">
          <div className="form-group">
            <label htmlFor="sm-team">Équipe</label>
            <select id="sm-team" value={teamFilter} onChange={(e) => setTeamFilter(e.target.value)}>
              <option value="">Toutes les équipes</option>
              {teams.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="sm-line">Ligne</label>
            <select id="sm-line" value={lineFilter} onChange={(e) => setLineFilter(e.target.value)}>
              <option value="">Toutes les lignes</option>
              {lines.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
        </div>

        <SkillMatrix
          operators={filteredOperators}
          operations={filteredOperations}
          snapshots={snapshots}
          loading={loading}
        />
      </Card>
    </div>
  )
}
