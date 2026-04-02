import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import { SkillMatrix } from '../components/SkillMatrix'
import type { Operator, Operation, SkillSnapshot } from '../types'

const operators: Operator[] = [
  { id: 1, matricule: 'OP-001', full_name: 'Ahmed Benali', team: 'A', shift: 'matin', status: 'present', created_at: '2024-01-01' },
  { id: 2, matricule: 'OP-002', full_name: 'Sofia Dupont', team: 'B', shift: 'aprem', status: 'present', created_at: '2024-01-01' },
]

const operations: Operation[] = [
  { id: 10, code: 'OP-A', name: 'Assemblage A', line: 'L1', criticality: 3 },
  { id: 11, code: 'OP-B', name: 'Soudure B',    line: 'L2', criticality: 5 },
]

const snapshots: SkillSnapshot[] = [
  { id: 1, operator_id: 1, operation_id: 10, mastery_score: 90, last_practice: '2024-01-15', decay_rate: 0.02, total_hours: 120 },
  { id: 2, operator_id: 1, operation_id: 11, mastery_score: 45, last_practice: '2024-01-01', decay_rate: 0.03, total_hours: 30 },
  { id: 3, operator_id: 2, operation_id: 10, mastery_score: 72, last_practice: '2024-01-10', decay_rate: 0.02, total_hours: 80 },
]

describe('SkillMatrix', () => {
  it('renders operator names', () => {
    render(<SkillMatrix operators={operators} operations={operations} snapshots={snapshots} />)
    expect(screen.getByText('Ahmed Benali')).toBeInTheDocument()
    expect(screen.getByText('Sofia Dupont')).toBeInTheDocument()
  })

  it('renders operation codes in header', () => {
    render(<SkillMatrix operators={operators} operations={operations} snapshots={snapshots} />)
    expect(screen.getByText('OP-A')).toBeInTheDocument()
    expect(screen.getByText('OP-B')).toBeInTheDocument()
  })

  it('shows expert cell for score >= 85', () => {
    render(<SkillMatrix operators={operators} operations={operations} snapshots={snapshots} />)
    const expertCell = screen.getByTitle('Ahmed Benali – Assemblage A: 90')
    expect(expertCell).toHaveClass('skill-cell--expert')
  })

  it('shows qualified cell for score 70–84', () => {
    render(<SkillMatrix operators={operators} operations={operations} snapshots={snapshots} />)
    const cell = screen.getByTitle('Sofia Dupont – Assemblage A: 72')
    expect(cell).toHaveClass('skill-cell--qualified')
  })

  it('shows beginner cell for score 30–49', () => {
    render(<SkillMatrix operators={operators} operations={operations} snapshots={snapshots} />)
    const cell = screen.getByTitle('Ahmed Benali – Soudure B: 45')
    expect(cell).toHaveClass('skill-cell--beginner')
  })

  it('shows none cell for missing snapshot', () => {
    render(<SkillMatrix operators={operators} operations={operations} snapshots={snapshots} />)
    const cell = screen.getByTitle('Sofia Dupont – Soudure B: –')
    expect(cell).toHaveClass('skill-cell--none')
  })

  it('shows tooltip on cell click', async () => {
    const user = userEvent.setup()
    render(<SkillMatrix operators={operators} operations={operations} snapshots={snapshots} />)
    const cell = screen.getByTitle('Ahmed Benali – Assemblage A: 90')
    await user.click(cell)
    expect(screen.getByText(/Assemblage A/)).toBeInTheDocument()
  })

  it('shows loading spinner when loading=true', () => {
    render(<SkillMatrix operators={[]} operations={[]} snapshots={[]} loading={true} />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
