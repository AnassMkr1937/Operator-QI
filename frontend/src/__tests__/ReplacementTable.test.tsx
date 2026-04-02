import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { ReplacementTable } from '../components/ReplacementTable'
import type { ReplacementCandidate } from '../types'

const mockCandidates: ReplacementCandidate[] = [
  {
    operator_id: 1,
    matricule: 'OP-001',
    full_name: 'Ahmed Benali',
    score: 87.5,
    mastery_score: 92,
    recency_factor: 0.95,
    quality_penalty: 0.5,
    adjacency_bonus: 5.0,
    days_since_practice: 3,
    reason: 'Maîtrise: 92, récent: 0.95, défauts: 0.8/100',
  },
  {
    operator_id: 2,
    matricule: 'OP-002',
    full_name: 'Sofia Dupont',
    score: 74.2,
    mastery_score: 78,
    recency_factor: 0.85,
    quality_penalty: 3.2,
    adjacency_bonus: 2.5,
    days_since_practice: 14,
    reason: 'Maîtrise: 78, pratique récente insuffisante',
  },
]

describe('ReplacementTable', () => {
  it('renders all candidates', () => {
    render(<ReplacementTable candidates={mockCandidates} />)
    expect(screen.getByText('Ahmed Benali')).toBeInTheDocument()
    expect(screen.getByText('Sofia Dupont')).toBeInTheDocument()
  })

  it('displays candidate matricules', () => {
    render(<ReplacementTable candidates={mockCandidates} />)
    expect(screen.getByText('OP-001')).toBeInTheDocument()
    expect(screen.getByText('OP-002')).toBeInTheDocument()
  })

  it('calls onAssign when Affecter is clicked', async () => {
    const onAssign = vi.fn()
    const user = userEvent.setup()
    render(<ReplacementTable candidates={mockCandidates} onAssign={onAssign} />)
    const buttons = screen.getAllByText('Affecter')
    await user.click(buttons[0])
    expect(onAssign).toHaveBeenCalledWith(mockCandidates[0])
  })

  it('shows reason on row expand', async () => {
    const user = userEvent.setup()
    render(<ReplacementTable candidates={mockCandidates} />)
    const detailsButtons = screen.getAllByText(/Détails/)
    await user.click(detailsButtons[0])
    expect(screen.getByText(/Maîtrise: 92/)).toBeInTheDocument()
  })

  it('shows loading spinner when loading=true', () => {
    render(<ReplacementTable candidates={[]} loading={true} />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows empty state when no candidates', () => {
    render(<ReplacementTable candidates={[]} />)
    expect(screen.getByText(/Aucun candidat/)).toBeInTheDocument()
  })
})
