/**
 * API service for the operator recommendation endpoints.
 *
 * In development (Vite proxy), requests to /api/* are forwarded to the backend
 * with the /api prefix stripped, so /api/api/v1/... reaches http://backend:8000/api/v1/...
 *
 * In production (nginx), /api/* is proxied to http://backend:8000/* with the
 * /api/ prefix stripped, giving the same result.
 */

import type {
  RecommendationRequest,
  RecommendationResponse,
} from "../types/recommendation";

const API_BASE = "/api";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function getRecommendations(
  request: RecommendationRequest,
): Promise<RecommendationResponse> {
  const response = await fetch(
    `${API_BASE}/api/v1/recommendations/operators`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    },
  );

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const err = (await response.json()) as { detail?: string };
      if (err.detail) {
        detail =
          typeof err.detail === "string"
            ? err.detail
            : JSON.stringify(err.detail);
      }
    } catch {
      // ignore JSON parse error; keep default message
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<RecommendationResponse>;
}
