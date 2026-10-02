(() => {
  const STORAGE_KEY = 'cloud247-language';
  const FAVORITES_KEY = 'cloud247-favorites';
  const supported = new Set(['no', 'en']);
  let currentLanguage = 'no';

  const metaDescriptions = {
    no: 'Cloud247 Cloud Toolbox: sjekk, overvåk og sikre domenet, e-posten og Microsoft-miljøet ditt.',
    en: 'Cloud247 Cloud Toolbox: check, monitor and secure your domain, email and Microsoft environment.'
  };

  const ogDescriptions = {
    no: 'Praktiske Cloud247-verktøy samlet på ett sted.',
    en: 'Practical Cloud247 tools in one place.'
  };

  const labels = {
    no: {
      favorite: (name) => `Favoritt: ${name}`,
      add: 'Legg til i favoritter',
      remove: 'Fjern fra favoritter',
      status: (count) => `Viser ${count} verktøy`
    },
    en: {
      favorite: (name) => `Favorite: ${name}`,
      add: 'Add to favorites',
      remove: 'Remove from favorites',
      status: (count) => `Showing ${count} ${count === 1 ? 'tool' : 'tools'}`
    }
  };

  const STAR_ICON = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"></path></svg>';

  const grid = document.querySelector('.tool-grid');
  const cards = grid ? Array.from(grid.querySelectorAll('.tool-card[data-tool]')) : [];
  const filterButtons = Array.from(document.querySelectorAll('.filter-chip[data-filter]'));
  const favoritesChip = document.querySelector('.filter-chip[data-filter="favorites"]');
  const filterStatus = document.getElementById('filter-status');
  const knownTools = new Set(cards.map((card) => card.dataset.tool));
  let activeFilter = 'all';
  let favorites = new Set();

  try {
    const saved = JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]');
    if (Array.isArray(saved)) favorites = new Set(saved.filter((id) => knownTools.has(id)));
  } catch (_) {}

  function decodeHtml(value) {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = value;
    return textarea.value;
  }

  function saveFavorites() {
    try { localStorage.setItem(FAVORITES_KEY, JSON.stringify(Array.from(favorites))); } catch (_) {}
  }

  function updateFavoriteLabels() {
    const text = labels[currentLanguage];
    cards.forEach((card) => {
      const button = card.querySelector('.favorite-button');
      if (!button) return;
      const isFavorite = favorites.has(card.dataset.tool);
      button.setAttribute('aria-label', text.favorite(card.dataset.name));
      button.setAttribute('aria-pressed', String(isFavorite));
      button.title = isFavorite ? text.remove : text.add;
    });
  }

  function updateStatus() {
    if (!filterStatus) return;
    const visible = cards.filter((card) => !card.hidden).length;
    filterStatus.textContent = labels[currentLanguage].status(visible);
  }

  function applyFilter() {
    cards.forEach((card) => {
      const categories = (card.dataset.categories || '').split(/\s+/);
      card.hidden = !(
        activeFilter === 'all' ||
        (activeFilter === 'favorites' && favorites.has(card.dataset.tool)) ||
        categories.includes(activeFilter)
      );
    });

    // A fixed card that would end up alone on the last row spans the full width instead
    const visible = cards.filter((card) => !card.hidden);
    cards.forEach((card) => {
      card.classList.toggle('is-wide', card.hasAttribute('data-fixed') && !card.hidden && visible.length % 2 === 1);
    });

    filterButtons.forEach((button) => {
      const active = button.dataset.filter === activeFilter;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', String(active));
    });

    updateStatus();
  }

  function renderFavorites() {
    const sorted = cards.slice().sort((a, b) => {
      // Fixed cards (the contact card) always stay last
      const fixedDiff = Number(a.hasAttribute('data-fixed')) - Number(b.hasAttribute('data-fixed'));
      if (fixedDiff) return fixedDiff;
      const favoriteDiff = Number(favorites.has(b.dataset.tool)) - Number(favorites.has(a.dataset.tool));
      return favoriteDiff || Number(a.dataset.order) - Number(b.dataset.order);
    });
    sorted.forEach((card) => {
      grid.appendChild(card);
      card.classList.toggle('is-favorite', favorites.has(card.dataset.tool));
    });

    if (favoritesChip) favoritesChip.hidden = favorites.size === 0;
    if (activeFilter === 'favorites' && favorites.size === 0) activeFilter = 'all';

    updateFavoriteLabels();
    applyFilter();
  }

  cards.forEach((card, index) => {
    const heading = card.querySelector('h2');
    if (!heading) return;
    card.dataset.order = String(index);
    card.dataset.name = heading.textContent.trim();
    if (card.hasAttribute('data-fixed')) return;

    const row = document.createElement('div');
    row.className = 'tool-title-row';
    heading.replaceWith(row);
    row.appendChild(heading);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'favorite-button';
    button.innerHTML = STAR_ICON;
    button.addEventListener('click', () => {
      const id = card.dataset.tool;
      if (favorites.has(id)) favorites.delete(id);
      else favorites.add(id);
      saveFavorites();
      renderFavorites();
      button.focus({ preventScroll: true });
    });
    row.appendChild(button);
  });

  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      activeFilter = button.dataset.filter;
      applyFilter();
    });
  });

  function setLanguage(language) {
    const lang = supported.has(language) ? language : 'no';
    currentLanguage = lang;
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

    updateFavoriteLabels();
    updateStatus();

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

  if (grid) renderFavorites();
  setLanguage(initialLanguage);
})();
