import type { CandidateRecommendation, RecommendationResponse } from "../types/recommendation";
import CandidateCard from "./CandidateCard";

interface Props {
  result: RecommendationResponse;
}

export default function CandidateList({ result }: Props) {
  const { recommendations, total_candidates, total_eligible, filtered_out, operation_id } =
    result;

  return (
    <section className="candidate-list" aria-label="Résultats de recommandation">
      <div className="candidate-list__summary">
        <h3 className="candidate-list__title">
          Résultats pour <em>{operation_id}</em>
        </h3>
        <p className="candidate-list__meta">
          {total_eligible} candidat{total_eligible !== 1 ? "s" : ""} éligible
          {total_eligible !== 1 ? "s" : ""} sur {total_candidates} fourni
          {total_candidates !== 1 ? "s" : ""}
          {filtered_out.length > 0 && (
            <span className="candidate-list__filtered">
              {" "}
              — {filtered_out.length} exclu
              {filtered_out.length !== 1 ? "s" : ""} (
              {filtered_out.join(", ")})
            </span>
          )}
        </p>
      </div>

      {recommendations.length === 0 ? (
        <div className="candidate-list__empty" role="status">
          <p>Aucun candidat éligible trouvé pour cette opération.</p>
          <p>
            Vérifiez que les compétences obligatoires sont couvertes et qu'il
            n'y a pas de conflits de planning.
          </p>
        </div>
      ) : (
        <ol className="candidate-list__items" aria-label="Candidats classés">
          {recommendations.map((candidate: CandidateRecommendation) => (
            <li key={candidate.operator_id} className="candidate-list__item">
              <CandidateCard candidate={candidate} />
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
