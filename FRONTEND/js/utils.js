export function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[char]);
}

export function errorMessage(error) { return error?.message || 'Something went wrong. Please try again.'; }

export function statusBadge(status) {
  return `<span class="badge badge-${escapeHtml(status)}">${escapeHtml(status)}</span>`;
}

export function dateLabel(date) {
  if (!date) return 'Not specified';
  return new Date(`${date}T00:00:00`).toLocaleDateString(undefined, { dateStyle: 'medium' });
}

export function formDataObject(form) { return Object.fromEntries(new FormData(form).entries()); }

export function setSubmitting(form, submitting) {
  const button = form.querySelector('[type="submit"]');
  if (button) { button.disabled = submitting; button.dataset.label ||= button.textContent; button.textContent = submitting ? 'Saving…' : button.dataset.label; }
}

export function showToast(message, type = 'success') {
  const toast = document.querySelector('#toast');
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => { toast.className = 'toast'; }, 3500);
}

export function today() { return new Date().toISOString().slice(0, 10); }
