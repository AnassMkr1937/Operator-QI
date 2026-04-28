import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import RecommendationForm from "../components/RecommendationForm";
import type { RecommendationRequest } from "../types/recommendation";

const VALID_CANDIDATES_JSON = JSON.stringify([
  {
    operator_id: "OP-A",
    name: "Alice Martin",
    is_active: true,
    skills: [{ skill_id: "welding", proficiency: 4, certified: true }],
    assignments: [],
  },
]);

describe("RecommendationForm — validation", () => {
  let onSubmit: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    onSubmit = vi.fn();
  });

  it("shows error when operation_id is empty", async () => {
    render(<RecommendationForm onSubmit={onSubmit} isLoading={false} />);
    fireEvent.click(screen.getByRole("button", { name: /recommandations/i }));
    expect(
      await screen.findByText(/identifiant d'opération est requis/i),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows error when name is empty", async () => {
    render(<RecommendationForm onSubmit={onSubmit} isLoading={false} />);
    fireEvent.change(screen.getByLabelText(/identifiant \*/i), {
      target: { value: "OP-001" },
    });
    fireEvent.click(screen.getByRole("button", { name: /recommandations/i }));
    expect(
      await screen.findByText(/nom de l'opération est requis/i),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows error when assignment_date is empty", async () => {
    render(<RecommendationForm onSubmit={onSubmit} isLoading={false} />);
    fireEvent.change(screen.getByLabelText(/identifiant \*/i), {
      target: { value: "OP-001" },
    });
    fireEvent.change(screen.getByLabelText(/nom de l'opération \*/i), {
      target: { value: "Ligne A" },
    });
    fireEvent.click(screen.getByRole("button", { name: /recommandations/i }));
    expect(
      await screen.findByText(/date d'affectation est requise/i),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows error when candidates_json is empty", async () => {
    render(<RecommendationForm onSubmit={onSubmit} isLoading={false} />);
    fireEvent.change(screen.getByLabelText(/identifiant \*/i), {
      target: { value: "OP-001" },
    });
    fireEvent.change(screen.getByLabelText(/nom de l'opération \*/i), {
      target: { value: "Ligne A" },
    });
    fireEvent.change(screen.getByLabelText(/date d'affectation \*/i), {
      target: { value: "2024-06-15" },
    });
    fireEvent.click(screen.getByRole("button", { name: /recommandations/i }));
    expect(
      await screen.findByText(/au moins un candidat/i),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows error when candidates_json is invalid JSON", async () => {
    render(<RecommendationForm onSubmit={onSubmit} isLoading={false} />);
    fireEvent.change(screen.getByLabelText(/identifiant \*/i), {
      target: { value: "OP-001" },
    });
    fireEvent.change(screen.getByLabelText(/nom de l'opération \*/i), {
      target: { value: "Ligne A" },
    });
    fireEvent.change(screen.getByLabelText(/date d'affectation \*/i), {
      target: { value: "2024-06-15" },
    });
    fireEvent.change(screen.getByLabelText(/candidats json/i), {
      target: { value: "not-valid-json{" },
    });
    fireEvent.click(screen.getByRole("button", { name: /recommandations/i }));
    expect(await screen.findByText(/json invalide/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows error when top_n is out of range", async () => {
    render(<RecommendationForm onSubmit={onSubmit} isLoading={false} />);
    fireEvent.change(screen.getByLabelText(/top-n \*/i), {
      target: { value: "0" },
    });
    fireEvent.click(screen.getByRole("button", { name: /recommandations/i }));
    expect(await screen.findByText(/top_n doit être entre/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("calls onSubmit with correct payload on valid form", async () => {
    render(<RecommendationForm onSubmit={onSubmit} isLoading={false} />);
    fireEvent.change(screen.getByLabelText(/identifiant \*/i), {
      target: { value: "OP-001" },
    });
    fireEvent.change(screen.getByLabelText(/nom de l'opération \*/i), {
      target: { value: "Ligne A" },
    });
    fireEvent.change(screen.getByLabelText(/date d'affectation \*/i), {
      target: { value: "2024-06-15" },
    });
    fireEvent.change(screen.getByLabelText(/candidats json/i), {
      target: { value: VALID_CANDIDATES_JSON },
    });
    fireEvent.click(screen.getByRole("button", { name: /recommandations/i }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    const payload = onSubmit.mock.calls[0][0] as RecommendationRequest;
    expect(payload.operation.operation_id).toBe("OP-001");
    expect(payload.operation.name).toBe("Ligne A");
    expect(payload.candidates).toHaveLength(1);
    expect(payload.candidates[0].operator_id).toBe("OP-A");
    expect(payload.top_n).toBe(5);
  });

  it("disables submit button when isLoading is true", () => {
    render(<RecommendationForm onSubmit={onSubmit} isLoading={true} />);
    expect(
      screen.getByRole("button", { name: /chargement/i }),
    ).toBeDisabled();
  });
});
