const translations = {
  'zh-CN': {
    navFeatures: '功能',
    navWorkflow: '链路',
    navQuickstart: '开始',
    navLinks: '链接',
    githubButton: 'GitHub',
    eyebrow: 'Mobile-first · SSH · tmux · AI Agents',
    heroTitle: '用手机远程控制你的 coding agents',
    heroText:
      'ClawDone 把手机浏览器、SSH 和远程 tmux pane 连接起来，让你随时查看 agent 状态、发送命令、中断任务、抓取输出，并跟踪轻量任务流。',
    primaryCta: '查看仓库',
    secondaryCta: '快速开始',
    pointOne: '连接远程 Linux 服务器上的 tmux pane',
    pointTwo: '在手机上调度 Codex 或其他 vibe-coding agents',
    pointThree: '内置任务、审计和风险策略',
    floatingLabelOne: 'Agent 状态',
    floatingValueOne: '3 个 pane 在线',
    floatingLabelTwo: '风险策略',
    floatingValueTwo: '危险命令执行前确认',
    statOne: '远程连接和目标管理',
    statTwo: '会话、窗口、pane 级别控制',
    statThree: '针对手机浏览器优化的控制界面',
    statFour: '任务证据、日志和轻量工作流',
    featuresEyebrow: 'What it does',
    featuresTitle: '为远程 AI 开发流程准备的控制面板',
    featuresLead: '不是完整远程桌面，而是一个更适合手机端的薄控制层：够快、够轻、够清晰。',
    featureOneTitle: '远程目标管理',
    featureOneText: '保存多个 SSH target，支持分组、标签、收藏、备注以及 SSH 覆盖参数。',
    featureTwoTitle: 'tmux 精准控制',
    featureTwoText: '列出 session、window、pane，把 pane 直接视为 agent endpoint 并发送命令或 Ctrl+C。',
    featureThreeTitle: '移动优先交互',
    featureThreeText: '支持命令模板、命令历史和浏览器语音转文字，减少手机输入摩擦。',
    featureFourTitle: '任务与审计',
    featureFourText: '把输出片段、摘要和状态变更留在任务记录里，方便回看与交付。',
    featureFiveTitle: '角色与风险策略',
    featureFiveText: '支持 Bearer Token、RBAC 和危险命令 allow / confirm / deny 策略。',
    featureSixTitle: '开放源码',
    featureSixText: 'Python 3.11+ 项目，适合作为个人远程 agent 控制台或二次开发基础。',
    workflowEyebrow: 'Workflow',
    workflowTitle: '从手机到 agent 的最短链路',
    workflowOneTitle: 'Mobile Browser',
    workflowOneText: '在手机浏览器打开 ClawDone 控制台。',
    workflowTwoTitle: 'ClawDone Service',
    workflowTwoText: 'Web 服务负责认证、任务状态和命令下发。',
    workflowThreeTitle: 'SSH + tmux',
    workflowThreeText: '通过 SSH 接管远程 tmux pane，发送命令并抓取输出。',
    workflowFourTitle: 'Coding Agent',
    workflowFourText: 'Codex 或其他 coding agents 接收任务并持续执行。',
    useCasesEyebrow: 'Use cases',
    useCasesTitle: '适合这些真实场景',
    useCaseOneTitle: '路上也能派活',
    useCaseOneText: '离开电脑后，仍可以从手机给远程 agent 安排实现任务、跑测试或继续修 bug。',
    useCaseTwoTitle: '多 agent 并行调度',
    useCaseTwoText: '为不同 pane 绑定别名，例如 backend-agent、research-agent、release-bot。',
    useCaseThreeTitle: '轻量任务交付',
    useCaseThreeText: '把 todo、证据和输出摘要保存在同一界面，方便回溯和状态同步。',
    quickstartEyebrow: 'Quick start',
    quickstartTitle: '三步跑起来',
    installTitle: '1. 安装',
    serveTitle: '2. 启动服务',
    openTitle: '3. 打开手机浏览器',
    linksEyebrow: 'Project links',
    linksTitle: '继续了解项目',
    repoLinkTitle: 'GitHub 仓库',
    repoLinkText: '查看源码、Issue 与发布记录',
    readmeLinkTitle: 'README',
    readmeLinkText: '阅读英文项目介绍和使用说明',
    zhReadmeLinkTitle: '中文文档',
    zhReadmeLinkText: '查看简体中文项目说明',
    footerText: 'ClawDone · 面向 SSH/tmux 托管 coding agents 的移动端控制面板。'
  },
  en: {
    navFeatures: 'Features',
    navWorkflow: 'Workflow',
    navQuickstart: 'Quick Start',
    navLinks: 'Links',
    githubButton: 'GitHub',
    eyebrow: 'Mobile-first · SSH · tmux · AI Agents',
    heroTitle: 'Control your coding agents from your phone',
    heroText:
      'ClawDone connects a mobile browser, SSH, and remote tmux panes so you can inspect agent state, send commands, interrupt work, capture output, and track lightweight task flow anywhere.',
    primaryCta: 'View on GitHub',
    secondaryCta: 'Quick Start',
    pointOne: 'Connect to tmux panes on remote Linux servers',
    pointTwo: 'Drive Codex and other vibe-coding agents on mobile',
    pointThree: 'Built-in tasks, audit trail, and risk policy',
    floatingLabelOne: 'Agent status',
    floatingValueOne: '3 panes online',
    floatingLabelTwo: 'Risk policy',
    floatingValueTwo: 'confirm before dangerous commands',
    statOne: 'Remote connection and target management',
    statTwo: 'Session, window, and pane level control',
    statThree: 'A control UI tuned for phone browsers',
    statFour: 'Task evidence, logs, and lightweight workflows',
    featuresEyebrow: 'What it does',
    featuresTitle: 'A focused control surface for remote AI development flows',
    featuresLead: 'Not a full remote desktop—just the lightweight mobile layer you need to monitor and steer long-running agents.',
    featureOneTitle: 'Remote target management',
    featureOneText: 'Save multiple SSH targets with groups, tags, favorites, notes, and per-target SSH overrides.',
    featureTwoTitle: 'Precise tmux control',
    featureTwoText: 'List sessions, windows, and panes, then treat each pane as an agent endpoint for commands or Ctrl+C.',
    featureThreeTitle: 'Mobile-first interaction',
    featureThreeText: 'Use command templates, command history, and browser speech-to-text to reduce mobile typing friction.',
    featureFourTitle: 'Tasks and audit trail',
    featureFourText: 'Keep snippets, summaries, and status transitions with the task so delivery and review stay visible.',
    featureFiveTitle: 'Roles and risk policy',
    featureFiveText: 'Support bearer tokens, RBAC, and allow / confirm / deny policies for dangerous commands.',
    featureSixTitle: 'Open source',
    featureSixText: 'A Python 3.11+ project ready for personal remote-agent control or downstream customization.',
    workflowEyebrow: 'Workflow',
    workflowTitle: 'The shortest path from your phone to an agent',
    workflowOneTitle: 'Mobile Browser',
    workflowOneText: 'Open the ClawDone control console in your phone browser.',
    workflowTwoTitle: 'ClawDone Service',
    workflowTwoText: 'The web service handles auth, task state, and command dispatch.',
    workflowThreeTitle: 'SSH + tmux',
    workflowThreeText: 'SSH reaches remote tmux panes to send commands and capture recent output.',
    workflowFourTitle: 'Coding Agent',
    workflowFourText: 'Codex or other coding agents receive work and keep running remotely.',
    useCasesEyebrow: 'Use cases',
    useCasesTitle: 'Built for real workflows like these',
    useCaseOneTitle: 'Dispatch work on the go',
    useCaseOneText: 'When you are away from your laptop, still assign implementation work, tests, or bug-fix tasks from your phone.',
    useCaseTwoTitle: 'Coordinate multiple agents',
    useCaseTwoText: 'Bind aliases such as backend-agent, research-agent, and release-bot to different panes.',
    useCaseThreeTitle: 'Deliver lightweight task updates',
    useCaseThreeText: 'Keep todos, evidence, and output summaries together so state and accountability stay clear.',
    quickstartEyebrow: 'Quick start',
    quickstartTitle: 'Get running in three steps',
    installTitle: '1. Install',
    serveTitle: '2. Start the service',
    openTitle: '3. Open your phone browser',
    linksEyebrow: 'Project links',
    linksTitle: 'Go deeper',
    repoLinkTitle: 'GitHub Repository',
    repoLinkText: 'Browse source, issues, and releases',
    readmeLinkTitle: 'README',
    readmeLinkText: 'Read the English introduction and usage docs',
    zhReadmeLinkTitle: 'Chinese Docs',
    zhReadmeLinkText: 'Open the Simplified Chinese project guide',
    footerText: 'ClawDone · A mobile-friendly control surface for SSH/tmux-hosted coding agents.'
  }
};

const languageButtons = document.querySelectorAll('[data-lang]');
const translatableNodes = document.querySelectorAll('[data-i18n]');

function applyLanguage(language) {
  const resolvedLanguage = translations[language] ? language : 'zh-CN';
  const dictionary = translations[resolvedLanguage];

  document.documentElement.lang = resolvedLanguage;
  document.title = resolvedLanguage === 'en'
    ? 'ClawDone · Mobile control surface for remote coding agents'
    : 'ClawDone · 面向远程 coding agents 的移动端控制台';

  translatableNodes.forEach((node) => {
    const key = node.dataset.i18n;
    if (dictionary[key]) {
      node.textContent = dictionary[key];
    }
  });

  languageButtons.forEach((button) => {
    button.classList.toggle('is-active', button.dataset.lang === resolvedLanguage);
  });

  localStorage.setItem('clawdone-language', resolvedLanguage);
}

const storedLanguage = localStorage.getItem('clawdone-language');
const browserLanguage = navigator.language.toLowerCase().startsWith('zh') ? 'zh-CN' : 'en';
applyLanguage(storedLanguage || browserLanguage);

languageButtons.forEach((button) => {
  button.addEventListener('click', () => applyLanguage(button.dataset.lang));
});
