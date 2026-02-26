/**
 * AI Trends Intelligence Platform — App Controller
 * Handles UI logic, page rendering, toast notifications, and navigation.
 */
const App = (() => {
    // ── Toast Notifications ─────────────────────────
    function showToast(message, type = 'info', duration = 4000) {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icons = { success: 'fa-check-circle', error: 'fa-times-circle', warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };
        toast.innerHTML = `
      <i class="fas ${icons[type] || icons.info}"></i>
      <span>${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
    `;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), duration);
    }

    // ── Auth Guard ──────────────────────────────────
    function requireAuth() {
        if (!API.isLoggedIn()) {
            window.location.href = '/login';
            return false;
        }
        return true;
    }

    // ── Sidebar Setup ───────────────────────────────
    function initSidebar() {
        const user = API.getUser();
        if (!user) return;

        // Set user info
        const nameEl = document.getElementById('sidebar-user-name');
        const roleEl = document.getElementById('sidebar-user-role');
        const avatarEl = document.getElementById('sidebar-user-avatar');
        if (nameEl) nameEl.textContent = user.username;
        if (roleEl) roleEl.textContent = user.role;
        if (avatarEl) avatarEl.textContent = user.username.charAt(0).toUpperCase();

        // Show/hide admin nav
        const adminNav = document.getElementById('admin-nav-section');
        if (adminNav) adminNav.style.display = user.role === 'admin' ? 'block' : 'none';

        // Active nav item
        const path = window.location.pathname;
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.getAttribute('href') === path);
        });

        // Mobile toggle
        const toggle = document.getElementById('menu-toggle');
        const sidebar = document.getElementById('sidebar');
        if (toggle && sidebar) {
            toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
            document.addEventListener('click', (e) => {
                if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            });
        }

        // Logout
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) logoutBtn.addEventListener('click', () => API.logout());
    }

    // ── Format Helpers ──────────────────────────────
    function timeAgo(dateStr) {
        if (!dateStr) return 'Unknown';
        const now = new Date();
        const date = new Date(dateStr);
        const seconds = Math.floor((now - date) / 1000);
        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return date.toLocaleDateString();
    }

    function scoreClass(score) {
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    }

    function truncate(text, len = 150) {
        if (!text) return '';
        return text.length > len ? text.slice(0, len) + '...' : text;
    }

    // ── Loading State ───────────────────────────────
    function setLoading(containerId, loading) {
        const el = document.getElementById(containerId);
        if (!el) return;
        if (loading) {
            el.innerHTML = `<div class="loading-overlay"><div class="spinner"></div></div>`;
        }
    }

    function showEmpty(containerId, icon, title, message) {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = `
      <div class="empty-state">
        <i class="fas ${icon}"></i>
        <h3>${title}</h3>
        <p>${message}</p>
      </div>
    `;
    }

    // ── Dashboard ───────────────────────────────────
    async function loadDashboard() {
        if (!requireAuth()) return;
        initSidebar();

        try {
            const stats = await API.getTrendStats();
            document.getElementById('stat-articles').textContent = stats.total_articles || 0;
            document.getElementById('stat-trends').textContent = stats.total_trends || 0;
            document.getElementById('stat-feeds').textContent = stats.active_feeds || 0;
            document.getElementById('stat-score').textContent = stats.average_score || 0;
            document.getElementById('stat-high').textContent = stats.high_impact_count || 0;

            // Load recent trends
            const trendsData = await API.getTrends('sort=trend_score&order=desc&per_page=10');
            renderTrendList('recent-trends', trendsData.trends || []);

            // Load category chart
            renderCategoryChart(stats.categories || {});
        } catch (err) {
            showToast(err.message || 'Failed to load dashboard', 'error');
        }
    }

    function renderTrendList(containerId, trends) {
        const el = document.getElementById(containerId);
        if (!el) return;

        if (!trends.length) {
            showEmpty(containerId, 'fa-chart-line', 'No Trends Yet', 'Click "Refresh Feeds" to fetch articles, then "Run Analysis" to generate trends.');
            return;
        }

        el.innerHTML = trends.map(t => `
      <div class="trend-item">
        <div class="score-badge ${scoreClass(t.trend_score || 0)}">${t.trend_score || 0}</div>
        <div class="trend-info">
          <div class="trend-title">${escapeHtml(t.article_title || t.title || 'Untitled')}</div>
          <div class="trend-meta">
            <span class="trend-category">${escapeHtml(t.category || 'General')}</span>
            <span class="trend-source"><i class="fas fa-rss"></i> ${escapeHtml(t.article_source || '')}</span>
            <span><i class="fas fa-clock"></i> ${timeAgo(t.published_at)}</span>
          </div>
          <div class="trend-summary">${escapeHtml(truncate(t.impact_summary || t.article_summary || '', 120))}</div>
        </div>
        <div class="trend-actions" style="display: flex; gap: 6px; flex-shrink: 0;">
          <button class="btn btn-sm btn-primary" title="Create Post by AI & Send to Telegram" onclick="event.stopPropagation(); App.createAIPost('${t.article_id || ''}')" style="white-space: nowrap;">
            <i class="fas fa-magic"></i> Create Post
          </button>
          <button class="btn-icon" title="Generate Content" onclick="event.stopPropagation(); App.quickGenerate('${t.article_id || ''}')">
            <i class="fas fa-pen"></i>
          </button>
          ${t.article_link ? `<a class="btn-icon" title="Open Article" href="${escapeHtml(t.article_link)}" target="_blank" onclick="event.stopPropagation();"><i class="fas fa-external-link-alt"></i></a>` : ''}
        </div>
      </div>
    `).join('');
    }

    function renderCategoryChart(categories) {
        const el = document.getElementById('category-chart');
        if (!el || !Object.keys(categories).length) return;

        const max = Math.max(...Object.values(categories));
        const colors = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899', '#14b8a6', '#f97316'];

        el.innerHTML = Object.entries(categories)
            .sort((a, b) => b[1] - a[1])
            .map(([name, count], i) => `
        <div class="flex items-center gap-3" style="margin-bottom: 12px;">
          <div style="width: 80px; font-size: 13px; color: var(--text-secondary); text-align: right;">${escapeHtml(name)}</div>
          <div style="flex: 1; height: 28px; background: var(--bg-glass); border-radius: 6px; overflow: hidden;">
            <div style="height: 100%; width: ${(count / max * 100).toFixed(1)}%; background: ${colors[i % colors.length]}; border-radius: 6px; transition: width 0.6s ease; display: flex; align-items: center; padding-left: 8px; font-size: 12px; font-weight: 600; color: #fff;">${count}</div>
          </div>
        </div>
      `).join('');
    }

    // ── Trends Page ─────────────────────────────────
    async function loadTrends() {
        if (!requireAuth()) return;
        initSidebar();

        try {
            const [trendsData, cats] = await Promise.all([
                API.getTrends('sort=trend_score&order=desc&per_page=20'),
                API.getCategories(),
            ]);

            // Populate category filter
            const catFilter = document.getElementById('filter-category');
            if (catFilter && cats.categories) {
                catFilter.innerHTML = '<option value="">All Categories</option>' +
                    cats.categories.map(c => `<option value="${c.name}">${c.name} (${c.count})</option>`).join('');
            }

            renderTrendList('trends-list', trendsData.trends || []);
            renderPagination('trends-pagination', trendsData);
        } catch (err) {
            showToast(err.message || 'Failed to load trends', 'error');
        }
    }

    async function filterTrends() {
        const category = document.getElementById('filter-category')?.value || '';
        const minScore = document.getElementById('filter-min-score')?.value || '';
        const sort = document.getElementById('filter-sort')?.value || 'trend_score';
        const search = document.getElementById('filter-search')?.value || '';

        let params = `sort=${sort}&order=desc&per_page=20`;
        if (category) params += `&category=${category}`;
        if (minScore) params += `&min_score=${minScore}`;
        if (search) params += `&search=${encodeURIComponent(search)}`;

        try {
            const data = await API.getTrends(params);
            renderTrendList('trends-list', data.trends || []);
            renderPagination('trends-pagination', data);
        } catch (err) {
            showToast(err.message || 'Filter failed', 'error');
        }
    }

    function renderPagination(containerId, data) {
        const el = document.getElementById(containerId);
        if (!el || !data.pages || data.pages <= 1) {
            if (el) el.innerHTML = '';
            return;
        }

        let html = '';
        for (let i = 1; i <= data.pages; i++) {
            html += `<button class="page-btn ${i === data.page ? 'active' : ''}" onclick="App.loadTrendsPage(${i})">${i}</button>`;
        }
        el.innerHTML = html;
    }

    // ── Search Page ─────────────────────────────────
    async function loadSearch() {
        if (!requireAuth()) return;
        initSidebar();

        try {
            const [suggestions, history] = await Promise.all([
                API.getSearchSuggestions().catch(() => ({ suggestions: [] })),
                API.getSearchHistory().catch(() => ({ history: [] })),
            ]);

            const sugEl = document.getElementById('search-suggestions');
            if (sugEl && suggestions.suggestions?.length) {
                sugEl.innerHTML = suggestions.suggestions.map(s =>
                    `<button class="suggestion-chip" onclick="App.performSearch('${escapeHtml(s.text)}')">${escapeHtml(s.text)}</button>`
                ).join('');
            }
        } catch { }
    }

    async function performSearch(query) {
        if (!query) {
            query = document.getElementById('search-query')?.value?.trim();
        }
        if (!query || query.length < 3) {
            showToast('Please enter at least 3 characters', 'warning');
            return;
        }

        const inputEl = document.getElementById('search-query');
        if (inputEl) inputEl.value = query;

        const resultEl = document.getElementById('search-result');
        if (resultEl) {
            resultEl.style.display = 'block';
            resultEl.innerHTML = '<div class="flex items-center justify-between gap-3" style="padding: 40px;"><div class="spinner"></div><span class="text-muted">Thinking...</span></div>';
        }

        try {
            const data = await API.search(query);
            const result = data.result || {};
            renderSearchResult(result, data.cached);
        } catch (err) {
            if (resultEl) {
                resultEl.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><h3>Search Failed</h3><p>${escapeHtml(err.message || 'Unknown error')}</p></div>`;
            }
        }
    }

    function renderSearchResult(result, cached) {
        const el = document.getElementById('search-result');
        if (!el) return;

        const answer = result.answer || 'No results found.';
        const insights = result.key_insights || [];
        const sources = result.sources_used || [];
        const suggested = result.suggested_post || {};

        el.innerHTML = `
      ${cached ? '<div class="tag info" style="margin-bottom: 16px;"><i class="fas fa-bolt"></i> Cached result</div>' : ''}
      <div class="search-answer">${formatMarkdown(answer)}</div>
      ${insights.length ? `
        <div style="margin-top: 24px;">
          <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 12px; color: var(--text-accent);">
            <i class="fas fa-lightbulb" style="margin-right: 8px;"></i>Key Insights
          </h4>
          <div class="search-insights">
            ${insights.map(i => `<div class="insight-card"><p style="font-size: 13px; color: var(--text-secondary);">${escapeHtml(i)}</p></div>`).join('')}
          </div>
        </div>
      ` : ''}
      ${sources.length ? `
        <div style="margin-top: 20px;">
          <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 12px; color: var(--text-accent);">
            <i class="fas fa-link" style="margin-right: 8px;"></i>Sources
          </h4>
          <div class="flex flex-col gap-2">
            ${sources.map(s => `
              <div class="flex items-center gap-2">
                <span class="tag ${s.relevance === 'high' ? 'success' : s.relevance === 'medium' ? 'warning' : ''}">${s.relevance || 'low'}</span>
                <span style="font-size: 13px;">${escapeHtml(s.title || 'Unknown source')}</span>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}
      <div style="margin-top: 16px; font-size: 12px; color: var(--text-muted);">
        Searched ${result.articles_searched || 0} articles • ${result.articles_matched || 0} relevant
        ${result.web_results ? ` • ${result.web_results} web sources` : ''}
        ${result.confidence ? ` • Confidence: ${(result.confidence * 100).toFixed(0)}%` : ''}
      </div>

      <!-- CREATE POST FROM SEARCH -->
      <div style="margin-top: 24px; padding: 20px; background: var(--bg-glass); border-radius: 12px; border: 1px solid rgba(139, 92, 246, 0.3);">
        <h4 style="font-size: 15px; font-weight: 700; margin-bottom: 12px; color: var(--accent-primary);">
          <i class="fas fa-magic" style="margin-right: 8px;"></i>Turn This Into a Post
        </h4>
        ${suggested.title ? `
          <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">
            <strong>Suggested:</strong> ${escapeHtml(suggested.title)}
          </div>
        ` : ''}
        <button class="btn btn-primary btn-lg w-full" onclick="App.openPostEditor(${JSON.stringify(suggested).replace(/"/g, '&quot;')})">
          <i class="fas fa-pen-fancy"></i> Create & Edit Post
        </button>
      </div>
    `;
    }

    // ── Admin Page ──────────────────────────────────
    async function loadAdmin() {
        if (!requireAuth()) return;
        initSidebar();
        if (!API.isAdmin()) {
            showToast('Admin access required', 'error');
            return;
        }

        try {
            const [stats, users, feeds] = await Promise.all([
                API.getSystemStats(),
                API.getUsers(),
                API.getFeeds(),
            ]);

            // System stats
            document.getElementById('admin-stat-articles').textContent = stats.articles?.total || 0;
            document.getElementById('admin-stat-analyzed').textContent = stats.articles?.analyzed || 0;
            document.getElementById('admin-stat-feeds').textContent = stats.feeds?.total || 0;
            document.getElementById('admin-stat-users').textContent = stats.users?.total || 0;
            document.getElementById('admin-stat-published').textContent = stats.publishing?.total_published || 0;
            document.getElementById('admin-stat-queue').textContent = stats.publishing?.queue_pending || 0;

            // Users table
            renderUsersTable(users.users || []);

            // Feeds table
            renderFeedsTable(feeds.feeds || []);
        } catch (err) {
            showToast(err.message || 'Failed to load admin page', 'error');
        }
    }

    function renderUsersTable(users) {
        const el = document.getElementById('users-tbody');
        if (!el) return;
        el.innerHTML = users.map(u => `
      <tr>
        <td><strong>${escapeHtml(u.username)}</strong></td>
        <td>${escapeHtml(u.email)}</td>
        <td><span class="tag ${u.role === 'admin' ? '' : 'info'}">${u.role}</span></td>
        <td><span class="tag ${u.active ? 'success' : 'danger'}">${u.active ? 'Active' : 'Inactive'}</span></td>
        <td>${timeAgo(u.created_at)}</td>
        <td>
          <div class="flex gap-2">
            <button class="btn-icon" title="Toggle Role" onclick="App.toggleUserRole('${u.id}', '${u.role}')">
              <i class="fas fa-user-shield"></i>
            </button>
            <button class="btn-icon" title="Toggle Active" onclick="App.toggleUserActive('${u.id}', ${u.active})">
              <i class="fas fa-${u.active ? 'ban' : 'check'}"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
    }

    function renderFeedsTable(feeds) {
        const el = document.getElementById('feeds-tbody');
        if (!el) return;
        el.innerHTML = feeds.map(f => `
      <tr>
        <td><strong>${escapeHtml(f.name)}</strong></td>
        <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(f.url)}">${escapeHtml(f.url)}</td>
        <td><span class="trend-category">${escapeHtml(f.category || 'General')}</span></td>
        <td><span class="tag ${f.enabled ? 'success' : 'danger'}">${f.enabled ? 'Active' : 'Disabled'}</span></td>
        <td>${f.article_count || 0}</td>
        <td>${timeAgo(f.last_fetched)}</td>
        <td>
          <div class="flex gap-2">
            <button class="btn-icon" title="Toggle" onclick="App.toggleFeed('${f.id}', ${f.enabled})">
              <i class="fas fa-${f.enabled ? 'pause' : 'play'}"></i>
            </button>
            <button class="btn-icon" title="Delete" onclick="App.deleteFeedItem('${f.id}')">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
    }

    // ── Admin Actions ───────────────────────────────
    async function toggleUserRole(userId, currentRole) {
        try {
            const newRole = currentRole === 'admin' ? 'user' : 'admin';
            await API.updateUser(userId, { role: newRole });
            showToast(`User role changed to ${newRole}`, 'success');
            loadAdmin();
        } catch (err) {
            showToast(err.message || 'Failed to update role', 'error');
        }
    }

    async function toggleUserActive(userId, currentActive) {
        try {
            await API.updateUser(userId, { active: !currentActive });
            showToast(`User ${currentActive ? 'deactivated' : 'activated'}`, 'success');
            loadAdmin();
        } catch (err) {
            showToast(err.message || 'Failed to update user', 'error');
        }
    }

    async function toggleFeed(feedId, currentEnabled) {
        try {
            await API.updateFeed(feedId, { enabled: !currentEnabled });
            showToast(`Feed ${currentEnabled ? 'disabled' : 'enabled'}`, 'success');
            loadAdmin();
        } catch (err) {
            showToast(err.message || 'Failed to update feed', 'error');
        }
    }

    async function deleteFeedItem(feedId) {
        if (!confirm('Delete this feed?')) return;
        try {
            await API.deleteFeed(feedId);
            showToast('Feed deleted', 'success');
            loadAdmin();
        } catch (err) {
            showToast(err.message || 'Failed to delete feed', 'error');
        }
    }

    async function addNewFeed() {
        const name = document.getElementById('new-feed-name')?.value?.trim();
        const url = document.getElementById('new-feed-url')?.value?.trim();
        const category = document.getElementById('new-feed-category')?.value?.trim() || 'General';

        if (!name || !url) {
            showToast('Name and URL required', 'warning');
            return;
        }

        try {
            await API.addFeed({ name, url, category });
            showToast('Feed added successfully', 'success');
            document.getElementById('new-feed-name').value = '';
            document.getElementById('new-feed-url').value = '';
            loadAdmin();
        } catch (err) {
            showToast(err.message || 'Failed to add feed', 'error');
        }
    }

    async function refreshAllFeeds() {
        showToast('Refreshing feeds...', 'info');
        try {
            const result = await API.refreshFeeds();
            showToast(`Fetched ${result.total_new} new articles from ${result.feeds_processed} feeds`, 'success');
            loadAdmin();
        } catch (err) {
            showToast(err.message || 'Failed to refresh feeds', 'error');
        }
    }

    async function triggerAnalysis() {
        showToast('Running AI analysis...', 'info');
        try {
            const result = await API.triggerAnalysis();
            showToast(result.message, 'success');
            loadAdmin();
        } catch (err) {
            showToast(err.message || 'Analysis failed', 'error');
        }
    }

    // ── Publish Page ────────────────────────────────
    async function loadPublish() {
        if (!requireAuth()) return;
        initSidebar();

        try {
            const [queueData, platforms, history, aiStatus] = await Promise.all([
                API.getQueue(),
                API.getPlatforms(),
                API.getPublishHistory(),
                API.getAIStatus().catch(() => ({})),
            ]);

            // Platform status
            const platEl = document.getElementById('platform-status');
            if (platEl && platforms.platforms) {
                platEl.innerHTML = Object.entries(platforms.platforms).map(([name, info]) => `
          <div class="stat-card">
            <div class="stat-card-icon ${info.enabled ? 'green' : 'red'}">
              <i class="fab fa-${name === 'twitter' ? 'x-twitter' : name}"></i>
            </div>
            <div class="stat-label">${name.charAt(0).toUpperCase() + name.slice(1)}</div>
            <div class="mt-2">
              <span class="tag ${info.enabled ? 'success' : 'danger'}">${info.enabled ? 'Enabled' : 'Disabled'}</span>
              <span class="tag ${info.configured ? 'info' : 'warning'}" style="margin-left: 4px;">${info.configured ? 'Configured' : 'Not Set'}</span>
            </div>
          </div>
        `).join('');
            }

            // Queue stats
            const stats = queueData.stats || {};
            const qp = document.getElementById('queue-pending');
            const qs = document.getElementById('queue-scheduled');
            const qpub = document.getElementById('queue-published');
            if (qp) qp.textContent = stats.pending || 0;
            if (qs) qs.textContent = stats.scheduled || 0;
            if (qpub) qpub.textContent = stats.published || 0;

            // Telegram status indicator
            const tgStatus = document.getElementById('telegram-status');
            if (tgStatus) {
                if (aiStatus.telegram_enabled) {
                    tgStatus.innerHTML = '<span class="tag success"><i class="fas fa-check"></i> Telegram Connected</span>';
                } else {
                    tgStatus.innerHTML = '<span class="tag warning"><i class="fas fa-exclamation-triangle"></i> Telegram Disabled — set TELEGRAM_ENABLED=true in .env</span>';
                }
            }

            // AI status indicator
            const aiEl = document.getElementById('ai-status');
            if (aiEl) {
                if (aiStatus.ai_configured) {
                    aiEl.innerHTML = '<span class="tag success"><i class="fas fa-check"></i> OpenRouter AI Active</span>';
                } else {
                    aiEl.innerHTML = '<span class="tag warning"><i class="fas fa-exclamation-triangle"></i> OpenRouter not configured — add OPENROUTER_API_KEY to .env</span>';
                }
            }

        } catch (err) {
            showToast(err.message || 'Failed to load publishing page', 'error');
        }
    }

    // ── Telegram Publishing ─────────────────────────
    async function sendToTelegram() {
        const title = document.getElementById('tg-title')?.value?.trim();
        const body = document.getElementById('tg-body')?.value?.trim();
        const hashtags = document.getElementById('tg-hashtags')?.value?.trim();
        const cta = document.getElementById('tg-cta')?.value?.trim();
        const genImage = document.getElementById('tg-gen-image')?.checked || false;

        if (!title) {
            showToast('Title is required', 'warning');
            return;
        }

        const btn = document.getElementById('tg-send-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px;"></div> Sending...';
        }

        try {
            const result = await API.publishToTelegram({
                title,
                body,
                hashtags,
                cta,
                generate_image: genImage,
            });

            if (result.success) {
                showToast('🎉 Post sent to Telegram!', 'success');
                // Clear form
                if (document.getElementById('tg-title')) document.getElementById('tg-title').value = '';
                if (document.getElementById('tg-body')) document.getElementById('tg-body').value = '';
                if (document.getElementById('tg-hashtags')) document.getElementById('tg-hashtags').value = '';
                if (document.getElementById('tg-cta')) document.getElementById('tg-cta').value = '';
            } else {
                showToast(result.error || 'Failed to send to Telegram', 'error');
            }
        } catch (err) {
            showToast(err.message || 'Telegram publish failed', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fab fa-telegram"></i> Send to Telegram';
            }
        }
    }

    // ── Content Generation ──────────────────────────
    async function quickGenerate(articleId) {
        showToast('Generating content...', 'info');
        try {
            const result = await API.generateContent(articleId, 'general');
            showContentModal(result);
        } catch (err) {
            showToast(err.message || 'Generation failed', 'error');
        }
    }

    // ── Create AI Post → Opens Editor with Language Selection FIRST ────
    async function createAIPost(articleId) {
        // Open editor with article context — user picks language FIRST, then generates
        openPostEditor({ articleId });
    }

    // ── Refresh Articles (any user) ─────────────────
    async function refreshArticles() {
        showToast('🔄 Fetching 50+ RSS feeds concurrently...', 'info', 60000);
        try {
            const result = await API.refreshArticles();
            showToast(`✅ Fetched ${result.total_new} new articles from ${result.feeds_ok || result.feeds_processed} feeds`, 'success', 5000);
            // Reload current page data
            if (window.location.pathname === '/trends') loadTrends();
            if (window.location.pathname === '/dashboard') loadDashboard();
        } catch (err) {
            showToast(err.message || 'Feed refresh failed', 'error');
        }
    }

    // ── Run Analysis (any user) ─────────────────────
    async function runAnalysis() {
        showToast('🧠 Running AI analysis...', 'info', 15000);
        try {
            const result = await API.triggerAnalysis();
            showToast(`✅ ${result.message}`, 'success', 5000);
            if (window.location.pathname === '/trends') loadTrends();
            if (window.location.pathname === '/dashboard') loadDashboard();
        } catch (err) {
            showToast(err.message || 'Analysis failed', 'error');
        }
    }

    function showContentModal(data) {
        const modal = document.getElementById('content-modal');
        if (!modal) return;

        const content = data.content || {};
        const hashtags = data.hashtags || {};
        const allTags = [...(hashtags.universal || []), ...(hashtags.niche || [])].slice(0, 8);

        document.getElementById('modal-content-title').textContent = content.title || '';
        document.getElementById('modal-content-hook').textContent = content.hook || '';
        document.getElementById('modal-content-body').textContent = content.body || '';
        document.getElementById('modal-content-cta').textContent = content.cta || '';
        document.getElementById('modal-content-hashtags').textContent = allTags.join(' ');

        modal.classList.add('active');
    }

    function closeModal(id) {
        document.getElementById(id)?.classList.remove('active');
    }

    function openTrend(trendId) {
        if (trendId) window.location.href = `/trends?detail=${trendId}`;
    }

    // ── Post Editor ────────────────────────────────
    // Store the current article context for generation
    let _editorArticleCtx = null;

    function openPostEditor(suggested) {
        suggested = suggested || {};
        const modal = document.getElementById('post-editor-modal');
        if (!modal) {
            showToast('Post editor not available on this page.', 'warning');
            return;
        }

        // Store article context for AI generation
        _editorArticleCtx = {
            articleId: suggested.articleId || '',
            title: suggested.title || '',
            body: suggested.body || '',
            link: suggested.link || '',
        };

        // Pre-fill fields
        const titleEl = document.getElementById('editor-title');
        const bodyEl = document.getElementById('editor-body');
        const ctaEl = document.getElementById('editor-cta');
        const hashEl = document.getElementById('editor-hashtags');
        const linkEl = document.getElementById('editor-link');

        if (titleEl) titleEl.value = suggested.title || '';
        if (bodyEl) bodyEl.value = suggested.body || '';
        if (ctaEl) ctaEl.value = suggested.cta || '💡 Follow for more AI updates!';
        if (hashEl) hashEl.value = suggested.hashtags || '#AI #ArtificialIntelligence #Tech';
        if (linkEl) linkEl.value = suggested.link || '';

        // Reset result
        const resEl = document.getElementById('editor-result');
        if (resEl) resEl.innerHTML = '';

        // Show modal
        modal.classList.add('active');
    }

    // ── Generate AI Content in Selected Language ────
    async function generateInEditor() {
        const language = document.getElementById('editor-language')?.value || 'en';
        const articleId = _editorArticleCtx?.articleId || '';
        const genBtn = document.getElementById('editor-generate-btn');

        if (genBtn) {
            genBtn.disabled = true;
            genBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        }

        try {
            const result = await API.createAIPost(articleId, 'general', language);
            const content = result.content || {};
            const hashtags = result.hashtags || {};
            const allTags = [...(hashtags.universal || []), ...(hashtags.niche || [])].slice(0, 8);

            const titleEl = document.getElementById('editor-title');
            const bodyEl = document.getElementById('editor-body');
            const ctaEl = document.getElementById('editor-cta');
            const hashEl = document.getElementById('editor-hashtags');
            const linkEl = document.getElementById('editor-link');

            if (titleEl) titleEl.value = content.title || _editorArticleCtx?.title || '';
            if (bodyEl) bodyEl.value = (content.hook ? content.hook + '\n\n' : '') + (content.body || '');
            if (ctaEl) ctaEl.value = content.cta || '💡 Follow for more AI updates!';
            if (hashEl) hashEl.value = allTags.join(' ') || '#AI #Tech';
            // Auto-fill source link
            if (linkEl && _editorArticleCtx?.link) linkEl.value = _editorArticleCtx.link;

            showToast('✅ AI content generated — review and edit before publishing!', 'success', 5000);
        } catch (err) {
            showToast(err.message || 'Generation failed', 'error');
        } finally {
            if (genBtn) {
                genBtn.disabled = false;
                genBtn.innerHTML = '<i class="fas fa-magic"></i> Generate AI Content';
            }
        }
    }

    async function publishFromEditor() {
        const title = document.getElementById('editor-title')?.value?.trim();
        const body = document.getElementById('editor-body')?.value?.trim();
        const cta = document.getElementById('editor-cta')?.value?.trim();
        const hashtags = document.getElementById('editor-hashtags')?.value?.trim();
        const link = document.getElementById('editor-link')?.value?.trim();
        const genImage = document.getElementById('editor-gen-image')?.checked;
        const imageModel = document.getElementById('editor-image-model')?.value || 'auto';
        const imageStyle = document.getElementById('editor-image-style')?.value || 'auto';
        const imageSize = document.getElementById('editor-image-size')?.value || 'auto';
        const language = document.getElementById('editor-language')?.value || 'en';

        // Read platform checkboxes
        const platforms = [];
        if (document.getElementById('editor-plat-telegram')?.checked) platforms.push('telegram');
        if (document.getElementById('editor-plat-twitter')?.checked) platforms.push('twitter');
        if (document.getElementById('editor-plat-linkedin')?.checked) platforms.push('linkedin');

        if (!title && !body) {
            showToast('Please enter a title or body', 'warning');
            return;
        }
        if (platforms.length === 0) {
            showToast('Select at least one platform to publish to', 'warning');
            return;
        }

        const btn = document.getElementById('editor-publish-btn');
        const resEl = document.getElementById('editor-result');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Publishing...';
        }

        try {
            const result = await API.createPost({
                title, body, cta, hashtags, link,
                generate_image: genImage,
                image_model: imageModel,
                image_style: imageStyle,
                image_size: imageSize,
                language: language,
                platforms: platforms,
            });

            if (result.success) {
                const platNames = platforms.map(p =>
                    p === 'telegram' ? 'Telegram' : p === 'twitter' ? '𝕏' : 'LinkedIn'
                ).join(', ');
                showToast(`🎉 Post published to ${platNames}!`, 'success', 6000);
                if (resEl) {
                    let html = '<div class="tag success" style="margin-top: 8px;"><i class="fas fa-check"></i> Published successfully!</div>';
                    // Show per-platform results
                    if (result.results) {
                        html += '<div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px;">';
                        for (const [plat, res] of Object.entries(result.results)) {
                            const icon = plat === 'telegram' ? '📱' : plat === 'twitter' ? '𝕏' : '💼';
                            html += `<span class="tag ${res.success ? 'success' : 'danger'}">${icon} ${plat}: ${res.success ? '✅' : res.error || '❌'}</span>`;
                        }
                        html += '</div>';
                    }
                    resEl.innerHTML = html;
                }
                if (result.image_url) {
                    if (resEl) resEl.innerHTML += `<div style="margin-top: 8px;"><img src="${result.image_url}" style="max-width: 100%; border-radius: 12px;"></div>`;
                }
            } else {
                const errMsg = result.error || 'Check platform configuration';
                showToast('⚠ ' + errMsg, 'warning', 5000);
                if (resEl) resEl.innerHTML = `<div class="tag warning" style="margin-top: 8px;"><i class="fas fa-exclamation-triangle"></i> ${errMsg}</div>`;
            }
        } catch (err) {
            showToast(err.message || 'Publishing failed', 'error');
            if (resEl) resEl.innerHTML = `<div class="tag" style="background: var(--accent-danger); margin-top: 8px;"><i class="fas fa-times"></i> Error: ${err.message}</div>`;
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-paper-plane"></i> Publish Post';
            }
        }
    }

    // ── Utility ─────────────────────────────────────
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    function formatMarkdown(text) {
        if (!text) return '';
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/^- (.*$)/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
    }

    return {
        showToast, requireAuth, initSidebar,
        loadDashboard, loadTrends, filterTrends, loadSearch, performSearch,
        loadAdmin, loadPublish, sendToTelegram,
        createAIPost, refreshArticles, runAnalysis,
        openPostEditor, publishFromEditor, generateInEditor,
        toggleUserRole, toggleUserActive, toggleFeed, deleteFeedItem,
        addNewFeed, refreshAllFeeds, triggerAnalysis,
        quickGenerate, showContentModal, closeModal, openTrend,
        timeAgo, scoreClass, escapeHtml,
    };
})();

// Global escape function
function escapeHtml(text) { return App.escapeHtml(text); }

