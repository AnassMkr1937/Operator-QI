import { useState } from "react";
import type { RecommendationRequest, RecommendationResponse } from "../types/recommendation";
import { getRecommendations, ApiError } from "../services/recommendationApi";
import RecommendationForm from "../components/RecommendationForm";
import CandidateList from "../components/CandidateList";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: RecommendationResponse }
  | { status: "error"; message: string };

export default function RecommendationPage() {
  const [state, setState] = useState<State>({ status: "idle" });

  async function handleSubmit(request: RecommendationRequest) {
    setState({ status: "loading" });
    try {
      const data = await getRecommendations(request);
      setState({ status: "success", data });
    } catch (err) {
      const message =
        err instanceof ApiError
          ? `Erreur API (${err.status}) : ${err.message}`
          : err instanceof Error
            ? err.message
            : "Une erreur inattendue s'est produite.";
      setState({ status: "error", message });
    }
  }

  function handleReset() {
    setState({ status: "idle" });
  }

  return (
    <div className="rec-page">
      <header className="rec-page__header">
        <h1 className="rec-page__title">OPERATOR-QI</h1>
        <p className="rec-page__subtitle">
          Recommandation de remplacement d&apos;opérateurs
        </p>
      </header>

      <div className="rec-page__body">
        <RecommendationForm
          onSubmit={handleSubmit}
          isLoading={state.status === "loading"}
        />

        <div className="rec-page__results" aria-live="polite">
          {state.status === "idle" && (
            <div className="rec-page__placeholder">
              <p>Remplissez le formulaire et soumettez pour obtenir les recommandations.</p>
            </div>
          )}

          {state.status === "loading" && (
            <div className="rec-page__loading" role="status" aria-label="Chargement">
              <span className="rec-page__spinner" aria-hidden="true" />
              <p>Calcul des recommandations en cours…</p>
            </div>
          )}

          {state.status === "error" && (
            <div className="rec-page__error" role="alert">
              <strong>Erreur :</strong> {state.message}
              <button
                type="button"
                className="rec-page__btn-retry"
                onClick={handleReset}
              >
                Réessayer
              </button>
            </div>
          )}

          {state.status === "success" && (
            <>
              <CandidateList result={state.data} />
              <button
                type="button"
                className="rec-page__btn-new"
                onClick={handleReset}
              >
                Nouvelle recherche
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
