const $ = (id) => document.getElementById(id);
const pageSize = 24;
const storageKey = 'coolcode-recallradar-watch-v1';
const labels = { TC: 'Transport Canada', CFIA: 'Canadian Food Inspection Agency', HC: 'Health Canada' };
const transportLink = 'https://tc.canada.ca/en/road-transportation/defects-recalls-vehicles-tires-child-car-seats';
const format = new Intl.NumberFormat('en-CA');
const normalized = (text) => text.toLowerCase().normalize('NFKD').replace(/\p{M}|['’]/gu, '').replace(/[^\p{L}\d]+/gu, ' ').trim();
let items;
let page = 0;
let saved = [];

try {
  const restored = JSON.parse(localStorage.getItem(storageKey) || '[]');
  if (Array.isArray(restored)) saved = restored.filter((item) => typeof item === 'string' && item.length <= 150).slice(0, 20);
} catch {}

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function button(label, action, accessibleName) {
  const result = node('button', label);
  result.type = 'button';
  if (accessibleName) result.setAttribute('aria-label', accessibleName);
  result.addEventListener('click', action);
  return result;
}

function filters() {
  return { query: normalized($('query').value).split(' ').filter(Boolean),
    issuer: $('issuer').value, archived: $('archive').checked };
}

function matches(item, { query, issuer, archived }) {
  if (!archived && item.archived) return false;
  if (issuer === 'other' && (item.org === 'TC' || item.org === 'CFIA')) return false;
  if (issuer && issuer !== 'other' && issuer !== item.org) return false;
  return query.every((term) => item.search.includes(term));
}

function notice(item) {
  const article = node('article', '', 'card');
  const headline = node('h3');
  const link = node('a', item.title);
  link.href = item.url || transportLink;
  headline.append(link);
  const details = [labels[item.org] || item.org,
    item.updated && `Updated ${item.updated}`, item.archived && 'Archived',
    item.category, item.number && `Recall ${item.number}`].filter(Boolean);
  article.append(headline, node('p', details.join(' · '), 'meta'));
  if (item.product) article.append(node('p', item.product));
  if (item.issue) article.append(node('p', item.issue, 'muted'));
  if (!item.url) article.append(node('p', 'Use the recall number to look up the notice in the official vehicle recall search.', 'muted'));
  if (item.transport) {
    const { vehicles, types, categories, date } = item.transport;
    const more = node('details');
    more.append(node('summary', vehicles.length ? `Vehicle details · ${format.format(vehicles.length)} listed combinations` : 'Vehicle details'));
    const note = [date && `Recall date ${date}`, ...types, ...categories].filter(Boolean).join(' · ');
    if (note) more.append(node('p', note, 'muted'));
    if (vehicles.length) {
      const list = node('ul');
      for (const vehicle of vehicles) list.append(node('li', vehicle.filter(Boolean).join(' ')));
      more.append(list);
    }
    article.append(more);
  }
  return article;
}

function render() {
  const current = filters();
  const term = $('query').value.trim();
  $('save').disabled = !current.query.length || saved.includes(term) || saved.length >= 20;
  if (!items) return;
  const matching = items.filter((item) => matches(item, current));
  const totalPages = Math.ceil(matching.length / pageSize);
  page = Math.min(page, Math.max(0, totalPages - 1));
  const start = page * pageSize;
  $('items').replaceChildren(...matching.slice(start, start + pageSize).map(notice));
  $('status').textContent = `${format.format(matching.length)} matching notices`;
  if (!matching.length) $('items').append(node('p', 'No notices match the current terms and filters.', 'muted'));
  $('page').textContent = totalPages ? `Page ${format.format(page + 1)} of ${format.format(totalPages)}` : '';
  $('back').disabled = page === 0;
  $('next').disabled = page + 1 >= totalPages;
}

function displayTerms() {
  $('watchlist').hidden = saved.length === 0;
  $('saved').replaceChildren(...saved.map((term) => {
    const item = node('li', '', 'saved-term');
    item.append(button(term, () => {
      $('query').value = term;
      $('issuer').value = '';
      $('archive').checked = false;
      page = 0;
      render();
    }), button('×', () => {
      saved = saved.filter((name) => name !== term);
      storeTerms();
    }, `Remove ${term}`));
    return item;
  }));
}

function storeTerms() {
  let storageUnavailable = false;
  try { localStorage.setItem(storageKey, JSON.stringify(saved)); }
  catch { storageUnavailable = true; }
  displayTerms();
  render();
  if (storageUnavailable) $('status').textContent = 'Saved search terms are available for this tab. This browser could not store them.';
}

function update() {
  page = 0;
  render();
}

$('search').addEventListener('submit', (event) => { event.preventDefault(); update(); });
$('query').addEventListener('input', update);
$('issuer').addEventListener('change', update);
$('archive').addEventListener('change', update);
$('save').addEventListener('click', () => {
  const term = $('query').value.trim();
  if (normalized(term) && !saved.includes(term) && saved.length < 20) {
    saved.push(term);
    storeTerms();
  }
});
$('reset').addEventListener('click', () => {
  $('search').reset();
  $('archive').checked = false;
  update();
  $('query').focus();
});
$('back').addEventListener('click', () => { page--; render(); });
$('next').addEventListener('click', () => { page++; render(); });
displayTerms();

async function loadSnapshot() {
  if (typeof DecompressionStream === 'function') {
    const response = await fetch('./notices.json.gz');
    if (response.ok && response.body) {
      return new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).json();
    }
  }
  const response = await fetch('./notices.json');
  if (!response.ok) throw new Error('Snapshot unavailable');
  return response.json();
}

try {
  const snapshot = await loadSnapshot();
  items = snapshot.rows.map((item) => ({
    ...item, search: normalized([item.title, item.product, item.issue, item.number, item.category,
      ...(item.transport?.vehicles.flat() ?? [])].filter(Boolean).join(' ')),
  }));
  $('updated').textContent = `Snapshot built ${snapshot.built}. ${format.format(snapshot.matched)} notices include matched vehicle details. Latest update in the vehicle feed ${snapshot.transportUpdated || 'unavailable'}.`;
  render();
} catch {
  $('status').textContent = 'The snapshot could not be loaded. Try reloading or open the official sources below.';
}
