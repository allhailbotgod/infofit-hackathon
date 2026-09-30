import { api } from '../api.js';
import { saveSession, saveToken, user } from '../auth.js';
import { providerCard, message } from '../components.js';
import { dateLabel, errorMessage, escapeHtml, formDataObject, setSubmitting, showToast, today } from '../utils.js';

export async function homePage() {
  const categories = await api.categories();
  return `<section class="hero"><div><p class="eyebrow">LOCAL SERVICES, MADE SIMPLE</p><h1>Find a capable hand nearby.</h1><p>Connect with local professionals for home, repair and everyday services.</p><div class="actions"><a class="button" href="#providers">Find a provider</a><a class="button button-secondary" href="#register">Join the marketplace</a></div></div></section>
  <section class="content-section"><div class="section-heading"><div><p class="eyebrow">BROWSE SERVICES</p><h2>What do you need help with?</h2></div><a href="#providers">See providers</a></div><div class="category-grid">${categories.length ? categories.map(category => `<a class="card category-card" href="#providers?service_id=${category.id}"><h3>${escapeHtml(category.name)}</h3><p>${escapeHtml(category.description)}</p></a>`).join('') : '<p>No service categories are available yet.</p>'}</div></section>`;
}

export function loginPage() {
  return `<section class="form-page"><form id="login-form" class="card form-card"><h1>Welcome back</h1><p class="muted">Log in to manage your service marketplace account.</p><div id="form-feedback"></div><label>Email<input name="email" type="email" autocomplete="email" required></label><label>Password<input name="password" type="password" autocomplete="current-password" required></label><button class="button" type="submit">Log in</button><p class="muted">New here? <a href="#register">Create an account</a>.</p></form></section>`;
}

export function registerPage() {
  return `<section class="form-page"><form id="register-form" class="card form-card"><h1>Create your account</h1><p class="muted">Choose customer to request services, or provider to offer them.</p><div id="form-feedback"></div><div class="two-columns"><label>Full name<input name="name" autocomplete="name" required maxlength="120"></label><label>Phone<input name="phone" type="tel" autocomplete="tel" required maxlength="30"></label></div><label>Email<input name="email" type="email" autocomplete="email" required></label><label>Password<input name="password" type="password" minlength="5" autocomplete="new-password" required></label><label>Account type<select name="role" id="registration-role"><option value="customer">Customer</option><option value="provider">Service provider</option></select></label><fieldset id="provider-fields" hidden><legend>Provider details</legend><label>Short bio<textarea name="bio" maxlength="1000"></textarea></label><div class="two-columns"><label>Years of experience<input name="experience_years" type="number" min="0" value="0"></label><label>Location<input name="location" maxlength="120"></label></div><label>Area<input name="area" maxlength="120"></label></fieldset><button class="button" type="submit">Create account</button><p class="muted">Already registered? <a href="#login">Log in</a>.</p></form></section>`;
}

export async function providersPage(params) {
  const [categories, providers] = await Promise.all([api.categories(), api.providers(params)]);
  const options = categories.map(category => `<option value="${category.id}" ${params.service_id === category.id ? 'selected' : ''}>${escapeHtml(category.name)}</option>`).join('');
  return `<section class="content-section"><div class="section-heading"><div><p class="eyebrow">DISCOVER</p><h1>Local service providers</h1></div></div><form id="provider-filter" class="filter-bar card"><label>Search<input name="search" value="${escapeHtml(params.search || '')}" placeholder="Name"></label><label>Service<select name="service_id"><option value="">All services</option>${options}</select></label><label>Location<input name="location" value="${escapeHtml(params.location || '')}" placeholder="e.g. Awka"></label><label>Area<input name="area" value="${escapeHtml(params.area || '')}" placeholder="Area"></label><label class="checkbox-label"><input name="is_available" type="checkbox" value="true" ${params.is_available === 'true' ? 'checked' : ''}> Available now</label><button class="button" type="submit">Search</button></form><div class="provider-grid">${providers.length ? providers.map(providerCard).join('') : `<div class="empty-state"><h2>No providers found</h2><p>Try changing your search or filters.</p></div>`}</div></section>`;
}

