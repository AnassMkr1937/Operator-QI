import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import CandidateList from "../components/CandidateList";
import type { RecommendationResponse } from "../types/recommendation";

const RESPONSE: RecommendationResponse = {
  operation_id: "OP-001",
  total_candidates: 2,
  total_eligible: 1,
  filtered_out: ["OP-B"],
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

describe("CandidateList", () => {
  it("renders operation_id in title", () => {
    render(<CandidateList result={RESPONSE} />);
    expect(screen.getByText("OP-001")).toBeInTheDocument();
  });

  it("shows eligible/total summary", () => {
    render(<CandidateList result={RESPONSE} />);
    expect(screen.getByText(/1 candidat éligible sur 2/)).toBeInTheDocument();
  });

  it("shows filtered_out IDs", () => {
    render(<CandidateList result={RESPONSE} />);
    expect(screen.getByText(/OP-B/)).toBeInTheDocument();
  });

  it("renders a candidate card", () => {
    render(<CandidateList result={RESPONSE} />);
    expect(screen.getByText("Alice Martin")).toBeInTheDocument();
  });

  it("renders empty state when recommendations is empty", () => {
    const empty: RecommendationResponse = {
      ...RESPONSE,
      recommendations: [],
      total_eligible: 0,
      filtered_out: ["OP-A", "OP-B"],
    };
    render(<CandidateList result={empty} />);
    expect(
      screen.getByText(/aucun candidat éligible/i),
    ).toBeInTheDocument();
  });
});

describe("CandidateList — expand a card from list", () => {
  it("expands breakdown when toggle is clicked", () => {
    render(<CandidateList result={RESPONSE} />);
    fireEvent.click(screen.getByRole("button", { name: /détails/i }));
    expect(screen.getByText("Décomposition du score")).toBeInTheDocument();
  });
});
