const NAV_ITEMS = [
  ['today', 'Today'],
  ['clients', 'Clients'],
  ['opportunities', 'Opportunities'],
  ['knowledge', 'Knowledge'],
  ['operations', 'Operations'],
];

const state = {
  data: null,
  route: location.hash.slice(1) || 'today',
  selectedClientId: 'client-lim',
  query: '',
  messages: [],
  liveMode: false,
};

const app = document.querySelector('#app');
const nav = document.querySelector('#primary-nav');
const toast = document.querySelector('#toast');

const escapeHtml = (value = '') => String(value).replace(/[&<>'"]/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
}[character]));

const clientById = (id) => state.data.clients.find((client) => client.id === id);

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  window.setTimeout(() => toast.classList.remove('show'), 2600);
}

function pageHeading(eyebrow, title, description, action = '') {
  return `<div class="page-heading"><div><p class="eyebrow">${eyebrow}</p><h1>${title}</h1><p>${description}</p></div>${action || `<span class="as-of">As of 08:30 SGT</span>`}</div>`;
}

function renderNav() {
  nav.innerHTML = NAV_ITEMS.map(([id, label]) => `<button class="nav-button ${state.route === id ? 'active' : ''}" data-route="${id}" type="button">${label}</button>`).join('');
  nav.querySelectorAll('[data-route]').forEach((button) => button.addEventListener('click', () => {
    location.hash = button.dataset.route;
  }));
}

function renderMetrics() {
  return `<section class="metric-grid" aria-label="Portfolio metrics">${state.data.metrics.map((metric) => `<article class="metric ${metric.tone}"><div class="metric-label">${metric.label}</div><div class="metric-value">${metric.value}</div><div class="metric-change">${metric.change}</div></article>`).join('')}</section>`;
}

function renderToday() {
  const topOpportunities = state.data.opportunities.slice(0, 3);
  app.innerHTML = `<div class="page">
    ${pageHeading('Wednesday, 12 August', `Good morning, ${state.data.rm.name.split(' ')[0]}`, 'Your day is organised around four client needs and one compliance priority.')}
    <section class="panel briefing"><div class="panel-body"><div class="briefing-copy"><h2>Morning portfolio pulse</h2><p>One maturity conversation is ready for today's meeting, a client profile refresh is approaching, and two proactive service windows opened overnight. The plan below keeps mandatory checks ahead of outreach.</p></div><div class="briefing-stats"><div class="briefing-stat"><strong>5</strong><span>planned actions</span></div><div class="briefing-stat"><strong>1h 45m</strong><span>estimated time saved</span></div></div></div></section>
    ${renderMetrics()}
    <div class="today-grid">
      <section class="panel"><div class="panel-header section-heading"><div><h2>Today's plan</h2><p>Sequenced around client commitments and required checks</p></div><button class="secondary-button" data-action="reset-day" type="button">Reset demo</button></div><div class="panel-body agenda-list">${state.data.agenda.map((item) => `<div class="agenda-item ${item.status}"><span class="agenda-time">${item.time}</span><span class="agenda-marker"></span><div><div class="agenda-title">${item.title}</div><div class="agenda-type">${item.type}</div></div><span class="agenda-status">${item.status}</span></div>`).join('')}</div></section>
      <section><div class="section-heading"><div><h2>Priority needs</h2><p>Evidence-backed, human-reviewed</p></div></div><div class="priority-list">${topOpportunities.map((opportunity) => { const client = clientById(opportunity.clientId); return `<article class="priority-card" data-open-opportunity="${opportunity.id}" tabindex="0"><div class="priority-top"><div><span class="priority-client">${client.name} · ${opportunity.priority}</span><h3>${opportunity.title}</h3></div><div class="score">${opportunity.confidence}<small>confidence</small></div></div><div class="priority-meta"><span>${opportunity.value}</span><span class="chip">${opportunity.type}</span></div></article>`; }).join('')}</div></section>
    </div>
  </div>`;
  bindSharedActions();
  document.querySelectorAll('[data-open-opportunity]').forEach((card) => {
    const open = () => { location.hash = `opportunities`; sessionStorage.setItem('openOpportunity', card.dataset.openOpportunity); };
    card.addEventListener('click', open);
    card.addEventListener('keydown', (event) => { if (event.key === 'Enter') open(); });
  });
}

