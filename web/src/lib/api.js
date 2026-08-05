const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `request failed (${status})`);
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${BASE}/api/v1${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (response.status === 204) return null;

  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    // FastAPI validation errors arrive as a list of objects; flatten to one line so
    // the form can show something a person can act on.
    const detail = Array.isArray(body?.detail)
      ? body.detail.map((d) => d.msg).join('; ')
      : body?.detail;
    throw new ApiError(response.status, detail);
  }
  return body;
}

export const api = {
  me: () => request('/auth/me'),
  devLogin: () => request('/auth/dev-login', { method: 'POST' }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  githubLoginUrl: () => `${BASE}/api/v1/auth/github/start`,

  createSubmission: (payload) =>
    request('/submissions', { method: 'POST', body: JSON.stringify(payload) }),
  getSubmission: (id) => request(`/submissions/${id}`),
  listSubmissions: (limit = 20) => request(`/submissions?limit=${limit}`),

  dueReviews: () => request('/reviews/due'),
  completeReview: (id, result) =>
    request(`/reviews/${id}/complete`, {
      method: 'POST',
      body: JSON.stringify({ result }),
    }),

  weakPatterns: () => request('/me/weak-patterns'),
  patterns: () => request('/patterns'),
};

export { ApiError };
