import { api } from './api.js';
import { clearSession, saveSession, token, user } from './auth.js';
import { message, renderNav } from './components.js';
import { bindPublicPage, accountPage, homePage, loadHomeCategories, loginPage, providerLoadingPage, providersLoadingPage, loadProvidersPage, providerPage, registerPage, requestFormLoadingPage, requestFormPage, showHomeCategoriesError } from './pages/public.js';
import { errorMessage } from './utils.js';

const app = document.querySelector('#app');
const nav = document.querySelector('#nav-links');
const protectedRoutes = { requests: ['customer', 'provider', 'admin'], account: ['customer'], 'provider-dashboard': ['provider'], admin: ['admin'], request: ['customer'] };
const dashboardRoutes = new Set(['requests', 'provider-dashboard', 'admin']);
let renderVersion = 0;

function dashboardLoadingPage(route) {
  const card = '<article class="card skeleton-card provider-skeleton" aria-hidden="true"><span class="skeleton-line skeleton-title"></span><span class="skeleton-line skeleton-medium"></span><span class="skeleton-line"></span><span class="skeleton-line skeleton-short"></span><span class="skeleton-button"></span></article>';
  if (route.name === 'requests') return `<section class="content-section"><div class="section-heading"><div><p class="eyebrow">YOUR ACTIVITY</p><h1>My service requests</h1></div></div><div class="request-list" aria-busy="true"><span class="sr-only">Loading service requests</span>${card}${card}${card}</div></section>`;
  if (route.name === 'admin') return `<section class="content-section"><div class="section-heading"><div><p class="eyebrow">ADMIN</p><h1>Marketplace overview</h1></div></div><div class="metrics" aria-busy="true"><span class="skeleton-input"></span><span class="skeleton-input"></span><span class="skeleton-input"></span><span class="skeleton-input"></span><span class="skeleton-input"></span><span class="skeleton-input"></span></div><div class="dashboard-grid">${card}${card}</div></section>`;
  return `<section class="content-section"><div class="section-heading"><div><p class="eyebrow">PROVIDER AREA</p><h1>Manage your profile</h1></div></div><div class="dashboard-grid" aria-busy="true"><span class="sr-only">Loading provider dashboard</span>${card}${card}${card}</div></section>`;
}

function routeInfo() {
  const [path = 'home', query = ''] = location.hash.slice(1).split('?');
  const segments = path.split('/');
  return { name: segments[0] || 'home', id: segments[1], params: Object.fromEntries(new URLSearchParams(query)) };
}

function refreshNav() {
  nav.innerHTML = renderNav(user());
  nav.querySelector('[data-logout]')?.addEventListener('click', () => { clearSession(); location.hash = '#home'; });
}

async function render() {
  const version = ++renderVersion;
  const route = routeInfo();
  const currentUser = user();
  refreshNav();
  if (protectedRoutes[route.name] && (!currentUser || !protectedRoutes[route.name].includes(currentUser.role))) {
    location.hash = currentUser ? '#home' : '#login';
    return;
  }
  if (route.name === 'home') app.innerHTML = homePage();
  else if (route.name === 'login') app.innerHTML = loginPage();
  else if (route.name === 'register') app.innerHTML = registerPage();
  else if (route.name === 'account') app.innerHTML = accountPage();
  else if (route.name === 'providers') app.innerHTML = providersLoadingPage();
  else if (route.name === 'provider' && route.id) app.innerHTML = providerLoadingPage();
  else if (route.name === 'request' && route.id) app.innerHTML = requestFormLoadingPage();
  else if (dashboardRoutes.has(route.name)) app.innerHTML = dashboardLoadingPage(route);
  else app.innerHTML = `<section class="page-state"><p>Loading…</p></section>`;
  bindPublicPage(route);
  app.focus();
  try {
    if (route.name === 'home') {
      const categoryGrid = app.querySelector('#category-grid');
      loadHomeCategories(categoryGrid).catch(error => {
        if (version === renderVersion) showHomeCategoriesError(categoryGrid, error, render);
      });
      return;
    }
    if (route.name === 'providers') {
      loadProvidersPage(app, route.params, () => version === renderVersion);
      return;
    }
    const dashboard = dashboardRoutes.has(route.name) ? await import('./pages/dashboard.js') : null;
    let html;
    if (route.name === 'login') html = loginPage();
    else if (route.name === 'register') html = registerPage();
    else if (route.name === 'provider' && route.id) html = await providerPage(route.id);
    else if (route.name === 'request' && route.id) html = await requestFormPage(route.id);
    else if (route.name === 'requests') html = await dashboard.requestsPage();
    else if (route.name === 'account') html = accountPage();
    else if (route.name === 'provider-dashboard') html = await dashboard.providerDashboardPage();
    else if (route.name === 'admin') html = await dashboard.adminPage();
    else { location.hash = '#home'; return; }
    if (version !== renderVersion) return;
    app.innerHTML = html;
    bindPublicPage(route);
    app.querySelector('[data-retry-route]')?.addEventListener('click', render);
    dashboard?.bindDashboardPage(route);
    app.focus();
  } catch (error) {
    if (version === renderVersion) showError(error);
  }
}

function showError(error) {
  app.innerHTML = `<section class="page-state">${message(errorMessage(error), 'error')}<button class="button button-secondary" id="try-again">Try again</button></section>`;
  app.querySelector('#try-again').addEventListener('click', render);
}

document.querySelector('#menu-toggle').addEventListener('click', () => nav.classList.toggle('open'));
nav.addEventListener('click', event => { if (event.target.matches('a, button')) nav.classList.remove('open'); });
window.addEventListener('hashchange', render);

async function start() {
  if (!location.hash) location.hash = '#home'; else render();
  if (token()) {
    try {
      saveSession(token(), await api.me());
      refreshNav();
      if (protectedRoutes[routeInfo().name]) render();
    } catch {
      clearSession();
      refreshNav();
    }
  }
}
start();
