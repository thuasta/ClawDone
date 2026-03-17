"""Embedded mobile web UI."""

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>PocketClaw</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0b1020;
      --card: #121a2f;
      --card-2: #192440;
      --line: #2d3b61;
      --text: #e5ecff;
      --muted: #9caecc;
      --accent: #4f8cff;
      --accent-2: #7cf7d4;
      --danger: #ff6b7a;
      --warn: #ffc86e;
      --shadow: 0 10px 30px rgba(0, 0, 0, 0.28);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #0b1020 0%, #0f1730 100%);
      color: var(--text);
    }
    .wrap {
      width: min(960px, 100%);
      margin: 0 auto;
      padding: 18px 14px 40px;
    }
    .hero {
      margin-bottom: 16px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 1.8rem;
    }
    .sub {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }
    .card {
      background: rgba(18, 26, 47, 0.95);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      padding: 14px;
      margin-bottom: 14px;
      backdrop-filter: blur(8px);
    }
    .grid {
      display: grid;
      gap: 12px;
    }
    .grid-2 {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .grid-3 {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .grid-4 {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
    label {
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 0.92rem;
    }
    input, select, textarea, button {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px 14px;
      background: var(--card-2);
      color: var(--text);
      font: inherit;
    }
    textarea {
      min-height: 124px;
      resize: vertical;
    }
    button {
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.15s ease, opacity 0.15s ease;
    }
    button:active { transform: scale(0.98); }
    .primary { background: var(--accent); }
    .secondary { background: #243559; }
    .danger { background: var(--danger); }
    .warn { background: #6a4b14; color: #ffe0a8; }
    .ghost {
      background: transparent;
      border-style: dashed;
    }
    .status {
      min-height: 24px;
      color: var(--accent-2);
      font-size: 0.95rem;
      margin-top: 10px;
    }
    .status.error { color: #ff9aa4; }
    .status.warn { color: var(--warn); }
    .hint {
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.45;
      margin-top: 4px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: #10213f;
      border: 1px solid #264170;
      color: var(--muted);
      font-size: 0.85rem;
    }
    .kpi {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px;
      background: rgba(12, 17, 32, 0.55);
    }
    .kpi strong {
      display: block;
      font-size: 1.15rem;
      margin-bottom: 4px;
    }
    pre {
      margin: 0;
      padding: 12px;
      background: #09101f;
      border-radius: 12px;
      border: 1px solid #22304f;
      color: #d5e2ff;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      min-height: 220px;
    }
    @media (max-width: 740px) {
      .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
      .wrap { padding-bottom: 120px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <span class="pill">PocketClaw · Mobile voice → SSH → tmux → agent</span>
      <h1>Control remote coding agents from your phone</h1>
      <p class="sub">Configure SSH host, account and password on mobile, pick a tmux session/window/pane, give it a friendly alias, then use local speech-to-text to send commands into the matching Codex agent.</p>
    </section>

    <section class="card grid">
      <div class="grid-2">
        <div>
          <label for="token">Access token</label>
          <input id="token" type="password" placeholder="Optional: only needed if server was started with --token">
        </div>
        <div>
          <label for="profileSelect">SSH profile</label>
          <select id="profileSelect"></select>
        </div>
      </div>
      <div class="grid-4">
        <div class="kpi"><strong id="profileCount">0</strong><span>Profiles</span></div>
        <div class="kpi"><strong id="sessionCount">0</strong><span>tmux sessions</span></div>
        <div class="kpi"><strong id="windowCount">0</strong><span>tmux windows</span></div>
        <div class="kpi"><strong id="paneCount">0</strong><span>agent panes</span></div>
      </div>
      <div id="status" class="status"></div>
    </section>

    <section class="card grid">
      <div class="grid-3">
        <div>
          <label for="profileName">Profile name / alias</label>
          <input id="profileName" placeholder="office-server">
        </div>
        <div>
          <label for="host">SSH host / IP</label>
          <input id="host" placeholder="192.168.1.20">
        </div>
        <div>
          <label for="port">SSH port</label>
          <input id="port" type="number" value="22">
        </div>
      </div>
      <div class="grid-2">
        <div>
          <label for="username">SSH username</label>
          <input id="username" placeholder="ubuntu">
        </div>
        <div>
          <label for="password">SSH password</label>
          <input id="password" type="password" placeholder="Stored on the PocketClaw server">
        </div>
      </div>
      <div class="grid-2">
        <div>
          <label for="keyFilename">SSH key path (optional)</label>
          <input id="keyFilename" placeholder="~/.ssh/id_ed25519">
        </div>
        <div>
          <label for="tmuxBin">tmux binary</label>
          <input id="tmuxBin" value="tmux">
        </div>
      </div>
      <div class="grid-4">
        <button class="primary" id="saveProfile">Save profile</button>
        <button class="secondary" id="testProfile">Test SSH</button>
        <button class="secondary" id="refreshState">Refresh agents</button>
        <button class="danger" id="deleteProfile">Delete profile</button>
      </div>
      <div class="hint">密码会保存在 PocketClaw 服务器本地配置文件中，适合内网/自托管场景。更安全的方式仍然是 SSH key。</div>
    </section>

    <section class="card grid">
      <div class="grid-3">
        <div>
          <label for="session">tmux session</label>
          <select id="session"></select>
        </div>
        <div>
          <label for="window">tmux window</label>
          <select id="window"></select>
        </div>
        <div>
          <label for="pane">Agent pane</label>
          <select id="pane"></select>
        </div>
      </div>
      <div class="grid-2">
        <div>
          <label for="agentAlias">Agent alias</label>
          <input id="agentAlias" placeholder="backend-codex">
        </div>
        <div>
          <label>&nbsp;</label>
          <button class="secondary" id="saveAlias">Save alias for selected agent</button>
        </div>
      </div>
      <div class="hint">Pane 会被视为一个可独立控制的 agent 线程，例如 `codex:1.0`。你可以给它起一个更容易识别的别名。</div>
    </section>

    <section class="card grid">
      <div>
        <label for="command">Command</label>
        <textarea id="command" placeholder="Say something like: implement login page, run tests, then summarize the diff"></textarea>
      </div>
      <div class="grid-4">
        <button class="primary" id="startVoice">Start voice</button>
        <button class="secondary" id="stopVoice">Stop voice</button>
        <button class="primary" id="sendCommand">Send to agent</button>
        <button class="danger" id="interrupt">Send Ctrl+C</button>
      </div>
      <div class="grid-2">
        <button class="ghost" id="appendNewline">Insert newline</button>
        <button class="ghost" id="refreshPane">Refresh output</button>
      </div>
      <div class="hint">语音转文字在手机浏览器本地完成，然后文本命令通过 PocketClaw 发到对应 SSH 主机上的 tmux pane。</div>
    </section>

    <section class="card grid">
      <div>
        <label for="paneOutput">Recent pane output</label>
        <pre id="paneOutput">Loading…</pre>
      </div>
    </section>
  </div>

  <script>
    const tokenInput = document.getElementById('token');
    const profileSelect = document.getElementById('profileSelect');
    const profileNameInput = document.getElementById('profileName');
    const hostInput = document.getElementById('host');
    const portInput = document.getElementById('port');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const keyFilenameInput = document.getElementById('keyFilename');
    const tmuxBinInput = document.getElementById('tmuxBin');
    const sessionSelect = document.getElementById('session');
    const windowSelect = document.getElementById('window');
    const paneSelect = document.getElementById('pane');
    const aliasInput = document.getElementById('agentAlias');
    const commandInput = document.getElementById('command');
    const statusEl = document.getElementById('status');
    const paneOutputEl = document.getElementById('paneOutput');
    const profileCountEl = document.getElementById('profileCount');
    const sessionCountEl = document.getElementById('sessionCount');
    const windowCountEl = document.getElementById('windowCount');
    const paneCountEl = document.getElementById('paneCount');

    const storedToken = localStorage.getItem('pocketclaw-token') || '';
    tokenInput.value = storedToken;

    let profilesCache = [];
    let stateCache = { sessions: [] };

    function headers() {
      const token = tokenInput.value.trim();
      if (token) {
        localStorage.setItem('pocketclaw-token', token);
      } else {
        localStorage.removeItem('pocketclaw-token');
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
      if (type === 'error') {
        statusEl.classList.add('error');
      }
      if (type === 'warn') {
        statusEl.classList.add('warn');
      }
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        ...options,
        headers: {
          ...headers(),
          ...(options.headers || {}),
        },
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || `Request failed (${response.status})`);
      }
      return payload;
    }

    function getSelectedProfileName() {
      return profileSelect.value.trim();
    }

    function currentProfile() {
      const name = getSelectedProfileName();
      return profilesCache.find((profile) => profile.name === name) || null;
    }

    function readProfileForm() {
      return {
        name: profileNameInput.value.trim(),
        host: hostInput.value.trim(),
        port: Number(portInput.value || '22'),
        username: usernameInput.value.trim(),
        password: passwordInput.value,
        key_filename: keyFilenameInput.value.trim(),
        tmux_bin: tmuxBinInput.value.trim() || 'tmux',
      };
    }

    function fillProfileForm(profile) {
      if (!profile) {
        profileNameInput.value = '';
        hostInput.value = '';
        portInput.value = '22';
        usernameInput.value = '';
        passwordInput.value = '';
        keyFilenameInput.value = '';
        tmuxBinInput.value = 'tmux';
        return;
      }
      profileNameInput.value = profile.name || '';
      hostInput.value = profile.host || '';
      portInput.value = String(profile.port || 22);
      usernameInput.value = profile.username || '';
      passwordInput.value = profile.password || '';
      keyFilenameInput.value = profile.key_filename || '';
      tmuxBinInput.value = profile.tmux_bin || 'tmux';
    }

    function updateKpis() {
      profileCountEl.textContent = String(profilesCache.length);
      const sessions = stateCache.sessions || [];
      const windows = sessions.flatMap((session) => session.windows || []);
      const panes = windows.flatMap((window) => window.panes || []);
      sessionCountEl.textContent = String(sessions.length);
      windowCountEl.textContent = String(windows.length);
      paneCountEl.textContent = String(panes.length);
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
      if (!session) {
        return null;
      }
      return (session.windows || []).find((window) => String(window.index) === windowSelect.value) || null;
    }

    function selectedPaneData() {
      const window = selectedWindowData();
      if (!window) {
        return null;
      }
      return (window.panes || []).find((pane) => pane.target === paneSelect.value) || null;
    }

    function renderSessions() {
      const currentSession = sessionSelect.value;
      sessionSelect.innerHTML = '';
      const sessions = stateCache.sessions || [];
      if (!sessions.length) {
        sessionSelect.appendChild(option('No tmux sessions', ''));
        windowSelect.innerHTML = '';
        paneSelect.innerHTML = '';
        aliasInput.value = '';
        updateKpis();
        return;
      }
      sessions.forEach((session) => {
        const label = `${session.name} (${(session.windows || []).length} windows)`;
        sessionSelect.appendChild(option(label, session.name));
      });
      sessionSelect.value = sessions.some((session) => session.name === currentSession) ? currentSession : sessions[0].name;
      renderWindows();
      updateKpis();
    }

    function renderWindows() {
      const session = selectedSessionData();
      const currentWindow = windowSelect.value;
      windowSelect.innerHTML = '';
      if (!session || !(session.windows || []).length) {
        windowSelect.appendChild(option('No windows', ''));
        paneSelect.innerHTML = '';
        aliasInput.value = '';
        return;
      }
      session.windows.forEach((window) => {
        const active = window.active ? ' · active' : '';
        windowSelect.appendChild(option(`${window.index}: ${window.name}${active}`, String(window.index)));
      });
      const fallback = session.windows.find((window) => window.active) || session.windows[0];
      windowSelect.value = session.windows.some((window) => String(window.index) === currentWindow) ? currentWindow : String(fallback.index);
      renderPanes();
    }

    function renderPanes() {
      const window = selectedWindowData();
      const currentTarget = paneSelect.value;
      paneSelect.innerHTML = '';
      if (!window || !(window.panes || []).length) {
        paneSelect.appendChild(option('No panes', ''));
        aliasInput.value = '';
        return;
      }
      window.panes.forEach((pane) => {
        const aliasLabel = pane.alias ? `${pane.alias} · ` : '';
        const commandLabel = pane.current_command || 'shell';
        const active = pane.active ? ' · active' : '';
        paneSelect.appendChild(option(`${aliasLabel}${pane.target} · ${commandLabel}${active}`, pane.target));
      });
      const fallback = window.panes.find((pane) => pane.active) || window.panes[0];
      paneSelect.value = window.panes.some((pane) => pane.target === currentTarget) ? currentTarget : fallback.target;
      syncAliasInput();
    }

    function syncAliasInput() {
      const pane = selectedPaneData();
      aliasInput.value = pane ? (pane.alias || '') : '';
    }

    async function loadProfiles(selectedName = null) {
      try {
        const data = await api('/api/profiles');
        profilesCache = data.profiles || [];
        const previous = selectedName || getSelectedProfileName();
        profileSelect.innerHTML = '';
        if (!profilesCache.length) {
          profileSelect.appendChild(option('No saved SSH profiles', ''));
          fillProfileForm(null);
          stateCache = { sessions: [] };
          renderSessions();
          paneOutputEl.textContent = 'Save an SSH profile first.';
          updateKpis();
          return;
        }
        profilesCache.forEach((profile) => profileSelect.appendChild(option(profile.name, profile.name)));
        profileSelect.value = profilesCache.some((profile) => profile.name === previous) ? previous : profilesCache[0].name;
        fillProfileForm(currentProfile());
        updateKpis();
        await loadRemoteState();
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function saveProfile() {
      const profile = readProfileForm();
      if (!profile.name || !profile.host || !profile.username) {
        setStatus('Profile name, host and username are required.', 'error');
        return;
      }
      try {
        await api('/api/profiles/save', {
          method: 'POST',
          body: JSON.stringify(profile),
        });
        setStatus(`Saved SSH profile ${profile.name}.`);
        await loadProfiles(profile.name);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function deleteProfile() {
      const name = getSelectedProfileName() || profileNameInput.value.trim();
      if (!name) {
        setStatus('Choose a profile to delete.', 'error');
        return;
      }
      try {
        await api('/api/profiles/delete', {
          method: 'POST',
          body: JSON.stringify({ name }),
        });
        setStatus(`Deleted SSH profile ${name}.`);
        await loadProfiles();
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function testProfile() {
      const profile = readProfileForm();
      if (!profile.name || !profile.host || !profile.username) {
        setStatus('Fill profile name, host and username first.', 'error');
        return;
      }
      try {
        const data = await api('/api/profiles/test', {
          method: 'POST',
          body: JSON.stringify(profile),
        });
        setStatus(`SSH ok · ${data.session_count} tmux session(s) visible.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function loadRemoteState() {
      const profile = getSelectedProfileName();
      if (!profile) {
        stateCache = { sessions: [] };
        renderSessions();
        return;
      }
      try {
        const sessionValue = sessionSelect.value;
        const windowValue = windowSelect.value;
        const paneValue = paneSelect.value;
        const data = await api(`/api/remote/state?profile=${encodeURIComponent(profile)}`);
        stateCache = data;
        renderSessions();
        if (sessionValue) {
          sessionSelect.value = (stateCache.sessions || []).some((session) => session.name === sessionValue) ? sessionValue : sessionSelect.value;
          renderWindows();
        }
        if (windowValue) {
          const session = selectedSessionData();
          if (session && (session.windows || []).some((window) => String(window.index) === windowValue)) {
            windowSelect.value = windowValue;
            renderPanes();
          }
        }
        if (paneValue) {
          const window = selectedWindowData();
          if (window && (window.panes || []).some((pane) => pane.target === paneValue)) {
            paneSelect.value = paneValue;
            syncAliasInput();
          }
        }
        updateKpis();
        await loadPane();
      } catch (error) {
        stateCache = { sessions: [] };
        renderSessions();
        paneOutputEl.textContent = error.message;
        setStatus(error.message, 'error');
      }
    }

    function currentTarget() {
      return paneSelect.value.trim();
    }

    async function saveAlias() {
      const profile = getSelectedProfileName();
      const target = currentTarget();
      if (!profile || !target) {
        setStatus('Choose a profile and agent pane first.', 'error');
        return;
      }
      try {
        await api('/api/alias/save', {
          method: 'POST',
          body: JSON.stringify({ profile, target, alias: aliasInput.value.trim() }),
        });
        setStatus(`Saved alias for ${target}.`);
        await loadRemoteState();
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function loadPane() {
      const profile = getSelectedProfileName();
      const target = currentTarget();
      if (!profile || !target) {
        paneOutputEl.textContent = 'Choose a profile and agent pane first.';
        return;
      }
      try {
        const data = await api(`/api/pane?profile=${encodeURIComponent(profile)}&target=${encodeURIComponent(target)}&lines=120`);
        paneOutputEl.textContent = data.output || '[empty pane]';
      } catch (error) {
        paneOutputEl.textContent = error.message;
        setStatus(error.message, 'error');
      }
    }

    async function sendCommand() {
      const profile = getSelectedProfileName();
      const target = currentTarget();
      const command = commandInput.value.trim();
      if (!profile || !target) {
        setStatus('Choose a profile and agent pane first.', 'error');
        return;
      }
      if (!command) {
        setStatus('Please enter a command first.', 'error');
        return;
      }
      try {
        await api('/api/send', {
          method: 'POST',
          body: JSON.stringify({ profile, target, command, press_enter: true }),
        });
        setStatus(`Sent command to ${target}.`);
        await loadPane();
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function interrupt() {
      const profile = getSelectedProfileName();
      const target = currentTarget();
      if (!profile || !target) {
        setStatus('Choose a profile and agent pane first.', 'error');
        return;
      }
      try {
        await api('/api/interrupt', {
          method: 'POST',
          body: JSON.stringify({ profile, target }),
        });
        setStatus(`Sent Ctrl+C to ${target}.`);
        await loadPane();
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function appendNewline() {
      const value = commandInput.value;
      commandInput.value = value.endsWith('\n') ? value : `${value}\n`;
      commandInput.focus();
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

    document.getElementById('saveProfile').addEventListener('click', saveProfile);
    document.getElementById('testProfile').addEventListener('click', testProfile);
    document.getElementById('refreshState').addEventListener('click', loadRemoteState);
    document.getElementById('deleteProfile').addEventListener('click', deleteProfile);
    document.getElementById('saveAlias').addEventListener('click', saveAlias);
    document.getElementById('startVoice').addEventListener('click', () => {
      if (!recognition) {
        setStatus('Voice input is unavailable in this browser.', 'error');
        return;
      }
      recognition.start();
      setStatus('Voice capture started.');
    });
    document.getElementById('stopVoice').addEventListener('click', () => {
      if (!recognition) {
        return;
      }
      recognition.stop();
      setStatus('Voice capture stopped.');
    });
    document.getElementById('sendCommand').addEventListener('click', sendCommand);
    document.getElementById('interrupt').addEventListener('click', interrupt);
    document.getElementById('appendNewline').addEventListener('click', appendNewline);
    document.getElementById('refreshPane').addEventListener('click', loadPane);

    profileSelect.addEventListener('change', async () => {
      fillProfileForm(currentProfile());
      await loadRemoteState();
    });
    sessionSelect.addEventListener('change', () => {
      renderWindows();
      loadPane();
    });
    windowSelect.addEventListener('change', () => {
      renderPanes();
      loadPane();
    });
    paneSelect.addEventListener('change', () => {
      syncAliasInput();
      loadPane();
    });
    tokenInput.addEventListener('change', () => loadProfiles(getSelectedProfileName()));

    loadProfiles();
    setInterval(() => {
      if (getSelectedProfileName()) {
        loadPane();
      }
    }, 5000);
    setInterval(() => {
      if (getSelectedProfileName()) {
        loadRemoteState();
      }
    }, 15000);
  </script>
</body>
</html>
"""
