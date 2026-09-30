const TOKEN_KEY = 'nearby_hands_token';
const USER_KEY = 'nearby_hands_user';

export function token() { return localStorage.getItem(TOKEN_KEY); }
export function user() {
  try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; }
}
export function saveToken(accessToken) { localStorage.setItem(TOKEN_KEY, accessToken); }
export function saveSession(accessToken, currentUser) {
  saveToken(accessToken);
  localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
}
export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