function filteredClients() {
  const query = state.query.trim().toLowerCase();
  if (!query) return state.data.clients;
  return state.data.clients.filter((client) => [client.name, client.segment, client.household, ...client.products].join(' ').toLowerCase().includes(query));
}

function clientDetail(client) {
  if (!client) return '<div class="panel empty">Select a client to view their context.</div>';
  return `<section class="panel client-detail"><div class="client-hero"><div class="client-name"><span class="client-initials">${client.initials}</span><div><h2>${client.name}</h2><p>${client.segment} · ${client.household}</p></div></div><button class="primary-button" data-client-opportunities="${client.id}" type="button">View opportunities</button></div><div class="detail-grid"><div class="detail-cell"><span>Assets under care</span><strong>${client.assets}</strong></div><div class="detail-cell"><span>Risk profile</span><strong>${client.riskProfile}</strong></div><div class="detail-cell"><span>Profile status</span><strong>${client.kycStatus}</strong></div><div class="detail-cell"><span>Contact preference</span><strong>${client.contactPreference}</strong></div><div class="detail-cell"><span>Consent</span><strong>${client.consent}</strong></div><div class="detail-cell"><span>Next meeting</span><strong>${client.nextMeeting}</strong></div></div><div class="detail-section"><h3>Relationship products</h3><div class="tag-list">${client.products.map((product) => `<span class="tag">${product}</span>`).join('')}</div></div><div class="detail-section"><h3>Signals requiring RM judgement</h3><ul class="signal-list">${client.signals.map((signal) => `<li>${signal}</li>`).join('')}</ul></div><div class="detail-section"><h3>Latest interaction</h3><p class="detail-copy">${client.recentInteraction}</p></div></section>`;
}

function renderClients() {
  const clients = filteredClients();
  if (!clients.some((client) => client.id === state.selectedClientId) && clients.length) state.selectedClientId = clients[0].id;
  const selected = clients.find((client) => client.id === state.selectedClientId);
  app.innerHTML = `<div class="page">${pageHeading('Relationship context', 'Clients', 'A single synthetic view of household needs, interactions, consent, and suitability context.')}<div class="toolbar"><input id="client-search" class="search" type="search" value="${escapeHtml(state.query)}" placeholder="Search clients, segments, or products" aria-label="Search clients"><span class="as-of">${clients.length} of ${state.data.clients.length} clients</span></div><div class="client-layout"><div class="client-list">${clients.map((client) => `<button class="client-row ${client.id === state.selectedClientId ? 'active' : ''}" data-client="${client.id}" type="button"><span class="client-initials">${client.initials}</span><span><strong>${client.name}</strong><small>${client.segment}</small></span><span class="client-assets">${client.assets}</span></button>`).join('') || '<div class="empty">No clients match this search.</div>'}</div>${clientDetail(selected)}</div></div>`;
  document.querySelector('#client-search').addEventListener('input', (event) => { state.query = event.target.value; renderClients(); document.querySelector('#client-search').focus(); });
  document.querySelectorAll('[data-client]').forEach((button) => button.addEventListener('click', () => { state.selectedClientId = button.dataset.client; renderClients(); }));
  document.querySelector('[data-client-opportunities]')?.addEventListener('click', (event) => { sessionStorage.setItem('filterClient', event.currentTarget.dataset.clientOpportunities); location.hash = 'opportunities'; });
}

