import { api } from "../api.js";
import { user } from "../auth.js";
import { message, requestCard } from "../components.js";
import {
  errorMessage,
  escapeHtml,
  formDataObject,
  setSubmitting,
  showToast,
} from "../utils.js";

export async function requestsPage() {
  const items = await api.requests();
  const role = user().role;
  return `<section class="content-section"><div class="section-heading"><div><p class="eyebrow">${role === "provider" ? "WORK INBOX" : "YOUR ACTIVITY"}</p><h1>${role === "provider" ? "Incoming requests" : "My service requests"}</h1></div></div><div id="review-panel"></div><div class="request-list">${items.length ? items.map((item) => requestCard(item, role)).join("") : `<div class="empty-state"><h2>Nothing here yet</h2><p>${role === "provider" ? "Requests from customers will appear here." : "Find a provider to create your first request."}</p></div>`}</div></section>`;
}

export async function providerDashboardPage() {
  const [profile, categories, ownServices, availability] = await Promise.all([
    api.ownProfile(),
    api.categories(),
    api.ownServices(),
    api.availability(),
  ]);
  const serviceIds = new Set(
    ownServices.map((service) => service.service_category_id),
  );
  const serviceOptions = categories
    .filter((category) => !serviceIds.has(category.id))
    .map(
      (category) =>
        `<option value="${category.id}">${escapeHtml(category.name)}</option>`,
    )
    .join("");
  const services =
    ownServices
      .map((service) => {
        const category = categories.find(
          (item) => item.id === service.service_category_id,
        );
        return `<li>${escapeHtml(category?.name || service.service_category_id)} <button class="link-button danger-text" data-remove-service="${service.service_category_id}">Remove</button></li>`;
      })
      .join("") || '<li class="muted">No services added.</li>';
  const times =
    availability
      .map(
        (item) =>
          `<li><strong>${escapeHtml(item.day_of_week)}</strong> · ${escapeHtml(item.start_time)}–${escapeHtml(item.end_time)} <button class="link-button" data-edit-availability='${escapeHtml(JSON.stringify(item))}'>Edit</button> <button class="link-button danger-text" data-remove-availability="${item.id}">Remove</button></li>`,
      )
      .join("") || '<li class="muted">No availability hours added.</li>';
  return `<section class="content-section"><div class="section-heading"><div><p class="eyebrow">PROVIDER AREA</p><h1>Manage your profile</h1></div><a class="button button-secondary" href="#requests">View requests</a></div><div class="dashboard-grid"><form id="profile-form" class="card"><h2>Profile</h2><div id="profile-feedback"></div><label>Bio<textarea name="bio" maxlength="1000">${escapeHtml(profile.bio)}</textarea></label><div class="two-columns"><label>Experience (years)<input name="experience_years" type="number" min="0" value="${profile.experience_years}" required></label><label>Location<input name="location" maxlength="120" value="${escapeHtml(profile.location)}" required></label></div><label>Area<input name="area" maxlength="120" value="${escapeHtml(profile.area)}" required></label><label class="checkbox-label"><input name="is_available" type="checkbox" ${profile.is_available ? "checked" : ""}> Accepting new requests</label><p>Verification: <span class="badge badge-${profile.verification_status}">${escapeHtml(profile.verification_status)}</span></p><button class="button" type="submit">Save profile</button></form><section class="card"><h2>Services</h2><ul class="manage-list">${services}</ul>${serviceOptions ? `<form id="service-form" class="inline-form"><label>Add a service<select name="service_category_id">${serviceOptions}</select></label><button class="button" type="submit">Add</button></form>` : '<p class="muted">All available categories have been added.</p>'}</section><section class="card"><h2>Availability</h2><ul class="manage-list">${times}</ul><form id="availability-form" class="inline-form"><input name="availability_id" type="hidden"><label>Day<input name="day_of_week" required placeholder="e.g. Monday"></label><label>Start<input name="start_time" type="time" required></label><label>End<input name="end_time" type="time" required></label><button class="button" type="submit">Save hours</button><button id="cancel-availability" class="link-button" type="button" hidden>Cancel edit</button></form></section></div></section>`;
}

