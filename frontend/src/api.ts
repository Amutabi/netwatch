const API = '/api';

function getToken() {
  return localStorage.getItem('token');
}

export function setAuth(token: string, user: object) {
  localStorage.setItem('token', token);
  localStorage.setItem('user', JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}

export function getUser() {
  const u = localStorage.getItem('user');
  return u ? JSON.parse(u) : null;
}

async function request(path: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  }

  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearAuth();
    window.location.href = '/auth';
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Request failed');
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res;
}

export const api = {
  signup: (data: { email: string; username: string; password: string }) =>
    request('/auth/signup', { method: 'POST', body: JSON.stringify(data) }),

  login: async (username: string, password: string) => {
    const form = new FormData();
    form.append('username', username);
    form.append('password', password);
    return request('/auth/login', { method: 'POST', body: form, headers: {} });
  },

  me: () => request('/auth/me'),
  dashboardStats: () => request('/dashboard/stats'),
  devices: () => request('/devices'),
  alerts: () => request('/devices/alerts'),
  poll: () => request('/devices/poll', { method: 'POST' }),
  syncTopology: () => request('/devices/sync-topology', { method: 'POST' }),
  deviceMetrics: (id: number, metric = 'latency_ms') =>
    request(`/devices/metrics/${id}?metric=${metric}`),
  configRequests: (status = 'pending') =>
    request(`/devices/config-requests?status=${status}`),
  approveConfig: (id: number) =>
    request(`/devices/config-requests/${id}/approve`, { method: 'POST' }),
  rejectConfig: (id: number) =>
    request(`/devices/config-requests/${id}/reject`, { method: 'POST' }),
  chat: (message: string, conversationId?: number) =>
    request('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),
  conversations: () => request('/conversations'),
  messages: (convId: number) => request(`/conversations/${convId}/messages`),
  logs: () => request('/logs'),
  reportData: (hours = 24) => request(`/reports/data?hours=${hours}`),
  downloadReport: (format: 'csv' | 'pdf', hours = 24) =>
    `${API}/reports/download/${format}?hours=${hours}`,
};

export function connectAlerts(onAlert: (data: unknown) => void) {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${window.location.host}/ws/alerts`);
  ws.onmessage = (e) => {
    try {
      onAlert(JSON.parse(e.data));
    } catch {}
  };
  return ws;
}
