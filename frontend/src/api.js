const API_BASE = import.meta.env.VITE_API_BASE || '';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function getHealth() {
  return request('/health');
}

export async function getPreferenceGuide() {
  return request('/v1/guide/preferences');
}

export async function getRecommendations(profile) {
  return request('/v1/recommend', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
}

export async function exploreCollege(params) {
  return request('/v1/college/explore', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function queryCollege(params) {
  return request('/v1/query', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getCollegeSignals(params) {
  return request('/v1/query/college-signals', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}
