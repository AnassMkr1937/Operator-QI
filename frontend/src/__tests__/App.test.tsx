import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "../App";

describe("App", () => {
  it("renders the app title", () => {
    render(<App />);
    expect(screen.getByText("OPERATOR-QI")).toBeInTheDocument();
  });

  it("renders the recommendation page subtitle", () => {
    render(<App />);
    expect(
      screen.getByText(/recommandation de remplacement/i)
    ).toBeInTheDocument();
  });
});