export async function adminPage() {
  const [dashboard, pending, categories] = await Promise.all([
    api.adminDashboard(),
    api.pendingProviders(),
    api.categories(),
  ]);
  const metrics = [
    ["Users", dashboard.total_users],
    ["Providers", dashboard.total_providers],
    ["Verified providers", dashboard.verified_providers],
    ["Pending providers", dashboard.pending_providers],
    ["Service requests", dashboard.total_service_requests],
    ["Completed", dashboard.completed_service_requests],
  ]
    .map(
      ([label, value]) =>
        `<article class="metric"><span>${escapeHtml(label)}</span><strong>${value}</strong></article>`,
    )
    .join("");
  const pendingRows = pending.length
    ? pending
        .map(
          (profile) =>
            `<tr><td class="id-text">${profile.user_id}</td><td>${escapeHtml(profile.location)} · ${escapeHtml(profile.area)}</td><td>${profile.experience_years} years</td><td><button class="button small-button" data-verify-provider="${profile.id}" data-verification="verified">Verify</button> <button class="button button-danger small-button" data-verify-provider="${profile.id}" data-verification="rejected">Reject</button></td></tr>`,
        )
        .join("")
    : '<tr><td colspan="4">No providers are awaiting review.</td></tr>';
  const categoryRows =
    categories
      .map(
        (category) =>
          `<li><strong>${escapeHtml(category.name)}</strong><span>${escapeHtml(category.description)}</span><button class="link-button" data-edit-category='${escapeHtml(JSON.stringify(category))}'>Edit</button><button class="link-button danger-text" data-delete-category="${category.id}">Delete</button></li>`,
      )
      .join("") || "<li>No categories found.</li>";
  return `<section class="content-section"><div class="section-heading"><div><p class="eyebrow">ADMIN</p><h1>Marketplace overview</h1></div></div><div class="metrics">${metrics}</div><div class="dashboard-grid"><section class="card wide-card"><h2>Pending provider verification</h2><div class="table-wrap"><table><thead><tr><th>Provider user ID</th><th>Location</th><th>Experience</th><th>Action</th></tr></thead><tbody>${pendingRows}</tbody></table></div></section><section class="card"><h2>Service categories</h2><ul class="manage-list">${categoryRows}</ul><form id="category-form" class="inline-form"><input name="category_id" type="hidden"><label>Name<input name="name" maxlength="120" required></label><label>Description<textarea name="description" maxlength="1000" required></textarea></label><button class="button" type="submit">Save category</button><button id="cancel-category" class="link-button" type="button" hidden>Cancel edit</button></form></section></div></section>`;
}

export function bindDashboardPage(route) {
  document
    .querySelectorAll("[data-request-status]")
    .forEach((button) => button.addEventListener("click", updateRequest));
  document
    .querySelectorAll("[data-review-id]")
    .forEach((button) => button.addEventListener("click", showReviewForm));
  document
    .querySelector("#profile-form")
    ?.addEventListener("submit", saveProfile);
  document
    .querySelector("#service-form")
    ?.addEventListener("submit", addService);
  document
    .querySelectorAll("[data-remove-service]")
    .forEach((button) => button.addEventListener("click", removeService));
  document
    .querySelector("#availability-form")
    ?.addEventListener("submit", saveAvailability);
  document
    .querySelectorAll("[data-remove-availability]")
    .forEach((button) => button.addEventListener("click", removeAvailability));
  document
    .querySelectorAll("[data-edit-availability]")
    .forEach((button) => button.addEventListener("click", editAvailability));
  document
    .querySelector("#cancel-availability")
    ?.addEventListener("click", resetAvailability);
  document
    .querySelectorAll("[data-verify-provider]")
    .forEach((button) => button.addEventListener("click", verifyProvider));
  document
    .querySelector("#category-form")
    ?.addEventListener("submit", saveCategory);
  document
    .querySelectorAll("[data-edit-category]")
    .forEach((button) => button.addEventListener("click", editCategory));
  document
    .querySelectorAll("[data-delete-category]")
    .forEach((button) => button.addEventListener("click", deleteCategory));
  document
    .querySelector("#cancel-category")
    ?.addEventListener("click", resetCategory);
}

async function updateRequest(event) {
  const button = event.currentTarget;
  let provider_response;
  if (user().role === "provider")
    provider_response =
      window.prompt("Optional message for the customer:", "") ?? undefined;
  button.disabled = true;
  try {
    await api.updateRequest(button.dataset.requestId, {
      status: button.dataset.requestStatus,
      ...(provider_response !== undefined ? { provider_response } : {}),
    });
    showToast("Request status updated.");
    location.hash = "#requests";
  } catch (error) {
    showToast(errorMessage(error), "error");
    button.disabled = false;
  }
}

function showReviewForm(event) {
  const id = event.currentTarget.dataset.reviewId;
  document.querySelector("#review-panel").innerHTML =
    `<form id="review-form" class="card inline-form" data-request-id="${id}"><h2>Leave a review</h2><label>Rating<select name="rating"><option value="5">5 — Excellent</option><option value="4">4 — Good</option><option value="3">3 — Okay</option><option value="2">2 — Poor</option><option value="1">1 — Bad</option></select></label><label>Comment<textarea name="comment" required maxlength="1000"></textarea></label><button class="button" type="submit">Submit review</button></form>`;
  document
    .querySelector("#review-form")
    .addEventListener("submit", submitReview);
}

