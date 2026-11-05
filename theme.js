// Light/dark theme toggle, shared by the front page and the blog.
// The initial theme is set by a small inline script in <head> (before the CSS
// paints), from the saved choice or the system setting.
(() => {
  const KEY = 'cloud247-theme';
  const root = document.documentElement;
  const systemDark = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  const buttons = Array.from(document.querySelectorAll('.theme-toggle'));

  const labels = {
    no: { dark: 'Bytt til mørk modus', light: 'Bytt til lys modus' },
    en: { dark: 'Switch to dark mode', light: 'Switch to light mode' }
  };

  function saved() {
    try {
      const value = localStorage.getItem(KEY);
      return value === 'dark' || value === 'light' ? value : null;
    } catch (_) {
      return null;
    }
  }

  function updateButtons() {
    const lang = root.lang === 'en' ? 'en' : 'no';
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    buttons.forEach((button) => {
      button.setAttribute('aria-label', labels[lang][next]);
      button.title = labels[lang][next];
      button.setAttribute('aria-pressed', String(root.dataset.theme === 'dark'));
    });
  }

  function apply(theme) {
    root.dataset.theme = theme;
    updateButtons();
  }

  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem(KEY, theme); } catch (_) {}
      apply(theme);
    });
  });

  // Follow the system setting until the visitor picks a theme themselves
  if (systemDark && systemDark.addEventListener) {
    systemDark.addEventListener('change', (event) => {
      if (!saved()) apply(event.matches ? 'dark' : 'light');
    });
  }

  // The front page switches language by changing <html lang>; keep the labels in step
  new MutationObserver(updateButtons).observe(root, { attributes: true, attributeFilter: ['lang'] });

  apply(root.dataset.theme === 'dark' ? 'dark' : 'light');
})();
