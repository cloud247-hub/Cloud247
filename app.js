(() => {
  const STORAGE_KEY = 'cloud247-language';
  const supported = new Set(['no', 'en']);

  const metaDescriptions = {
    no: 'Cloud247 Cloud Toolbox samler gratis verkt\u00f8y for Microsoft 365, domenesikkerhet, e-postsikkerhet, sikker fildeling og Intune.',
    en: 'Cloud247 Cloud Toolbox brings together free tools for Microsoft 365, domain security, email security, secure file sharing and Intune.'
  };

  const ogDescriptions = {
    no: 'Praktiske Cloud247-verkt\u00f8y samlet p\u00e5 ett sted.',
    en: 'Practical Cloud247 tools in one place.'
  };

  function decodeHtml(value) {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = value;
    return textarea.value;
  }

  function setLanguage(language) {
    const lang = supported.has(language) ? language : 'no';
    document.documentElement.lang = lang;

    document.querySelectorAll('[data-no][data-en]').forEach((element) => {
      const value = element.dataset[lang];
      if (value !== undefined) element.textContent = decodeHtml(value);
    });

    document.querySelectorAll('[data-aria-no][data-aria-en]').forEach((element) => {
      const value = lang === 'en' ? element.dataset.ariaEn : element.dataset.ariaNo;
      if (value !== undefined) element.setAttribute('aria-label', decodeHtml(value));
    });

    document.querySelectorAll('.language-button').forEach((button) => {
      const active = button.dataset.language === lang;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', String(active));
    });

    const meta = document.getElementById('meta-description');
    const og = document.getElementById('og-description');
    if (meta) meta.setAttribute('content', metaDescriptions[lang]);
    if (og) og.setAttribute('content', ogDescriptions[lang]);

    try { localStorage.setItem(STORAGE_KEY, lang); } catch (_) {}
  }

  let initialLanguage = 'no';
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (supported.has(saved)) initialLanguage = saved;
  } catch (_) {}

  document.querySelectorAll('.language-button').forEach((button) => {
    button.addEventListener('click', () => setLanguage(button.dataset.language));
  });

  const year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  setLanguage(initialLanguage);
})();
