const SHORTLIST_KEY = 'cc_shortlist';
const PROFILE_KEY = 'cc_profile';
const SHORTLIST_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

export function saveShortlist(profile, results) {
  try {
    const data = { profile, results, savedAt: Date.now() };
    window.localStorage.setItem(SHORTLIST_KEY, JSON.stringify(data));
  } catch { /* ignore */ }
}

export function loadShortlist() {
  try {
    const raw = window.localStorage.getItem(SHORTLIST_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (Date.now() - data.savedAt > SHORTLIST_TTL_MS) {
      window.localStorage.removeItem(SHORTLIST_KEY);
      return null;
    }
    return data;
  } catch { return null; }
}

export function clearShortlist() {
  try { window.localStorage.removeItem(SHORTLIST_KEY); } catch { /* ignore */ }
}

export function saveProfile(profile) {
  try {
    window.localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  } catch { /* ignore */ }
}

export function loadProfile() {
  try {
    const raw = window.localStorage.getItem(PROFILE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

export function encodeShortlistIds(collegeIds) {
  try {
    return btoa(JSON.stringify(collegeIds));
  } catch { return null; }
}

export function decodeShortlistIds(encoded) {
  try {
    return JSON.parse(atob(encoded));
  } catch { return null; }
}