function renderOpportunities() {
  const filterClient = sessionStorage.getItem('filterClient');
  const opportunities = filterClient ? state.data.opportunities.filter((item) => item.clientId === filterClient) : state.data.opportunities;
  const filterName = filterClient ? clientById(filterClient)?.name : null;
  const requestedOpen = sessionStorage.getItem('openOpportunity');
  app.innerHTML = `<div class="page">${pageHeading('Human-reviewed recommendations', 'Opportunities', filterName ? `Showing needs for ${filterName}.` : 'Prioritised by urgency, evidence quality, and expected client value.', `<button class="secondary-button" id="clear-filter" type="button">${filterClient ? 'Show all opportunities' : 'Refresh evidence'}</button>`)}<div class="opportunity-list">${opportunities.map((opportunity, index) => { const client = clientById(opportunity.clientId); const isOpen = requestedOpen === opportunity.id || (!requestedOpen && index === 0); return `<article class="opportunity ${isOpen ? 'open' : ''}" data-opportunity="${opportunity.id}"><button class="opportunity-summary" type="button" aria-expanded="${isOpen}"><span class="opportunity-rank">${String(index + 1).padStart(2, '0')}</span><span><span class="priority-client">${client.name} · ${opportunity.priority}</span><h3>${opportunity.title}</h3><span class="opportunity-sub">${opportunity.summary}</span></span><span class="opportunity-value"><strong>${opportunity.value}</strong><span>${opportunity.channel} · ${opportunity.time}</span></span><span class="confidence">${opportunity.confidence}%<span>confidence</span></span><span class="chevron">⌄</span></button><div class="opportunity-detail"><div><h3>Why this deserves attention</h3><p class="detail-copy">${opportunity.summary}</p><div class="detail-label">Evidence used</div><div class="tag-list">${opportunity.evidence.map((item) => `<span class="tag">${item}</span>`).join('')}</div><div class="detail-label">Mandatory checks</div><ul class="check-list">${opportunity.checks.map((item) => `<li>${item}</li>`).join('')}</ul></div><div><h3>Suggested opening</h3><div class="draft">“${opportunity.opening}”</div><div class="detail-label">Recommended contact</div><p class="detail-copy"><strong>${opportunity.channel}</strong><br>${opportunity.time}</p><div class="action-row"><button class="primary-button" data-complete="${opportunity.id}" type="button">Mark prepared</button><button class="secondary-button" data-draft="${opportunity.id}" type="button">Edit draft</button></div></div></div></article>`; }).join('')}</div></div>`;
  sessionStorage.removeItem('openOpportunity');
  document.querySelector('#clear-filter').addEventListener('click', () => { sessionStorage.removeItem('filterClient'); renderOpportunities(); });
  document.querySelectorAll('.opportunity-summary').forEach((button) => button.addEventListener('click', () => { const item = button.closest('.opportunity'); item.classList.toggle('open'); button.setAttribute('aria-expanded', item.classList.contains('open')); }));
  document.querySelectorAll('[data-complete]').forEach((button) => button.addEventListener('click', () => { button.textContent = 'Prepared'; button.disabled = true; showToast('Preparation recorded in the demo session.'); }));
  document.querySelectorAll('[data-draft]').forEach((button) => button.addEventListener('click', () => showToast('Draft editing will connect to the shared AI backend in the next slice.')));
}

function localAnswer(question) {
  const words = question.toLowerCase().split(/[^a-z0-9-]+/).filter((word) => word.length > 2);
  let best = null;
  let score = 0;
  state.data.knowledge.forEach((entry) => {
    const candidate = entry.keywords.reduce((total, keyword) => total + (question.toLowerCase().includes(keyword) ? 2 : 0), 0) + words.filter((word) => entry.title.toLowerCase().includes(word)).length;
    if (candidate > score) { best = entry; score = candidate; }
  });
  return best && score > 0 ? { text: best.answer, citation: `${best.source} [${best.id}]` } : { text: 'I cannot answer that from the approved demonstration knowledge. Please consult the relevant product, compliance, or operations owner before communicating with a client.', citation: 'No approved source found · escalation required' };
}

