"""Embedded JavaScript for the mobile UI."""

INDEX_SCRIPT = r"""
    const tokenInput = document.getElementById('token');
    const statusEl = document.getElementById('status');
    const profileSelect = document.getElementById('profileSelect');
    const targetListEl = document.getElementById('targetList');
    const profileNameInput = document.getElementById('profileName');
    const profileGroupInput = document.getElementById('profileGroup');
    const profileTagsInput = document.getElementById('profileTags');
    const hostInput = document.getElementById('host');
    const portInput = document.getElementById('port');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const passwordRefInput = document.getElementById('passwordRef');
    const keyFilenameInput = document.getElementById('keyFilename');
    const tmuxBinInput = document.getElementById('tmuxBin');
    const profileDescriptionInput = document.getElementById('profileDescription');
    const hostKeyPolicySelect = document.getElementById('hostKeyPolicy');
    const sshTimeoutInput = document.getElementById('sshTimeout');
    const sshCommandTimeoutInput = document.getElementById('sshCommandTimeout');
    const sshRetriesInput = document.getElementById('sshRetries');
    const sshRetryBackoffMsInput = document.getElementById('sshRetryBackoffMs');
    const profileFavoriteInput = document.getElementById('profileFavorite');
    const sessionSelect = document.getElementById('session');
    const windowSelect = document.getElementById('window');
    const paneSelect = document.getElementById('pane');
    const aliasInput = document.getElementById('agentAlias');
    const templateSelect = document.getElementById('templateSelect');
    const templateNameInput = document.getElementById('templateName');
    const templateScopeSelect = document.getElementById('templateScope');
    const paneLinesInput = document.getElementById('paneLines');
    const targetPageSizeInput = document.getElementById('targetPageSize');
    const historyPageSizeInput = document.getElementById('historyPageSize');
    const todoPageSizeInput = document.getElementById('todoPageSize');
    const historyListEl = document.getElementById('historyList');
    const todoBoardEl = document.getElementById('todoBoard');
    const chatFeedEl = document.getElementById('chatFeed');
    const chatSessionSelect = document.getElementById('chatSessionSelect');
    const chatConversationHintEl = document.getElementById('chatConversationHint');
    const conversationListEl = document.getElementById('conversationList');
    const workerListEl = document.getElementById('workerList');
    const targetPaginationEl = document.getElementById('targetPagination');
    const historyPaginationEl = document.getElementById('historyPagination');
    const todoPaginationEl = document.getElementById('todoPagination');
    const viewButtons = Array.from(document.querySelectorAll('[data-view-button]'));
    const dashboardViewEl = document.getElementById('view-dashboard');
    const authViewEl = document.getElementById('view-auth');
    const chatViewEl = document.getElementById('view-chat');
    const todoViewEl = document.getElementById('view-todo');
    const deliveryViewEl = document.getElementById('view-delivery');
    const historySelect = document.getElementById('historySelect');
    const commandInput = document.getElementById('command');
    const paneOutputEl = document.getElementById('paneOutput');
    const selectedPaneLabel = document.getElementById('selectedPaneLabel');
    const currentAgentLabelEl = document.getElementById('currentAgentLabel');
    const currentAgentHintEl = document.getElementById('currentAgentHint');
    const deliveryAgentLabelEl = document.getElementById('deliveryAgentLabel');
    const deliveryAgentHintEl = document.getElementById('deliveryAgentHint');
    const deliveryTodoMetaEl = document.getElementById('deliveryTodoMeta');
    const deliveryTimelineEl = document.getElementById('deliveryTimeline');
    const deliveryResultEl = document.getElementById('deliveryResult');
    const deliveryEvidenceEl = document.getElementById('deliveryEvidence');
    const deliveryAuditEl = document.getElementById('deliveryAudit');
    const deliveryPaneOutputEl = document.getElementById('deliveryPaneOutput');
    const todoTitleInput = document.getElementById('todoTitle');
    const todoDetailInput = document.getElementById('todoDetail');
    const todoPrioritySelect = document.getElementById('todoPriority');
    const todoAssigneeInput = document.getElementById('todoAssignee');
    const createTodoButton = document.getElementById('createTodo');
    const quickTodoButton = document.getElementById('quickTodo');
    const todoSelect = document.getElementById('todoSelect');
    const todoStatusSelect = document.getElementById('todoStatus');
    const todoProgressNoteInput = document.getElementById('todoProgressNote');
    const todoEvidenceInput = document.getElementById('todoEvidence');
    const todoTemplateSelect = document.getElementById('todoTemplateSelect');
    const todoTemplateNameInput = document.getElementById('todoTemplateName');
    const todoTimelineEl = null; // replaced by Gantt chart in #todoGantt
    const todoEvidenceListEl = document.getElementById('todoEvidenceList');
    const auditSelect = document.getElementById('auditSelect');
    const todoMetaEl = document.getElementById('todoMeta');
    const profileCountEl = document.getElementById('profileCount');
    const supervisorConfigIdInput = document.getElementById('supervisorConfigId');
    const supervisorNameInput = document.getElementById('supervisorName');
    const supervisorModelInput = document.getElementById('supervisorModel');
    const supervisorBaseUrlInput = document.getElementById('supervisorBaseUrl');
    const supervisorApiKeyInput = document.getElementById('supervisorApiKey');
    const supervisorApiKeyRefInput = document.getElementById('supervisorApiKeyRef');
    const supervisorLoadStateEl = document.getElementById('supervisorLoadState');
    const supervisorEnabledInput = document.getElementById('supervisorEnabled');
    const supervisorCanDispatchInput = document.getElementById('supervisorCanDispatch');
    const supervisorCanReviewInput = document.getElementById('supervisorCanReview');
    const supervisorCanAcceptInput = document.getElementById('supervisorCanAccept');
    const supervisorAutoDispatchInput = document.getElementById('supervisorAutoDispatch');
    const supervisorAutoReviewInput = document.getElementById('supervisorAutoReview');
    const supervisorAutoAcceptInput = document.getElementById('supervisorAutoAccept');
    const supervisorSystemPromptInput = document.getElementById('supervisorSystemPrompt');
    const onlineCountEl = document.getElementById('onlineCount');
    const sessionCountEl = document.getElementById('sessionCount');
    const paneCountEl = document.getElementById('paneCount');

    function safeStorageGet(key, fallback = '') {
      try {
        const value = window.localStorage.getItem(key);
        return value === null ? fallback : value;
      } catch (_) {
        return fallback;
      }
    }

    function safeStorageSet(key, value) {
      try {
        window.localStorage.setItem(key, String(value));
        return true;
      } catch (_) {
        return false;
      }
    }

    function safeStorageRemove(key) {
      try {
        window.localStorage.removeItem(key);
        return true;
      } catch (_) {
        return false;
      }
    }

    const storedToken = safeStorageGet('clawdone-token', '') || '';
    tokenInput.value = storedToken;

    const MIN_PANE_LINES = 20;
    const MAX_PANE_LINES = 200;
    const MAX_COMMAND_STREAM_LINES = 40;
    const UI_STATE_ENDPOINT = '/api/ui-state';
    const PROFILE_SELECTION_STORAGE_KEY = 'clawdone-selected-profile';
    const PROFILE_DRAFT_STORAGE_KEY = 'clawdone-profile-draft';

    const DEFAULT_UI_SETTINGS = {
      paneLines: 80,
      targetPageSize: 6,
      historyPageSize: 8,
      todoPageSize: 6,
    };

    function normalizeUiSettingsPayload(raw) {
      const source = raw && typeof raw === 'object' ? raw : {};
      return {
        paneLines: Math.max(MIN_PANE_LINES, positiveInt(source.paneLines, DEFAULT_UI_SETTINGS.paneLines, MAX_PANE_LINES)),
        targetPageSize: positiveInt(source.targetPageSize, DEFAULT_UI_SETTINGS.targetPageSize, 24),
        historyPageSize: positiveInt(source.historyPageSize, DEFAULT_UI_SETTINGS.historyPageSize, 30),
        todoPageSize: positiveInt(source.todoPageSize, DEFAULT_UI_SETTINGS.todoPageSize, 20),
      };
    }

    function loadUiSettings() {
      try {
        return normalizeUiSettingsPayload(JSON.parse(safeStorageGet('clawdone-ui-settings', '{}') || '{}') || {});
      } catch (_) {
        return { ...DEFAULT_UI_SETTINGS };
      }
    }

    function supervisorPermissions() {
      const permissions = [];
      if (supervisorCanDispatchInput.checked) permissions.push('dispatch');
      if (supervisorCanReviewInput.checked) permissions.push('review');
      if (supervisorCanAcceptInput.checked) permissions.push('accept');
      return permissions;
    }

    function setSupervisorLoadState(message, type = 'info') {
      if (!supervisorLoadStateEl) return;
      supervisorLoadStateEl.textContent = message;
      supervisorLoadStateEl.classList.remove('error', 'warn');
      if (type === 'error') supervisorLoadStateEl.classList.add('error');
      if (type === 'warn') supervisorLoadStateEl.classList.add('warn');
    }

    function summarizeSupervisorConfig(config) {
      if (!config) return 'No config loaded.';
      const enabled = config.enabled ? 'enabled' : 'disabled';
      const model = config.model || 'unknown model';
      const keyState = config.has_api_key || config.api_key_ref ? 'API key ready' : 'no API key';
      const autoFlags = [
        config.auto_dispatch ? 'auto-dispatch' : null,
        config.auto_review ? 'auto-review' : null,
        config.auto_accept ? 'auto-accept' : null,
      ].filter(Boolean).join(' / ') || 'manual only';
      return `${model} · ${enabled} · ${keyState} · ${autoFlags}`;
    }

    function fillSupervisorConfig(config, options = {}) {
      const force = Boolean(options && options.force);
      const sourceProfile = String((config && config.profile) || currentProfileName() || '').trim();
      if (!force && supervisorFormDirty && sourceProfile && sourceProfile === supervisorFormSourceProfile) {
        return;
      }
      supervisorConfigCache = config || null;
      setSupervisorLoadState(summarizeSupervisorConfig(config), config ? 'info' : 'warn');
      supervisorConfigIdInput.value = config ? (config.id || '') : '';
      supervisorNameInput.value = config ? (config.name || '') : 'ClawDone';
      supervisorModelInput.value = config ? (config.model || 'gpt-4.1-mini') : 'gpt-4.1-mini';
      supervisorBaseUrlInput.value = config ? (config.base_url || 'https://api.openai.com/v1') : 'https://api.openai.com/v1';
      supervisorApiKeyInput.value = '';
      supervisorApiKeyRefInput.value = config ? (config.api_key_ref || '') : '';
      supervisorEnabledInput.checked = config ? Boolean(config.enabled) : true;
      const permissions = new Set((config && config.permissions) || ['dispatch', 'review', 'accept']);
      supervisorCanDispatchInput.checked = permissions.has('dispatch');
      supervisorCanReviewInput.checked = permissions.has('review');
      supervisorCanAcceptInput.checked = permissions.has('accept');
      supervisorAutoDispatchInput.checked = config ? Boolean(config.auto_dispatch ?? true) : true;
      supervisorAutoReviewInput.checked = config ? Boolean(config.auto_review ?? true) : true;
      supervisorAutoAcceptInput.checked = config ? Boolean(config.auto_accept ?? true) : true;
      supervisorSystemPromptInput.value = config ? (config.system_prompt || '') : '';
      supervisorFormSourceProfile = sourceProfile;
      supervisorFormDirty = false;
    }

    async function loadSupervisorConfig() {
      const profile = currentProfileName();
      if (!profile) {
        fillSupervisorConfig(null, { force: true });
        setSupervisorLoadState('Choose a target first to load ClawDone config.', 'warn');
        return;
      }
      try {
        const data = await api(`/api/supervisor/config?profile=${encodeURIComponent(profile)}`);
        const config = data.config || null;
        fillSupervisorConfig(config);
        if (config) {
          setSupervisorLoadState(`${profile} · ${summarizeSupervisorConfig(config)}`);
        } else {
          setSupervisorLoadState(`${profile} · no config`, 'warn');
        }
      } catch (_) {
        fillSupervisorConfig(null);
        setSupervisorLoadState(`${profile} · no config`, 'warn');
      }
    }

    async function saveSupervisorConfig() {
      const profile = currentProfileName();
      if (!profile) {
        setStatus('Choose a profile first.', 'error');
        return;
      }
      try {
        const data = await api('/api/supervisor/config/save', {
          method: 'POST',
          body: JSON.stringify({
            id: supervisorConfigIdInput.value.trim(),
            name: supervisorNameInput.value.trim() || 'ClawDone',
            profile,
            base_url: supervisorBaseUrlInput.value.trim(),
            model: supervisorModelInput.value.trim(),
            api_key: supervisorApiKeyInput.value,
            api_key_ref: supervisorApiKeyRefInput.value.trim(),
            enabled: supervisorEnabledInput.checked,
            permissions: supervisorPermissions(),
            auto_dispatch: supervisorAutoDispatchInput.checked,
            auto_review: supervisorAutoReviewInput.checked,
            auto_accept: supervisorAutoAcceptInput.checked,
            system_prompt: supervisorSystemPromptInput.value.trim(),
          }),
        });
        fillSupervisorConfig(data.config || null, { force: true });
        setSupervisorLoadState(`ClawDone saved for ${profile}. ${summarizeSupervisorConfig(data.config || null)}`);
        setStatus('ClawDone config saved.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function deleteSupervisorConfig() {
      const id = supervisorConfigIdInput.value.trim();
      if (!id) {
        fillSupervisorConfig(null);
        setSupervisorLoadState('No ClawDone config to delete.', 'warn');
        setStatus('No ClawDone config to delete.', 'warn');
        return;
      }
      try {
        await api('/api/supervisor/config/delete', {
          method: 'POST',
          body: JSON.stringify({ id }),
        });
        fillSupervisorConfig(null, { force: true });
        setSupervisorLoadState('ClawDone config deleted from current target.', 'warn');
        setStatus('ClawDone config deleted.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function initializeFoldPanels() {
      foldPanels.forEach((panel) => {
        const key = panel.dataset.foldKey;
        if (!key) return;
        const stored = safeStorageGet(`clawdone-fold-${key}`, '');
        if (stored === 'open') panel.open = true;
        if (stored === 'closed') panel.open = false;
        panel.addEventListener('toggle', () => {
          safeStorageSet(`clawdone-fold-${key}`, panel.open ? 'open' : 'closed');
          saveUiStateToServer();
        });
      });
    }

    function collectFoldStates() {
      const states = {};
      foldPanels.forEach((panel) => {
        const key = panel.dataset.foldKey;
        if (!key) return;
        states[key] = panel.open ? 'open' : 'closed';
      });
      return states;
    }

    function applyFoldStates(states) {
      if (!states || typeof states !== 'object') return;
      foldPanels.forEach((panel) => {
        const key = panel.dataset.foldKey;
        if (!key) return;
        const state = String(states[key] || '').trim().toLowerCase();
        if (state === 'open') panel.open = true;
        if (state === 'closed') panel.open = false;
      });
    }

    let profilesCache = [];
    let dashboardCache = { targets: [] };
    let stateCache = { sessions: [] };
    let templatesCache = [];
    let historyCache = [];
    let supervisorConfigCache = null;
    let todosCache = [];
    let selectedTodoIds = new Set();
    let todoTemplatesCache = [];
    let auditLogsCache = [];
    let todoStream = null;
    let latestPaneOutput = 'Choose a target and window first.';
    let uiSettings = loadUiSettings();
    const serverActiveView = normalizeView((document.querySelector('.page-view.active') || {}).id || 'dashboard');
    let uiState = {
      targetPage: 1,
      historyPage: 1,
      todoPage: 1,
      currentView: normalizeView(safeStorageGet('clawdone-view', serverActiveView) || serverActiveView),
      selectedProfile: safeStorageGet(PROFILE_SELECTION_STORAGE_KEY, '').trim(),
    };
    const foldPanels = Array.from(document.querySelectorAll('details[data-fold-key]'));
    let paneLoadVersion = 0;
    let todoLoadVersion = 0;
    let remoteStateLoadVersion = 0;
    let checklistActionBusy = false;
    let profileFormDirty = false;
    let profileFormSourceName = '';
    let supervisorFormDirty = false;
    let uiStateSaveTimer = null;
    let supervisorFormSourceProfile = '';

    function saveProfileDraft() {
      safeStorageSet(PROFILE_DRAFT_STORAGE_KEY, JSON.stringify({
        selected_profile: currentProfileName(),
        source_name: profileFormSourceName,
        form: readProfileForm(),
      }));
    }

    function clearProfileDraft() {
      safeStorageRemove(PROFILE_DRAFT_STORAGE_KEY);
    }

    function loadProfileDraft() {
      try {
        const raw = JSON.parse(safeStorageGet(PROFILE_DRAFT_STORAGE_KEY, '{}') || '{}');
        if (!raw || typeof raw !== 'object' || !raw.form || typeof raw.form !== 'object') {
          return null;
        }
        return raw;
      } catch (_) {
        return null;
      }
    }

    function syncProfileDraftLifecycle() {
      if (uiState.currentView === 'auth') {
        applyStoredProfileDraft();
      }
    }

    function setCurrentProfileSelection(name, options = {}) {
      const selectedProfile = String(name || '').trim();
      uiState.selectedProfile = selectedProfile;
      if (!options.skipDomSync) {
        profileSelect.value = selectedProfile;
      }
      if (selectedProfile) {
        safeStorageSet(PROFILE_SELECTION_STORAGE_KEY, selectedProfile);
      } else {
        safeStorageRemove(PROFILE_SELECTION_STORAGE_KEY);
      }
      if (!options.skipSave) {
        saveUiStateToServer();
      }
    }

    function markProfileFormDirty() {
      profileFormDirty = true;
      saveProfileDraft();
    }

    function bindProfileFormDirtyTracking() {
      [
        profileNameInput,
        profileGroupInput,
        profileTagsInput,
        hostInput,
        portInput,
        usernameInput,
        passwordInput,
        passwordRefInput,
        keyFilenameInput,
        tmuxBinInput,
        profileDescriptionInput,
        hostKeyPolicySelect,
        sshTimeoutInput,
        sshCommandTimeoutInput,
        sshRetriesInput,
        sshRetryBackoffMsInput,
        profileFavoriteInput,
      ].forEach((field) => {
        if (!field) return;
        field.addEventListener('input', markProfileFormDirty);
        field.addEventListener('change', markProfileFormDirty);
      });
    }

    function markSupervisorFormDirty() {
      supervisorFormDirty = true;
    }

    function bindSupervisorFormDirtyTracking() {
      [
        supervisorConfigIdInput,
        supervisorNameInput,
        supervisorModelInput,
        supervisorBaseUrlInput,
        supervisorApiKeyInput,
        supervisorApiKeyRefInput,
        supervisorEnabledInput,
        supervisorCanDispatchInput,
        supervisorCanReviewInput,
        supervisorCanAcceptInput,
        supervisorAutoDispatchInput,
        supervisorAutoReviewInput,
        supervisorAutoAcceptInput,
        supervisorSystemPromptInput,
      ].forEach((field) => {
        if (!field) return;
        field.addEventListener('input', markSupervisorFormDirty);
        field.addEventListener('change', markSupervisorFormDirty);
      });
    }

    function headers() {
      const token = tokenInput.value.trim();
      if (token) {
        safeStorageSet('clawdone-token', token);
      } else {
        safeStorageRemove('clawdone-token');
      }
      const result = { 'Content-Type': 'application/json' };
      if (token) {
        result['Authorization'] = `Bearer ${token}`;
      }
      return result;
    }

    function setStatus(message, type = 'info') {
      statusEl.textContent = message;
      statusEl.classList.remove('error', 'warn');
      if (type === 'error') statusEl.classList.add('error');
      if (type === 'warn') statusEl.classList.add('warn');
    }

    function optionalIntOrZero(value) {
      const parsed = Number.parseInt(String(value || '').trim(), 10);
      if (!Number.isFinite(parsed)) return 0;
      return Math.max(0, parsed);
    }

    function positiveInt(value, fallback, max = 500) {
      const parsed = Number.parseInt(String(value || '').trim(), 10);
      if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
      return Math.min(parsed, max);
    }

    function syncUiSettingsInputs() {
      paneLinesInput.value = String(uiSettings.paneLines);
      targetPageSizeInput.value = String(uiSettings.targetPageSize);
      historyPageSizeInput.value = String(uiSettings.historyPageSize);
      todoPageSizeInput.value = String(uiSettings.todoPageSize);
    }

    function currentUiSettings() {
      return {
        paneLines: Math.max(MIN_PANE_LINES, positiveInt(paneLinesInput.value, DEFAULT_UI_SETTINGS.paneLines, MAX_PANE_LINES)),
        targetPageSize: positiveInt(targetPageSizeInput.value, DEFAULT_UI_SETTINGS.targetPageSize, 24),
        historyPageSize: positiveInt(historyPageSizeInput.value, DEFAULT_UI_SETTINGS.historyPageSize, 30),
        todoPageSize: positiveInt(todoPageSizeInput.value, DEFAULT_UI_SETTINGS.todoPageSize, 20),
      };
    }

    function saveUiSettings() {
      uiSettings = currentUiSettings();
      uiState = { targetPage: 1, historyPage: 1, todoPage: 1, currentView: uiState.currentView, selectedProfile: uiState.selectedProfile };
      safeStorageSet('clawdone-ui-settings', JSON.stringify(uiSettings));
      saveUiStateToServer();
      syncUiSettingsInputs();
      renderTargetCards();
      renderHistory();
      renderTodos();
      renderChatFeed();
      loadPane().catch(() => {});
      setStatus('Settings saved. Front-end pagination and chat view updated.');
    }

    function resetUiSettings() {
      uiSettings = { ...DEFAULT_UI_SETTINGS };
      uiState = { targetPage: 1, historyPage: 1, todoPage: 1, currentView: uiState.currentView, selectedProfile: uiState.selectedProfile };
      safeStorageRemove('clawdone-ui-settings');
      saveUiStateToServer();
      syncUiSettingsInputs();
      renderTargetCards();
      renderHistory();
      renderTodos();
      renderChatFeed();
      loadPane().catch(() => {});
      setStatus('View settings reset to defaults.');
    }

    function clampPage(page, totalPages) {
      return Math.min(Math.max(1, page), Math.max(1, totalPages));
    }

    function paginate(items, page, pageSize) {
      const totalPages = Math.max(1, Math.ceil(items.length / Math.max(1, pageSize)));
      const safePage = clampPage(page, totalPages);
      const start = (safePage - 1) * pageSize;
      return {
        items: items.slice(start, start + pageSize),
        page: safePage,
        totalPages,
        totalItems: items.length,
      };
    }

    function buildPageTokens(page, totalPages) {
      if (totalPages <= 5) {
        return Array.from({ length: totalPages }, (_, index) => index + 1);
      }
      const tokens = [1];
      const start = Math.max(2, page - 1);
      const end = Math.min(totalPages - 1, page + 1);
      if (start > 2) tokens.push('…');
      for (let current = start; current <= end; current += 1) {
        tokens.push(current);
      }
      if (end < totalPages - 1) tokens.push('…');
      tokens.push(totalPages);
      return tokens;
    }

    function renderPager(container, page, totalPages, onSelect) {
      container.innerHTML = '';
      if (totalPages <= 1) return;

      const prevButton = document.createElement('button');
      prevButton.type = 'button';
      prevButton.className = 'ghost';
      prevButton.textContent = '‹';
      prevButton.disabled = page <= 1;
      prevButton.addEventListener('click', () => onSelect(page - 1));
      container.appendChild(prevButton);

      buildPageTokens(page, totalPages).forEach((token) => {
        if (token === '…') {
          const ellipsis = document.createElement('span');
          ellipsis.className = 'page-ellipsis';
          ellipsis.textContent = '…';
          container.appendChild(ellipsis);
          return;
        }
        const button = document.createElement('button');
        button.type = 'button';
        button.className = token === page ? 'ghost page-current' : 'ghost';
        button.textContent = String(token);
        button.disabled = token === page;
        button.addEventListener('click', () => onSelect(token));
        container.appendChild(button);
      });

      const nextButton = document.createElement('button');
      nextButton.type = 'button';
      nextButton.className = 'ghost';
      nextButton.textContent = '›';
      nextButton.disabled = page >= totalPages;
      nextButton.addEventListener('click', () => onSelect(page + 1));
      container.appendChild(nextButton);
    }

    function escapeHtml(text) {
      return String(text || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    /*
     * Timestamp utilities — date arithmetic and relative-time formatting.
     * Adapted from frappe/gantt (https://github.com/frappe/gantt), MIT License.
     * Copyright (c) 2016 Frappe Technologies Pvt. Ltd.
     * Original source: src/date_utils.js
     * Modifications: stripped Gantt-specific helpers, added timeAgo() for
     * human-readable relative timestamps used throughout ClawDone's UI.
     */
    const frappeDate = {
      parse(date) {
        if (date instanceof Date) return date;
        if (typeof date === 'string') {
          // Accept ISO-8601 strings like "2026-03-24T15:48:36Z"
          const d = new Date(date);
          if (!isNaN(d)) return d;
          // Fallback: "YYYY-MM-DD HH:mm:ss" without timezone
          const parts = date.split(' ');
          const dp = parts[0].split('-').map((v) => parseInt(v, 10));
          const tp = parts[1] ? parts[1].split(/[.:]/).map((v) => parseFloat(v)) : [0, 0, 0, 0];
          dp[1] = dp[1] ? dp[1] - 1 : 0;
          return new Date(...dp.concat(tp));
        }
        return new Date();
      },

      diff(dateA, dateB, scale = 'day') {
        const a = this.parse(dateA);
        const b = this.parse(dateB);
        const ms = a - b + (b.getTimezoneOffset() - a.getTimezoneOffset()) * 60000;
        const map = {
          millisecond: ms,
          second: ms / 1000,
          minute: ms / 60000,
          hour: ms / 3600000,
          day: ms / 86400000,
        };
        const s = scale.endsWith('s') ? scale : scale + 's';
        return Math.round((map[s] ?? map.days) * 100) / 100;
      },

      format(date, fmt = 'YYYY-MM-DD HH:mm') {
        const d = this.parse(date);
        if (isNaN(d)) return String(date || '-');
        const pad = (n, len = 2) => String(n).padStart(len, '0');
        return fmt
          .replace('YYYY', d.getFullYear())
          .replace('MM', pad(d.getMonth() + 1))
          .replace('DD', pad(d.getDate()))
          .replace('HH', pad(d.getHours()))
          .replace('mm', pad(d.getMinutes()))
          .replace('ss', pad(d.getSeconds()));
      },
    };

    function timeAgo(isoString) {
      if (!isoString) return '-';
      const d = frappeDate.parse(isoString);
      if (isNaN(d)) return String(isoString);
      const diffSec = (Date.now() - d.getTime()) / 1000;
      if (diffSec < 0) return frappeDate.format(d, 'YYYY-MM-DD HH:mm');
      if (diffSec < 60) return 'just now';
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
      if (diffSec < 86400 * 7) return `${Math.floor(diffSec / 86400)}d ago`;
      return frappeDate.format(d, 'YYYY-MM-DD');
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        ...options,
        headers: { ...headers(), ...(options.headers || {}) },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || `Request failed (${response.status})`);
      }
      return payload;
    }

    function saveUiStateToServer() {
      if (uiStateSaveTimer) {
        clearTimeout(uiStateSaveTimer);
      }
      uiStateSaveTimer = setTimeout(async () => {
        uiStateSaveTimer = null;
        try {
          await api('/api/ui-state/save', {
            method: 'POST',
            body: JSON.stringify({
              ui_settings: uiSettings,
              current_view: uiState.currentView,
              selected_profile: uiState.selectedProfile,
              fold_states: collectFoldStates(),
            }),
          });
        } catch (_) {
          // Keep local behavior even when server-side state sync fails.
        }
      }, 240);
    }

    async function loadUiStateFromServer() {
      try {
        const payload = await api(UI_STATE_ENDPOINT);
        const state = payload && typeof payload.ui_state === 'object' ? payload.ui_state : null;
        if (!state) return;
        if (state.ui_settings && typeof state.ui_settings === 'object') {
          uiSettings = normalizeUiSettingsPayload(state.ui_settings);
          safeStorageSet('clawdone-ui-settings', JSON.stringify(uiSettings));
        }
        if (state.current_view) {
          uiState.currentView = normalizeView(state.current_view);
          safeStorageSet('clawdone-view', uiState.currentView);
        }
        if (Object.prototype.hasOwnProperty.call(state, 'selected_profile')) {
          uiState.selectedProfile = String(state.selected_profile || '').trim();
          if (uiState.selectedProfile) {
            safeStorageSet(PROFILE_SELECTION_STORAGE_KEY, uiState.selectedProfile);
          } else {
            safeStorageRemove(PROFILE_SELECTION_STORAGE_KEY);
          }
        }
        if (state.fold_states && typeof state.fold_states === 'object') {
          applyFoldStates(state.fold_states);
          const foldStates = collectFoldStates();
          Object.keys(foldStates).forEach((key) => {
            safeStorageSet(`clawdone-fold-${key}`, foldStates[key]);
          });
        }
      } catch (_) {
        // Local storage remains the fallback when server-side state is unavailable.
      }
    }

    function currentProfileName() {
      return profileSelect.value.trim() || String(uiState.selectedProfile || '').trim();
    }

    function currentProfile() {
      return profilesCache.find((profile) => profile.name === currentProfileName()) || null;
    }

    function currentWindowLabel(window) {
      if (!window) return 'No window selected';
      return `${window.index}: ${window.name || 'unnamed window'}`;
    }

    function normalizeView(view) {
      const raw = String(view || '').replace(/^#/, '').trim();
      const normalized = raw.startsWith('view-') ? raw.slice(5) : raw;
      return ['dashboard', 'auth', 'chat', 'todo', 'delivery'].includes(normalized) ? normalized : 'dashboard';
    }

    function setActiveView(view, options = {}) {
      const safeView = normalizeView(view);
      uiState.currentView = safeView;
      safeStorageSet('clawdone-view', safeView);
      saveUiStateToServer();
      if (window.history && typeof window.history.replaceState === 'function') {
        const nextUrl = new URL(window.location.href);
        nextUrl.searchParams.set('view', safeView);
        window.history.replaceState(null, '', nextUrl.toString());
      }
      const activeViewEl = {
        dashboard: dashboardViewEl,
        auth: authViewEl,
        chat: chatViewEl,
        todo: todoViewEl,
        delivery: deliveryViewEl,
      }[safeView] || dashboardViewEl;
      [dashboardViewEl, authViewEl, chatViewEl, todoViewEl, deliveryViewEl].forEach((panel) => {
        panel.classList.toggle('active', panel === activeViewEl);
        panel.classList.remove('view-entering');
      });
      void activeViewEl.offsetWidth;
      activeViewEl.classList.add('view-entering');
      if (options.announce) {
        setStatus(`Opened ${safeView}.`);
      }
      syncProfileDraftLifecycle();
      viewButtons.forEach((button) => {
        const isActive = button.dataset.viewButton === safeView;
        button.classList.toggle('active', isActive);
        if (isActive) {
          button.setAttribute('aria-current', 'page');
        } else {
          button.removeAttribute('aria-current');
        }
      });
      if (typeof window.scrollTo === 'function') {
        window.scrollTo(0, 0);
      }
    }
    window.__clawdoneShowView = setActiveView;

    function currentDashboardTarget() {
      return (dashboardCache.targets || []).find((target) => target.name === currentProfileName()) || null;
    }

    function profileLabel(profile) {
      const favorite = profile.favorite ? '★ ' : '';
      const group = profile.group ? ` · ${profile.group}` : '';
      return `${favorite}${profile.name}${group}`;
    }

    function targetStatusLabel(target) {
      const status = target.online ? 'online' : 'offline';
      return `${target.name} · ${status} · ${target.session_count} sessions · ${target.window_count} windows`;
    }

    function setProfileFormValues(values = {}, options = {}) {
      const profile = values && typeof values === 'object' ? values : {};
      const tags = Array.isArray(profile.tags) ? profile.tags.join(', ') : String(profile.tags || '').trim();
      profileNameInput.value = profile.name || '';
      profileGroupInput.value = profile.group || 'General';
      profileTagsInput.value = tags;
      hostInput.value = profile.host || '';
      portInput.value = String(profile.port || 22);
      usernameInput.value = profile.username || '';
      passwordInput.value = options.keepPasswordValue ? String(profile.password || '') : '';
      passwordRefInput.value = profile.password_ref || '';
      passwordInput.placeholder = options.passwordPlaceholder || 'Optional password';
      keyFilenameInput.value = profile.key_filename || '';
      tmuxBinInput.value = profile.tmux_bin || 'tmux';
      profileDescriptionInput.value = profile.description || '';
      hostKeyPolicySelect.value = profile.host_key_policy || '';
      sshTimeoutInput.value = profile.ssh_timeout ? String(profile.ssh_timeout) : '';
      sshCommandTimeoutInput.value = profile.ssh_command_timeout ? String(profile.ssh_command_timeout) : '';
      sshRetriesInput.value = profile.ssh_retries ? String(profile.ssh_retries) : '';
      sshRetryBackoffMsInput.value = profile.ssh_retry_backoff_ms ? String(profile.ssh_retry_backoff_ms) : '';
      profileFavoriteInput.checked = Boolean(profile.favorite);
    }

    function applyStoredProfileDraft() {
      const draft = loadProfileDraft();
      if (!draft) return false;
      const draftSelectedProfile = String(draft.selected_profile || '').trim();
      const selectedProfile = currentProfileName();
      if (draftSelectedProfile !== selectedProfile) {
        return false;
      }
      setProfileFormValues(draft.form, {
        keepPasswordValue: true,
        passwordPlaceholder: draft.form && draft.form.password ? 'Unsaved password draft' : 'Optional password',
      });
      profileFormSourceName = String(draft.source_name || draftSelectedProfile || '').trim();
      profileFormDirty = true;
      return true;
    }

    function fillProfileForm(profile, options = {}) {
      const force = Boolean(options && options.force);
      const sourceName = profile ? String(profile.name || '') : '';
      if (!force && profileFormDirty && sourceName && sourceName === profileFormSourceName) {
        return;
      }
      if (!profile) {
        setProfileFormValues({}, { passwordPlaceholder: 'Leave blank to keep existing password' });
        profileFormSourceName = '';
        profileFormDirty = false;
        return;
      }
      setProfileFormValues(profile, {
        passwordPlaceholder: profile.has_password ? 'Stored password is kept unless you enter a new one' : 'Optional password',
      });
      profileFormSourceName = String(profile.name || '');
      profileFormDirty = false;
    }

    function readProfileForm() {
      return {
        name: profileNameInput.value.trim(),
        group: profileGroupInput.value.trim() || 'General',
        tags: profileTagsInput.value.trim(),
        host: hostInput.value.trim(),
        port: Number(portInput.value || '22'),
        username: usernameInput.value.trim(),
        password: passwordInput.value,
        password_ref: passwordRefInput.value.trim(),
        key_filename: keyFilenameInput.value.trim(),
        tmux_bin: tmuxBinInput.value.trim() || 'tmux',
        description: profileDescriptionInput.value.trim(),
        host_key_policy: hostKeyPolicySelect.value.trim(),
        ssh_timeout: optionalIntOrZero(sshTimeoutInput.value),
        ssh_command_timeout: optionalIntOrZero(sshCommandTimeoutInput.value),
        ssh_retries: optionalIntOrZero(sshRetriesInput.value),
        ssh_retry_backoff_ms: optionalIntOrZero(sshRetryBackoffMsInput.value),
        favorite: profileFavoriteInput.checked,
      };
    }

    function updateKpis() {
      profileCountEl.textContent = String(dashboardCache.profile_count || profilesCache.length || 0);
      onlineCountEl.textContent = String(dashboardCache.online_count || 0);
      const sessions = stateCache.sessions || [];
      const windows = sessions.flatMap((session) => session.windows || []);
      sessionCountEl.textContent = String(sessions.length);
      paneCountEl.textContent = String(windows.length);
    }

    function option(label, value) {
      const element = document.createElement('option');
      element.value = value;
      element.textContent = label;
      return element;
    }

    function selectedSessionData() {
      return (stateCache.sessions || []).find((session) => session.name === sessionSelect.value) || null;
    }

    function selectedWindowData() {
      const session = selectedSessionData();
      return session ? (session.windows || []).find((window) => String(window.index) === windowSelect.value) || null : null;
    }

    function defaultPaneForWindow(window) {
      if (!window || !(window.panes || []).length) return null;
      return (window.panes || []).find((pane) => pane.active) || window.panes[0] || null;
    }

    function selectedPaneData() {
      const window = selectedWindowData();
      if (!window) return null;
      return (window.panes || []).find((pane) => pane.target === paneSelect.value) || defaultPaneForWindow(window);
    }

    function currentTarget() {
      const pane = selectedPaneData();
      return pane && pane.target ? String(pane.target).trim() : paneSelect.value.trim();
    }

    function currentTargetLabel() {
      const profile = currentProfileName();
      const session = selectedSessionData();
      const window = selectedWindowData();
      if (!profile || !session || !window) return 'No window selected';
      const pane = selectedPaneData();
      const alias = pane && pane.alias ? ` (${pane.alias})` : '';
      return `${profile} → ${session.name}:${window.index}${alias}`;
    }

    function streamSnapshot(output, maxLines = MAX_COMMAND_STREAM_LINES) {
      const text = String(output || '');
      if (!text.trim()) return { text, truncated: false };
      const lines = text.split('\n');
      if (lines.length <= maxLines) return { text, truncated: false };
      return {
        text: lines.slice(-maxLines).join('\n'),
        truncated: true,
      };
    }

    function renderChatFeed() {
      const profile = currentProfileName();
      const target = currentTarget();
      chatFeedEl.innerHTML = '';
      if (!profile || !target) {
        chatFeedEl.innerHTML = '<div class="empty-state">Select a window to start.</div>';
        return;
      }
      const relatedHistory = historyCache.filter((entry) => entry.profile === profile);
      const historyPage = paginate(relatedHistory, uiState.historyPage, uiSettings.historyPageSize);
      uiState.historyPage = historyPage.page;

      if (!historyPage.items.length && !latestPaneOutput.trim()) {
        chatFeedEl.innerHTML = '<div class="empty-state">No messages yet.</div>';
        return;
      }

      [...historyPage.items].reverse().forEach((entry) => {
        const node = document.createElement('div');
        node.className = 'message user';
        const alias = entry.alias || entry.target;
        node.innerHTML = `
          <div class="message-meta">You · ${escapeHtml(timeAgo(entry.created_at))} · ${escapeHtml(alias)}</div>
          <div class="message-body">${escapeHtml(entry.command || '')}</div>
        `;        chatFeedEl.appendChild(node);
      });

      const pane = selectedPaneData();
      const alias = (pane && pane.alias) || target;
      const snapshot = streamSnapshot(latestPaneOutput);
      const truncatedHint = snapshot.truncated ? ` · last ${MAX_COMMAND_STREAM_LINES} lines` : '';
      const agentNode = document.createElement('div');
      agentNode.className = 'message agent';
      agentNode.innerHTML = `
        <div class="message-meta">ClawDone · live window snapshot${truncatedHint} · ${escapeHtml(alias)}</div>
        <div class="message-body">${escapeHtml(snapshot.text || '[empty window]')}</div>
      `;
      chatFeedEl.appendChild(agentNode);
      chatFeedEl.scrollTop = chatFeedEl.scrollHeight;
    }

    function renderChatSessionSelect() {
      const previous = chatSessionSelect.value;
      chatSessionSelect.innerHTML = '';
      const sessions = stateCache.sessions || [];
      if (!sessions.length) {
        chatSessionSelect.appendChild(option('No tmux sessions', ''));
        return;
      }
      sessions.forEach((session) => {
        chatSessionSelect.appendChild(option(`${session.name} (${(session.windows || []).length} windows)`, session.name));
      });
      chatSessionSelect.value = sessions.some((session) => session.name === previous) ? previous : sessionSelect.value;
    }

    function renderConversationList() {
      conversationListEl.innerHTML = '';
      const session = selectedSessionData();
      if (!session || !(session.windows || []).length) {
        conversationListEl.innerHTML = '<div class="empty-state">No threads.</div>';
        chatConversationHintEl.textContent = 'No threads yet.';
        return;
      }
      const currentWindow = selectedWindowData();
      chatConversationHintEl.textContent = `${session.name} · ${session.windows.length} conversation(s)`;
      session.windows.forEach((entry) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `thread-card ${currentWindow && String(currentWindow.index) === String(entry.index) ? 'active' : ''}`;
        const workerNames = (entry.panes || []).map((pane) => pane.alias || pane.target).slice(0, 4).join(' · ');
        button.innerHTML = `
          <div class="thread-title"><span>${escapeHtml(currentWindowLabel(entry))}</span><span class="muted">${(entry.panes || []).length} workers</span></div>
          <div class="hint">${escapeHtml(workerNames || 'No workers yet')}</div>
        `;
        button.addEventListener('click', () => {
          windowSelect.value = String(entry.index);
          uiState.historyPage = 1;
          uiState.todoPage = 1;
          renderPanes();
          renderConversationList();
          renderWorkerList();
          loadPane();
          loadTodos();
        });
        conversationListEl.appendChild(button);
      });
    }

    function workerDisplayName(pane) {
      if (!pane) return 'Agent';
      return String(pane.alias || pane.target || 'Agent').trim() || 'Agent';
    }

    function workerInitials(pane) {
      const label = workerDisplayName(pane)
        .replace(/[_:.]+/g, ' ')
        .trim();
      const parts = label.split(/\s+/).filter(Boolean);
      if (!parts.length) return 'AG';
      if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase();
      }
      return `${parts[0][0] || ''}${parts[1][0] || ''}`.toUpperCase();
    }

    function workerToneClass(pane) {
      const seed = `${pane?.alias || ''}:${pane?.target || ''}`;
      let hash = 0;
      for (let index = 0; index < seed.length; index += 1) {
        hash = (hash * 31 + seed.charCodeAt(index)) % 6;
      }
      return `tone-${Math.abs(hash) % 6}`;
    }

    function workerGlyph(pane) {
      const command = String(pane?.current_command || '').toLowerCase();
      if (command.includes('codex') || command.includes('agent') || command.includes('claude')) return '✦';
      if (command.includes('python') || command.includes('uvicorn') || command.includes('fastapi')) return 'λ';
      if (command.includes('node') || command.includes('npm') || command.includes('pnpm') || command.includes('yarn')) return '◈';
      if (command.includes('tmux') || command.includes('ssh') || command.includes('mosh')) return '⇄';
      if (command.includes('bash') || command.includes('zsh') || command.includes('fish') || command.includes('sh')) return '⌘';
      return '•';
    }

    function renderWorkerList() {
      workerListEl.innerHTML = '';
      const currentWindow = selectedWindowData();
      if (!currentWindow || !(currentWindow.panes || []).length) {
        workerListEl.innerHTML = '<div class="empty-state">No agents.</div>';
        return;
      }
      currentWindow.panes.forEach((pane) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `worker-chip ${pane.target === paneSelect.value ? 'active' : ''}`;
        const label = workerDisplayName(pane);
        const command = pane.current_command || 'shell';
        const initials = workerInitials(pane);
        const liveClass = pane.active ? 'live' : '';
        const toneClass = workerToneClass(pane);
        const glyph = workerGlyph(pane);
        button.title = `${pane.target} · ${command}`;
        button.innerHTML = `
          <div class="worker-avatar" data-tone="${toneClass}"><span class="worker-glyph">${escapeHtml(glyph)}</span><span class="worker-initials">${escapeHtml(initials)}</span><span class="worker-dot ${liveClass}"></span></div>
          <div class="worker-copy">
            <div class="worker-name">${escapeHtml(label)}</div>
            <div class="worker-meta">${escapeHtml(command)} · ${escapeHtml(pane.target || '')}</div>
          </div>
        `;
        button.addEventListener('click', () => {
          paneSelect.value = pane.target;
          uiState.historyPage = 1;
          uiState.todoPage = 1;
          syncAliasInput();
          renderWorkerList();
          loadPane();
          loadTodos();
        });
        workerListEl.appendChild(button);
      });
    }

    function syncDeliveryView() {
      deliveryAgentLabelEl.textContent = currentTargetLabel();
      deliveryAgentHintEl.textContent = currentAgentHintEl.textContent;
      deliveryPaneOutputEl.textContent = latestPaneOutput || '[empty window]';

      const todo = selectedTodo();
      if (!todo) {
        deliveryTodoMetaEl.textContent = 'No result yet.';
        deliveryTimelineEl.textContent = 'No result yet.';
        deliveryResultEl.textContent = 'Select a completed task to review the result.';
        deliveryEvidenceEl.textContent = 'No evidence yet.';
      } else {
        const status = String(todo.status || 'todo').replaceAll('_', ' ');
        const title = todo.title || 'Task';
        const result = String(todo.progress_note || todo.detail || '').trim() || 'No written result yet.';
        deliveryTodoMetaEl.textContent = `${status} · ${title}`;
        const evLines = (todo.events || []).map((ev) => `${timeAgo(ev.created_at)} · ${ev.actor || 'unknown'}${ev.status ? ' [' + ev.status + ']' : ''} · ${ev.note || ''}`);
        deliveryTimelineEl.textContent = evLines.length ? evLines.join('\n') : 'No timeline events.';
        deliveryResultEl.textContent = result;
        deliveryEvidenceEl.textContent = todoEvidenceListEl.textContent;
      }

      if (!auditLogsCache.length) {
        deliveryAuditEl.textContent = 'No audit events.';
        return;
      }
      deliveryAuditEl.textContent = auditLogsCache
        .slice(0, 12)
        .map((entry) => `${timeAgo(entry.created_at)} · ${entry.action || '-'} · ${entry.actor || 'unknown'} · ${entry.note || entry.status || '-'}`)
        .join('\n');
    }

    function updateCurrentAgentCard() {
      const profile = currentProfileName();
      const target = currentTarget();
      currentAgentLabelEl.textContent = currentTargetLabel();
      if (!profile || !target) {
        currentAgentHintEl.textContent = 'Select a window.';
        syncDeliveryView();
        return;
      }
      const pane = selectedPaneData();
      const window = selectedWindowData();
      const session = selectedSessionData();
      const alias = pane && pane.alias ? pane.alias : '(no alias)';
      const cmd = pane && pane.current_command ? pane.current_command : 'shell';
      const conversation = window ? currentWindowLabel(window) : 'no window';
      currentAgentHintEl.textContent = `${profile} · ${session ? session.name : '-'} · ${conversation} · ${cmd}${alias && alias !== '(no alias)' ? ` · ${alias}` : ''}`;
      syncDeliveryView();
    }

    function requireCurrentAgent(action, silent = false) {
      const profile = currentProfileName();
      const target = currentTarget();
      if (!profile || !target) {
        if (!silent) setStatus(`Choose a target and window before ${action}.`, 'error');
        return null;
      }
      return { profile, target };
    }

    function selectedTodo() {
      return todosCache.find((todo) => todo.id === todoSelect.value) || null;
    }

    function requireSelectedTodo(action = 'this action') {
      const todo = selectedTodo();
      if (todo) return todo;
      setStatus(`Choose a todo first before ${action}.`, 'error');
      return null;
    }

    async function recoverMissingTodo(error) {
      const message = String(error && error.message ? error.message : error || '');
      if (!message.includes('todo not found:')) return false;
      await loadTodos();
      await loadDashboard();
      setStatus('Selected task was already removed. Checklist refreshed.', 'warn');
      return true;
    }

    async function runTodoAction(action, options = {}) {
      const { refresh = true, recoverMissing = true } = options;
      try {
        const result = await action();
        if (refresh) {
          await Promise.all([loadTodos(), loadDashboard()]);
        }
        return { ok: true, result };
      } catch (error) {
        if (recoverMissing && await recoverMissingTodo(error)) {
          return { ok: false, recovered: true };
        }
        setStatus(error.message, 'error');
        return { ok: false, error };
      }
    }

    function parseEvidenceInput(raw) {
      const text = String(raw || '').trim();
      if (!text) return null;
      if ((text.startsWith('{') && text.endsWith('}')) || (text.startsWith('[') && text.endsWith(']'))) {
        try {
          return JSON.parse(text);
        } catch (_) {
          return text;
        }
      }
      return text;
    }

    function parseChecklistLines(raw) {
      const normalized = String(raw || '').split('\n').join('\n');
      return normalized
        .split(/\n+/)
        .map((line) => String(line || '').trim())
        .map((line) => line.replace(/^[-*•]\s+/, ''))
        .map((line) => line.replace(/^\d+[.)]\s+/, ''))
        .map((line) => line.replace(/^\[(?: |x|X)?\]\s+/, ''))
        .map((line) => line.replace(/^-\s*\[(?: |x|X)?\]\s+/, ''))
        .map((line) => line.trim())
        .filter(Boolean);
    }

    function normalizeChecklistItemKey(value) {
      return String(value || '').trim().replace(/\s+/g, ' ').toLowerCase();
    }

    function dedupeChecklistItems(items) {
      const seen = new Set();
      const deduped = [];
      (items || []).forEach((item) => {
        const text = String(item || '').trim();
        const key = normalizeChecklistItemKey(text);
        if (!key || seen.has(key)) return;
        seen.add(key);
        deduped.push(text);
      });
      return deduped;
    }

    function openChecklistTodosForTarget(selected) {
      if (!selected) return [];
      return (todosCache || []).filter((todo) => {
        if (String(todo.profile || '').trim() !== selected.profile) return false;
        if (String(todo.target || '').trim() !== selected.target) return false;
        const status = String(todo.status || '').trim().toLowerCase();
        return !['done', 'verified'].includes(status);
      });
    }

    function setChecklistActionBusy(busy) {
      checklistActionBusy = Boolean(busy);
      if (createTodoButton) createTodoButton.disabled = checklistActionBusy;
      if (quickTodoButton) quickTodoButton.disabled = checklistActionBusy;
    }

    async function pushChecklistDraft(selected, options = {}) {
      const response = await api('/api/checklist/push', {
        method: 'POST',
        body: JSON.stringify({
          profile: selected.profile,
          target: selected.target,
          alias: ((selectedPaneData() || {}).alias) || '',
          priority: todoPrioritySelect.value,
          assignee: todoAssigneeInput.value.trim(),
          role: 'general',
          raw_text: todoDetailInput.value,
          dispatch: Boolean(options.dispatch),
          press_enter: true,
          expected_target: selected.target,
        }),
      });
      return {
        created: response.created || [],
        skipped: Number(response.skipped || 0),
        parsedCount: Number(response.parsed_count || 0),
        dispatch: response.dispatch || { queued: false, count: 0 },
      };
    }

    async function saveChecklistItems(selected, items) {
      const dedupedItems = dedupeChecklistItems(items);
      const pane = selectedPaneData();
      const existingKeys = new Set(
        openChecklistTodosForTarget(selected)
          .map((todo) => normalizeChecklistItemKey(todo.title))
          .filter(Boolean)
      );
      const created = [];
      for (const item of dedupedItems) {
        const key = normalizeChecklistItemKey(item);
        if (!key || existingKeys.has(key)) continue;
        const response = await api('/api/todos/quick', {
          method: 'POST',
          body: JSON.stringify({
            title: item.slice(0, 140),
            detail: '',
            profile: selected.profile,
            target: selected.target,
            alias: (pane && pane.alias) || '',
            priority: todoPrioritySelect.value,
            assignee: todoAssigneeInput.value.trim(),
            dispatch: false,
          }),
        });
        created.push(response.todo);
        existingKeys.add(key);
      }
      return { created, skipped: Math.max(0, dedupedItems.length - created.length) };
    }

    function applyCreatedChecklistItems(created) {
      if (!Array.isArray(created) || !created.length) return;
      todoDetailInput.value = '';
      const first = created[0] || null;
      if (!first) return;
      todoTitleInput.value = first.title || '';
      todoSelect.value = first.id || '';
    }

    function withPlural(value, noun) {
      return `${value} ${noun}${value === 1 ? '' : 's'}`;
    }

    function checklistSaveStatus(target, createdCount, skippedCount) {
      if (!createdCount && skippedCount > 0) {
        return `No new checklist items. ${withPlural(skippedCount, 'item')} already exist for ${target}.`;
      }
      if (skippedCount > 0) {
        return `Saved ${withPlural(createdCount, 'checklist item')} for ${target}; skipped ${withPlural(skippedCount, 'existing item')}.`;
      }
      return `Saved ${withPlural(createdCount, 'checklist item')} for ${target}.`;
    }

    async function runChecklistAction(action) {
      if (checklistActionBusy) {
        setStatus('Checklist action already in progress.', 'warn');
        return false;
      }
      setChecklistActionBusy(true);
      try {
        await action();
        return true;
      } catch (error) {
        setStatus(error.message, 'error');
        return false;
      } finally {
        setChecklistActionBusy(false);
      }
    }

    function checklistPromptText(items) {
      return [
        'Work through this checklist. Mark items complete as you finish them and report progress when blocked.',
        '',
        ...items.map((item) => `- [ ] ${item}`),
      ].join('\n');
    }

    function closeTodoStream() {
      if (todoStream) {
        todoStream.close();
        todoStream = null;
      }
    }

    function openTodoStream() {
      closeTodoStream();
      const selected = requireCurrentAgent('starting live updates', true);
      if (!selected || !window.EventSource) return;
      const token = tokenInput.value.trim();
      const query = new URLSearchParams({
        profile: selected.profile,
        target: selected.target,
        interval: '3',
      });
      if (token) query.set('token', token);
      const streamUrl = `/api/todos/stream?${query.toString()}`;
      todoStream = new EventSource(streamUrl);
      todoStream.onmessage = (event) => {
        try {
          JSON.parse(event.data || '{}');
          loadTodos().catch(() => {});
          loadDashboard().catch(() => {});
        } catch (_) {
          // ignore malformed chunks
        }
      };
      todoStream.onerror = () => {
        // Connection may be rotated by server; fallback polling remains active.
      };
    }

    function renderProfileSelect() {
      const previous = currentProfileName();
      const preferred = previous || String(uiState.selectedProfile || '').trim() || safeStorageGet(PROFILE_SELECTION_STORAGE_KEY, '').trim();
      profileSelect.innerHTML = '';
      if (!profilesCache.length) {
        profileSelect.appendChild(option('No saved targets', ''));
        setCurrentProfileSelection('', { skipSave: true });
        fillProfileForm(null, { force: true });
        applyStoredProfileDraft();
        return;
      }
      profilesCache.forEach((profile) => profileSelect.appendChild(option(profileLabel(profile), profile.name)));
      const nextProfile = profilesCache.some((profile) => profile.name === preferred) ? preferred : profilesCache[0].name;
      setCurrentProfileSelection(nextProfile, { skipSave: true });
      fillProfileForm(currentProfile());
      applyStoredProfileDraft();
    }

    function renderTargetCards() {
      targetListEl.innerHTML = '';
      const targets = dashboardCache.targets || [];
      if (!targets.length) {
        targetListEl.innerHTML = '<div class="muted">No targets yet. Save one to get started.</div>';
        targetPaginationEl.innerHTML = '';
        return;
      }
      const page = paginate(targets, uiState.targetPage, uiSettings.targetPageSize);
      uiState.targetPage = page.page;
      renderPager(targetPaginationEl, page.page, page.totalPages, (nextPage) => {
        uiState.targetPage = nextPage;
        renderTargetCards();
      });
      page.items.forEach((target) => {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = `target-card ${target.name === currentProfileName() ? 'active' : ''}`;
        const todoSummary = target.todo_summary || {};
        const inProgress = Number(todoSummary.in_progress_count || 0);
        const lastNote = String(todoSummary.last_note || '').trim();
        card.innerHTML = `
          <div class="target-card-head">
            <div class="target-card-name">
              <strong>${target.favorite ? '★ ' : ''}${escapeHtml(target.name)}</strong>
              <span class="target-card-host">${escapeHtml(target.host || 'No host')}</span>
            </div>
            <span class="badge ${target.online ? 'ok' : 'bad'}">${target.online ? 'Online' : 'Offline'}</span>
          </div>
          <div class="badge-row">
            <span class="badge">${escapeHtml(target.group || 'General')}</span>
            <span class="badge">${target.session_count} sessions</span>
            <span class="badge">${target.window_count} windows</span>
            <span class="badge">${inProgress} active tasks</span>
          </div>
          <div class="hint">${escapeHtml(target.error ? target.error : (lastNote || target.description || target.tags.join(', ') || 'Ready'))}</div>
          <div class="target-card-foot"><span>${escapeHtml((target.tags || []).slice(0, 3).join(' · ') || 'No tags')}</span><span>${target.online ? 'Available' : 'Needs attention'}</span></div>
        `;
        card.addEventListener('click', async () => {
          setCurrentProfileSelection(target.name);
          fillProfileForm(currentProfile());
          await loadSelectedProfile();
        });
        targetListEl.appendChild(card);
      });
    }

    function renderSessions() {
      const previousSession = sessionSelect.value;
      sessionSelect.innerHTML = '';
      const sessions = stateCache.sessions || [];
      if (!sessions.length) {
        sessionSelect.appendChild(option('No tmux sessions', ''));
        chatSessionSelect.innerHTML = '';
        chatSessionSelect.appendChild(option('No tmux sessions', ''));
        windowSelect.innerHTML = '';
        paneSelect.innerHTML = '';
        aliasInput.value = '';
        selectedPaneLabel.textContent = currentTargetLabel();
        renderConversationList();
        renderWorkerList();
        updateKpis();
        return;
      }
      sessions.forEach((session) => {
        sessionSelect.appendChild(option(`${session.name} (${(session.windows || []).length} windows)`, session.name));
      });
      sessionSelect.value = sessions.some((session) => session.name === previousSession) ? previousSession : sessions[0].name;
      renderChatSessionSelect();
      renderWindows();
      updateKpis();
    }

    function renderWindows() {
      const previousWindow = windowSelect.value;
      const session = selectedSessionData();
      windowSelect.innerHTML = '';
      if (!session || !(session.windows || []).length) {
        windowSelect.appendChild(option('No windows', ''));
        paneSelect.innerHTML = '';
        aliasInput.value = '';
        selectedPaneLabel.textContent = currentTargetLabel();
        renderConversationList();
        renderWorkerList();
        return;
      }
      session.windows.forEach((window) => {
        const primaryPane = defaultPaneForWindow(window);
        const cmd = primaryPane && primaryPane.current_command ? ` · ${primaryPane.current_command}` : '';
        windowSelect.appendChild(option(`${window.index}: ${window.name}${window.active ? ' · active' : ''}${cmd}`, String(window.index)));
      });
      const fallback = session.windows.find((window) => window.active) || session.windows[0];
      windowSelect.value = session.windows.some((window) => String(window.index) === previousWindow) ? previousWindow : String(fallback.index);
      renderPanes();
      renderConversationList();
    }

    function renderPanes() {
      const previousPane = paneSelect.value;
      const window = selectedWindowData();
      paneSelect.innerHTML = '';
      if (!window || !(window.panes || []).length) {
        paneSelect.appendChild(option('No window target', ''));
        aliasInput.value = '';
        selectedPaneLabel.textContent = currentTargetLabel();
        renderWorkerList();
        return;
      }
      window.panes.forEach((pane) => {
        paneSelect.appendChild(option(pane.target, pane.target));
      });
      const fallback = defaultPaneForWindow(window);
      paneSelect.value = window.panes.some((pane) => pane.target === previousPane) ? previousPane : (fallback ? fallback.target : '');
      syncAliasInput();
      renderWorkerList();
    }

    function syncAliasInput() {
      const pane = selectedPaneData();
      aliasInput.value = pane ? (pane.alias || '') : '';
      selectedPaneLabel.textContent = currentTargetLabel();
      renderConversationList();
      renderWorkerList();
      updateCurrentAgentCard();
    }

    function renderTemplates() {
      templateSelect.innerHTML = '';
      if (!templatesCache.length) {
        templateSelect.appendChild(option('No templates yet', ''));
        return;
      }
      templatesCache.forEach((template) => {
        const scope = template.profile ? ` · ${template.profile}` : ' · global';
        templateSelect.appendChild(option(`${template.name}${scope}`, template.id));
      });
    }

    function renderHistory() {
      historySelect.innerHTML = '';
      historyListEl.innerHTML = '';
      if (!historyCache.length) {
        historySelect.appendChild(option('No recent commands', ''));
        historyListEl.innerHTML = '<div class="empty-state">No recent commands for this target yet.</div>';
        historyPaginationEl.innerHTML = '';
        renderChatFeed();
        return;
      }
      historyCache.forEach((entry) => {
        const label = `${entry.profile} · ${entry.alias || entry.target} · ${entry.command.slice(0, 40)}`;
        historySelect.appendChild(option(label, entry.id));
      });
      const page = paginate(historyCache, uiState.historyPage, uiSettings.historyPageSize);
      uiState.historyPage = page.page;
      renderPager(historyPaginationEl, page.page, page.totalPages, async (nextPage) => {
        uiState.historyPage = nextPage;
        await loadHistory();
      });
      page.items.forEach((entry, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'list-item';
        button.innerHTML = `
          <strong>${escapeHtml(entry.alias || entry.target || 'agent')}</strong>
          <span class="hint">${escapeHtml(timeAgo(entry.created_at))}</span>
          <span class="hint">${escapeHtml((entry.command || '').slice(0, 160))}</span>
        `;
        button.addEventListener('click', () => {
          historySelect.value = entry.id;
          applyHistory();
          renderHistory();
        });
        if (historySelect.value === entry.id || (!historySelect.value && index === 0)) {
          historySelect.value = entry.id;
          button.classList.add('active');
        }
        historyListEl.appendChild(button);
      });
      renderChatFeed();
    }

    function renderTodoTemplates() {
      if (!todoTemplateSelect || !todoTemplateNameInput) return;
      const previous = todoTemplateSelect.value;
      todoTemplateSelect.innerHTML = '';
      if (!todoTemplatesCache.length) {
        todoTemplateSelect.appendChild(option('No todo templates', ''));
        todoTemplateNameInput.value = '';
        return;
      }
      todoTemplatesCache.forEach((template) => {
        const scope = template.target ? ` · ${template.target}` : (template.profile ? ` · ${template.profile}` : ' · global');
        todoTemplateSelect.appendChild(option(`${template.name}${scope}`, template.id));
      });
      todoTemplateSelect.value = todoTemplatesCache.some((item) => item.id === previous) ? previous : todoTemplatesCache[0].id;
      const selected = todoTemplatesCache.find((item) => item.id === todoTemplateSelect.value);
      todoTemplateNameInput.value = selected ? selected.name : '';
    }

    function renderAuditLogs() {
      auditSelect.innerHTML = '';
      if (!auditLogsCache.length) {
        auditSelect.appendChild(option('No audit events', ''));
        syncDeliveryView();
        return;
      }
      auditLogsCache.forEach((entry) => {
        const actor = entry.actor || 'unknown';
        const label = `${timeAgo(entry.created_at)} · ${entry.action} · ${actor} · ${entry.note || entry.status || '-'}`;
        auditSelect.appendChild(option(label.slice(0, 140), entry.id));
      });
      syncDeliveryView();
    }

    function todoStatusClass(status) {
      const value = String(status || 'todo').trim().toLowerCase() || 'todo';
      return `status-${value}`;
    }

    function todoProgressPercent(status) {
      const value = String(status || 'todo').trim().toLowerCase();
      if (value === 'verified') return 100;
      if (value === 'done') return 80;
      if (value === 'in_progress') return 45;
      if (value === 'blocked') return 100;
      return 12;
    }

    function nextTodoStatus(status) {
      const value = String(status || 'todo').trim().toLowerCase() || 'todo';
      if (value === 'todo') return 'in_progress';
      if (value === 'in_progress') return 'done';
      if (value === 'done') return 'verified';
      if (value === 'blocked') return 'in_progress';
      return value;
    }

    function todoCheckLabel(status) {
      const value = String(status || 'todo').trim().toLowerCase() || 'todo';
      if (value === 'verified') return '✓';
      if (value === 'done') return '✓';
      if (value === 'in_progress') return '…';
      if (value === 'blocked') return '!';
      return '○';
    }

    function currentTodoTargets() {
      const window = selectedWindowData();
      if (window && (window.panes || []).length) {
        return (window.panes || []).map((pane) => ({
          target: pane.target,
          alias: pane.alias || '',
          command: pane.current_command || 'shell',
          pane,
        }));
      }
      const targets = [];
      const seen = new Set();
      todosCache.forEach((todo) => {
        const target = String(todo.target || '').trim();
        if (!target || seen.has(target)) return;
        seen.add(target);
        targets.push({ target, alias: todo.alias || '', command: '', pane: null });
      });
      return targets;
    }

    function selectTodo(todoId, options = {}) {
      const nextId = String(todoId || '').trim();
      if (!nextId) return;
      selectedTodoIds.clear();
      todoSelect.value = nextId;
      if (options.openAdvanced) {
        const advanced = document.querySelector('[data-fold-key="todo-advanced"]');
        if (advanced) advanced.open = true;
      }
      // Only update active classes — never rebuild the DOM here to avoid hover flicker
      todoBoardEl.querySelectorAll('.checklist-row[data-todo-id]').forEach((row) => {
        row.classList.toggle('active', row.dataset.todoId === nextId);
      });
      syncTodoInspector();
    }

    async function toggleChecklistTodo(todoId) {
      const todo = todosCache.find((item) => item.id === todoId);
      if (!todo) return;
      selectTodo(todo.id, { openAdvanced: true });
      setStatus('Task status and evidence are managed by the agent. Use Delivery for review details.', 'warn');
    }

    function quickTodoUse(todoId) {
      const todo = todosCache.find((item) => item.id === todoId);
      if (!todo) return;
      selectTodo(todo.id, { openAdvanced: true });
      applyTodoToCommand();
      setActiveView('chat');
    }

    function renderTodos() {
      const previous = todoSelect.value;
      todoSelect.innerHTML = '';
      todoBoardEl.innerHTML = '';
      todoPaginationEl.innerHTML = '';

      const allTodos = todosCache
        .slice()
        .sort((left, right) => String(left.created_at || '').localeCompare(String(right.created_at || '')));

      allTodos.forEach((todo) => {
        const shortTitle = todo.title.length > 42 ? `${todo.title.slice(0, 42)}...` : todo.title;
        const label = `[${todo.status}] ${shortTitle}`;
        todoSelect.appendChild(option(label, todo.id));
      });

      const visibleTodos = allTodos.filter((todo) => !['done', 'verified'].includes(String(todo.status || '').toLowerCase()));
      const preferredTodo = allTodos.find((todo) => todo.id === previous) || visibleTodos[0] || allTodos[0] || null;
      todoSelect.value = preferredTodo ? preferredTodo.id : '';

      if (!allTodos.length) {
        todoSelect.innerHTML = '';
        todoSelect.appendChild(option('No tasks', ''));
        todoStatusSelect.value = 'todo';
        todoProgressNoteInput.value = '';
        todoMetaEl.textContent = 'No tasks yet.';
        todoBoardEl.innerHTML = '<div class="empty-state">No checklist items yet.</div>';
        renderGanttChart();
        return;
      }

      if (!visibleTodos.length) {
        todoMetaEl.textContent = '0 active tasks';
        todoBoardEl.innerHTML = '<div class="empty-state">No active tasks. Delivery keeps accepted results.</div>';
        renderGanttChart();
        syncTodoInspector();
        return;
      }

      const pane = selectedPaneData();
      const group = document.createElement('section');
      group.className = 'checklist-group';
      const acceptedCount = Math.max(allTodos.length - visibleTodos.length, 0);
      group.innerHTML = `
        <div class="checklist-group-head">
          <div class="checklist-group-copy">
            <strong>${escapeHtml(currentProfileName() || 'Tasks')}</strong>
          </div>
          <div class="checklist-counter">${visibleTodos.length} active${acceptedCount ? ` · ${acceptedCount} accepted` : ''}</div>
        </div>
        <div class="checklist-items"></div>
      `;
      const itemsEl = group.querySelector('.checklist-items');
      visibleTodos.forEach((todo) => {
        const row = document.createElement('article');
        const complete = ['done', 'verified'].includes(String(todo.status || '').toLowerCase());
        const detail = String(todo.progress_note || todo.detail || '').trim();
        row.dataset.todoId = todo.id;
        row.className = `checklist-row has-detail ${selectedTodoIds.has(todo.id) || todo.id === todoSelect.value ? 'active' : ''} ${complete ? 'is-complete' : ''}`;
        row.innerHTML = `
          <button type="button" class="checklist-toggle ${complete ? 'is-complete' : ''}" aria-label="View task status">${complete ? '✓' : ''}</button>
          <div class="checklist-copy">
            <div class="checklist-text">${escapeHtml(todo.title || '')}</div>
            ${detail ? `<div class="checklist-sub">${escapeHtml(detail)}</div>` : ''}
            <div class="checklist-sub">${escapeHtml(todo.alias || todo.target || '')} · ${escapeHtml(todo.status || 'todo')} · ${timeAgo(todo.updated_at || todo.created_at)}</div>
          </div>
        `;
        row.addEventListener('click', () => selectTodo(todo.id, { openAdvanced: false }));
        row.querySelector('.checklist-toggle').addEventListener('click', async (event) => {
          event.stopPropagation();
          await toggleChecklistTodo(todo.id);
        });
        itemsEl.appendChild(row);
      });
      todoBoardEl.appendChild(group);

      todoMetaEl.textContent = `${visibleTodos.length} active task${visibleTodos.length === 1 ? '' : 's'}`;
      renderGanttChart();
      syncTodoInspector();
    }

    function renderGanttChart() {
      const container = document.getElementById('todoGantt');
      if (!container) return;
      const todos = todosCache
        .filter((todo) => !['done', 'verified'].includes(String(todo.status || '').toLowerCase()))
        .sort((a, b) => String(a.created_at || '').localeCompare(String(b.created_at || '')));
      if (!todos.length) {
        container.innerHTML = '<div class="gantt-empty">No active tasks to display.</div>';
        return;
      }

      const now = Date.now();
      let minMs = Infinity, maxMs = -Infinity;
      todos.forEach((todo) => {
        const s = frappeDate.parse(todo.created_at).getTime();
        const e = frappeDate.parse(todo.updated_at || todo.created_at).getTime();
        if (!isNaN(s)) { minMs = Math.min(minMs, s); maxMs = Math.max(maxMs, s); }
        if (!isNaN(e)) maxMs = Math.max(maxMs, e);
      });
      if (!isFinite(minMs)) { container.innerHTML = '<div class="gantt-empty">No valid timestamps.</div>'; return; }
      maxMs = Math.max(maxMs, now);

      const span = maxMs - minMs || 3600000;
      minMs -= span * 0.02;
      maxMs += span * 0.04;
      const totalSpan = maxMs - minMs;

      const LABEL_W = 128;
      const ROW_H = 32;
      const HEADER_H = 26;
      const BAR_H = 14;
      const BAR_PAD = (ROW_H - BAR_H) / 2;
      const W = Math.max(320, (container.clientWidth || 480) - 2);
      const CHART_W = W - LABEL_W;
      const H = HEADER_H + todos.length * ROW_H + 4;

      const STATUS_COLOR = {
        todo: '#52525b', in_progress: '#3b82f6',
        done: '#22c55e', verified: '#14b8a6', blocked: '#ef4444',
      };

      const toX = (ms) => LABEL_W + ((ms - minMs) / totalSpan) * CHART_W;

      const useDayFmt = totalSpan > 86400000 * 1.5;
      const tickCount = Math.max(2, Math.min(6, Math.floor(CHART_W / 72)));
      const tickStep = totalSpan / tickCount;

      const parts = [
        `<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">`,
        `<defs><clipPath id="gc-lbl"><rect x="0" y="0" width="${LABEL_W - 4}" height="${H}"/></clipPath></defs>`,
        `<rect x="${LABEL_W}" y="${HEADER_H}" width="${CHART_W}" height="${H - HEADER_H}" fill="rgba(255,255,255,0.012)" rx="2"/>`,
      ];

      for (let i = 0; i <= tickCount; i++) {
        const ms = minMs + i * tickStep;
        const x = toX(ms);
        const lbl = frappeDate.format(new Date(ms), useDayFmt ? 'MM-DD' : 'HH:mm');
        parts.push(`<line x1="${x.toFixed(1)}" y1="${HEADER_H}" x2="${x.toFixed(1)}" y2="${H}" stroke="rgba(255,255,255,0.07)" stroke-width="1"/>`);
        parts.push(`<text x="${x.toFixed(1)}" y="${HEADER_H - 5}" text-anchor="middle" fill="#71717a" font-size="10">${lbl}</text>`);
      }

      const nowX = toX(now);
      if (nowX >= LABEL_W && nowX <= W) {
        parts.push(`<line x1="${nowX.toFixed(1)}" y1="${HEADER_H}" x2="${nowX.toFixed(1)}" y2="${H}" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.6"/>`);
        parts.push(`<text x="${nowX.toFixed(1)}" y="${HEADER_H - 5}" text-anchor="middle" fill="#60a5fa" font-size="10" font-weight="600">now</text>`);
      }

      const activeStatuses = new Set(['todo', 'in_progress', 'blocked']);
      todos.forEach((todo, i) => {
        const y = HEADER_H + i * ROW_H;
        const startMs = frappeDate.parse(todo.created_at).getTime();
        const endMs = activeStatuses.has(todo.status) ? now : frappeDate.parse(todo.updated_at || todo.created_at).getTime();
        const x1 = toX(startMs);
        const x2 = Math.max(x1 + 6, toX(endMs));
        const bw = x2 - x1;
        const color = STATUS_COLOR[todo.status] || STATUS_COLOR.todo;
        const isSelected = todo.id === todoSelect.value || selectedTodoIds.has(todo.id);

        if (i % 2 === 0) parts.push(`<rect x="0" y="${y}" width="${W}" height="${ROW_H}" fill="rgba(255,255,255,0.012)"/>`);
        if (isSelected) parts.push(`<rect x="0" y="${y}" width="${W}" height="${ROW_H}" fill="rgba(59,130,246,0.07)"/>`);

        const lbl = todo.title.length > 17 ? todo.title.slice(0, 17) + '…' : todo.title;
        parts.push(`<text x="${LABEL_W - 6}" y="${y + ROW_H / 2 + 4}" text-anchor="end" fill="${isSelected ? '#93c5fd' : '#a1a1aa'}" font-size="11" clip-path="url(#gc-lbl)">${escapeHtml(lbl)}</text>`);
        parts.push(`<rect x="${x1.toFixed(1)}" y="${(y + BAR_PAD).toFixed(1)}" width="${bw.toFixed(1)}" height="${BAR_H}" rx="3" fill="${color}" opacity="0.82"/>`);

        if (bw > 44) {
          parts.push(`<text x="${(x1 + bw / 2).toFixed(1)}" y="${(y + BAR_PAD + BAR_H / 2 + 4).toFixed(1)}" text-anchor="middle" fill="rgba(255,255,255,0.92)" font-size="10">${todo.status}</text>`);
        }
      });

      parts.push('</svg>');
      container.innerHTML = parts.join('');
    }

    function syncTodoInspector() {
      const todo = selectedTodo();
      if (!todo) {
        todoStatusSelect.value = 'todo';
        todoProgressNoteInput.value = '';
        todoMetaEl.textContent = todosCache.length ? 'Tasks' : 'No tasks yet.';
        todoEvidenceListEl.textContent = 'No evidence yet.';
        syncDeliveryView();
        return;
      }
      todoStatusSelect.value = todo.status || 'todo';
      todoProgressNoteInput.value = todo.progress_note || '';
      todoMetaEl.textContent = todo.title || 'Task';
      const timelineLines = (todo.events || []).map((event) => {
        const ts = timeAgo(event.created_at);
        const actor = event.actor || 'unknown';
        const status = event.status ? ` [${event.status}]` : '';
        const note = event.note || '';
        return `${ts} · ${actor}${status} · ${note}`;
      });
      const evidenceLines = (todo.evidence || []).map((entry) => {
        const ts = timeAgo(entry.created_at);
        const source = entry.source ? ` · ${entry.source}` : '';
        return `${ts} · ${entry.type}${source}
${entry.content}`;
      });
      todoEvidenceListEl.textContent = evidenceLines.length ? evidenceLines.join('\n\n') : 'No evidence yet.';
      syncDeliveryView();
    }

    async function loadProfiles() {
      const data = await api('/api/profiles');
      profilesCache = data.profiles || [];
      renderProfileSelect();
    }

    async function loadDashboard() {
      const data = await api('/api/dashboard');
      dashboardCache = data;
      renderTargetCards();
      updateKpis();
    }

    async function loadTemplates() {
      const profile = currentProfileName();
      const data = await api(`/api/templates?profile=${encodeURIComponent(profile)}`);
      templatesCache = data.templates || [];
      renderTemplates();
    }

    async function loadHistory() {
      const profile = currentProfileName();
      const limit = Math.max(uiSettings.historyPageSize * Math.max(uiState.historyPage, 1), uiSettings.historyPageSize);
      const data = await api(`/api/history?profile=${encodeURIComponent(profile)}&limit=${limit}`);
      historyCache = data.history || [];
      renderHistory();
    }

    async function loadTodoTemplates() {
      const profile = currentProfileName();
      const target = currentTarget();
      const data = await api(`/api/todo-templates?profile=${encodeURIComponent(profile)}&target=${encodeURIComponent(target)}`);
      todoTemplatesCache = data.templates || [];
      renderTodoTemplates();
    }

    async function loadAuditLogs() {
      const selected = requireCurrentAgent('loading audit logs', true);
      if (!selected) {
        auditLogsCache = [];
        renderAuditLogs();
        return;
      }
      const data = await api(`/api/audit?profile=${encodeURIComponent(selected.profile)}&target=${encodeURIComponent(selected.target)}&limit=25`);
      auditLogsCache = data.logs || [];
      renderAuditLogs();
    }

    async function loadTodos() {
      const requestVersion = ++todoLoadVersion;
      const profile = currentProfileName();
      const selectedTarget = currentTarget();
      if (!profile) {
        if (requestVersion !== todoLoadVersion) return;
        todosCache = [];
        renderTodos();
        await loadAuditLogs();
        updateCurrentAgentCard();
        closeTodoStream();
        return;
      }
      const data = await api(`/api/todos?profile=${encodeURIComponent(profile)}`);
      if (requestVersion !== todoLoadVersion || currentProfileName() !== profile) {
        return;
      }
      todosCache = data.todos || [];
      selectedTodoIds.clear();
      const selectAllBtn = document.getElementById('selectAllTodos');
      if (selectAllBtn) selectAllBtn.textContent = 'Select all';
      renderTodos();
      await Promise.all([loadTodoTemplates(), loadAuditLogs()]);
      if (requestVersion !== todoLoadVersion || currentProfileName() !== profile) {
        return;
      }
      if (selectedTarget) {
        openTodoStream();
      } else {
        closeTodoStream();
      }
      updateCurrentAgentCard();
    }

    async function loadRemoteState() {
      const requestVersion = ++remoteStateLoadVersion;
      const profile = currentProfileName();
      if (!profile) {
        if (requestVersion !== remoteStateLoadVersion) return;
        stateCache = { sessions: [] };
        renderSessions();
        latestPaneOutput = 'Choose a target and window first.';
        paneOutputEl.textContent = latestPaneOutput;
        todosCache = [];
        renderTodos();
        updateCurrentAgentCard();
        renderChatFeed();
        return;
      }
      const currentSession = sessionSelect.value;
      const currentWindow = windowSelect.value;
      const currentPane = paneSelect.value;
      const data = await api(`/api/remote/state?profile=${encodeURIComponent(profile)}`);
      if (requestVersion !== remoteStateLoadVersion || currentProfileName() !== profile) {
        return;
      }
      stateCache = data;
      renderSessions();
      if (currentSession) {
        const session = (stateCache.sessions || []).find((item) => item.name === currentSession);
        if (session) {
          sessionSelect.value = currentSession;
          renderWindows();
        }
      }
      if (currentWindow) {
        const window = selectedSessionData() ? (selectedSessionData().windows || []).find((item) => String(item.index) === currentWindow) : null;
        if (window) {
          windowSelect.value = currentWindow;
          renderPanes();
        }
      }
      if (currentPane) {
        const pane = selectedWindowData() ? (selectedWindowData().panes || []).find((item) => item.target === currentPane) : null;
        if (pane) {
          paneSelect.value = currentPane;
        }
      }
      syncAliasInput();
      await loadPane();
      await loadTodos();
      if (requestVersion !== remoteStateLoadVersion || currentProfileName() !== profile) {
        return;
      }
      updateCurrentAgentCard();
    }

    async function loadPane() {
      const requestVersion = ++paneLoadVersion;
      const profile = currentProfileName();
      const target = currentTarget();
      selectedPaneLabel.textContent = currentTargetLabel();
      if (!profile || !target) {
        if (requestVersion !== paneLoadVersion) return;
        latestPaneOutput = 'Choose a target and window first.';
        paneOutputEl.textContent = latestPaneOutput;
        renderChatFeed();
        syncDeliveryView();
        return;
      }
      const data = await api(`/api/pane?profile=${encodeURIComponent(profile)}&target=${encodeURIComponent(target)}&lines=${uiSettings.paneLines}`);
      if (requestVersion !== paneLoadVersion || currentProfileName() !== profile || currentTarget() !== target) {
        return;
      }
      latestPaneOutput = data.output || '[empty window]';
      paneOutputEl.textContent = latestPaneOutput;
      renderChatFeed();
      syncDeliveryView();
    }

    async function loadSelectedProfile() {
      uiState.historyPage = 1;
      uiState.todoPage = 1;
      setCurrentProfileSelection(currentProfileName(), { skipDomSync: true });
      fillProfileForm(currentProfile());
      await Promise.all([loadTemplates(), loadHistory(), loadSupervisorConfig()]);
      try {
        await loadRemoteState();
      } catch (error) {
        stateCache = { sessions: [] };
        renderSessions();
        latestPaneOutput = error.message;
        paneOutputEl.textContent = latestPaneOutput;
        todosCache = [];
        renderTodos();
        closeTodoStream();
        updateCurrentAgentCard();
        renderChatFeed();
        setStatus(error.message, 'error');
      }
      renderTargetCards();
    }

    async function refreshAll() {
      try {
        await Promise.all([loadProfiles(), loadDashboard()]);
        await loadSelectedProfile();
        setStatus('Dashboard refreshed.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function saveProfile() {
      const profile = readProfileForm();
      if (!profile.name || !profile.host || !profile.username) {
        setStatus('Name, host and username are required.', 'error');
        return;
      }
      try {
        await api('/api/profiles/save', { method: 'POST', body: JSON.stringify(profile) });
        await Promise.all([loadProfiles(), loadDashboard()]);
        clearProfileDraft();
        setCurrentProfileSelection(profile.name);
        await loadSelectedProfile();
        setStatus(`Saved target ${profile.name}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function testProfile() {
      const profile = readProfileForm();
      if (!profile.name || !profile.host || !profile.username) {
        setStatus('Fill name, host and username first.', 'error');
        return;
      }
      try {
        const data = await api('/api/profiles/test', { method: 'POST', body: JSON.stringify(profile) });
        if (data.ok) {
          setStatus(`SSH ok · ${data.session_count} session(s), ${data.window_count} window(s).`);
        } else {
          setStatus(data.error || 'SSH test failed.', 'error');
        }
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function deleteProfile() {
      const name = currentProfileName() || profileNameInput.value.trim();
      if (!name) {
        setStatus('Choose a target to delete.', 'error');
        return;
      }
      try {
        await api('/api/profiles/delete', { method: 'POST', body: JSON.stringify({ name }) });
        await Promise.all([loadProfiles(), loadDashboard()]);
        clearProfileDraft();
        await loadSelectedProfile();
        setStatus(`Deleted target ${name}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function saveAlias() {
      const profile = currentProfileName();
      const target = currentTarget();
      if (!profile || !target) {
        setStatus('Choose a window first.', 'error');
        return;
      }
      try {
        await api('/api/alias/save', { method: 'POST', body: JSON.stringify({ profile, target, alias: aliasInput.value.trim() }) });
        await Promise.all([loadDashboard(), loadRemoteState()]);
        setStatus(`Saved alias for ${target}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function saveTemplate() {
      const name = templateNameInput.value.trim();
      const command = commandInput.value.trim();
      if (!name || !command) {
        setStatus('Template name and command are required.', 'error');
        return;
      }
      const profile = templateScopeSelect.value === 'current' ? currentProfileName() : '';
      try {
        await api('/api/templates/save', { method: 'POST', body: JSON.stringify({ id: templateSelect.value, name, command, profile, target: currentTarget() }) });
        await loadTemplates();
        setStatus(`Saved template ${name}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function deleteTemplate() {
      const id = templateSelect.value.trim();
      if (!id) {
        setStatus('Choose a template first.', 'error');
        return;
      }
      try {
        await api('/api/templates/delete', { method: 'POST', body: JSON.stringify({ id }) });
        templateNameInput.value = '';
        await loadTemplates();
        setStatus('Template deleted.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function applyTemplate() {
      const template = templatesCache.find((item) => item.id === templateSelect.value);
      if (!template) {
        setStatus('Choose a template first.', 'error');
        return;
      }
      templateNameInput.value = template.name || '';
      commandInput.value = template.command || '';
      templateScopeSelect.value = template.profile ? 'current' : '';
      setStatus(`Applied template ${template.name}.`);
    }

    function applyHistory() {
      const entry = historyCache.find((item) => item.id === historySelect.value);
      if (!entry) {
        setStatus('Choose a history item first.', 'error');
        return;
      }
      commandInput.value = entry.command || '';
      setStatus('Applied recent command.');
    }

    async function clearHistory() {
      try {
        await api('/api/history/clear', { method: 'POST', body: JSON.stringify({ profile: currentProfileName() }) });
        await loadHistory();
        setStatus('History cleared for current target.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function createTodo() {
      const selected = requireCurrentAgent('saving a checklist');
      if (!selected) return;
      if (!String(todoDetailInput.value || '').trim()) {
        setStatus('Please enter at least one checklist item.', 'error');
        return;
      }
      await runChecklistAction(async () => {
        const { created = [], skipped = 0, parsedCount = 0, dispatch = { queued: false, count: 0, attempted_count: 0 } } = await pushChecklistDraft(selected, { dispatch: true });
        if (!created.length && parsedCount <= 0) {
          setStatus('No actionable checklist items found in the pasted text.', 'warn');
          return;
        }
        applyCreatedChecklistItems(created);
        await Promise.all([loadTodos(), loadDashboard()]);
        syncTodoInspector();
        const createdCount = created.length;
        const skippedCount = Number(skipped || 0);
        const saveSummary = checklistSaveStatus(selected.target, createdCount, skippedCount);
        const dispatchedCount = Number(dispatch.count || 0);
        const attemptedCount = Number(dispatch.attempted_count || 0);
        if (dispatchedCount > 0) {
          setStatus(`${saveSummary} ClawDone dispatched ${withPlural(dispatchedCount, 'task')}.`);
          return;
        }
        if (attemptedCount > 0) {
          setStatus(`${saveSummary} ClawDone kept ${withPlural(attemptedCount, 'task')} pending for routing.`, 'warn');
          return;
        }
        setStatus(saveSummary, (!createdCount && skippedCount > 0) ? 'warn' : 'info');
      });
    }

    async function quickTodo() {
      const selected = requireCurrentAgent('sending a checklist');
      if (!selected) return;
      await runChecklistAction(async () => {
        const { created = [], skipped = 0, parsedCount = 0, dispatch = { queued: false, count: 0 } } = await pushChecklistDraft(selected, { dispatch: true });
        if (!dispatch.queued && Number(dispatch.count || 0) <= 0) {
          if (String(todoDetailInput.value || '').trim() && parsedCount <= 0) {
            setStatus('No actionable checklist items found in the pasted text.', 'warn');
            return;
          }
          setStatus('No saved checklist items for current agent. Add tasks first.', 'warn');
          return;
        }
        applyCreatedChecklistItems(created);
        await Promise.all([loadTodos(), loadDashboard(), loadPane()]);
        setActiveView('chat');
        const createdCount = created.length;
        const skippedCount = Number(skipped || 0);
        const dispatchedCount = Number(dispatch.count || 0);
        if (String(todoDetailInput.value || '').trim()) {
          const saveSummary = checklistSaveStatus(selected.target, createdCount, skippedCount);
          setStatus(`${saveSummary} Queued ${withPlural(dispatchedCount, 'task')} for ${selected.target}.`);
        } else {
          setStatus(`Queued ${withPlural(dispatchedCount, 'saved task')} for ${selected.target}.`);
        }
      });
    }

    async function createTripletWorkflow() {
      const selected = requireCurrentAgent('creating triplet workflow');
      if (!selected) return;
      const title = todoTitleInput.value.trim();
      if (!title) {
        setStatus('Todo title is required for triplet workflow.', 'error');
        return;
      }
      const detail = todoDetailInput.value.trim();
      const handoffPacket = {
        context: detail || title,
        constraints: 'Keep changes minimal, do not break existing behavior.',
        acceptance: 'All relevant tests pass and summary is provided.',
        rollback: 'If blocked, stop and provide rollback-safe patch plan.',
      };
      try {
        const response = await api('/api/workflows/triplet', {
          method: 'POST',
          body: JSON.stringify({
            title,
            detail,
            profile: selected.profile,
            target: selected.target,
            planner_target: selected.target,
            executor_target: selected.target,
            reviewer_target: selected.target,
            priority: todoPrioritySelect.value,
            handoff_packet: handoffPacket,
          }),
        });
        await loadTodos();
        await loadDashboard();
        const dispatched = Array.isArray(response.dispatches) ? response.dispatches.filter((item) => item && item.dispatched).length : 0;
        setStatus(dispatched ? `Triplet workflow created and dispatched: ${response.workflow_id}.` : `Triplet workflow created: ${response.workflow_id}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function selectAllTodos() {
      const btn = document.getElementById('selectAllTodos');
      const allSelected = selectedTodoIds.size === todosCache.length && todosCache.length > 0;
      if (allSelected) {
        selectedTodoIds.clear();
        if (btn) btn.textContent = 'Select all';
      } else {
        selectedTodoIds = new Set(todosCache.map((t) => t.id));
        if (btn) btn.textContent = 'Deselect all';
      }
      // Only update active classes — no DOM rebuild
      todoBoardEl.querySelectorAll('.checklist-row[data-todo-id]').forEach((row) => {
        row.classList.toggle('active', selectedTodoIds.has(row.dataset.todoId) || row.dataset.todoId === todoSelect.value);
      });
    }

    async function clearAllTodos() {
      const profile = currentProfileName();
      if (!profile) {
        setStatus('Choose a profile first.', 'error');
        return;
      }
      const scopedTodos = Array.isArray(todosCache)
        ? todosCache.filter((todo) => String(todo.profile || '').trim() === profile)
        : [];
      if (!scopedTodos.length) {
        setStatus('No tasks to clear.');
        return;
      }
      if (!window.confirm(`Delete all ${scopedTodos.length} task${scopedTodos.length === 1 ? '' : 's'} in ${profile}?`)) {
        return;
      }

      let removedCount = 0;
      let failedCount = 0;
      let lastError = '';
      for (const todo of scopedTodos) {
        try {
          await api('/api/todos/delete', {
            method: 'POST',
            body: JSON.stringify({ id: todo.id }),
          });
          removedCount += 1;
        } catch (error) {
          const message = error && error.message ? String(error.message) : String(error);
          if (message.includes('todo not found:')) {
            continue;
          }
          failedCount += 1;
          lastError = message;
        }
      }

      await loadTodos();
      await loadDashboard();
      if (failedCount <= 0) {
        setStatus(`Deleted ${removedCount} task${removedCount === 1 ? '' : 's'}.`);
      } else if (removedCount > 0) {
        setStatus(`Deleted ${removedCount} task${removedCount === 1 ? '' : 's'}; ${failedCount} failed.`, 'warn');
      } else {
        setStatus(lastError || 'Failed to clear tasks.', 'error');
      }
    }

    async function clearCompletedTodos() {
      const profile = currentProfileName();
      if (!profile) {
        setStatus('Choose a profile first.', 'error');
        return;
      }
      const keepRecent = 0;
      const minAgeDays = 0;
      const scopeLabel = profile;
      if (!window.confirm(`Clear all completed tasks in ${scopeLabel}?`)) {
        return;
      }
      try {
        const response = await api('/api/todos/clear-completed', {
          method: 'POST',
          body: JSON.stringify({ profile, target: '', keep_recent: keepRecent, min_age_days: minAgeDays }),
        });
        const removedCount = Number(response.removed_count || 0);
        await loadTodos();
        await loadDashboard();
        if (removedCount > 0) {
          setStatus(`Cleared ${removedCount} completed task${removedCount === 1 ? '' : 's'}.`);
        } else {
          setStatus('No completed tasks to clear.');
        }
      } catch (error) {
        if (await recoverMissingTodo(error)) return;
        setStatus(error.message, 'error');
      }
    }

    async function supervisorDispatchTodo() {
      const todo = requireSelectedTodo('dispatching with ClawDone');
      if (!todo) return;
      const outcome = await runTodoAction(() => api('/api/supervisor/dispatch', {
          method: 'POST',
          body: JSON.stringify({ todo_id: todo.id, apply: true, auto_send: true }),
        }),
      );
      if (!outcome.ok) return;
      const response = outcome.result || {};
      setStatus(response.decision && response.decision.reason ? `ClawDone routed task: ${response.decision.reason}` : 'ClawDone routed the task.');
    }

    async function supervisorReviewTodo() {
      const todo = requireSelectedTodo('reviewing with ClawDone');
      if (!todo) return;
      const outcome = await runTodoAction(() => api('/api/supervisor/review', {
          method: 'POST',
          body: JSON.stringify({ todo_id: todo.id, apply: false, include_pane_output: true }),
        }),
        { refresh: false },
      );
      if (!outcome.ok) return;
      const response = outcome.result || {};
      const review = response.review || {};
      const summary = review.summary ? review.summary : 'Review complete.';
      todoProgressNoteInput.value = summary;
      setStatus(`ClawDone review: ${review.verdict}.`);
    }

    async function supervisorAcceptTodo() {
      const todo = requireSelectedTodo('accepting with ClawDone');
      if (!todo) return;
      const outcome = await runTodoAction(() => api('/api/supervisor/accept', {
          method: 'POST',
          body: JSON.stringify({ todo_id: todo.id, include_pane_output: true }),
        }),
      );
      if (!outcome.ok) return;
      const response = outcome.result || {};
      const review = response.review || {};
      setStatus(response.accepted ? 'ClawDone accepted and submitted the task.' : `ClawDone did not accept: ${review.verdict}.`);
    }

    function applyTodoTemplate() {
      if (!todoTemplateSelect || !todoTemplateNameInput) return;
      const template = todoTemplatesCache.find((item) => item.id === todoTemplateSelect.value);
      if (!template) {
        setStatus('Choose a todo template first.', 'error');
        return;
      }
      todoTemplateNameInput.value = template.name || '';
      todoTitleInput.value = template.title || '';
      todoDetailInput.value = template.detail || '';
      todoPrioritySelect.value = template.priority || 'medium';
      todoAssigneeInput.value = template.assignee || '';
      setStatus(`Applied todo template ${template.name}.`);
    }

    async function saveTodoTemplate() {
      if (!todoTemplateSelect || !todoTemplateNameInput) return;
      const selected = requireCurrentAgent('saving todo template');
      if (!selected) return;
      const name = todoTemplateNameInput.value.trim();
      const title = todoTitleInput.value.trim();
      if (!name || !title) {
        setStatus('Template name and todo title are required.', 'error');
        return;
      }
      try {
        await api('/api/todo-templates/save', {
          method: 'POST',
          body: JSON.stringify({
            id: todoTemplateSelect.value,
            name,
            title,
            detail: todoDetailInput.value.trim(),
            priority: todoPrioritySelect.value,
            assignee: todoAssigneeInput.value.trim(),
            profile: selected.profile,
            target: selected.target,
          }),
        });
        await loadTodoTemplates();
        await loadAuditLogs();
        setStatus(`Saved todo template ${name}.`);
      } catch (error) {
        if (await recoverMissingTodo(error)) return;
        setStatus(error.message, 'error');
      }
    }

    async function deleteTodoTemplate() {
      if (!todoTemplateSelect) return;
      const id = todoTemplateSelect.value.trim();
      if (!id) {
        setStatus('Choose a todo template first.', 'error');
        return;
      }
      try {
        await api('/api/todo-templates/delete', { method: 'POST', body: JSON.stringify({ id }) });
        await loadTodoTemplates();
        await loadAuditLogs();
        setStatus('Todo template deleted.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function applyTodoToCommand() {
      const todo = requireSelectedTodo('copying task content');
      if (!todo) return;
      commandInput.value = todo.detail ? todo.detail : todo.title;
      setStatus('Todo content copied into command box.');
    }

    async function sendCommand() {
      const profile = currentProfileName();
      const target = currentTarget();
      const command = commandInput.value.trim();
      if (!profile || !target) {
        setStatus('Choose a target and window first.', 'error');
        return;
      }
      if (!command) {
        setStatus('Enter a command first.', 'error');
        return;
      }
      try {
        await api('/api/send', {
          method: 'POST',
          body: JSON.stringify({ profile, target, command, press_enter: true, expected_target: target }),
        });
        commandInput.value = '';
        await Promise.all([loadHistory(), loadPane()]);
        setStatus(`Sent command to ${target}.`);
      } catch (error) {
        if (String(error.message || '').includes('confirm_risk=true')) {
          const ok = window.confirm('This command looks dangerous. Send anyway?');
          if (ok) {
            try {
              await api('/api/send', {
                method: 'POST',
                body: JSON.stringify({ profile, target, command, press_enter: true, expected_target: target, confirm_risk: true }),
              });
              commandInput.value = '';
              await Promise.all([loadHistory(), loadPane()]);
              setStatus(`Sent command to ${target} with risk confirmation.`, 'warn');
              return;
            } catch (retryError) {
              setStatus(retryError.message, 'error');
              return;
            }
          }
          setStatus('Cancelled risky command.', 'warn');
          return;
        }
        setStatus(error.message, 'error');
      }
    }

    async function interrupt() {
      const profile = currentProfileName();
      const target = currentTarget();
      if (!profile || !target) {
        setStatus('Choose a target and window first.', 'error');
        return;
      }
      try {
        await api('/api/interrupt', { method: 'POST', body: JSON.stringify({ profile, target }) });
        await loadPane();
        setStatus(`Sent Ctrl+C to ${target}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function appendNewline() {
      const value = commandInput.value;
      commandInput.value = value.endsWith('\n') ? value : `${value}\n`;
      commandInput.focus();
    }

    async function copyTargetLabel() {
      try {
        await navigator.clipboard.writeText(currentTargetLabel());
        setStatus('Copied selected target label.');
      } catch (error) {
        setStatus('Clipboard is unavailable in this browser.', 'warn');
      }
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = navigator.language || 'en-US';
      recognition.onresult = (event) => {
        let transcript = '';
        for (let index = event.resultIndex; index < event.results.length; index += 1) {
          transcript += event.results[index][0].transcript;
        }
        commandInput.value = transcript.trim();
        setStatus('Listening… local speech-to-text is updating the command box.');
      };
      recognition.onerror = (event) => {
        setStatus(`Voice input error: ${event.error}`, 'error');
      };
    } else {
      setStatus('Voice input is unavailable in this browser. Use Chrome-based browsers or type commands manually.', 'warn');
    }

    function bindClick(id, handler) {
      const node = document.getElementById(id);
      if (!node) return;
      node.addEventListener('click', handler);
    }

    bindClick('refreshDashboard', refreshAll);
    bindClick('refreshState', loadSelectedProfile);
    bindClick('saveUiSettings', saveUiSettings);
    bindClick('resetUiSettings', resetUiSettings);
    bindClick('saveSupervisorConfig', saveSupervisorConfig);
    bindClick('loadSupervisorConfig', loadSupervisorConfig);
    bindClick('deleteSupervisorConfig', deleteSupervisorConfig);
    bindClick('saveProfile', saveProfile);
    bindClick('testProfile', testProfile);
    bindClick('loadProfileState', loadSelectedProfile);
    bindClick('deleteProfile', deleteProfile);
    bindClick('saveAlias', saveAlias);
    bindClick('saveTemplate', saveTemplate);
    bindClick('deleteTemplate', deleteTemplate);
    bindClick('applyTemplate', applyTemplate);
    bindClick('applyHistory', applyHistory);
    bindClick('clearHistory', clearHistory);
    if (createTodoButton) createTodoButton.addEventListener('click', createTodo);
    if (quickTodoButton) quickTodoButton.addEventListener('click', quickTodo);
    bindClick('createTriplet', createTripletWorkflow);
    bindClick('refreshTodos', loadTodos);
    bindClick('clearCompletedTodos', clearCompletedTodos);
    bindClick('clearAllTodos', clearAllTodos);
    bindClick('selectAllTodos', selectAllTodos);
    bindClick('applyTodoToCommand', applyTodoToCommand);
    bindClick('supervisorDispatchTodo', supervisorDispatchTodo);
    bindClick('supervisorReviewTodo', supervisorReviewTodo);
    bindClick('supervisorAcceptTodo', supervisorAcceptTodo);
    bindClick('applyTodoTemplate', applyTodoTemplate);
    bindClick('saveTodoTemplate', saveTodoTemplate);
    bindClick('deleteTodoTemplate', deleteTodoTemplate);
    bindClick('sendCommand', sendCommand);
    bindClick('interrupt', interrupt);
    bindClick('appendNewline', appendNewline);
    bindClick('copyTargetLabel', copyTargetLabel);
    bindClick('refreshPane', loadPane);
    bindClick('refreshChatPane', loadPane);
    bindClick('startVoice', () => {
      if (!recognition) {
        setStatus('Voice input is unavailable in this browser.', 'error');
        return;
      }
      recognition.start();
      setStatus('Voice capture started.');
    });
    bindClick('stopVoice', () => {
      if (!recognition) return;
      recognition.stop();
      setStatus('Voice capture stopped.');
    });

    tokenInput.addEventListener('change', refreshAll);
    profileSelect.addEventListener('change', () => {
      setCurrentProfileSelection(profileSelect.value);
      loadSelectedProfile();
    });
    viewButtons.forEach((button) => {
      button.addEventListener('click', () => {
        setActiveView(button.dataset.viewButton || 'dashboard', { announce: true });
      });
    });
    chatSessionSelect.addEventListener('change', () => {
      sessionSelect.value = chatSessionSelect.value;
      uiState.historyPage = 1;
      uiState.todoPage = 1;
      renderWindows();
      loadPane();
      loadTodos();
    });
    sessionSelect.addEventListener('change', () => { uiState.historyPage = 1; uiState.todoPage = 1; renderWindows(); loadPane(); loadTodos(); });
    windowSelect.addEventListener('change', () => { uiState.historyPage = 1; uiState.todoPage = 1; renderPanes(); loadPane(); loadTodos(); });
    paneSelect.addEventListener('change', () => { uiState.historyPage = 1; uiState.todoPage = 1; syncAliasInput(); loadPane(); loadTodos(); });
    templateSelect.addEventListener('change', () => {
      const template = templatesCache.find((item) => item.id === templateSelect.value);
      templateNameInput.value = template ? template.name : '';
      templateScopeSelect.value = template && template.profile ? 'current' : '';
    });
    todoSelect.addEventListener('change', syncTodoInspector);
    if (todoTemplateSelect && todoTemplateNameInput) {
      todoTemplateSelect.addEventListener('change', () => {
        const template = todoTemplatesCache.find((item) => item.id === todoTemplateSelect.value);
        todoTemplateNameInput.value = template ? template.name : '';
      });
    }

    bindProfileFormDirtyTracking();
    bindSupervisorFormDirtyTracking();
    window.addEventListener('pagehide', () => {
      saveProfileDraft();
    });
    window.addEventListener('pageshow', () => {
      syncProfileDraftLifecycle();
    });
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        saveProfileDraft();
        return;
      }
      syncProfileDraftLifecycle();
    });
    async function bootstrapClientState() {
      initializeFoldPanels();
      await loadUiStateFromServer();
      syncUiSettingsInputs();
      setActiveView(uiState.currentView || serverActiveView || 'dashboard');
      refreshAll();
    }
    bootstrapClientState();
    setInterval(() => {
      if (currentProfileName()) {
        loadPane().catch(() => {});
      }
    }, 5000);
    setInterval(() => {
      // SSE handles near-real-time todo updates; this is a fallback refresh.
      if (currentProfileName() && currentTarget()) {
        loadTodos().catch(() => {});
      }
    }, 45000);
    setInterval(() => {
      loadDashboard().catch(() => {});
    }, 20000);
  """
