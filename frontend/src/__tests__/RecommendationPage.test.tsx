import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import RecommendationPage from "../pages/RecommendationPage";
import * as api from "../services/recommendationApi";
import type { RecommendationResponse } from "../types/recommendation";

const MOCK_RESPONSE: RecommendationResponse = {
  operation_id: "OP-001",
  total_candidates: 1,
  total_eligible: 1,
  filtered_out: [],
  recommendations: [
    {
      operator_id: "OP-A",
      name: "Alice Martin",
      rank: 1,
      total_score: 0.826,
      breakdown: {
        skills_score: 0.346,
        availability_score: 0.3,
        history_score: 0.0,
        experience_score: 0.032,
        raw_skills: 0.865,
        raw_availability: 1.0,
        raw_history: 0.0,
        raw_experience: 0.32,
      },
      unmet_requirements: [],
      explanation: "covers 1/1 required skill(s).",
    },
  ],
};

const CANDIDATES_JSON = JSON.stringify([
  {
    operator_id: "OP-A",
    name: "Alice Martin",
    is_active: true,
    skills: [{ skill_id: "welding", proficiency: 4, certified: true }],
    assignments: [],
  },
]);

describe("RecommendationPage", () => {
  let spy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    spy = vi.spyOn(api, "getRecommendations");
  });

  afterEach(() => {
    spy.mockRestore();
  });

  it("renders initial idle state", () => {
    render(<RecommendationPage />);
    expect(
      screen.getByText(/remplissez le formulaire/i),
    ).toBeInTheDocument();
  });

  it("shows results after successful API call", async () => {
    spy.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<RecommendationPage />);

    const { fireEvent: fe } = await import("@testing-library/react");
    fe.change(screen.getByLabelText(/identifiant \*/i), {
      target: { value: "OP-001" },
    });
    fe.change(screen.getByLabelText(/nom de l'opération \*/i), {
      target: { value: "Ligne A" },
    });
    fe.change(screen.getByLabelText(/date d'affectation \*/i), {
      target: { value: "2024-06-15" },
    });
    fe.change(screen.getByLabelText(/candidats json/i), {
      target: { value: CANDIDATES_JSON },
    });
    fe.click(screen.getByRole("button", { name: /recommandations/i }));

    await waitFor(() =>
      expect(screen.getByText("Alice Martin")).toBeInTheDocument(),
    );
    expect(screen.getByText(/résultats pour/i)).toBeInTheDocument();
  });

  it("shows error state on API failure", async () => {
    spy.mockRejectedValueOnce(
      new api.ApiError("Internal Server Error", 500),
    );
    render(<RecommendationPage />);

    const { fireEvent: fe } = await import("@testing-library/react");
    fe.change(screen.getByLabelText(/identifiant \*/i), {
      target: { value: "OP-001" },
    });
    fe.change(screen.getByLabelText(/nom de l'opération \*/i), {
      target: { value: "Ligne A" },
    });
    fe.change(screen.getByLabelText(/date d'affectation \*/i), {
      target: { value: "2024-06-15" },
    });
    fe.change(screen.getByLabelText(/candidats json/i), {
      target: { value: CANDIDATES_JSON },
    });
    fe.click(screen.getByRole("button", { name: /recommandations/i }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toBeInTheDocument(),
    );
    expect(screen.getByText(/erreur api/i)).toBeInTheDocument();
  });

  it("returns to idle after clicking Réessayer", async () => {
    spy.mockRejectedValueOnce(
      new api.ApiError("Internal Server Error", 500),
    );
    render(<RecommendationPage />);

    const { fireEvent: fe } = await import("@testing-library/react");
    fe.change(screen.getByLabelText(/identifiant \*/i), {
      target: { value: "OP-001" },
    });
    fe.change(screen.getByLabelText(/nom de l'opération \*/i), {
      target: { value: "Ligne A" },
    });
    fe.change(screen.getByLabelText(/date d'affectation \*/i), {
      target: { value: "2024-06-15" },
    });
    fe.change(screen.getByLabelText(/candidats json/i), {
      target: { value: CANDIDATES_JSON },
    });
    fe.click(screen.getByRole("button", { name: /recommandations/i }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toBeInTheDocument(),
    );
    fe.click(screen.getByRole("button", { name: /réessayer/i }));
    await waitFor(() =>
      expect(screen.getByText(/remplissez le formulaire/i)).toBeInTheDocument(),
    );
  });

  it("shows empty state when API returns no recommendations", async () => {
    spy.mockResolvedValueOnce({
      ...MOCK_RESPONSE,
      recommendations: [],
      total_eligible: 0,
      filtered_out: ["OP-A"],
    });
    render(<RecommendationPage />);

    const { fireEvent: fe } = await import("@testing-library/react");
    fe.change(screen.getByLabelText(/identifiant \*/i), {
      target: { value: "OP-001" },
    });
    fe.change(screen.getByLabelText(/nom de l'opération \*/i), {
      target: { value: "Ligne A" },
    });
    fe.change(screen.getByLabelText(/date d'affectation \*/i), {
      target: { value: "2024-06-15" },
    });
    fe.change(screen.getByLabelText(/candidats json/i), {
      target: { value: CANDIDATES_JSON },
    });
    fe.click(screen.getByRole("button", { name: /recommandations/i }));

    await waitFor(() =>
      expect(screen.getByText(/aucun candidat éligible/i)).toBeInTheDocument(),
    );
  });
});
