import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import CandidateCard from "../components/CandidateCard";
import type { CandidateRecommendation } from "../types/recommendation";

const CANDIDATE: CandidateRecommendation = {
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
};

describe("CandidateCard", () => {
  it("renders rank, name and operator_id", () => {
    render(<CandidateCard candidate={CANDIDATE} />);
    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.getByText("Alice Martin")).toBeInTheDocument();
    expect(screen.getByText("(OP-A)")).toBeInTheDocument();
  });

  it("renders total score as percentage", () => {
    render(<CandidateCard candidate={CANDIDATE} />);
    expect(screen.getByText("83%")).toBeInTheDocument();
  });

  it("does not show breakdown before toggle", () => {
    render(<CandidateCard candidate={CANDIDATE} />);
    expect(screen.queryByText("Décomposition du score")).not.toBeInTheDocument();
  });

  it("shows breakdown after clicking toggle", () => {
    render(<CandidateCard candidate={CANDIDATE} />);
    fireEvent.click(screen.getByRole("button", { name: /détails/i }));
    expect(screen.getByText("Décomposition du score")).toBeInTheDocument();
    expect(screen.getByText("Compétences")).toBeInTheDocument();
    expect(screen.getByText("Disponibilité")).toBeInTheDocument();
    expect(screen.getByText("Historique")).toBeInTheDocument();
    expect(screen.getByText("Expérience")).toBeInTheDocument();
  });

  it("shows explanation in details", () => {
    render(<CandidateCard candidate={CANDIDATE} />);
    fireEvent.click(screen.getByRole("button", { name: /détails/i }));
    expect(screen.getByText(/covers 1\/1 required skill/)).toBeInTheDocument();
  });

  it("collapses after toggle again", () => {
    render(<CandidateCard candidate={CANDIDATE} />);
    const btn = screen.getByRole("button", { name: /détails/i });
    fireEvent.click(btn);
    expect(screen.getByText("Décomposition du score")).toBeInTheDocument();
    fireEvent.click(btn);
    expect(screen.queryByText("Décomposition du score")).not.toBeInTheDocument();
  });

  it("shows unmet requirements when present", () => {
    const c = { ...CANDIDATE, unmet_requirements: ["welding proficiency < 3"] };
    render(<CandidateCard candidate={c} />);
    fireEvent.click(screen.getByRole("button", { name: /détails/i }));
    expect(screen.getByText("welding proficiency < 3")).toBeInTheDocument();
  });
});
