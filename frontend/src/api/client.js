// Use same origin in production. Override with VITE_API_URL if needed.
const API_BASE = import.meta.env.VITE_API_URL || '';

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
  } catch {
    throw new Error(
      'Cannot reach the backend. Open http://localhost:8000 (not port 5173). ' +
        'If the app is not running, double-click "Start ParcelPilot.bat".'
    );
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail;
    const msg = typeof detail === 'string' ? detail : JSON.stringify(detail);
    throw new Error(msg || `Request failed (${res.status})`);
  }
  return data;
}

export const api = {
  health: () => request('/api/health'),
  accounts: () => request('/api/accounts'),
  validateSession: (session) =>
    request('/api/session/validate', { method: 'POST', body: JSON.stringify(session) }),
  chat: (messages, session) =>
    request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        messages,
        session: { role: session.role, account_id: session.account_id ?? null },
      }),
    }),
  confirmEscalation: (payload) =>
    request('/api/escalations/confirm', {
      method: 'POST',
      body: JSON.stringify({
        ...payload,
        session: {
          role: payload.session.role,
          account_id: payload.session.account_id ?? null,
        },
      }),
    }),
  issues: (session) =>
    request(
      `/api/issues?role=${encodeURIComponent(session.role)}&account_id=${encodeURIComponent(session.account_id || '')}`
    ),
  sources: (session) =>
    request(
      `/api/sources?role=${encodeURIComponent(session.role)}&account_id=${encodeURIComponent(session.account_id || '')}`
    ),
};