async function submitReview(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setSubmitting(form, true);
  try {
    const data = formDataObject(form);
    data.rating = Number(data.rating);
    await api.createReview(form.dataset.requestId, data);
    showToast("Thanks for your review.");
    location.hash = "#requests";
  } catch (error) {
    showToast(errorMessage(error), "error");
    setSubmitting(form, false);
  }
}
async function saveProfile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = formDataObject(form);
  data.experience_years = Number(data.experience_years);
  data.is_available = form.is_available.checked;
  setSubmitting(form, true);
  try {
    await api.updateProfile(data);
    showToast("Profile saved.");
    location.hash = "#provider-dashboard";
  } catch (error) {
    form.querySelector("#profile-feedback").innerHTML = message(
      errorMessage(error),
      "error",
    );
    setSubmitting(form, false);
  }
}
async function addService(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setSubmitting(form, true);
  try {
    await api.addService(formDataObject(form).service_category_id);
    showToast("Service added.");
    location.hash = "#provider-dashboard";
  } catch (error) {
    showToast(errorMessage(error), "error");
    setSubmitting(form, false);
  }
}
async function removeService(event) {
  if (!confirm("Remove this service?")) return;
  try {
    await api.removeService(event.currentTarget.dataset.removeService);
    showToast("Service removed.");
    location.hash = "#provider-dashboard";
  } catch (error) {
    showToast(errorMessage(error), "error");
  }
}
async function saveAvailability(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = formDataObject(form);
  const id = data.availability_id;
  delete data.availability_id;
  setSubmitting(form, true);
  try {
    if (id) await api.updateAvailability(id, data);
    else await api.addAvailability(data);
    showToast("Availability saved.");
    location.hash = "#provider-dashboard";
  } catch (error) {
    showToast(errorMessage(error), "error");
    setSubmitting(form, false);
  }
}
function editAvailability(event) {
  const item = JSON.parse(event.currentTarget.dataset.editAvailability);
  const form = document.querySelector("#availability-form");
  Object.entries(item).forEach(([key, value]) => {
    if (form.elements[key]) form.elements[key].value = value;
  });
  form.querySelector('button[type="submit"]').textContent = "Update hours";
  document.querySelector("#cancel-availability").hidden = false;
  form.scrollIntoView({ behavior: "smooth", block: "center" });
}
function resetAvailability() {
  const form = document.querySelector("#availability-form");
  form.reset();
  form.availability_id.value = "";
  form.querySelector('button[type="submit"]').textContent = "Save hours";
  document.querySelector("#cancel-availability").hidden = true;
}
async function removeAvailability(event) {
  if (!confirm("Remove these availability hours?")) return;
  try {
    await api.removeAvailability(
      event.currentTarget.dataset.removeAvailability,
    );
    showToast("Availability removed.");
    location.hash = "#provider-dashboard";
  } catch (error) {
    showToast(errorMessage(error), "error");
  }
}
async function verifyProvider(event) {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    await api.verifyProvider(
      button.dataset.verifyProvider,
      button.dataset.verification,
    );
    showToast(`Provider ${button.dataset.verification}.`);
    location.hash = "#admin";
  } catch (error) {
    showToast(errorMessage(error), "error");
    button.disabled = false;
  }
}
async function saveCategory(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = formDataObject(form);
  const id = data.category_id;
  delete data.category_id;
  setSubmitting(form, true);
  try {
    if (id) await api.updateCategory(id, data);
    else await api.createCategory(data);
    showToast("Category saved.");
    location.hash = "#admin";
  } catch (error) {
    showToast(errorMessage(error), "error");
    setSubmitting(form, false);
  }
}
function editCategory(event) {
  const item = JSON.parse(event.currentTarget.dataset.editCategory);
  const form = document.querySelector("#category-form");
  form.category_id.value = item.id;
  form.name.value = item.name;
  form.description.value = item.description;
  form.querySelector('button[type="submit"]').textContent = "Update category";
  document.querySelector("#cancel-category").hidden = false;
  form.scrollIntoView({ behavior: "smooth", block: "center" });
}
function resetCategory() {
  const form = document.querySelector("#category-form");
  form.reset();
  form.category_id.value = "";
  form.querySelector('button[type="submit"]').textContent = "Save category";
  document.querySelector("#cancel-category").hidden = true;
}
async function deleteCategory(event) {
  if (!confirm("Delete this category? This cannot be undone.")) return;
  try {
    await api.deleteCategory(event.currentTarget.dataset.deleteCategory);
    showToast("Category deleted.");
    location.hash = "#admin";
  } catch (error) {
    showToast(errorMessage(error), "error");
  }
}
