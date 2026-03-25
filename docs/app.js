const translations = {
  'zh-CN': {
    githubButton: 'GitHub',
    eyebrow: 'Phone · SSH · tmux · Agents',
    heroTitle: '更轻的远程控制台',
    heroText: '给 coding agents 派活。',
    primaryCta: 'GitHub',
    secondaryCta: '文档',
    pointOne: 'SSH',
    pointTwo: 'tmux',
    pointThree: 'Mobile'
  },
  en: {
    githubButton: 'GitHub',
    eyebrow: 'Phone · SSH · tmux · Agents',
    heroTitle: 'A lighter remote console',
    heroText: 'Dispatch work to coding agents.',
    primaryCta: 'GitHub',
    secondaryCta: 'Docs',
    pointOne: 'SSH',
    pointTwo: 'tmux',
    pointThree: 'Mobile'
  }
};

const languageButtons = document.querySelectorAll('[data-lang]');
const translatableNodes = document.querySelectorAll('[data-i18n]');
const heroTitleNode = document.querySelector('[data-i18n="heroTitle"]');
const heroTextNode = document.querySelector('[data-i18n="heroText"]');
const searchParams = new URLSearchParams(window.location.search);

function getOverrides() {
  return {
    title: searchParams.get('title')?.trim(),
    headline: searchParams.get('headline')?.trim(),
    tagline: searchParams.get('tagline')?.trim()
  };
}

function applyOverrides(overrides) {
  if (overrides.headline && heroTitleNode) {
    heroTitleNode.textContent = overrides.headline;
  }

  if (overrides.tagline && heroTextNode) {
    heroTextNode.textContent = overrides.tagline;
  }

  document.title = overrides.title || 'ClawDone';
}

function applyLanguage(language) {
  const resolvedLanguage = translations[language] ? language : 'zh-CN';
  const dictionary = translations[resolvedLanguage];

  document.documentElement.lang = resolvedLanguage;

  translatableNodes.forEach((node) => {
    const key = node.dataset.i18n;
    if (dictionary[key]) node.textContent = dictionary[key];
  });

  applyOverrides(getOverrides());

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
