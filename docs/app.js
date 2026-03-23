const translations = {
  'zh-CN': {
    navFeatures: '功能',
    navQuickstart: '开始',
    navLinks: '链接',
    githubButton: 'GitHub',
    eyebrow: 'Phone · SSH · tmux · Agents',
    heroTitle: '用手机控制远程 coding agents',
    heroText: '一个更轻的远程控制台。',
    primaryCta: '查看仓库',
    secondaryCta: '快速开始',
    pointOne: 'SSH',
    pointTwo: 'tmux',
    pointThree: 'Mobile',
    statOne: '远程连接',
    statTwo: 'Pane 控制',
    statThree: '更少输入',
    statFour: '轻量跟踪',
    featuresEyebrow: 'Features',
    featuresTitle: '只保留最有用的部分',
    featureOneTitle: '多目标',
    featureOneText: '多个 SSH 服务器。',
    featureTwoTitle: '多 Pane',
    featureTwoText: '多个 agent 分开控制。',
    featureThreeTitle: '更快',
    featureThreeText: '模板、历史、语音输入。',
    quickstartEyebrow: 'Quick start',
    quickstartTitle: '三步开始',
    installTitle: '1. 安装',
    serveTitle: '2. 启动',
    openTitle: '3. 打开',
    linksEyebrow: 'Links',
    linksTitle: '更多信息',
    repoLinkTitle: 'GitHub',
    repoLinkText: '源码',
    readmeLinkTitle: 'README',
    readmeLinkText: 'English',
    zhReadmeLinkTitle: '中文文档',
    zhReadmeLinkText: '简体中文',
    footerText: 'ClawDone · Mobile control for remote coding agents.'
  },
  en: {
    navFeatures: 'Features',
    navQuickstart: 'Quick Start',
    navLinks: 'Links',
    githubButton: 'GitHub',
    eyebrow: 'Phone · SSH · tmux · Agents',
    heroTitle: 'Control remote coding agents from your phone',
    heroText: 'A lighter remote console.',
    primaryCta: 'View on GitHub',
    secondaryCta: 'Quick Start',
    pointOne: 'SSH',
    pointTwo: 'tmux',
    pointThree: 'Mobile',
    statOne: 'Remote access',
    statTwo: 'Pane control',
    statThree: 'Less typing',
    statFour: 'Lightweight tasks',
    featuresEyebrow: 'Features',
    featuresTitle: 'Only the useful parts',
    featureOneTitle: 'Multi-target',
    featureOneText: 'Multiple SSH servers.',
    featureTwoTitle: 'Multi-pane',
    featureTwoText: 'Control each agent separately.',
    featureThreeTitle: 'Faster',
    featureThreeText: 'Templates, history, and voice input.',
    quickstartEyebrow: 'Quick start',
    quickstartTitle: 'Start in three steps',
    installTitle: '1. Install',
    serveTitle: '2. Start',
    openTitle: '3. Open',
    linksEyebrow: 'Links',
    linksTitle: 'Learn more',
    repoLinkTitle: 'GitHub',
    repoLinkText: 'Source',
    readmeLinkTitle: 'README',
    readmeLinkText: 'English',
    zhReadmeLinkTitle: 'Chinese Docs',
    zhReadmeLinkText: 'Simplified Chinese',
    footerText: 'ClawDone · Mobile control for remote coding agents.'
  }
};

const languageButtons = document.querySelectorAll('[data-lang]');
const translatableNodes = document.querySelectorAll('[data-i18n]');

function applyLanguage(language) {
  const resolvedLanguage = translations[language] ? language : 'zh-CN';
  const dictionary = translations[resolvedLanguage];

  document.documentElement.lang = resolvedLanguage;
  document.title = resolvedLanguage === 'en'
    ? 'ClawDone · Mobile control for coding agents'
    : 'ClawDone · 用手机控制远程 coding agents';

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
