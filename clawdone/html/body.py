"""Static HTML body and shell markup."""

INDEX_BODY = """
</head>
<body>
  <div class="wrap">
    <nav class="view-switcher" aria-label="Page">
      <button class="view-chip active" type="button" data-view-button="dashboard" aria-current="page">Home</button>
      <button class="view-chip" type="button" data-view-button="chat">Work</button>
      <button class="view-chip" type="button" data-view-button="todo">Tasks</button>
      <button class="view-chip" type="button" data-view-button="delivery">Delivery</button>
      <button class="view-chip" type="button" data-view-button="auth">Settings</button>
    </nav>
    <div class="page-view active" id="view-dashboard">
    <section class="hero">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">
          <img class="brand-logo" src="/assets/logo.png" alt="ClawDone logo">
        </div>
        <div class="brand-copy">
          <div class="brand-kicker">Focused control</div>
          <h1>ClawDone</h1>
        </div>
      </div>
    </section>

    <section class="card grid">
      <div class="section-title"><h2>Overview</h2></div>
      <div class="stats-grid">
        <div class="kpi"><strong id="profileCount">0</strong><span>Targets</span></div>
        <div class="kpi"><strong id="onlineCount">0</strong><span>Online</span></div>
        <div class="kpi"><strong id="sessionCount">0</strong><span>Sessions</span></div>
        <div class="kpi"><strong id="paneCount">0</strong><span>Windows</span></div>
      </div>
      <div class="action-strip">
        <button class="secondary" id="refreshDashboard">Refresh</button>
        <button class="ghost" id="refreshState">Reload target</button>
      </div>
      <div id="status" class="status"></div>
    </section>

    <section class="workspace-grid">
      <details class="card grid fold fold-panel" data-fold-key="dashboard-targets" open>
        <summary><div class="fold-head"><strong>Targets</strong><span>Select a machine</span></div></summary>
        <div class="fold-body">
          <div>
            <label for="profileSelect">Saved target</label>
            <select id="profileSelect"></select>
          </div>
          <div id="targetList" class="list"></div>
          <div class="pagination" id="targetPagination"></div>
        </div>
      </details>

      <div class="panel-stack">
        <details class="card grid fold fold-panel" data-fold-key="dashboard-pane" open>
          <summary><div class="fold-head"><strong>Session & Window</strong><span>tmux target</span></div></summary>
          <div class="fold-body">
            <div class="grid-2">
              <div>
                <label for="session">Session</label>
                <select id="session"></select>
              </div>
              <div>
                <label for="window">Window</label>
                <select id="window"></select>
              </div>
            </div>
            <select id="pane" class="hidden-select"></select>
            <div class="grid-2">
              <div>
                <label for="agentAlias">Window alias</label>
                <input id="agentAlias" placeholder="backend-agent">
              </div>
              <div class="action-strip">
                <button class="secondary" id="saveAlias">Save alias</button>
                <button class="ghost" id="refreshPane">Refresh</button>
              </div>
            </div>
          </div>
        </details>
      </div>
    </section>
    </div>

    <div class="page-view" id="view-auth">
    <section class="card grid settings-page">
      <div class="section-title"><h2>Settings</h2></div>
      <div class="settings-shell">
        <details class="fold fold-panel" data-fold-key="settings-access" open>
          <summary><div class="fold-head"><strong>Access & View</strong><span>Token · pagination</span></div></summary>
          <div class="fold-body settings-card">
            <div class="settings-inputs">
              <div class="grid-2">
                <div>
                  <label for="token">Token</label>
                  <input id="token" type="password" placeholder="Optional">
                </div>
                <div>
                  <label for="paneLines">Pane lines</label>
                  <input id="paneLines" type="number" min="20" max="200" value="80">
                </div>
              </div>
              <div class="grid-3">
                <div>
                  <label for="targetPageSize">Targets / page</label>
                  <input id="targetPageSize" type="number" min="1" max="24" value="6">
                </div>
                <div>
                  <label for="historyPageSize">Messages / page</label>
                  <input id="historyPageSize" type="number" min="1" max="30" value="8">
                </div>
                <div>
                  <label for="todoPageSize">Todos / page</label>
                  <input id="todoPageSize" type="number" min="1" max="20" value="6">
                </div>
              </div>
            </div>
            <div class="settings-actions">
              <button class="primary" id="saveUiSettings">Save</button>
              <button class="ghost" id="resetUiSettings" type="button">Reset</button>
            </div>
          </div>
        </details>

        <details class="fold fold-panel" data-fold-key="settings-supervisor">
          <summary><div class="fold-head"><strong>ClawDone</strong><span>Automation</span></div></summary>
          <div class="fold-body settings-card">
            <input id="supervisorConfigId" type="hidden">
            <div class="grid-3">
              <div>
                <label for="supervisorName">Name</label>
                <input id="supervisorName" placeholder="Supervisor">
              </div>
              <div>
                <label for="supervisorModel">Model</label>
                <input id="supervisorModel" placeholder="gpt-4.1-mini">
              </div>
              <div>
                <label for="supervisorEnabled">Status</label>
                <div class="checkbox-row"><input id="supervisorEnabled" type="checkbox" checked><span>Enabled</span></div>
              </div>
            </div>
            <div class="grid-2">
              <div>
                <label for="supervisorBaseUrl">Base URL</label>
                <input id="supervisorBaseUrl" placeholder="https://api.openai.com/v1">
              </div>
              <div>
                <label for="supervisorApiKey">API key</label>
                <input id="supervisorApiKey" type="password" placeholder="sk-...">
              </div>
            </div>
            <div>
              <label for="supervisorApiKeyRef">Key ref</label>
              <input id="supervisorApiKeyRef" placeholder="env:KEY or file:~/.key">
            </div>
            <div class="settings-options">
              <div class="checkbox-row"><input id="supervisorCanDispatch" type="checkbox" checked><span>Dispatch</span></div>
              <div class="checkbox-row"><input id="supervisorCanReview" type="checkbox" checked><span>Review</span></div>
              <div class="checkbox-row"><input id="supervisorCanAccept" type="checkbox" checked><span>Accept</span></div>
            </div>
            <div class="settings-options">
              <div class="checkbox-row"><input id="supervisorAutoDispatch" type="checkbox" checked><span>Auto dispatch</span></div>
              <div class="checkbox-row"><input id="supervisorAutoReview" type="checkbox" checked><span>Auto review</span></div>
              <div class="checkbox-row"><input id="supervisorAutoAccept" type="checkbox" checked><span>Auto accept</span></div>
            </div>
            <div>
              <label for="supervisorSystemPrompt">Prompt</label>
              <textarea id="supervisorSystemPrompt" placeholder="Routing and review prompt"></textarea>
            </div>
            <div class="settings-actions">
              <button class="primary" id="saveSupervisorConfig">Save</button>
              <button class="secondary" id="loadSupervisorConfig">Reload</button>
              <button class="danger" id="deleteSupervisorConfig">Delete</button>
            </div>
            <div id="supervisorLoadState" class="status">No config loaded.</div>
          </div>
        </details>

        <details class="fold fold-panel" data-fold-key="settings-profile">
          <summary><div class="fold-head"><strong>Target Profile</strong><span>SSH</span></div></summary>
          <div class="fold-body settings-card">
            <div class="grid-3">
              <div>
                <label for="profileName">Name</label>
                <input id="profileName" placeholder="gpu-box">
              </div>
              <div>
                <label for="host">Host</label>
                <input id="host" placeholder="192.168.1.20">
              </div>
              <div>
                <label for="username">User</label>
                <input id="username" placeholder="ubuntu">
              </div>
            </div>
            <div class="grid-2">
              <div>
                <label for="password">Password</label>
                <input id="password" type="password" placeholder="Optional">
              </div>
              <div>
                <label for="keyFilename">SSH key</label>
                <input id="keyFilename" placeholder="~/.ssh/id_ed25519">
              </div>
            </div>
            <div class="settings-actions">
              <button class="primary" id="saveProfile">Save</button>
              <button class="secondary" id="testProfile">Test SSH</button>
              <button class="secondary" id="loadProfileState">Load tmux</button>
              <button class="danger" id="deleteProfile">Delete</button>
            </div>
            <details class="fold" data-fold-key="settings-profile-advanced-v2">
              <summary>Advanced</summary>
              <div class="fold-body">
                <div class="grid-3">
                  <div>
                    <label for="port">Port</label>
                    <input id="port" type="number" value="22">
                  </div>
                  <div>
                    <label for="profileGroup">Group</label>
                    <input id="profileGroup" placeholder="work">
                  </div>
                  <div>
                    <label for="profileTags">Tags</label>
                    <input id="profileTags" placeholder="gpu, research">
                  </div>
                </div>
                <div class="grid-2">
                  <div>
                    <label for="passwordRef">Password ref</label>
                    <input id="passwordRef" placeholder="env:PWD or file:~/.pwd">
                  </div>
                  <div>
                    <label for="tmuxBin">tmux</label>
                    <input id="tmuxBin" value="tmux">
                  </div>
                </div>
                <div>
                  <label for="profileDescription">Note</label>
                  <input id="profileDescription" placeholder="Research box">
                </div>
                <div class="grid-3">
                  <div>
                    <label for="hostKeyPolicy">Host key</label>
                    <select id="hostKeyPolicy">
                      <option value="">Default</option>
                      <option value="strict">strict</option>
                      <option value="accept-new">accept-new</option>
                      <option value="insecure">insecure</option>
                    </select>
                  </div>
                  <div>
                    <label for="sshTimeout">Connect timeout</label>
                    <input id="sshTimeout" type="number" min="0" placeholder="0">
                  </div>
                  <div>
                    <label for="sshCommandTimeout">Command timeout</label>
                    <input id="sshCommandTimeout" type="number" min="0" placeholder="0">
                  </div>
                </div>
                <div class="grid-2">
                  <div>
                    <label for="sshRetries">Retries</label>
                    <input id="sshRetries" type="number" min="0" placeholder="0">
                  </div>
                  <div>
                    <label for="sshRetryBackoffMs">Backoff ms</label>
                    <input id="sshRetryBackoffMs" type="number" min="0" placeholder="250">
                  </div>
                </div>
                <div class="checkbox-row"><input id="profileFavorite" type="checkbox"><span>Favorite</span></div>
              </div>
            </details>
          </div>
        </details>
      </div>
    </section>
    </div>

    <div hidden>
      <select id="templateSelect"></select>
      <input id="templateName">
      <select id="templateScope"><option value=""></option><option value="current">current</option></select>
      <button id="applyTemplate" type="button"></button>
      <button id="saveTemplate" type="button"></button>
      <button id="deleteTemplate" type="button"></button>
      <select id="historySelect"></select>
      <div id="historyList"></div>
      <div id="historyPagination"></div>
      <button id="applyHistory" type="button"></button>
      <button id="clearHistory" type="button"></button>
      <input id="todoTitle" type="hidden">
      <input id="todoPriority" type="hidden" value="medium">
      <input id="todoAssignee" type="hidden">
      <input id="todoStatus" type="hidden" value="todo">
      <input id="todoProgressNote" type="hidden">
      <textarea id="todoEvidence"></textarea>
      <input id="todoTemplateName" type="hidden">
      <pre id="todoEvidenceList">No evidence yet.</pre>
      <select id="auditSelect"></select>
    </div>

    <div class="page-view" id="view-chat">
    <section class="chatbot-layout">
      <aside class="chat-sidebar">
        <div class="chatbot-sidebar-header">
          <h2>Work</h2>
        </div>
        <div class="chatbot-agent-card">
          <div class="chatbot-sidebar-title">Active agent</div>
          <strong id="currentAgentLabel">No window selected</strong>
          <span id="currentAgentHint">Select a window.</span>
        </div>
        <div class="chatbot-sidebar-panel">
          <div class="chatbot-sidebar-title">Agents</div>
          <div id="workerList" class="worker-strip"></div>
        </div>
        <div class="chatbot-sidebar-panel">
          <label for="chatSessionSelect">Session</label>
          <select id="chatSessionSelect"></select>
          <div class="hint" id="chatConversationHint">Choose a thread to focus the feed.</div>
        </div>
        <div class="chatbot-sidebar-panel">
          <div class="chatbot-sidebar-title">Threads</div>
          <div id="conversationList" class="thread-list"></div>
        </div>
      </aside>

      <section class="chat-main">
        <div class="chat-main-header">
          <div>
            <h2>Command stream</h2>
            <span class="hint" id="selectedPaneLabel">No window selected</span>
          </div>
          <div class="chat-main-actions">
            <button class="ghost" id="copyTargetLabel">Copy</button>
            <button class="secondary" id="refreshChatPane">Refresh</button>
            <button class="danger" id="interrupt">Interrupt</button>
          </div>
        </div>
        <div id="chatFeed" class="chat-feed"></div>
        <pre id="paneOutput" style="display:none">Choose a target and window first.</pre>
        <div class="composer">
          <div class="composer-head">
            <label for="command">Message</label>
          </div>
          <textarea id="command" class="chat-input" placeholder="Describe the next step for the selected agent. Example: analyze the bug, patch it, run tests, then summarize the changes."></textarea>
          <div class="composer-actions">
            <div class="row-inline">
              <button class="primary" id="sendCommand">Send</button>
              <button class="ghost" id="appendNewline">New line</button>
              <button class="primary" id="startVoice">Start voice</button>
              <button class="secondary" id="stopVoice">Stop voice</button>
            </div>
          </div>
        </div>
      </section>
    </section>
    </div>

    <div class="page-view" id="view-todo">
    <section class="todo-shell">
      <section class="card checklist-compose">
        <div class="section-title"><h2>Tasks</h2></div>
        <div class="checklist-stage">
          <strong id="todoMeta">No tasks yet.</strong>
        </div>
        <div>
          <label for="todoDetail">Tasks</label>
          <textarea id="todoDetail" placeholder="- Fix login 500 error
- Add a regression test
- Summarize the changes"></textarea>
        </div>
        <div class="checklist-toolbar">
          <div class="checklist-actions">
            <button class="primary" id="createTodo">Save checklist</button>
            <button class="ghost" id="refreshTodos">Refresh checklist</button>
            <button class="danger" id="clearCompletedTodos">Clear completed</button>
            <button class="danger" id="clearAllTodos">Clear all tasks</button>
            <button class="ghost" id="selectAllTodos">Select all</button>
          </div>
        </div>
        <details class="fold fold-panel" data-fold-key="todo-list" open>
          <summary><div class="fold-head"><strong>Task list</strong><span>Current agent</span></div></summary>
          <div class="fold-body">
            <select id="todoSelect" class="hidden-select"></select>
            <div id="todoBoard" class="todo-board"></div>
            <div class="pagination" id="todoPagination" style="display:none"></div>
          </div>
        </details>
        <details class="fold fold-panel" data-fold-key="todo-gantt">
          <summary><div class="fold-head"><strong>Timeline</strong><span>Gantt view</span></div></summary>
          <div class="fold-body">
            <div id="todoGantt" class="gantt-container"></div>
          </div>
        </details>
      </section>

    </section>
    </div>

    <div class="page-view" id="view-delivery">
    <section class="delivery-shell">
      <section class="card grid delivery-page">
        <div class="section-title"><h2>Delivery</h2></div>
        <div class="delivery-head">
          <strong id="deliveryAgentLabel">No target selected</strong>
          <span class="hint" id="deliveryTodoMeta">No result yet.</span>
          <span class="hint" id="deliveryAgentHint" hidden></span>
        </div>
        <details class="fold fold-panel" data-fold-key="delivery-summary" open>
          <summary><div class="fold-head"><strong>Result</strong><span>Final outcome</span></div></summary>
          <div class="fold-body">
            <pre id="deliveryResult">No result yet.</pre>
          </div>
        </details>
        <details class="fold fold-panel" data-fold-key="delivery-output">
          <summary><div class="fold-head"><strong>Evidence</strong><span>Optional</span></div></summary>
          <div class="fold-body">
            <pre id="deliveryEvidence">No evidence yet.</pre>
          </div>
        </details>
      </section>
      <div hidden>
        <pre id="deliveryTimeline">No result yet.</pre>
        <pre id="deliveryAudit">No audit events.</pre>
        <pre id="deliveryPaneOutput">Choose a target and window first.</pre>
      </div>
    </section>
    </div>
  </div>

  """
