/**
 * Visual score bar (0–100) with color gradient.
 * Green > 80, Yellow 50–80, Red < 50
 */
interface ScoreBarProps {
  score: number
  showLabel?: boolean
}

export function ScoreBar({ score, showLabel = true }: ScoreBarProps) {
  const clampedScore = Math.max(0, Math.min(100, score))

  let colorClass: string
  if (clampedScore >= 80) colorClass = 'score-bar__fill--high'
  else if (clampedScore >= 50) colorClass = 'score-bar__fill--medium'
  else colorClass = 'score-bar__fill--low'

  return (
    <div className="score-bar">
      <div className="score-bar__track">
        <div
          className={`score-bar__fill ${colorClass}`}
          style={{ width: `${clampedScore}%` }}
          role="progressbar"
          aria-valuenow={clampedScore}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      {showLabel && (
        <span className="score-bar__label">{clampedScore.toFixed(0)}</span>
      )}
    </div>
  )
}
