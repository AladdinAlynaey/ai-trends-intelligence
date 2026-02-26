/**
 * AI Trends Intelligence Platform — API Client
 * Handles all API communication, auth token management, and error handling.
 */
const API = (() => {
  const BASE = '/api';
  let accessToken = localStorage.getItem('access_token') || '';
  let refreshToken = localStorage.getItem('refresh_token') || '';
  let currentUser = JSON.parse(localStorage.getItem('current_user') || 'null');

  // ── Token Management ────────────────────────────
  function setTokens(access, refresh) {
    accessToken = access;
    refreshToken = refresh;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }

  function setUser(user) {
    currentUser = user;
    localStorage.setItem('current_user', JSON.stringify(user));
  }

  function clearAuth() {
    accessToken = '';
    refreshToken = '';
    currentUser = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('current_user');
  }

  function getUser() { return currentUser; }
  function isLoggedIn() { return !!accessToken; }
  function isAdmin() { return currentUser?.role === 'admin'; }

  // ── HTTP Client ─────────────────────────────────
  async function request(method, path, body = null, retry = true) {
    const url = path.startsWith('http') ? path : `${BASE}${path}`;
    const opts = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (accessToken) {
      opts.headers['Authorization'] = `Bearer ${accessToken}`;
    }
    if (body) {
      opts.body = JSON.stringify(body);
    }

    let resp = await fetch(url, opts);

    // Token refresh on 401
    if (resp.status === 401 && retry && refreshToken) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        opts.headers['Authorization'] = `Bearer ${accessToken}`;
        resp = await fetch(url, opts);
      } else {
        clearAuth();
        window.location.href = '/login';
        throw new Error('Session expired');
      }
    }

    const data = await resp.json().catch(() => ({}));

    if (!resp.ok) {
      throw { status: resp.status, message: data.error || 'Request failed', data };
    }

    return data;
  }

  async function refreshAccessToken() {
    try {
      const resp = await fetch(`${BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!resp.ok) return false;
      const data = await resp.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  // ── API Methods ─────────────────────────────────
  const get = (path) => request('GET', path);
  const post = (path, body) => request('POST', path, body);
  const put = (path, body) => request('PUT', path, body);
  const del = (path) => request('DELETE', path);

  // Auth
  async function login(username, password) {
    const data = await post('/auth/login', { username, password });
    setTokens(data.access_token, data.refresh_token);
    setUser(data.user);
    return data;
  }

  async function register(username, email, password) {
    return post('/auth/register', { username, email, password });
  }

  async function logout() {
    try { await post('/auth/logout'); } catch { }
    clearAuth();
    window.location.href = '/login';
  }

  async function getMe() {
    const data = await get('/auth/me');
    setUser(data);
    return data;
  }

  // Trends
  const getTrends = (params = '') => get(`/trends${params ? '?' + params : ''}`);
  const getTrend = (id) => get(`/trends/${id}`);
  const getCategories = () => get('/trends/categories');
  const getTrendStats = () => get('/trends/stats');
  const generateContent = (articleId, platform) =>
    post('/trends/generate-content', { article_id: articleId, platform });
  const generateImage = (articleId) =>
    post('/trends/generate-image', { article_id: articleId });
  const createAIPost = (articleId, platform = 'telegram') =>
    post('/trends/create-post', { article_id: articleId, platform });
  const refreshArticles = () => post('/trends/refresh');

  // Search
  const search = (query) => post('/search', { query });
  const getSearchSuggestions = () => get('/search/suggestions');
  const getSearchHistory = () => get('/search/history');

  // Publishing
  const addToQueue = (data) => post('/publish/queue', data);
  const getQueue = (status = '') => get(`/publish/queue${status ? '?status=' + status : ''}`);
  const processQueue = () => post('/publish/process');
  const getPublishHistory = (page = 1) => get(`/publish/history?page=${page}`);
  const getPlatforms = () => get('/publish/platforms');
  const previewPost = (articleId, platform) =>
    post('/publish/preview', { article_id: articleId, platform });
  const publishToTelegram = (data) => post('/publish/telegram', data);
  const getAIStatus = () => get('/publish/ai-status');
  const createPost = (data) => post('/publish/create-post', data);

  // Admin
  const getUsers = () => get('/admin/users');
  const updateUser = (id, data) => put(`/admin/users/${id}`, data);
  const deleteUser = (id) => del(`/admin/users/${id}`);
  const getFeeds = () => get('/admin/feeds');
  const addFeed = (data) => post('/admin/feeds', data);
  const updateFeed = (id, data) => put(`/admin/feeds/${id}`, data);
  const deleteFeed = (id) => del(`/admin/feeds/${id}`);
  const refreshFeeds = () => post('/admin/feeds/refresh');
  const getSystemStats = () => get('/admin/system/stats');
  const triggerAnalysis = () => post('/admin/system/analyze');
  const getAuditLogs = () => get('/admin/audit-logs');

  return {
    login, register, logout, getMe, getUser, isLoggedIn, isAdmin, clearAuth,
    getTrends, getTrend, getCategories, getTrendStats, generateContent, generateImage,
    createAIPost, refreshArticles,
    search, getSearchSuggestions, getSearchHistory,
    addToQueue, getQueue, processQueue, getPublishHistory, getPlatforms, previewPost,
    publishToTelegram, getAIStatus, createPost,
    getUsers, updateUser, deleteUser,
    getFeeds, addFeed, updateFeed, deleteFeed, refreshFeeds,
    getSystemStats, triggerAnalysis, getAuditLogs,
    get, post, put, del,
  };
})();
