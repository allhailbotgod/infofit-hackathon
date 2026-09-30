import { API_BASE_URL } from "./config.js";
import { clearSession, token } from "./auth.js";

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (token()) headers.set("Authorization", `Bearer ${token()}`);
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !(options.body instanceof URLSearchParams)
  )
    headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : null;
  if (!response.ok) {
    if (response.status === 401 && token()) {
      clearSession();
      if (!location.hash.startsWith("#login")) location.hash = "#login";
    }
    const detail = Array.isArray(body?.detail)
      ? body.detail.map((item) => item.msg).join(", ")
      : body?.detail;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return body;
}

function query(params = {}) {
  const clean = Object.entries(params).filter(
    ([, value]) => value !== "" && value !== null && value !== undefined,
  );
  return clean.length ? `?${new URLSearchParams(clean)}` : "";
}

export const api = {
  register: (data) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  async login(email, password) {
    const body = new URLSearchParams({ username: email, password });
    return request("/auth/login", {
      method: "POST",
      body,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  me: () => request("/auth/me"),
  categories: () => request("/categories"),
  createCategory: (data) =>
    request("/categories", { method: "POST", body: JSON.stringify(data) }),
  updateCategory: (id, data) =>
    request(`/categories/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteCategory: (id) => request(`/categories/${id}`, { method: "DELETE" }),
  providers: (filters) => request(`/providers${query(filters)}`),
  provider: (id) => request(`/providers/${id}`),
  reviews: (id) => request(`/providers/${id}/reviews`),
  ownProfile: () => request("/provider/profile"),
  updateProfile: (data) =>
    request("/provider/profile", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  ownServices: () => request("/provider/services"),
  addService: (service_category_id) =>
    request("/provider/services", {
      method: "POST",
      body: JSON.stringify({ service_category_id }),
    }),
  removeService: (id) =>
    request(`/provider/services/${id}`, { method: "DELETE" }),
  availability: () => request("/provider/availability"),
  addAvailability: (data) =>
    request("/provider/availability", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateAvailability: (id, data) =>
    request(`/provider/availability/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  removeAvailability: (id) =>
    request(`/provider/availability/${id}`, { method: "DELETE" }),
  requests: () => request("/requests"),
  createRequest: (data) =>
    request("/requests", { method: "POST", body: JSON.stringify(data) }),
  updateRequest: (id, data) =>
    request(`/requests/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  createReview: (id, data) =>
    request(`/requests/${id}/review`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  adminDashboard: () => request("/admin/dashboard"),
  pendingProviders: () => request("/admin/providers/pending"),
  verifyProvider: (id, verification_status) =>
    request(`/admin/providers/${id}/verification`, {
      method: "PATCH",
      body: JSON.stringify({ verification_status }),
    }),
};
