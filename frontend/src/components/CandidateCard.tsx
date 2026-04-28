import { useState } from "react";
import type { CandidateRecommendation } from "../types/recommendation";

interface Props {
  candidate: CandidateRecommendation;
}

const BREAKDOWN_LABELS: Record<
  string,
  { label: string; weight: string; rawKey: string }
> = {
  skills_score: {
    label: "Compétences",
    weight: "40%",
    rawKey: "raw_skills",
  },
  availability_score: {
    label: "Disponibilité",
    weight: "30%",
    rawKey: "raw_availability",
  },
  history_score: {
    label: "Historique",
    weight: "20%",
    rawKey: "raw_history",
  },
  experience_score: {
    label: "Expérience",
    weight: "10%",
    rawKey: "raw_experience",
  },
};

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function scoreClass(score: number): string {
  if (score >= 0.7) return "score--high";
  if (score >= 0.4) return "score--medium";
  return "score--low";
}

export default function CandidateCard({ candidate }: Props) {
  const [expanded, setExpanded] = useState(false);
  const { breakdown } = candidate;

  return (
    <article className={`candidate-card ${scoreClass(candidate.total_score)}`}>
      <div className="candidate-card__header">
        <span className="candidate-card__rank">#{candidate.rank}</span>
        <div className="candidate-card__identity">
          <strong className="candidate-card__name">{candidate.name}</strong>
          <span className="candidate-card__id">({candidate.operator_id})</span>
        </div>
        <div className="candidate-card__score-block">
          <span className="candidate-card__score-label">Score global</span>
          <span className="candidate-card__score-value">
            {pct(candidate.total_score)}
          </span>
          <div
            className="score-bar"
            role="progressbar"
            aria-valuenow={Math.round(candidate.total_score * 100)}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className="score-bar__fill"
              style={{ width: pct(candidate.total_score) }}
            />
          </div>
        </div>
        <button
          type="button"
          className="candidate-card__toggle"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          aria-controls={`breakdown-${candidate.operator_id}`}
        >
          {expanded ? "Réduire ▲" : "Détails ▼"}
        </button>
      </div>

      {expanded && (
        <div
          id={`breakdown-${candidate.operator_id}`}
          className="candidate-card__details"
        >
          <h4 className="candidate-card__details-title">Décomposition du score</h4>
          <table className="breakdown-table">
            <thead>
              <tr>
                <th>Composant</th>
                <th>Poids</th>
                <th>Brut</th>
                <th>Pondéré</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(BREAKDOWN_LABELS).map(
                ([key, { label, weight, rawKey }]) => {
                  const weightedVal =
                    breakdown[key as keyof typeof breakdown] as number;
                  const rawVal =
                    breakdown[rawKey as keyof typeof breakdown] as number;
                  return (
                    <tr key={key}>
                      <td>{label}</td>
                      <td>{weight}</td>
                      <td>{pct(rawVal)}</td>
                      <td>{pct(weightedVal)}</td>
                    </tr>
                  );
                },
              )}
            </tbody>
          </table>

          <p className="candidate-card__explanation">
            <em>{candidate.explanation}</em>
          </p>

          {candidate.unmet_requirements.length > 0 && (
            <div className="candidate-card__unmet">
              <strong>Exigences non satisfaites :</strong>
              <ul>
                {candidate.unmet_requirements.map((req, i) => (
                  <li key={i}>{req}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </article>
  );
}
