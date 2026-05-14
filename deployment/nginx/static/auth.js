/**
 * auth.js — shared client-side authentication helpers.
 *
 * All state lives in localStorage:
 *   "token"    — the JWT bearer token returned by /auth/login
 *   "username" — the logged-in user's name (for display only)
 *
 * Include this script on any page that needs auth awareness.
 */

/** Return the stored JWT token, or null if not logged in. */
function getToken() {
    return localStorage.getItem("token");
}

/** Return the stored username, or null. */
function getUsername() {
    return localStorage.getItem("username");
}

/**
 * Redirect to /login.html if there is no token in storage.
 * Call this at the top of any page that requires authentication.
 */
function requireLogin() {
    if (!getToken()) {
        window.location.href = "/login.html";
    }
}

/** Clear session data and redirect to the login page. */
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    window.location.href = "/login.html";
}

/**
 * Build a fetch options object with the Authorization header pre-filled.
 * Use this when calling protected API endpoints.
 *
 * Example:
 *   fetch("/api/data", authFetch({ method: "GET" }))
 */
function authFetch(options = {}) {
    const token = getToken();
    const headers = { ...(options.headers || {}) };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    return { ...options, headers };
}
