import { escapeHtml, statusBadge } from './utils.js';

export function loading(label = 'Loading…') { return `<section class="page-state"><p>${escapeHtml(label)}</p></section>`; }
export function message(text, kind = 'info') { return `<p class="message ${kind}">${escapeHtml(text)}</p>`; }

export function providerCard(provider) {
  const services = provider.services.map(service => `<span class="tag">${escapeHtml(service.name)}</span>`).join('') || '<span class="muted">No services listed</span>';
  const rating = provider.average_rating === null ? 'No ratings yet' : `★ ${provider.average_rating.toFixed(1)} (${provider.review_count})`;
  return `<article class="card provider-card">
    <div class="card-heading"><div><h3>${escapeHtml(provider.name)}</h3><p class="muted">${escapeHtml(provider.location)}${provider.area ? ` · ${escapeHtml(provider.area)}` : ''}</p></div>${statusBadge(provider.verification_status)}</div>
    <p>${escapeHtml(provider.bio || 'No profile description yet.')}</p>
    <p class="small"><strong>${provider.experience_years}</strong> years experience · ${provider.is_available ? 'Available' : 'Currently unavailable'} · ${rating}</p>
    <div class="tags">${services}</div>
    <a class="button button-secondary" href="#provider/${provider.id}">View profile</a>
  </article>`;
}

export function requestCard(item, role) {
  let actions = '';
  if (role === 'customer' && ['pending', 'accepted'].includes(item.status)) actions = `<button class="button button-danger small-button" data-request-status="cancelled" data-request-id="${item.id}">Cancel</button>`;
  if (role === 'customer' && item.status === 'completed') actions += `<button class="button button-secondary small-button" data-review-id="${item.id}">Leave review</button>`;
  if (role === 'provider' && item.status === 'pending') actions = `<button class="button small-button" data-request-status="accepted" data-request-id="${item.id}">Accept</button><button class="button button-danger small-button" data-request-status="rejected" data-request-id="${item.id}">Reject</button>`;
  if (role === 'provider' && item.status === 'accepted') actions = `<button class="button small-button" data-request-status="completed" data-request-id="${item.id}">Mark completed</button>`;
  return `<article class="card request-card"><div class="card-heading"><h3>Service request</h3>${statusBadge(item.status)}</div>
    <p>${escapeHtml(item.description)}</p><dl class="details"><div><dt>Date</dt><dd>${escapeHtml(item.requested_date)} at ${escapeHtml(item.requested_time)}</dd></div><div><dt>Service ID</dt><dd class="id-text">${escapeHtml(item.service_category_id)}</dd></div></dl>
    ${item.provider_response ? `<p class="provider-note"><strong>Provider note:</strong> ${escapeHtml(item.provider_response)}</p>` : ''}<div class="actions">${actions}</div></article>`;
}

export function renderNav(currentUser) {
  const base = '<a href="#home">Home</a><a href="#providers">Find providers</a>';
  if (!currentUser) return `${base}<a href="#login">Login</a><a class="nav-cta" href="#register">Register</a>`;
  if (currentUser.role === 'customer') return `${base}<a href="#requests">My requests</a><a href="#account">Account</a><button data-logout>Logout</button>`;
  if (currentUser.role === 'provider') return `<a href="#home">Home</a><a href="#requests">Requests</a><a href="#provider-dashboard">My profile</a><button data-logout>Logout</button>`;
  return `<a href="#home">Home</a><a href="#admin">Admin dashboard</a><a href="#providers">Providers</a><button data-logout>Logout</button>`;
}
