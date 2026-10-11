import { api } from './api.js';
import { clearSession, saveSession, token, user } from './auth.js';
import { loading, message, renderNav } from './components.js';
import { bindPublicPage, accountPage, homePage, loadHomeCategories, loginPage, providerPage, providersPage, registerPage, requestFormPage } from './pages/public.js';
import { errorMessage } from './utils.js';

const app = document.querySelector('#app');
const nav = document.querySelector('#nav-links');
const protectedRoutes = { requests: ['customer', 'provider', 'admin'], account: ['customer'], 'provider-dashboard': ['provider'], admin: ['admin'], request: ['customer'] };
const dashboardRoutes = new Set(['requests', 'provider-dashboard', 'admin']);
let renderVersion = 0;

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
  if (!['home', 'login', 'register', 'account'].includes(route.name)) app.innerHTML = loading();
  try {
    const dashboard = dashboardRoutes.has(route.name) ? await import('./pages/dashboard.js') : null;
    let html;
    if (route.name === 'home') html = homePage();
    else if (route.name === 'login') html = loginPage();
    else if (route.name === 'register') html = registerPage();
    else if (route.name === 'providers') html = await providersPage(route.params);
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
    dashboard?.bindDashboardPage(route);
    app.focus();
    if (route.name === 'home') {
      const categoryGrid = app.querySelector('#category-grid');
      loadHomeCategories(categoryGrid).catch(error => {
        if (version === renderVersion) showError(error);
      });
    }
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
  if (token()) {
    try { saveSession(token(), await api.me()); } catch { clearSession(); }
  }
  if (!location.hash) location.hash = '#home'; else render();
}
start();