export async function providerPage(id) {
  const [provider, reviews] = await Promise.all([api.provider(id), api.reviews(id)]);
  const currentUser = user();
  const services = provider.services.map(service => `<li>${escapeHtml(service.name)}<span>${escapeHtml(service.description)}</span></li>`).join('') || '<li>No services listed.</li>';
  const reviewMarkup = reviews.length ? reviews.map(review => `<article class="review"><strong>${'★'.repeat(review.rating)}${'☆'.repeat(5 - review.rating)}</strong><p>${escapeHtml(review.comment)}</p><small>${dateLabel(review.created_at.slice(0, 10))}</small></article>`).join('') : '<p class="muted">No reviews yet.</p>';
  const requestAction = currentUser?.role === 'customer' ? `<a class="button" href="#request/${provider.id}">Request service</a>` : !currentUser ? '<a class="button" href="#login">Log in to request service</a>' : '';
  return `<section class="content-section"><a class="back-link" href="#providers">← Back to providers</a><div class="detail-layout"><article class="card provider-detail"><div class="card-heading"><div><h1>${escapeHtml(provider.name)}</h1><p class="muted">${escapeHtml(provider.location)}${provider.area ? ` · ${escapeHtml(provider.area)}` : ''}</p></div><span class="badge badge-${provider.verification_status}">${escapeHtml(provider.verification_status)}</span></div><p>${escapeHtml(provider.bio || 'No profile description yet.')}</p><dl class="details"><div><dt>Experience</dt><dd>${provider.experience_years} years</dd></div><div><dt>Availability</dt><dd>${provider.is_available ? 'Available to take requests' : 'Not currently available'}</dd></div><div><dt>Rating</dt><dd>${provider.average_rating === null ? 'No ratings yet' : `★ ${provider.average_rating.toFixed(1)} from ${provider.review_count} review(s)`}</dd></div></dl>${requestAction}</article><aside class="card"><h2>Services</h2><ul class="service-list">${services}</ul></aside></div><section class="reviews"><h2>Reviews</h2>${reviewMarkup}</section></section>`;
}

export async function requestFormPage(providerId) {
  const provider = await api.provider(providerId);
  const options = provider.services.map(service => `<option value="${service.service_category_id}">${escapeHtml(service.name)}</option>`).join('');
  if (!options) return `<section class="content-section">${message('This provider has no services available to request.', 'error')}</section>`;
  return `<section class="form-page"><form id="create-request-form" class="card form-card" data-provider-id="${provider.id}"><h1>Request ${escapeHtml(provider.name)}</h1><p class="muted">Tell the provider what you need and when.</p><div id="form-feedback"></div><label>Service<select name="service_category_id" required>${options}</select></label><label>What do you need?<textarea name="description" minlength="1" maxlength="1000" required></textarea></label><div class="two-columns"><label>Preferred date<input name="requested_date" type="date" min="${today()}" required></label><label>Preferred time<input name="requested_time" type="time" required></label></div><button class="button" type="submit">Send request</button></form></section>`;
}

export function accountPage() {
  const currentUser = user();
  return `<section class="form-page"><article class="card form-card"><h1>Account</h1><dl class="details"><div><dt>Name</dt><dd>${escapeHtml(currentUser.name)}</dd></div><div><dt>Email</dt><dd>${escapeHtml(currentUser.email)}</dd></div><div><dt>Phone</dt><dd>${escapeHtml(currentUser.phone)}</dd></div><div><dt>Role</dt><dd>${escapeHtml(currentUser.role)}</dd></div></dl><p class="muted">Account editing is not available in the current API.</p></article></section>`;
}

export function bindPublicPage(route) {
  document.querySelector('#registration-role')?.addEventListener('change', event => { document.querySelector('#provider-fields').hidden = event.target.value !== 'provider'; });
  document.querySelector('#login-form')?.addEventListener('submit', login);
  document.querySelector('#register-form')?.addEventListener('submit', register);
  document.querySelector('#provider-filter')?.addEventListener('submit', event => { event.preventDefault(); const values = formDataObject(event.currentTarget); if (!event.currentTarget.is_available.checked) delete values.is_available; location.hash = `#providers?${new URLSearchParams(values)}`; });
  document.querySelector('#create-request-form')?.addEventListener('submit', createRequest);
}

async function login(event) {
  event.preventDefault(); const form = event.currentTarget; const feedback = form.querySelector('#form-feedback'); setSubmitting(form, true); feedback.innerHTML = '';
  try { const data = formDataObject(form); const session = await api.login(data.email, data.password); saveToken(session.access_token); const currentUser = await api.me(); saveSession(session.access_token, currentUser); showToast('You are logged in.'); location.hash = currentUser.role === 'admin' ? '#admin' : currentUser.role === 'provider' ? '#provider-dashboard' : '#providers'; } catch (error) { feedback.innerHTML = message(errorMessage(error), 'error'); } finally { setSubmitting(form, false); }
}

async function register(event) {
  event.preventDefault(); const form = event.currentTarget; const feedback = form.querySelector('#form-feedback'); const data = formDataObject(form); if (data.role === 'provider') data.experience_years = Number(data.experience_years || 0); else ['bio', 'experience_years', 'location', 'area'].forEach(key => delete data[key]); setSubmitting(form, true); feedback.innerHTML = '';
  try { await api.register(data); showToast('Account created. Please log in.'); location.hash = '#login'; } catch (error) { feedback.innerHTML = message(errorMessage(error), 'error'); } finally { setSubmitting(form, false); }
}

async function createRequest(event) {
  event.preventDefault(); const form = event.currentTarget; const feedback = form.querySelector('#form-feedback'); const data = { ...formDataObject(form), provider_id: form.dataset.providerId }; setSubmitting(form, true); feedback.innerHTML = '';
  try { await api.createRequest(data); showToast('Your service request has been sent.'); location.hash = '#requests'; } catch (error) { feedback.innerHTML = message(errorMessage(error), 'error'); } finally { setSubmitting(form, false); }
}