function renderKnowledge() {
  const suggestions = ['What should I check before a fixed deposit matures?', 'Can I discuss investments before a KYC refresh?', 'How should I contact a client with a recorded preference?', 'What information is needed for a cross-border transfer?'];
  const welcome = state.messages.length ? '' : `<div class="message assistant"><strong>Frontier Knowledge</strong>Ask about approved demonstration procedures. Answers are grounded in the fictional knowledge set and include a citation.</div>`;
  app.innerHTML = `<div class="page">${pageHeading('Grounded internal assistance', 'Knowledge', 'Answers stay within approved fictional guidance and escalate when a source is unavailable.')}<div class="knowledge-layout"><section class="panel chat-panel"><div id="chat-stream" class="chat-stream">${welcome}${state.messages.map((message) => `<div class="message ${message.role}">${message.role === 'assistant' ? '<strong>Frontier Knowledge</strong>' : ''}${escapeHtml(message.text)}${message.citation ? `<span class="citation">${escapeHtml(message.citation)}</span>` : ''}</div>`).join('')}</div><form id="chat-form" class="chat-input"><input id="chat-question" autocomplete="off" placeholder="Ask about a procedure or client preparation step" aria-label="Ask Frontier Knowledge"><button class="primary-button" type="submit">Ask</button></form></section><aside><div class="section-heading"><div><h2>Suggested questions</h2><p>Designed for this synthetic scenario</p></div></div><div class="suggestion-list">${suggestions.map((question) => `<button class="suggestion" data-question="${question}" type="button">${question}</button>`).join('')}</div><div class="boundary-note"><strong>Human review required.</strong><br>Do not communicate generated output to a client without checking the current approved source and completing applicable suitability or compliance steps.</div></aside></div></div>`;
  const ask = async (question) => {
    if (!question.trim()) return;
    state.messages.push({ role: 'user', text: question.trim() });
    renderKnowledge();
    let answer;
    try {
      const response = await fetch('/api/knowledge/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim() }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      answer = {
        text: result.answer,
        citation: result.citations.length
          ? result.citations.map((item) => `${item.source} [${item.id}]`).join(' · ')
          : 'No approved source found · escalation required',
      };
    } catch (error) {
      answer = localAnswer(question);
      answer.citation += ' · browser fallback';
      console.warn('Knowledge API unavailable; using deterministic browser fallback.', error);
    }
    state.messages.push({ role: 'assistant', ...answer });
    renderKnowledge();
    const stream = document.querySelector('#chat-stream');
    stream.scrollTop = stream.scrollHeight;
  };
  document.querySelector('#chat-form').addEventListener('submit', (event) => { event.preventDefault(); const input = document.querySelector('#chat-question'); ask(input.value); });
  document.querySelectorAll('[data-question]').forEach((button) => button.addEventListener('click', () => ask(button.dataset.question)));
}

function renderOperations() {
  const services = [
    ['Web cockpit', 'Connected'],
    ['Synthetic data provider', 'Connected'],
    ['Deterministic knowledge provider', 'Connected'],
    ['Azure OpenAI provider', 'Planned after resource-group gate'],
    ['Microsoft Teams bot', 'Local scaffold pending'],
  ];
  app.innerHTML = `<div class="page">${pageHeading('Transparent system status', 'Operations', 'Only connected components are marked live; future services remain explicit.')}<div class="operations-grid"><section class="panel"><div class="panel-header"><h2>Service health</h2></div><div class="panel-body health-list">${services.map(([name, status], index) => `<div class="health-row"><strong>${name}</strong><span class="health-state ${index > 2 ? 'planned' : ''}">${status}</span></div>`).join('')}</div></section><section class="panel"><div class="panel-header"><h2>Synthetic signal stream</h2></div><div class="panel-body">${state.data.signals.map((signal) => `<div class="signal-row"><span class="signal-time">${signal.time}</span><span class="signal-label">${signal.label}</span><div class="signal-text"><strong>${signal.client}</strong><span>${signal.text}</span></div></div>`).join('')}</div></section></div><section class="panel" style="margin-top:16px"><div class="panel-header"><h2>Provisioning boundary</h2></div><div class="panel-body"><p class="detail-copy"><strong>No Azure writes are enabled.</strong> Subscription name and ID must be confirmed first. The initial Azure operation will create and verify <code>rg-frontier-rm-ebc-dev</code>; all resource-group-capable services will target it explicitly.</p></div></section></div>`;
}

function bindSharedActions() {
  document.querySelector('[data-action="reset-day"]')?.addEventListener('click', () => showToast('Demo state reset to 08:30 SGT.'));
}

function render() {
  renderNav();
  const renderers = { today: renderToday, clients: renderClients, opportunities: renderOpportunities, knowledge: renderKnowledge, operations: renderOperations };
  (renderers[state.route] || renderToday)();
  app.focus({ preventScroll: true });
}

window.addEventListener('hashchange', () => {
  state.route = location.hash.slice(1) || 'today';
  render();
});

document.querySelector('#mode-switch').addEventListener('click', (event) => {
  state.liveMode = !state.liveMode;
  event.currentTarget.classList.toggle('live', state.liveMode);
  document.querySelector('#mode-label').textContent = state.liveMode ? 'Live provider unavailable' : 'Demo mode';
  showToast(state.liveMode ? 'Azure is locked until the resource-group gate is approved. Staying in deterministic demo mode.' : 'Deterministic demo mode active.');
});

try {
  const response = await fetch('/packages/demo-data/data.json');
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  state.data = await response.json();
  render();
} catch (error) {
  app.innerHTML = `<div class="empty"><h2>Demo data could not be loaded</h2><p>Start the local server from the project root with <code>python services/api/server.py</code>.</p></div>`;
  console.error(error);
}
