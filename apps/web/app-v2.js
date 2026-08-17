const NAV_ITEMS = [
  ['today', 'Today'],
  ['clients', 'Clients'],
  ['opportunities', 'Opportunities'],
  ['sources', 'Sources'],
  ['operations', 'Operations'],
  ['houseview', 'Houseview'],
];

const state = {
  data: null,
  health: null,
  route: location.hash.slice(1) || 'today',
  selectedClientId: 'client-lim',
  query: '',
  mode: 'live',
  messages: [],
  prepared: new Set(JSON.parse(sessionStorage.getItem('frontier-prepared') || '[]')),
  completedAgenda: new Set(JSON.parse(sessionStorage.getItem('frontier-agenda') || '[0]')),
  drafts: JSON.parse(sessionStorage.getItem('frontier-drafts') || '{}'),
  generated: {},
  groundingMode: 'fabric-iq',
  activeJourneyAction: 'briefing',
  sources: [],
  selectedSourceId: null,
  sourceTypeFilter: 'all',
  sourceClientFilter: 'all',
  selectedHouseviewId: 'houseview-2026-q4',
  houseviewAdvisory: null,
  copilotOpen: false,
  liveSignals: [],
  signalIndex: 0,
  presentation: null,
  presentationRecommendation: null,
  agentRun: null,
  agentRuns: [],
  agentCatalog: [],
  agentEventFilter: 'All',
  modalReturnFocus: null,
};

const app = document.querySelector('#app');
const nav = document.querySelector('#primary-nav');
const toast = document.querySelector('#toast');
const ticker = document.querySelector('#signal-ticker');
const presentationRoot = document.querySelector('#presentation-root');
const modalRoot = document.querySelector('#modal-root');
const copilotPanel = document.querySelector('#copilot-panel');
const copilotToggle = document.querySelector('#copilot-toggle');

const escapeHtml = (value = '') => String(value).replace(/[&<>'"]/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
}[character]));
const clientById = (id) => state.data.clients.find((client) => client.id === id);
const opportunityByClient = (id) => state.data.opportunities.find((item) => item.clientId === id);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const todayDisplayDate = new Intl.DateTimeFormat('en-SG', {
  weekday: 'long', day: 'numeric', month: 'long', timeZone: 'Asia/Singapore',
}).format(new Date());

function persist() {
  sessionStorage.setItem('frontier-prepared', JSON.stringify([...state.prepared]));
  sessionStorage.setItem('frontier-agenda', JSON.stringify([...state.completedAgenda]));
  sessionStorage.setItem('frontier-drafts', JSON.stringify(state.drafts));
}

function showToast(message, tone = 'default') {
  toast.textContent = message;
  toast.dataset.tone = tone;
  toast.classList.add('show');
  window.setTimeout(() => toast.classList.remove('show'), 2800);
}

function pageHeading(eyebrow, title, description, action = '') {
  return `<div class="page-heading"><div><p class="eyebrow">${eyebrow}</p><h1>${title}</h1><p>${description}</p></div>${action || `<span class="as-of live-asof"><i></i> Live · 08:30 SGT</span>`}</div>`;
}

function renderNav() {
  nav.innerHTML = NAV_ITEMS.map(([id, label]) => `<button class="nav-button ${state.route === id ? 'active' : ''}" data-route="${id}" type="button">${label}</button>`).join('');
  nav.querySelectorAll('[data-route]').forEach((button) => button.addEventListener('click', () => { location.hash = button.dataset.route; }));
}

function updateModeControl() {
  const button = document.querySelector('#mode-switch');
  const isLive = state.mode === 'live';
  button.classList.toggle('live', isLive);
  document.querySelector('#mode-label').textContent = isLive
    ? `Live · ${state.health?.provider === 'azure-openai' ? 'Azure AI' : 'connecting'}`
    : 'Rehearsal mode';
}

function startTicker() {
  const paint = () => {
    if (!state.data) return;
    const signals = [...state.liveSignals, ...state.data.signals];
    const signal = signals[state.signalIndex % signals.length];
    ticker.innerHTML = `<span class="ticker-live"><i></i> SIGNAL STREAM</span><span class="ticker-client">${escapeHtml(signal.client)}</span><span>${escapeHtml(signal.text)}</span><span class="ticker-time">${signal.time || 'now'}</span>`;
    state.signalIndex += 1;
  };
  paint();
  setInterval(paint, 3600);
  setInterval(() => {
    if (!state.data) return;
    const source = state.data.signals[(Date.now() / 7000 | 0) % state.data.signals.length];
    state.liveSignals.unshift({ ...source, time: new Date().toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' }) });
    state.liveSignals = state.liveSignals.slice(0, 8);
    if (state.route === 'operations') renderOperations();
  }, 7000);
}

function animatedMetric(id, label, value, change, tone, delay) {
  return `<button class="metric ${tone} motion-rise" style="--delay:${delay}ms" data-metric-report="${id}" type="button" aria-label="Open ${label} report"><div class="metric-label">${label}<span aria-hidden="true">↗</span></div><div class="metric-value">${value}</div><div class="metric-change">${change}</div><div class="metric-spark"><span></span><span></span><span></span><span></span><span></span></div></button>`;
}

function renderMetrics() {
  const prepared = state.prepared.size;
  const completed = state.completedAgenda.size;
  return `<section class="metric-grid" aria-label="Portfolio metrics">
    ${animatedMetric('assets', 'Assets under care', 'S$184.6M', '+2.8% this quarter', 'neutral', 0)}
    ${animatedMetric('needs', 'Needs advanced', `${prepared} / 4`, prepared ? `${prepared} client plans prepared` : 'Start with Daniel', 'positive', 80)}
    ${animatedMetric('reviews', 'Reviews due', String(Math.max(0, 12 - prepared)), `${4 - Math.min(4, prepared)} this week`, 'attention', 160)}
    ${animatedMetric('completed', 'Today completed', `${completed} / 5`, `${Math.round(completed / 5 * 100)}% of plan`, 'positive', 240)}
  </section>`;
}

const RM_WORKFLOWS = [
  { id: 'client-lim', stage: 'briefing', step: '01', label: 'Pre-meeting', title: 'Prepare the client briefing', detail: 'Unify Fabric facts, past emails, meeting notes, consent, and governed questions.', action: 'Generate briefing' },
  { id: 'client-lim', stage: 'recommendation', step: '02', label: 'In the meeting', title: 'Shape custom recommendations', detail: 'Compare fictional product candidates against objectives, liquidity, horizon, and risk.', action: 'Review recommendations' },
  { id: 'client-lim', stage: 'opportunity-draft', step: '03', label: 'After the meeting', title: 'Create the opportunity draft', detail: 'Turn the reviewed solution into an editable client email and CRM opportunity record.', action: 'Prepare drafts' },
];

function renderWorkflowStories() {
  return `<section class="workflow-section"><div class="section-heading"><div><h2>One client journey, three RM artifacts</h2><p>Prepare before the meeting, decide with evidence, and follow up through RM-approved drafts</p></div></div><div class="workflow-grid three-stage">${RM_WORKFLOWS.map((workflow, index) => `<button class="workflow-card motion-rise" style="--delay:${index * 70}ms" data-workflow-client="${workflow.id}" data-workflow-stage="${workflow.stage}" type="button"><span class="workflow-step">${workflow.step}</span><span class="workflow-label">${workflow.label}</span><strong>${workflow.title}</strong><p>${workflow.detail}</p><b>${workflow.action} <span aria-hidden="true">→</span></b></button>`).join('')}</div></section>`;
}

function outcomeProgress() {
  const prepared = state.prepared.size;
  const complete = state.completedAgenda.size;
  return `<section class="outcome-band panel">
    <div><p class="eyebrow">CLIENT OUTCOMES</p><h2>Momentum without sales theatre</h2><p>Progress moves when John prepares or completes genuine client work.</p></div>
    <div class="outcome-grid">
      <div><span>Meeting readiness</span><strong>${prepared}/4</strong><b style="--p:${prepared * 25}%"></b></div>
      <div><span>Daily coverage</span><strong>${complete}/5</strong><b style="--p:${complete * 20}%"></b></div>
      <div><span>Profile hygiene</span><strong>92%</strong><b style="--p:92%"></b></div>
    </div>
  </section>`;
}

function renderToday() {
  const top = state.data.opportunities.slice(0, 3);
  const complete = state.completedAgenda.size;
  app.innerHTML = `<div class="page">
    <section class="story-hero">
      <div class="hero-grid"></div><div class="hero-glow"></div>
      <div class="hero-content"><p class="hero-kicker"><i></i> FRONTIER RM · LIVE DAY</p><h1>A relationship manager's day,<br><em>orchestrated around client needs.</em></h1><p>John starts with 128 households, four material signals and one hour before his first client conversation.</p><div class="hero-actions"><button class="hero-primary" data-start-story>▶ Start the guided story <span>60 sec</span></button><button class="hero-secondary" data-open-client="client-lim">Open Daniel's brief →</button></div></div>
      <div class="hero-pulse"><div class="pulse-ring" style="--score:${complete / 5 * 360}deg"><span><strong>${complete}/5</strong><small>day plan</small></span></div><p>AI prioritised · RM controlled</p></div>
    </section>
    ${pageHeading(todayDisplayDate, `Good morning, ${state.data.rm.name.split(' ')[0]}`, 'Your day is sequenced around client commitments, consent and mandatory checks.')}
    <section class="panel briefing motion-rise"><div class="panel-body"><div class="briefing-copy"><span class="briefing-icon">☀</span><div><h2>Morning portfolio pulse</h2><p>Daniel's maturity is the most time-sensitive need. Mei's profile refresh must precede any portfolio discussion. Two service windows opened overnight.</p></div></div><div class="briefing-stats"><div class="briefing-stat"><strong>4</strong><span>material signals</span></div><div class="briefing-stat"><strong>1h 45m</strong><span>time returned</span></div></div></div></section>
    ${renderMetrics()}
    ${renderWorkflowStories()}
    ${outcomeProgress()}
    <div class="today-grid">
      <section class="panel"><div class="panel-header section-heading"><div><h2>Today's plan</h2><p>Click an item to complete it and watch the day rebalance</p></div><button class="secondary-button" data-reset type="button">↻ Reset story</button></div><div class="panel-body agenda-list">${state.data.agenda.map((item, index) => { const done = state.completedAgenda.has(index); return `<button class="agenda-item ${done ? 'complete' : index === complete ? 'next' : ''}" data-agenda="${index}" type="button"><span class="agenda-time">${item.time}</span><span class="agenda-marker">${done ? '✓' : ''}</span><span><span class="agenda-title">${item.title}</span><span class="agenda-type">${item.type}</span></span><span class="agenda-status">${done ? 'done' : index === complete ? 'next' : 'scheduled'}</span></button>`; }).join('')}</div></section>
      <section><div class="section-heading"><div><h2>Priority needs</h2><p>Open one to watch the evidence resolve</p></div><span class="live-chip"><i></i> LIVE AI</span></div><div class="priority-list">${top.map((opportunity, index) => { const client = clientById(opportunity.clientId); const prepared = state.prepared.has(opportunity.id); return `<article class="priority-card motion-rise ${prepared ? 'prepared' : ''}" style="--delay:${index * 90}ms" data-generate="${client.id}" tabindex="0"><div class="priority-top"><div><span class="priority-client">${client.name} · ${opportunity.priority}</span><h3>${opportunity.title}</h3></div><div class="score">${opportunity.confidence}<small>confidence</small></div></div><div class="priority-meta"><span>${opportunity.value}</span><span class="chip">${prepared ? '✓ prepared' : opportunity.type}</span></div></article>`; }).join('')}</div></section>
    </div>
  </div>`;
  bindGlobalActions();
  document.querySelectorAll('[data-agenda]').forEach((button) => button.addEventListener('click', () => toggleAgenda(Number(button.dataset.agenda))));
  document.querySelectorAll('[data-metric-report]').forEach((button) => button.addEventListener('click', () => openMetricReport(button.dataset.metricReport, button)));
  document.querySelectorAll('[data-workflow-client]').forEach((button) => button.addEventListener('click', () => { state.selectedClientId = button.dataset.workflowClient; state.activeJourneyAction = button.dataset.workflowStage; location.hash = 'opportunities'; }));
  document.querySelector('[data-reset]').addEventListener('click', resetExperience);
}

function toggleAgenda(index) {
  if (state.completedAgenda.has(index)) state.completedAgenda.delete(index); else state.completedAgenda.add(index);
  persist(); renderToday(); showToast(state.completedAgenda.has(index) ? 'Action completed. Today and coverage metrics updated.' : 'Action reopened.', 'success');
}

function resetExperience() {
  state.prepared.clear(); state.completedAgenda = new Set([0]); state.drafts = {}; state.generated = {}; state.messages = []; state.activeJourneyAction = 'briefing'; persist(); render(); renderCopilot(); showToast('Story reset to 08:30 SGT.');
}

function metricReportData(id) {
  const prepared = state.prepared.size;
  const reports = {
    assets: { eyebrow: 'PORTFOLIO REPORT', title: 'Assets under care', value: 'S$184.6M', context: '128 households · +2.8% this quarter', rows: state.data.clients.slice(0, 8).map((client) => [client.name, client.segment, client.assets, client.riskProfile]) },
    needs: { eyebrow: 'WORKFLOW REPORT', title: 'Needs advanced', value: `${prepared} / 4`, context: 'Plans move only after John reviews the prepared action', rows: state.data.opportunities.slice(0, 8).map((opportunity) => { const client = clientById(opportunity.clientId); return [client.name, opportunity.type, opportunity.priority, state.prepared.has(opportunity.id) ? 'Prepared' : 'Open']; }) },
    reviews: { eyebrow: 'GOVERNANCE REPORT', title: 'Reviews due', value: String(Math.max(0, 12 - prepared)), context: `${4 - Math.min(4, prepared)} priority reviews remain this week`, rows: state.data.clients.slice(0, 8).map((client) => [client.name, client.kycStatus, client.consent, client.riskProfile]) },
    completed: { eyebrow: 'DAY PLAN REPORT', title: 'Today completed', value: `${state.completedAgenda.size} / 5`, context: `${Math.round(state.completedAgenda.size / 5 * 100)}% of the working plan complete`, rows: state.data.agenda.map((item, index) => [item.time, item.title, item.type, state.completedAgenda.has(index) ? 'Complete' : 'Scheduled']) },
  };
  return reports[id] || reports.assets;
}

function openDialog(content, trigger) {
  state.modalReturnFocus = trigger || document.activeElement;
  modalRoot.innerHTML = `<div class="modal-backdrop" data-modal-backdrop><section class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">${content}</section></div>`;
  modalRoot.querySelectorAll('.modal-close').forEach((button) => button.addEventListener('click', closeModal));
  modalRoot.querySelector('[data-modal-backdrop]')?.addEventListener('click', (event) => { if (event.target === event.currentTarget) closeModal(); });
  modalRoot.querySelector('button, input, textarea, select')?.focus();
}

function openMetricReport(id, trigger) {
  const report = metricReportData(id);
  const headers = id === 'completed' ? ['Time', 'Action', 'Type', 'Status'] : id === 'reviews' ? ['Client', 'Profile', 'Consent', 'Risk'] : id === 'needs' ? ['Client', 'Need', 'Priority', 'State'] : ['Client', 'Segment', 'Assets', 'Risk'];
  openDialog(`<button class="modal-close" type="button" aria-label="Close report">×</button><p class="eyebrow">${report.eyebrow} · SNAPSHOT 08:30 SGT</p><div class="report-heading"><div><h2 id="modal-title">${report.title}</h2><p>${report.context}</p></div><strong>${report.value}</strong></div><div class="report-table-wrap"><table class="report-table"><thead><tr>${headers.map((header) => `<th>${header}</th>`).join('')}</tr></thead><tbody>${report.rows.map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><footer class="report-footer"><span>Fabric snapshot · ${escapeHtml(state.data.asOf || '12 Aug 2026')}</span><button class="secondary-button modal-close" type="button">Close</button></footer>`, trigger);
}

function filteredClients() {
  const query = state.query.trim().toLowerCase();
  if (!query) return state.data.clients;
  return state.data.clients.filter((client) => [client.name, client.segment, client.household, ...client.products].join(' ').toLowerCase().includes(query));
}

function allocationFor(client) {
  const sets = { 'client-lim': [38, 31, 19, 12], 'client-tan': [24, 46, 20, 10], 'client-ng': [57, 18, 15, 10], 'client-lee': [28, 39, 21, 12] };
  return sets[client.id] || [40, 30, 20, 10];
}

function clientDetail(client) {
  if (!client) return '<div class="panel empty">Select a client to view their context.</div>';
  const allocation = allocationFor(client);
  const advisory = client.advisoryProfile;
  const activity = client.investmentActivity?.[0];
  return `<section class="panel client-detail motion-rise"><div class="client-hero"><div class="client-name"><span class="client-initials">${client.initials}</span><div><p class="eyebrow">CLIENT 360</p><h2>${client.name}</h2><p>${client.segment}</p></div></div><div class="action-row"><button class="secondary-button" data-meeting-brief="${client.id}">Meeting brief</button><button class="primary-button" data-generate="${client.id}">✦ Open journey</button></div></div>
    <div class="client-intelligence"><div class="allocation"><div class="donut" style="--a:${allocation[0] * 3.6}deg;--b:${(allocation[0] + allocation[1]) * 3.6}deg;--c:${(allocation[0] + allocation[1] + allocation[2]) * 3.6}deg"><span><strong>${client.assets}</strong><small>assets under care</small></span></div><div class="legend"><span><i></i>Deposits ${allocation[0]}%</span><span><i></i>Investments ${allocation[1]}%</span><span><i></i>Lending ${allocation[2]}%</span><span><i></i>Liquidity ${allocation[3]}%</span></div></div><div class="timeline"><p class="eyebrow">RELATIONSHIP TIMELINE</p><div><i></i><strong>Yesterday</strong><span>${client.recentInteraction}</span></div><div><i></i><strong>Next</strong><span>${client.nextMeeting}</span></div><div><i></i><strong>Profile</strong><span>${client.kycStatus}</span></div></div></div>
    <div class="detail-grid"><div class="detail-cell"><span>Investment Risk Profile</span><strong>${advisory.declared_risk_score} · ${escapeHtml(advisory.declared_risk_label)}</strong></div><div class="detail-cell"><span>Contact preference</span><strong>${client.contactPreference}</strong></div><div class="detail-cell"><span>Consent</span><strong>${client.consent}</strong></div></div><section class="risk-evidence"><div class="risk-score-card"><span>Declared profile</span><strong>${advisory.declared_risk_score}</strong><small>${escapeHtml(advisory.declared_risk_label)} · effective ${new Date(advisory.profile_effective_at).toLocaleDateString('en-SG', { dateStyle: 'medium' })}</small></div><div class="risk-score-card observed ${advisory.risk_review_status.toLowerCase().replace('_','-')}"><span>Observed behaviour</span><strong>${advisory.observed_behaviour_indicator}</strong><small>${escapeHtml(advisory.observed_behaviour_label)} · ${escapeHtml(advisory.risk_review_status.replaceAll('_',' '))}</small></div><div class="risk-activity"><span>Latest activity evidence</span><strong>${activity ? `${activity.activity_type} ${activity.asset_class} · S$${Number(activity.amount).toLocaleString('en-SG')}` : 'No material activity'}</strong><small>${activity ? escapeHtml(activity.explanation) : 'Declared profile remains unchanged.'}</small></div></section><div class="profile-boundary">Observed activity can trigger review. It does not silently change the client-declared Investment Risk Profile.</div><div class="detail-section"><h3>Signals requiring RM judgement</h3><ul class="signal-list">${client.signals.map((signal, i) => `<li style="--delay:${i * 100}ms" class="motion-rise">${signal}</li>`).join('')}</ul></div></section>`;
}

function renderClients() {
  const clients = filteredClients();
  if (!clients.some((client) => client.id === state.selectedClientId) && clients.length) state.selectedClientId = clients[0].id;
  const selected = clients.find((client) => client.id === state.selectedClientId);
  app.innerHTML = `<div class="page">${pageHeading('Relationship intelligence', 'Client 360', 'Individual client context, engagement history, consent and suitability in one decision surface.')}<div class="toolbar"><input id="client-search" class="search" type="search" value="${escapeHtml(state.query)}" placeholder="Search clients, needs or products"><span class="as-of">${clients.length} clients</span></div><div class="client-layout"><div class="client-list">${clients.map((client, i) => `<button class="client-row motion-rise ${client.id === state.selectedClientId ? 'active' : ''}" style="--delay:${i * 70}ms" data-client="${client.id}"><span class="client-initials">${client.initials}</span><span><strong>${client.name}</strong><small>${client.segment}</small></span><span class="client-assets">${client.assets}</span></button>`).join('')}</div>${clientDetail(selected)}</div></div>`;
  document.querySelector('#client-search').addEventListener('input', (event) => { state.query = event.target.value; renderClients(); document.querySelector('#client-search').focus(); });
  document.querySelectorAll('[data-client]').forEach((button) => button.addEventListener('click', () => { state.selectedClientId = button.dataset.client; renderClients(); }));
  document.querySelector('[data-meeting-brief]')?.addEventListener('click', () => openMeetingBrief(selected.id));
  bindGlobalActions();
}

function renderOpportunities() {
  const comparisonControl = `<div class="opportunity-heading-actions"><div class="iq-toggle" role="group" aria-label="Artifact grounding mode"><button class="${state.groundingMode === 'fabric-iq' ? 'active' : ''}" data-grounding-mode="fabric-iq" type="button"><span>✦</span>With Fabric IQ</button><button class="${state.groundingMode === 'general' ? 'active' : ''}" data-grounding-mode="general" type="button">Without Fabric IQ</button></div><span class="model-badge"><i></i>${state.mode === 'live' ? 'gpt-4.1-mini · managed identity' : 'deterministic rehearsal'}</span></div>`;
  app.innerHTML = `<div class="page">${pageHeading('Three-stage client journey', 'Opportunity studio', 'Generate the same RM artifacts with or without the governed Fabric IQ context envelope.', comparisonControl)}<section class="comparison-explainer ${state.groundingMode}"><strong>${state.groundingMode === 'fabric-iq' ? 'Fabric IQ grounded' : 'General AI draft'}</strong><span>${state.groundingMode === 'fabric-iq' ? 'Client 360, enterprise sources, Houseview, activity, relationships and regulatory controls are applied.' : 'Uses only basic client and opportunity facts. Enterprise evidence and Fabric IQ controls are intentionally excluded.'}</span></section><section class="ai-studio panel journey-studio"><aside><p class="eyebrow">PRIORITISED CLIENTS</p>${state.data.clients.map((client) => { const opp = opportunityByClient(client.id); return `<button class="studio-client ${state.selectedClientId === client.id ? 'active' : ''}" data-studio-client="${client.id}"><span>${client.initials}</span><b>${client.name}<small>${client.signals[0]}</small></b><em>${opp.confidence}%</em></button>`; }).join('')}</aside><div class="studio-workspace" id="studio-workspace">${journeyWorkspace(state.selectedClientId)}</div></section><section class="opportunity-list-section"><div class="section-heading"><div><h2>Current action portfolio</h2><p>Preparation state persists throughout the EBC session</p></div></div><div class="opportunity-list">${state.data.opportunities.map((base, index) => opportunityRow(opportunityByClient(base.clientId), index)).join('')}</div></section></div>`;
  document.querySelectorAll('[data-grounding-mode]').forEach((button) => button.addEventListener('click', () => { state.groundingMode = button.dataset.groundingMode; renderOpportunities(); }));
  document.querySelectorAll('[data-studio-client]').forEach((button) => button.addEventListener('click', () => { state.selectedClientId = button.dataset.studioClient; renderOpportunities(); }));
  bindJourneyActions();
  bindOpportunityActions();
}

const JOURNEY_STAGES = [
  { id: 'briefing', step: '01', title: 'Prepare briefing', detail: 'Pre-meeting context, email history, talk track, and questions.' },
  { id: 'recommendation', step: '02', title: 'Custom recommendations', detail: 'Fictional product candidates with suitability gates and trade-offs.' },
  { id: 'opportunity-draft', step: '03', title: 'Create opportunity draft', detail: 'Editable client email and CRM opportunity record.' },
];

function generatedArtifact(clientId, action, groundingMode = state.groundingMode) { return state.generated[clientId]?.[groundingMode]?.[action]; }
function stageAvailable(clientId, action) {
  if (action === 'briefing') return true;
  if (action === 'recommendation') return Boolean(generatedArtifact(clientId, 'briefing'));
  return Boolean(generatedArtifact(clientId, 'recommendation'));
}

function journeyStepper(clientId) {
  return `<div class="journey-stepper">${JOURNEY_STAGES.map((stage) => { const generated = Boolean(generatedArtifact(clientId, stage.id)); const available = stageAvailable(clientId, stage.id); return `<button class="journey-step ${state.activeJourneyAction === stage.id ? 'active' : ''} ${generated ? 'complete' : ''}" data-journey-stage="${stage.id}" type="button" ${available ? '' : 'disabled'}><span>${generated ? '✓' : stage.step}</span><b>${stage.title}</b><small>${available ? (generated ? 'Generated · open artifact' : stage.detail) : 'Complete the previous stage first'}</small></button>`; }).join('')}</div>`;
}

function journeyWorkspace(clientId) {
  const result = generatedArtifact(clientId, state.activeJourneyAction);
  return `<div class="journey-workspace">${journeyStepper(clientId)}<div class="journey-output">${result ? renderJourneyResult(result) : journeyIdle(clientId, state.activeJourneyAction)}</div></div>`;
}

function journeyIdle(clientId, action) {
  const client = clientById(clientId); const stage = JOURNEY_STAGES.find((item) => item.id === action); const available = stageAvailable(clientId, action);
  return `<div class="studio-empty"><div class="orbit"><i></i><i></i><i></i><span>✦</span></div><p class="eyebrow">${stage.step} · ${stage.title} · ${state.groundingMode === 'fabric-iq' ? 'WITH FABRIC IQ' : 'WITHOUT FABRIC IQ'}</p><h2>${client.name}</h2><p>${stage.detail}</p><button class="hero-primary" data-run-journey="${action}" type="button" ${available ? '' : 'disabled'}>Generate ${stage.title.toLowerCase()} with ${state.mode === 'live' ? 'Azure AI' : 'rehearsal engine'} →</button>${available ? '' : '<small class="stage-lock">Complete the previous artifact in this comparison mode first.</small>'}</div>`;
}

function bindJourneyActions() {
  document.querySelectorAll('[data-journey-stage]').forEach((button) => button.addEventListener('click', () => { state.activeJourneyAction = button.dataset.journeyStage; renderOpportunities(); }));
  document.querySelector('[data-run-journey]')?.addEventListener('click', (event) => runRecommendation(state.selectedClientId, event.currentTarget.dataset.runJourney));
  document.querySelector('[data-view-rationale]')?.addEventListener('click', (event) => openRationale(state.selectedClientId, event.currentTarget.dataset.viewRationale, event.currentTarget));
  document.querySelectorAll('[data-source-citation]').forEach((button) => button.addEventListener('click', () => openSourceCitation(button.dataset.sourceCitation)));
  document.querySelectorAll('[data-houseview-citation]').forEach((button) => button.addEventListener('click', () => { state.selectedHouseviewId = button.dataset.houseviewId || state.selectedHouseviewId; location.hash = 'houseview'; setTimeout(() => document.querySelector(`#${button.dataset.houseviewCitation}`)?.scrollIntoView({ behavior: 'smooth' }), 150); }));
  document.querySelectorAll('[data-control-detail]').forEach((button) => button.addEventListener('click', () => openRegulatoryControl(button.dataset.controlDetail, button)));
  document.querySelector('[data-edit-result-draft]')?.addEventListener('click', (event) => editDraft(event.currentTarget.dataset.editResultDraft));
  document.querySelector('[data-prepare]')?.addEventListener('click', (event) => prepareOpportunity(event.currentTarget.dataset.prepare));
  document.querySelector('[data-open-next-stage]')?.addEventListener('click', (event) => { state.activeJourneyAction = event.currentTarget.dataset.openNextStage; renderOpportunities(); });
  document.querySelector('[data-approve-artifact]')?.addEventListener('click', () => showToast('Draft approved for later RM use. Nothing was sent or committed.', 'success'));
}

function opportunityRow(opportunity, index) {
  const client = clientById(opportunity.clientId); const prepared = state.prepared.has(state.data.opportunities.find((x) => x.clientId === opportunity.clientId)?.id);
  return `<article class="opportunity ${index === 0 ? 'open' : ''} ${prepared ? 'prepared' : ''}" data-opportunity="${opportunity.clientId}"><button class="opportunity-summary"><span class="opportunity-rank">${String(index + 1).padStart(2, '0')}</span><span><span class="priority-client">${client.name} · ${opportunity.priority}</span><h3>${opportunity.title}</h3><span class="opportunity-sub">${opportunity.summary}</span></span><span class="opportunity-value"><strong>${opportunity.value}</strong><span>${opportunity.channel} · ${opportunity.time}</span></span><span class="confidence">${opportunity.confidence}%<span>confidence</span></span><span class="chevron">⌄</span></button><div class="opportunity-detail"><div><h3>Evidence and guardrails</h3><div class="tag-list">${opportunity.evidence.map((item) => `<span class="tag">${item}</span>`).join('')}</div><div class="detail-label">Mandatory checks</div><ul class="check-list">${opportunity.checks.map((item) => `<li>${item}</li>`).join('')}</ul></div><div><h3>Editable opening</h3><div class="draft">“${escapeHtml(state.drafts[opportunity.clientId] || opportunity.opening)}”</div><div class="action-row"><button class="primary-button" data-prepare="${opportunity.clientId}">${prepared ? '✓ Prepared' : 'Mark prepared'}</button><button class="secondary-button" data-edit-draft="${opportunity.clientId}">Edit draft</button></div></div></div></article>`;
}

function bindOpportunityActions() {
  document.querySelectorAll('.opportunity-summary').forEach((button) => button.addEventListener('click', () => { const row = button.closest('.opportunity'); row.classList.toggle('open'); }));
  document.querySelectorAll('[data-prepare]').forEach((button) => button.addEventListener('click', () => prepareOpportunity(button.dataset.prepare)));
  document.querySelectorAll('[data-edit-draft]').forEach((button) => button.addEventListener('click', () => editDraft(button.dataset.editDraft)));
}

async function runRecommendation(clientId, action = 'briefing', presentation = false, groundingMode = presentation ? 'fabric-iq' : state.groundingMode) {
  const client = clientById(clientId); state.selectedClientId = clientId;
  if (!presentation) {
    const workspace = document.querySelector('#studio-workspace');
    const trace = groundingMode === 'fabric-iq' ? ['Fabric Client 360', 'Enterprise sources and Houseview', 'Activity and regulatory controls', 'Governed artifact design'] : ['Basic client facts', 'Generic need framing', 'Mandatory safety checks', 'General draft composition'];
    workspace.innerHTML = `<div class="reasoning-live"><p class="eyebrow"><i></i> ${groundingMode === 'fabric-iq' ? 'FABRIC IQ EVIDENCE TRACE' : 'GENERAL AI PREPARATION'}</p><h2>Generating ${JOURNEY_STAGES.find((stage) => stage.id === action).title.toLowerCase()} for ${client.name}</h2><div class="reasoning-steps">${trace.map((label, i) => `<div data-reason-step="${i}"><i></i><span><strong>${label}</strong><small>queued</small></span></div>`).join('')}</div><div class="reasoning-wave"><i></i><i></i><i></i><i></i><i></i></div></div>`;
  }
  let result;
  const request = fetch('/api/opportunities/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ clientId, action, houseviewId: state.selectedHouseviewId, groundingMode: groundingMode }) }).then((response) => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); });
  for (let index = 0; index < 4; index += 1) {
    await sleep(620);
    document.querySelector(`[data-reason-step="${index}"]`)?.classList.add('done');
    const small = document.querySelector(`[data-reason-step="${index}"] small`); if (small) small.textContent = 'resolved';
  }
  try { result = await request; } catch { result = action === 'briefing' ? fallbackRecommendation(clientId) : null; }
  if (!result) { showToast('This artifact could not be generated.'); renderOpportunities(); return null; }
  state.generated[clientId] ||= {}; state.generated[clientId][groundingMode] ||= {}; state.generated[clientId][groundingMode][action] = result; state.activeJourneyAction = action; if (presentation) state.presentationRecommendation = result;
  if (presentation && state.presentation?.index === 3) renderPresentation();
  if (!presentation) renderOpportunities();
  return result;
}

function fallbackRecommendation(clientId) {
  const client = clientById(clientId); const opportunity = state.data.opportunities.find((item) => item.clientId === clientId);
  return { ...opportunity, clientId, provider: 'deterministic-mock', meetingObjective: `Understand ${client.name}'s current priorities and agree the next governed step.`, clientContext: [`${client.segment} relationship with ${client.assets} in assets under care.`, `Recorded risk profile: ${client.riskProfile}.`, `Latest interaction: ${client.recentInteraction}.`], whatChanged: client.signals, talkTrack: [{ topic: 'Open with priorities', guidance: opportunity.opening }, { topic: 'Explore liquidity and horizon', guidance: 'Clarify near-term commitments, accessible liquidity, and the investment horizon for any remaining amount.' }, { topic: 'Discuss allocation themes', guidance: 'Only after reconfirming the client profile, discuss diversified allocation themes without naming a fund or concluding suitability.' }, { topic: 'Agree the next step', guidance: 'Document the client’s answers and complete required checks before any product comparison.' }], discoveryQuestions: ['What has changed in your priorities since our last review?', 'How much liquidity will you need over the next 12 to 24 months?', 'What investment horizon and level of fluctuation would feel appropriate?', 'Which existing holdings or commitments should shape the next discussion?'], allocationThemes: ['Preserve an appropriate liquidity reserve before discussing investments.', 'Explore diversified income, balanced, or growth themes only after objectives and risk capacity are reconfirmed.', 'Assess existing holdings and concentration before preparing any product-level comparison.'], suitabilityChecks: opportunity.checks, unresolvedItems: ['Confirm objectives, horizon, liquidity needs, and risk capacity.', 'Confirm KYC, consent, and local product eligibility.'], followUpActions: ['Record the client’s answers and material changes.', 'Complete or escalate outstanding profile checks.', 'Prepare an approved comparison only if the client asks to continue.'], evidenceStages: [{ label: 'Relationship context', detail: `Reviewed ${client.assets} relationship.` }, { label: 'Need signals', detail: `Correlated ${client.signals.length} verified signals.` }, { label: 'Governance', detail: 'Applied suitability and contact checks.' }, { label: 'Action design', detail: 'Prepared the next human-reviewed conversation.' }] };
}

function briefList(items = []) {
  return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
}

function sourceChips(sources = []) {
  return `<div class="artifact-sources">${sources.map((source) => `<button data-source-citation="${source.id}" type="button"><span>${source.type === 'email' ? '✉' : '▤'}</span>${escapeHtml(source.title)}</button>`).join('')}</div>`;
}

function artifactHeader(result) {
  const grounded = result.groundingMode !== 'general';
  return `<div class="artifact-mode-banner ${grounded ? 'fabric-iq' : 'general'}"><strong>${escapeHtml(result.groundingLabel || (grounded ? 'Fabric IQ grounded' : 'General AI draft'))}</strong><span>${escapeHtml(result.comparisonSummary || (grounded ? 'Governed enterprise context and evidence are applied.' : 'Limited enterprise context; human review required.'))}</span></div><header class="artifact-header"><div><span class="live-chip"><i></i>${result.provider === 'azure-openai' ? 'AZURE AI · LIVE' : 'REHEARSAL'}</span><h2>${escapeHtml(result.title)}</h2><p>${escapeHtml(result.summary)}</p></div><div class="artifact-confidence"><strong>${result.confidence}%</strong><span>confidence</span></div></header>`;
}

function artifactFooter(result) {
  const sourceContent = result.sources?.length ? sourceChips(result.sources) : '<p class="no-enterprise-sources">No enterprise citations in general mode.</p>';
  return `<footer class="artifact-footer"><div><span>Sources used</span>${sourceContent}</div><button class="secondary-button" data-view-rationale="${result.action}" type="button">Why this? View evidence and rationale</button></footer>`;
}

function renderJourneyResult(result) {
  if (result.action === 'recommendation') return renderProductRecommendations(result);
  if (result.action === 'opportunity-draft') return renderOpportunityDraft(result);
  return renderBriefingArtifact(result);
}

function renderBriefingArtifact(result) {
  return `<article class="recommendation-result prebrief-workspace motion-rise">${artifactHeader(result)}<section class="brief-objective"><span>Meeting objective</span><strong>${escapeHtml(result.meetingObjective || result.artifact?.meetingObjective || result.summary)}</strong></section><div class="prebrief-grid"><section><h3>Client context</h3>${briefList(result.clientContext)}</section><section><h3>What changed</h3>${briefList(result.whatChanged || result.evidence)}</section></div><section class="talk-track"><div class="prebrief-title"><h3>Conversation talk track</h3><span>Pre-meeting preparation</span></div>${(result.talkTrack || []).map((item, index) => `<article><b>${String(index + 1).padStart(2, '0')}</b><div><strong>${escapeHtml(item.topic)}</strong><p>${escapeHtml(item.guidance)}</p></div></article>`).join('')}</section><div class="prebrief-grid"><section><h3>Discovery questions</h3>${briefList(result.discoveryQuestions)}</section><section><h3>Suitability and compliance</h3>${briefList(result.suitabilityChecks || result.checks)}</section></div><section class="editable-opening"><span>Editable opening</span><blockquote>${escapeHtml(state.drafts[result.clientId] || result.opening)}</blockquote><button class="secondary-button" data-edit-result-draft="${result.clientId}" type="button">Edit opening</button></section>${artifactFooter(result)}<div class="result-action"><div><span>Recommended moment</span><strong>${escapeHtml(result.channel)} · ${escapeHtml(result.time)}</strong></div><button class="primary-button" data-prepare="${result.clientId}" type="button">Mark briefing reviewed</button></div></article>`;
}

function renderProductRecommendations(result) {
  const artifact = result.artifact;
  return `<article class="recommendation-result product-workspace motion-rise">${artifactHeader(result)}${renderRecommendationGrounding(result)}<div class="artifact-boundary"><strong>Fictional positioning candidates</strong><span>RM review, eligibility and suitability confirmation are required. Nothing can be transacted here.</span></div><div class="product-comparison">${artifact.products.map((product, index) => `<section><header><span>0${index + 1}</span><div><h3>${escapeHtml(product.name)}</h3><small>${escapeHtml(product.intendedRole)}</small></div></header><dl><div><dt>Why it may fit</dt><dd>${escapeHtml(product.fitRationale)}</dd></div><div><dt>Objective</dt><dd>${escapeHtml(product.objectiveAlignment)}</dd></div><div><dt>Risk alignment</dt><dd>${escapeHtml(product.riskAlignment)}</dd></div></dl><h4>Material risks</h4>${briefList(product.risks)}<div class="product-evidence">${(product.evidenceIds || []).map((id) => id.startsWith('hv-') ? `<button data-houseview-citation="${id}" data-houseview-id="${result.houseviewContext.reportId}" type="button">${escapeHtml(id)}</button>` : `<span>${escapeHtml(id)}</span>`).join('')}</div></section>`).join('')}</div><div class="prebrief-grid"><section><h3>Suitability gates</h3>${briefList(artifact.gates)}</section><section class="open-items"><h3>Still unresolved</h3>${briefList(result.unresolvedItems)}</section></div><p class="artifact-disclaimer">${escapeHtml(artifact.disclaimer)}</p>${artifactFooter(result)}<div class="result-action"><div><span>Next stage</span><strong>Review candidates before drafting client communication</strong></div><button class="primary-button" data-open-next-stage="opportunity-draft" type="button">Continue to opportunity draft</button></div></article>`;
}

function renderRecommendationGrounding(result) {
  if (!result.houseviewContext) return '';
  const risk = result.riskContext;
  const activity = result.activityEvidence?.[0];
  return `<section class="recommendation-grounding"><header><div><p class="eyebrow">GROUNDED POSITIONING</p><h3>${escapeHtml(result.houseviewContext.title)}</h3><span>${escapeHtml(result.houseviewContext.cioStance)} · as of ${new Date(result.houseviewContext.asOf).toLocaleDateString('en-SG', { dateStyle: 'medium' })}</span></div><button data-houseview-citation="${result.houseviewContext.sections[0]?.houseview_section_id}" data-houseview-id="${result.houseviewContext.reportId}" type="button">Open Houseview →</button></header><div class="grounding-grid"><div><span>Declared profile</span><strong>${risk.declaredScore} · ${escapeHtml(risk.declaredLabel)}</strong></div><div><span>Observed behaviour</span><strong>${risk.observedIndicator} · ${escapeHtml(risk.observedLabel)}</strong></div><div><span>Review status</span><strong>${escapeHtml(risk.reviewStatus.replaceAll('_',' '))}</strong></div><div><span>Activity evidence</span><strong>${activity ? `${activity.activity_type} ${activity.asset_class} · S$${Number(activity.amount).toLocaleString('en-SG')}` : 'None'}</strong></div></div><div class="suppressed-strip"><strong>${result.suppressedCandidates.length} candidates suppressed</strong><span>${result.suppressedCandidates.slice(0,2).map((item) => `${item.name}: ${item.reasons[0]}`).join(' · ')}</span></div><div class="control-chips">${result.regulatoryControls.map((control) => `<button class="${control.status.toLowerCase()}" data-control-detail="${control.ruleId}" type="button">${escapeHtml(control.ruleId)} · ${escapeHtml(control.status.replaceAll('_',' '))}</button>`).join('')}</div></section>`;
}

function renderOpportunityDraft(result) {
  const artifact = result.artifact;
  return `<article class="recommendation-result draft-workspace motion-rise">${artifactHeader(result)}<div class="draft-grid"><section class="email-draft"><header><div><span>✉</span><strong>Client email draft</strong></div><b>${escapeHtml(artifact.email.subject)}</b></header><textarea data-email-body aria-label="Editable client email body">${escapeHtml(artifact.email.body)}</textarea><h4>Required disclosures</h4>${briefList(artifact.email.disclosures)}<div class="draft-placeholders">${artifact.email.placeholders.map((item) => `<span>${escapeHtml(item)}</span>`).join('')}</div></section><section class="crm-draft"><header><span>CRM</span><strong>Opportunity record</strong></header>${Object.entries({ Need: artifact.crm.need, Stage: artifact.crm.stage, 'Estimated scope': artifact.crm.estimatedScope, Owner: artifact.crm.owner, 'Next action': artifact.crm.nextAction, 'Next action at': artifact.crm.nextActionAt, Approval: artifact.crm.approvalState }).map(([label,value]) => `<div><span>${label}</span><strong>${escapeHtml(value)}</strong></div>`).join('')}<h4>Evidence</h4><div class="product-evidence">${artifact.crm.evidenceIds.map((id) => `<button data-source-citation="${id}" type="button">${escapeHtml(id)}</button>`).join('')}</div></section></div><div class="prebrief-grid"><section class="open-items"><h3>Unresolved before use</h3>${briefList(result.unresolvedItems)}</section><section><h3>Mandatory checks</h3>${briefList(result.checks)}</section></div>${artifactFooter(result)}<div class="result-action"><div><span>Draft state</span><strong>Not sent · Not committed to CRM</strong></div><button class="primary-button" data-approve-artifact type="button">Approve draft for later use</button></div></article>`;
}

function openSourceCitation(sourceId) {
  if (!state.sources.some((source) => source.id === sourceId)) return;
  state.selectedSourceId = sourceId; state.sourceTypeFilter = 'all'; state.sourceClientFilter = 'all'; location.hash = 'sources';
}

function openRationale(clientId, action, trigger) {
  const result = generatedArtifact(clientId, action); if (!result) return;
  const reasoning = result.reasoning;
  const section = (title, content) => `<section class="rationale-section"><h3>${title}</h3>${content}</section>`;
  const evidenceControl = (item) => item.id.startsWith('hv-') ? `<button data-houseview-citation="${item.id}" data-houseview-id="${result.houseviewContext?.reportId || state.selectedHouseviewId}" type="button">${escapeHtml(item.label)}</button>` : item.id.startsWith('FAA-N16-') || item.id.startsWith('INTERNAL-') ? `<button data-control-detail="${item.id}" type="button">${escapeHtml(item.label)}</button>` : state.sources.some((source) => source.id === item.id) ? `<button data-source-citation="${item.id}" type="button">${escapeHtml(item.label)}</button>` : `<span>${escapeHtml(item.label)}</span>`;
  openDialog(`<button class="modal-close" type="button" aria-label="Close rationale">×</button><p class="eyebrow">EVIDENCE AND RATIONALE · ${action.replace('-', ' ')}</p><h2 id="modal-title">Why this artifact?</h2><p>This is a concise public decision-support trace. Private model reasoning is not exposed.</p><div class="rationale-grid">${section('Evidence used', `<div class="rationale-evidence">${reasoning.evidenceUsed.map(evidenceControl).join('')}</div>`)}${section('Decision rules', briefList(reasoning.decisionRules))}${section('Why this fits', briefList(reasoning.whyThisFits))}${section('Alternatives considered', briefList(reasoning.alternativesConsidered))}${section('Assumptions', briefList(reasoning.assumptions))}${section('Limitations', briefList(reasoning.limitations))}${section('Unresolved checks', briefList(result.unresolvedItems))}</div><div class="modal-actions"><button class="secondary-button modal-close" type="button">Close</button></div>`, trigger);
  modalRoot.querySelector('.modal')?.classList.add('rationale-modal');
  modalRoot.querySelectorAll('[data-source-citation]').forEach((button) => button.addEventListener('click', () => { closeModal(); openSourceCitation(button.dataset.sourceCitation); }));
  modalRoot.querySelectorAll('[data-houseview-citation]').forEach((button) => button.addEventListener('click', () => { closeModal(); state.selectedHouseviewId = button.dataset.houseviewId; location.hash = 'houseview'; }));
  modalRoot.querySelectorAll('[data-control-detail]').forEach((button) => button.addEventListener('click', () => { const id = button.dataset.controlDetail; closeModal(); setTimeout(() => openRegulatoryControl(id, null), 0); }));
}

function prepareOpportunity(clientId) {
  const base = state.data.opportunities.find((item) => item.clientId === clientId); state.prepared.add(base.id);
  const agendaIndex = state.data.agenda.findIndex((item) => item.clientId === clientId); if (agendaIndex >= 0) state.completedAgenda.add(agendaIndex);
  persist(); showToast(`${clientById(clientId).name}'s plan is prepared. Portfolio metrics advanced.`, 'success');
  if (state.route === 'opportunities') renderOpportunities(); else render();
}

function editDraft(clientId) {
  const opportunity = opportunityByClient(clientId); const current = state.drafts[clientId] || opportunity.opening;
  openDialog(`<button class="modal-close" type="button" aria-label="Close editor">×</button><p class="eyebrow">HUMAN IN THE LOOP</p><h2 id="modal-title">Edit client opening</h2><p>AI drafted. John remains accountable for tone, accuracy and suitability.</p><textarea id="draft-editor">${escapeHtml(current)}</textarea><div class="modal-actions"><button class="secondary-button modal-close" type="button">Cancel</button><button class="primary-button" id="save-draft" type="button">Save approved draft</button></div>`, document.querySelector(`[data-edit-result-draft="${clientId}"], [data-edit-draft="${clientId}"]`));
  document.querySelector('#save-draft').addEventListener('click', () => { state.drafts[clientId] = document.querySelector('#draft-editor').value.trim(); persist(); closeModal(); renderOpportunities(); showToast('Approved draft saved for this session.', 'success'); });
}

function openMeetingBrief(clientId) {
  const client = clientById(clientId); const opportunity = opportunityByClient(clientId);
  openDialog(`<button class="modal-close" type="button" aria-label="Close brief">×</button><p class="eyebrow">MEETING BRIEF · ${client.nextMeeting}</p><h2 id="modal-title">${client.name}</h2><div class="brief-grid"><div><span>Relationship</span><strong>${client.assets}</strong></div><div><span>Risk</span><strong>${client.riskProfile}</strong></div><div><span>Profile</span><strong>${client.kycStatus}</strong></div></div><h3>What changed</h3><ul class="check-list">${client.signals.map((item) => `<li>${item}</li>`).join('')}</ul><h3>Recommended posture</h3><p class="draft">${opportunity.summary}</p><div class="modal-actions"><button class="secondary-button modal-close" type="button">Close</button><button class="primary-button" data-generate="${clientId}" type="button">Generate live action</button></div>`, document.querySelector(`[data-meeting-brief="${clientId}"]`));
  modalRoot.querySelector('[data-generate]').addEventListener('click', () => { closeModal(); location.hash = 'opportunities'; setTimeout(() => runRecommendation(clientId), 100); });
}
function closeModal() { modalRoot.innerHTML = ''; state.modalReturnFocus?.focus?.(); state.modalReturnFocus = null; }

function contextualQuestions() {
  const client = clientById(state.selectedClientId);
  if (state.route === 'opportunities') return [`What checks apply before recommending to ${client.name}?`, 'What evidence supports this opportunity?'];
  if (state.route === 'clients') return [`What should I review for ${client.name}?`, 'Which consent rules apply?'];
  if (state.route === 'sources') return ['How should email evidence be used?', 'Which source governs suitability?'];
  if (state.route === 'houseview') return ['What changed in the CIO view?', `Why is a candidate suppressed for ${client.name}?`, 'Which FAA-N16 control applies?'];
  return ['What should I check before a fixed deposit matures?', 'Can I discuss investments before a KYC refresh?'];
}

function renderCopilot() {
  const questions = contextualQuestions();
  copilotPanel.classList.toggle('open', state.copilotOpen);
  copilotPanel.setAttribute('aria-hidden', String(!state.copilotOpen));
  copilotToggle.setAttribute('aria-expanded', String(state.copilotOpen));
  copilotToggle.setAttribute('aria-label', state.copilotOpen ? 'Close Frontier Copilot' : 'Open Frontier Copilot');
  document.body.classList.toggle('copilot-open', state.copilotOpen);
  copilotPanel.innerHTML = `<header class="copilot-header"><div><span>F</span><div><strong>Frontier Copilot</strong><small>${state.mode === 'live' ? 'Grounded with Azure AI' : 'Rehearsal knowledge'}</small></div></div><button data-close-copilot type="button" aria-label="Close copilot">×</button></header><div id="copilot-stream" class="copilot-stream">${state.messages.length ? state.messages.map((message) => `<div class="message ${message.role}">${message.role === 'assistant' ? `<strong>Frontier Copilot <em>${message.provider || ''}</em></strong>` : ''}<span>${escapeHtml(message.text)}</span>${message.citation ? `<small class="citation">${escapeHtml(message.citation)}</small>` : ''}</div>`).join('') : `<div class="copilot-welcome"><span>✦</span><h2>How can I help?</h2><p>Ask about the selected client, evidence, suitability, or process boundaries.</p></div>`}</div><div class="copilot-starters">${questions.map((question) => `<button data-copilot-question="${escapeHtml(question)}" type="button">${escapeHtml(question)}</button>`).join('')}</div><form id="copilot-form" class="copilot-input"><input id="copilot-question" placeholder="Ask Frontier Copilot…" aria-label="Ask Frontier Copilot"><button type="submit" aria-label="Send question">→</button></form><footer>Human review required · Approved sources only</footer>`;
  copilotPanel.querySelector('[data-close-copilot]')?.addEventListener('click', closeCopilot);
  copilotPanel.querySelector('#copilot-form')?.addEventListener('submit', (event) => { event.preventDefault(); askKnowledge(copilotPanel.querySelector('#copilot-question').value); });
  copilotPanel.querySelectorAll('[data-copilot-question]').forEach((button) => button.addEventListener('click', () => askKnowledge(button.dataset.copilotQuestion)));
  const stream = copilotPanel.querySelector('#copilot-stream'); if (stream) stream.scrollTop = stream.scrollHeight;
}

function openCopilot() { state.copilotOpen = true; renderCopilot(); copilotPanel.querySelector('#copilot-question')?.focus(); }
function closeCopilot() { state.copilotOpen = false; renderCopilot(); copilotToggle.focus(); }

async function askKnowledge(question) {
  if (!question.trim()) return;
  state.messages.push({ role: 'user', text: question.trim() }); renderCopilot();
  const started = performance.now(); let result;
  try { const response = await fetch('/api/knowledge/query', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) }); result = await response.json(); } catch { result = { answer: 'The live assistant is unavailable. Use the approved process owner.', citations: [], provider: 'fallback' }; }
  const citation = result.citations?.length ? result.citations.map((item) => `${item.source} [${item.id}]`).join(' · ') : 'No approved source · escalation required';
  state.messages.push({ role: 'assistant', text: result.answer, citation, provider: result.provider === 'azure-openai' ? 'LIVE' : 'REHEARSAL', latency: Math.round(performance.now() - started) });
  renderCopilot();
}

function filteredSources() {
  return state.sources.filter((source) => (state.sourceTypeFilter === 'all' || source.type === state.sourceTypeFilter) && (state.sourceClientFilter === 'all' || source.clientId === state.sourceClientFilter));
}

function sourceReadingPane(source) {
  if (!source) return '<section class="source-reading empty"><h2>Select a message or document</h2><p>Open authored client correspondence or an approved internal document.</p></section>';
  const client = clientById(source.clientId);
  return `<section class="source-reading"><header><p class="eyebrow">${source.container} · ${source.folder}</p><h2>${escapeHtml(source.subject || source.title)}</h2><div class="source-participants"><strong>${escapeHtml(source.sender || source.author)}</strong><span>${new Date(source.timestamp).toLocaleString('en-SG', { dateStyle: 'medium', timeStyle: 'short' })}</span></div>${source.recipients ? `<small>To: ${source.recipients.map(escapeHtml).join(', ')}</small>` : `<small>Version ${escapeHtml(source.version)}</small>`}</header><article><p>${escapeHtml(source.body)}</p>${source.attachments?.length ? `<div class="source-attachments">${source.attachments.map((attachment) => `<span>▣ ${escapeHtml(attachment)}</span>`).join('')}</div>` : ''}</article><footer><span>${escapeHtml(client.name)} · ${escapeHtml(source.sensitivity)}</span><small>${escapeHtml(source.provenance)}</small></footer></section>`;
}

function renderSources() {
  const sources = filteredSources();
  if (!sources.some((source) => source.id === state.selectedSourceId)) state.selectedSourceId = sources[0]?.id || null;
  const selected = state.sources.find((source) => source.id === state.selectedSourceId);
  app.innerHTML = `<div class="page">${pageHeading('Client evidence', 'Sources', 'Client correspondence and internal documents used to prepare grounded RM artifacts.')}<div class="source-toolbar"><div class="source-segments">${[['all','All'],['email','Mail'],['document','Documents']].map(([id,label]) => `<button class="${state.sourceTypeFilter === id ? 'active' : ''}" data-source-type="${id}" type="button">${label}</button>`).join('')}</div><select data-source-client aria-label="Filter sources by client"><option value="all">All clients</option>${state.data.clients.slice(0, 4).map((client) => `<option value="${client.id}" ${state.sourceClientFilter === client.id ? 'selected' : ''}>${client.name}</option>`).join('')}</select></div><section class="source-explorer panel"><aside class="source-folders"><h3>Sources</h3><button class="active" type="button">▱ Client correspondence <span>${state.sources.filter((item) => item.type === 'email').length}</span></button><button type="button">▤ Advisory documents <span>${state.sources.filter((item) => item.type === 'document').length}</span></button></aside><div class="source-list">${sources.map((source) => `<button class="source-row ${source.id === state.selectedSourceId ? 'active' : ''}" data-source-id="${source.id}" type="button"><span class="source-icon">${source.type === 'email' ? '✉' : '▤'}</span><span><strong>${escapeHtml(source.subject || source.title)}</strong><small>${escapeHtml(clientById(source.clientId).name)} · ${escapeHtml(source.sender || source.author)}</small><p>${escapeHtml(source.preview)}</p></span><time>${new Date(source.timestamp).toLocaleDateString('en-SG', { day: '2-digit', month: 'short' })}</time></button>`).join('') || '<div class="empty">No sources match these filters.</div>'}</div>${sourceReadingPane(selected)}</section></div>`;
  document.querySelectorAll('[data-source-type]').forEach((button) => button.addEventListener('click', () => { state.sourceTypeFilter = button.dataset.sourceType; renderSources(); }));
  document.querySelector('[data-source-client]').addEventListener('change', (event) => { state.sourceClientFilter = event.target.value; renderSources(); });
  document.querySelectorAll('[data-source-id]').forEach((button) => button.addEventListener('click', () => { state.selectedSourceId = button.dataset.sourceId; renderSources(); }));
}

function houseviewReport() {
  return state.data.houseviews.find((report) => report.houseview_id === state.selectedHouseviewId) || state.data.houseviews[0];
}

function renderHouseview() {
  const report = houseviewReport();
  const client = clientById(state.selectedClientId);
  const advisory = state.houseviewAdvisory?.clientId === client.id && state.houseviewAdvisory?.houseviewContext?.reportId === report.houseview_id ? state.houseviewAdvisory : null;
  app.innerHTML = `<div class="page">${pageHeading('Chief Investment Office', 'CIO Houseview', 'Translate a unified market outlook into client-specific, evidence-backed positioning candidates.')}<section class="houseview-layout"><aside class="houseview-list panel"><div class="panel-header"><h2>Research library</h2><p>Fictional CIO reports</p></div>${state.data.houseviews.map((item) => `<button class="houseview-row ${item.houseview_id === report.houseview_id ? 'active' : ''}" data-houseview-id="${item.houseview_id}" type="button"><span class="houseview-status ${item.status.toLowerCase()}">${item.status}</span><strong>${escapeHtml(item.title)}</strong><small>${new Date(item.as_of_date).toLocaleDateString('en-SG', { dateStyle: 'medium' })}</small><p>${escapeHtml(item.cio_stance)}</p></button>`).join('')}</aside><article class="houseview-reader panel"><header><p class="eyebrow">${escapeHtml(report.status)} · AS OF ${new Date(report.as_of_date).toLocaleDateString('en-SG', { dateStyle: 'long' })}</p><h2>${escapeHtml(report.title)}</h2><p>${escapeHtml(report.executive_summary)}</p><span>${escapeHtml(report.cio_stance)}</span></header><div class="houseview-sections">${report.sections.map((section) => `<section id="${section.houseview_section_id}"><div><span>${escapeHtml(section.houseview_section_id)}</span><h3>${escapeHtml(section.title)}</h3></div><p>${escapeHtml(section.view)}</p><strong>Positioning</strong><p>${escapeHtml(section.positioning)}</p><small>Risks: ${escapeHtml(section.risks)}</small></section>`).join('')}</div><footer>Fictional internal demonstration report. Market views may change and do not constitute a recommendation.</footer></article><aside class="houseview-client panel"><div class="panel-header"><h2>Tailor to client</h2><select data-houseview-client aria-label="Select client">${state.data.clients.slice(0, 4).map((item) => `<option value="${item.id}" ${item.id === client.id ? 'selected' : ''}>${item.name}</option>`).join('')}</select></div>${advisory ? renderHouseviewAdvisory(advisory) : '<div class="houseview-loading"><span class="loader"></span> Applying client and control context…</div>'}</aside></section></div>`;
  document.querySelectorAll('[data-houseview-id]').forEach((button) => button.addEventListener('click', () => { state.selectedHouseviewId = button.dataset.houseviewId; state.houseviewAdvisory = null; renderHouseview(); loadHouseviewAdvisory(); }));
  document.querySelector('[data-houseview-client]').addEventListener('change', (event) => { state.selectedClientId = event.target.value; state.houseviewAdvisory = null; renderHouseview(); loadHouseviewAdvisory(); });
  document.querySelector('[data-tailor-positioning]')?.addEventListener('click', () => { state.activeJourneyAction = 'recommendation'; location.hash = 'opportunities'; });
  document.querySelectorAll('[data-control-detail]').forEach((button) => button.addEventListener('click', () => openRegulatoryControl(button.dataset.controlDetail, button)));
  if (!advisory) loadHouseviewAdvisory();
}

function renderHouseviewAdvisory(context) {
  const risk = context.riskContext;
  const activity = context.activityEvidence[0];
  return `<div class="houseview-client-body"><section class="houseview-risk"><div><span>Declared profile</span><strong>${risk.declaredScore}</strong><small>${escapeHtml(risk.declaredLabel)}</small></div><div><span>Observed behaviour</span><strong>${risk.observedIndicator}</strong><small>${escapeHtml(risk.reviewStatus.replaceAll('_',' '))}</small></div></section><div class="profile-boundary">${risk.declaredScore !== risk.observedIndicator ? `Observed activity changed from ${risk.previousObservedIndicator} to ${risk.observedIndicator}; declared profile remains ${risk.declaredScore} pending review.` : 'Observed activity is aligned with the declared profile.'}</div><section class="houseview-activity"><span>Latest activity</span><strong>${activity.activity_type} ${activity.asset_class} · S$${Number(activity.amount).toLocaleString('en-SG')}</strong><small>${escapeHtml(activity.explanation)}</small></section><h3>Retained candidates</h3><div class="candidate-list retained">${context.retainedCandidates.map((candidate) => `<div><span>✓</span><strong>${escapeHtml(candidate.name)}</strong><small>${escapeHtml(candidate.category.replaceAll('_',' '))}</small></div>`).join('') || '<p>No candidate passes every current gate.</p>'}</div><h3>Suppressed candidates</h3><div class="candidate-list suppressed">${context.suppressedCandidates.map((candidate) => `<details><summary><span>×</span><strong>${escapeHtml(candidate.name)}</strong></summary>${briefList(candidate.reasons)}</details>`).join('')}</div><h3>Regulatory controls</h3><div class="control-list">${context.regulatoryControls.map((control) => `<button class="${control.status.toLowerCase()}" data-control-detail="${control.ruleId}" type="button"><span>${escapeHtml(control.status.replaceAll('_',' '))}</span><strong>${escapeHtml(control.ruleId)}</strong><small>${escapeHtml(control.explanation)}</small></button>`).join('')}</div><button class="primary-button tailor-button" data-tailor-positioning type="button">Tailor positioning in Opportunity studio →</button><p class="houseview-disclaimer">${escapeHtml(context.disclaimer)}</p></div>`;
}

async function loadHouseviewAdvisory() {
  try {
    const response = await fetch(`/api/clients/${encodeURIComponent(state.selectedClientId)}/advisory-context?houseviewId=${encodeURIComponent(state.selectedHouseviewId)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.houseviewAdvisory = (await response.json()).context;
    if (state.route === 'houseview') renderHouseview();
  } catch (error) {
    showToast('Houseview advisory context is unavailable.');
    console.warn(error);
  }
}

async function openRegulatoryControl(ruleId, trigger) {
  if (ruleId.startsWith('INTERNAL-')) {
    openDialog(`<button class="modal-close" type="button" aria-label="Close control">×</button><p class="eyebrow">INTERNAL ADVISORY CONTROL</p><h2 id="modal-title">Retirement enhanced review</h2><p>Require current income, liquidity, commitments, objectives, horizon, risk capacity and applicable knowledge or experience before complex-product discussion.</p><div class="boundary-note">This is an internal safeguard. It is not an MAS automatic risk-score rule or a universal derivatives prohibition.</div><div class="modal-actions"><button class="secondary-button modal-close">Close</button></div>`, trigger);
    return;
  }
  try {
    const response = await fetch(`/api/regulatory-controls/${encodeURIComponent(ruleId)}`);
    const rule = (await response.json()).rule;
    openDialog(`<button class="modal-close" type="button" aria-label="Close control">×</button><p class="eyebrow">FRONTIER REGULATORY CONTROL PACK</p><h2 id="modal-title">${escapeHtml(rule.regulatory_rule_id)}</h2><p><strong>FAA-N16 paragraph ${escapeHtml(rule.paragraph)} · ${escapeHtml(rule.title)}</strong></p><p>${escapeHtml(rule.summary)}</p><div class="boundary-note">Curated internal demo extract. Consult the authoritative notice and Compliance or Legal owners.</div><div class="modal-actions"><button class="secondary-button modal-close">Close</button></div>`, trigger);
  } catch { showToast('Regulatory control could not be opened.'); }
}

function renderOperations() {
  const signals = [...state.liveSignals, ...state.data.signals].slice(0, 8);
  const services = [['Web cockpit', 'Healthy'], ['Azure OpenAI · gpt-4.1-mini', 'Live'], ['Fabric capacity · F4', 'Active'], ['FrontierRMLakehouse', 'Connected'], ['Teams bot', 'Healthy'], ['Deterministic fallback', 'Ready']];
  app.innerHTML = `<div class="page">${pageHeading('System pulse', 'Operations', 'Deployed service health, synthetic demo telemetry, and selectable captured agent runs.')}<div class="operations-truth"><strong>What is live?</strong><span>Service health reflects deployed components. The signal stream is synthetic demo telemetry. Agent events below replay the selected operator capture and do not execute continuously.</span></div><div class="operations-hero"><div><p class="eyebrow"><i></i> ALL SYSTEMS OPERATIONAL</p><h2>Frontier RM services are deployed</h2><p>Managed identity · grounded Azure AI · authenticated delivery</p></div><div class="ops-wave">${Array.from({ length: 24 }, (_, i) => `<i style="--h:${20 + (i * 17 % 70)}%"></i>`).join('')}</div></div><div class="operations-grid"><section class="panel"><div class="panel-header"><h2>Connected services</h2></div><div class="panel-body health-list">${services.map(([name, status], i) => `<div class="health-row motion-rise" style="--delay:${i * 80}ms"><strong>${name}</strong><span class="health-state">${status}</span></div>`).join('')}</div></section><section class="panel"><div class="panel-header section-heading"><div><h2>Synthetic signal telemetry</h2><p>Animated from the fictional demonstration dataset</p></div><span class="telemetry-chip">DEMO MOTION</span></div><div class="panel-body signal-feed">${signals.map((signal, i) => `<div class="signal-row motion-rise" style="--delay:${i * 70}ms"><span class="signal-time">${signal.time}</span><span class="signal-label">${signal.label}</span><div class="signal-text"><strong>${signal.client}</strong><span>${signal.text}</span></div></div>`).join('')}</div></section></div>${renderAgentRun()}<section class="architecture-flow panel"><div><span>RM cockpit</span><small>client context</small></div><b>→</b><div><span>Managed identity</span><small>no keys</small></div><b>→</b><div><span>Azure OpenAI</span><small>grounded preparation</small></div><b>→</b><div><span>Human review</span><small>RM-controlled action</small></div></section></div>`;
  document.querySelectorAll('[data-agent-filter]').forEach((button) => button.addEventListener('click', () => {
    state.agentEventFilter = button.dataset.agentFilter;
    renderOperations();
  }));
  document.querySelector('[data-run-select]')?.addEventListener('change', (event) => selectAgentRun(event.target.value));
  document.querySelectorAll('[data-agent-detail]').forEach((button) => button.addEventListener('click', () => openAgentDetail(button.dataset.agentDetail, button)));
}

function renderAgentRun() {
  const bundle = state.agentRun;
  if (!bundle) return `<section class="agent-review panel"><div class="agent-review-empty"><p class="eyebrow">TRANSPARENT AI</p><h2>Review Agents in Action</h2><p>No validated run bundle is available. Existing service telemetry remains unaffected.</p></div></section>`;
  const filters = ['All', ...new Set(bundle.events.map((event) => event.type))];
  const events = state.agentEventFilter === 'All' ? bundle.events : bundle.events.filter((event) => event.type === state.agentEventFilter);
  const modeLabel = bundle.run.mode === 'captured-live' ? 'Captured live run' : 'Contract rehearsal';
  const capturedAt = new Date(bundle.run.completedAt).toLocaleString('en-SG', { dateStyle: 'medium', timeStyle: 'short' });
  return `<section class="agent-review">
    <div class="section-heading agent-review-heading"><div><p class="eyebrow">TRANSPARENT AI · CAPTURED REPLAY</p><h2>Review Agents in Action</h2><p>Observable plans, delegation, evidence and verification. Select a capture or open an agent to inspect its safe operating contract.</p></div><div class="run-controls"><label for="run-select">Captured run</label><select id="run-select" data-run-select>${state.agentRuns.map((run) => `<option value="${run.id}" ${run.id === bundle.run.id ? 'selected' : ''}>${escapeHtml(run.displayLabel || run.mode)} · ${new Date(run.completedAt).toLocaleString('en-SG', { dateStyle: 'medium', timeStyle: 'short' })}</option>`).join('')}</select><span class="run-mode ${bundle.run.mode}">${modeLabel} · ${capturedAt}</span></div></div>
    <div class="agent-fleet">${bundle.agents.map((agent, index) => `<button class="agent-worker motion-rise" style="--delay:${index * 80}ms" data-agent-detail="${agent.id}" type="button"><div class="agent-worker-top"><span>${agent.name.split(' ').map((part) => part[0]).join('').slice(0, 2)}</span><b class="agent-status ${agent.status}">${agent.status}</b></div><h3>${agent.name}</h3><p>${agent.role}</p><small>View operating contract →</small></button>`).join('')}</div>
    <div class="agent-console">
      <section class="agent-events panel"><div class="panel-header"><div class="agent-events-title"><div><h3>Run event stream</h3><p>${bundle.run.clientName} · ${bundle.run.id}</p></div><strong>${events.length} events</strong></div><div class="event-filters">${filters.map((filter) => `<button class="${state.agentEventFilter === filter ? 'active' : ''}" data-agent-filter="${filter}">${filter}</button>`).join('')}</div></div><div class="agent-event-list">${events.map((event) => `<details class="agent-event"><summary><time>${new Date(event.timestamp).toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</time><span class="event-type">${event.type}</span><b>${bundle.agents.find((agent) => agent.id === event.agentId)?.name || event.agentId}</b><p>${escapeHtml(event.summary)}</p><i>⌄</i></summary><div><p>${escapeHtml(event.detail || 'No additional detail was retained for this event.')}</p>${event.evidenceIds?.length ? `<div class="event-evidence">${event.evidenceIds.map((id) => `<span>${escapeHtml(id)}</span>`).join('')}</div>` : ''}</div></details>`).join('')}</div></section>
      <aside class="verified-outcome panel"><div class="verified-mark">✓</div><p class="eyebrow">VERIFIED OUTCOME</p><h3>${bundle.outcome.verificationStatus === 'verified' ? 'Ready for RM review' : 'Revision required'}</h3><div class="outcome-meta"><span><b>${bundle.outcome.evidenceCount}</b> evidence references</span><span>Snapshot ${new Date(bundle.run.dataSnapshotAt).toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })}</span></div><h4>Meeting brief</h4><p>${escapeHtml(bundle.outcome.meetingBrief)}</p><h4>Unresolved</h4><ul>${bundle.outcome.unresolvedQuestions.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul><h4>Recommended actions</h4><ol>${bundle.outcome.recommendedActions.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ol><footer>Human review required before client communication.</footer></aside>
    </div>
  </section>`;
}

function openAgentDetail(agentId, trigger) {
  const agent = state.agentCatalog.find((item) => item.id === agentId);
  if (!agent) return;
  const section = (title, content) => `<section class="agent-contract-section"><h3>${title}</h3>${content}</section>`;
  openDialog(`<button class="modal-close" type="button" aria-label="Close agent details">×</button><p class="eyebrow">AGENT OPERATING CONTRACT · VERSION ${escapeHtml(agent.version)}</p><h2 id="modal-title">${escapeHtml(agent.name)}</h2><p>Presenter-safe operational summary. Verbatim private prompts and model reasoning are not retained here.</p><div class="agent-contract">${section('Objective', `<p>${escapeHtml(agent.objective)}</p>`)}${section('Runtime Task Prompt', `<p>${escapeHtml(agent.runtimeTaskPrompt)}</p>`)}${section('Agent System Instructions', `<p>${escapeHtml(agent.systemInstructions)}</p>`)}${section('Shared System Constraints', briefList(agent.sharedConstraints))}${section('Input Context', `<div class="contract-tags">${agent.inputContext.map((item) => `<span>${escapeHtml(item)}</span>`).join('')}</div>`)}${section('Structured Output', `<div class="contract-tags">${agent.structuredOutput.map((item) => `<span>${escapeHtml(item)}</span>`).join('')}</div>`)}${section('Workflow Handoff', `<p>${escapeHtml(agent.workflowHandoff)}</p>`)}</div><div class="modal-actions"><button class="secondary-button modal-close" type="button">Close</button></div>`, trigger);
  modalRoot.querySelector('.modal')?.classList.add('agent-modal');
}

async function loadAgentRun() {
  try {
    const listResponse = await fetch('/api/meeting-preparation/runs');
    if (!listResponse.ok) return;
    const listing = await listResponse.json();
    state.agentRuns = listing.runs || [];
    const latest = listing.runs?.[0];
    if (!latest) return;
    await selectAgentRun(latest.id, false);
  } catch (error) {
    console.warn('Agent run replay is unavailable.', error);
  }
}

async function selectAgentRun(runId, rerender = true) {
  try {
    const [summaryResponse, eventsResponse] = await Promise.all([
      fetch(`/api/meeting-preparation/runs/${encodeURIComponent(runId)}`),
      fetch(`/api/meeting-preparation/runs/${encodeURIComponent(runId)}/events`),
    ]);
    if (!summaryResponse.ok || !eventsResponse.ok) throw new Error(`Run ${runId} is unavailable`);
    const summary = await summaryResponse.json();
    const eventPayload = await eventsResponse.json();
    state.agentRun = { ...summary, events: eventPayload.events };
    state.agentEventFilter = 'All';
    if (rerender && state.route === 'operations') renderOperations();
  } catch (error) {
    showToast('The selected captured run could not be loaded.');
    console.warn('Agent run selection failed.', error);
  }
}

const STORY_SCENES = [
  { id: 'opening', label: 'The day begins', duration: 6500 },
  { id: 'signals', label: 'Sources converge', duration: 8000 },
  { id: 'client', label: 'Client 360', duration: 8000 },
  { id: 'reason', label: 'Briefing prepared', duration: 11000 },
  { id: 'govern', label: 'Recommendations', duration: 9000 },
  { id: 'act', label: 'Draft approved', duration: 7500 },
  { id: 'impact', label: 'Day in motion', duration: 7500 },
];

function startPresentation(initialIndex = 0) {
  state.presentation = { index: Math.max(0, Math.min(STORY_SCENES.length - 1, Number(initialIndex) || 0)), elapsed: 0, playing: true, last: performance.now() };
  state.presentationRecommendation = null; renderPresentation(); presentationFrame();
  setTimeout(() => runRecommendation('client-lim', 'briefing', true), state.presentation.index >= 3 ? 150 : 16000);
}
function closePresentation() { state.presentation = null; presentationRoot.innerHTML = ''; }
function presentationFrame(now = performance.now()) {
  if (!state.presentation) return;
  const p = state.presentation; const dt = now - p.last; p.last = now;
  if (p.playing) { p.elapsed += dt; const duration = STORY_SCENES[p.index].duration; if (p.elapsed >= duration) { if (p.index < STORY_SCENES.length - 1) { p.index += 1; p.elapsed = 0; renderPresentation(); } else p.playing = false; } updatePresentationProgress(); }
  requestAnimationFrame(presentationFrame);
}
function movePresentation(delta) { const p = state.presentation; p.index = Math.max(0, Math.min(STORY_SCENES.length - 1, p.index + delta)); p.elapsed = 0; p.playing = true; renderPresentation(); }
function updatePresentationProgress() { const p = state.presentation; const bar = document.querySelector(`[data-story-progress="${p.index}"]`); if (bar) bar.style.width = `${Math.min(100, p.elapsed / STORY_SCENES[p.index].duration * 100)}%`; }

function renderPresentation() {
  const p = state.presentation; const scene = STORY_SCENES[p.index];
  presentationRoot.innerHTML = `<div class="presentation"><div class="presentation-grid"></div><header><div class="presentation-brand"><span>F</span><b>FRONTIER RM<small>A day with intelligent banking</small></b></div><div class="story-progress">${STORY_SCENES.map((item, i) => `<button data-story-goto="${i}"><i><b data-story-progress="${i}" style="width:${i < p.index ? 100 : 0}%"></b></i><span>${item.label}</span></button>`).join('')}</div><button class="presentation-close">×</button></header><main>${sceneContent(scene.id, p.elapsed)}</main><footer><div class="presentation-ticker"><i></i>${escapeHtml(state.data.signals[(p.index + 1) % state.data.signals.length].client)} · ${escapeHtml(state.data.signals[(p.index + 1) % state.data.signals.length].text)}</div><div class="presentation-controls"><button data-story-prev>←</button><button data-story-play>${p.playing ? 'Ⅱ' : '▶'}</button><button data-story-next>→</button></div></footer></div>`;
  document.querySelector('.presentation-close').addEventListener('click', closePresentation);
  document.querySelector('[data-story-prev]').addEventListener('click', () => movePresentation(-1));
  document.querySelector('[data-story-next]').addEventListener('click', () => movePresentation(1));
  document.querySelector('[data-story-play]').addEventListener('click', () => { p.playing = !p.playing; renderPresentation(); });
  document.querySelectorAll('[data-story-goto]').forEach((button) => button.addEventListener('click', () => { p.index = Number(button.dataset.storyGoto); p.elapsed = 0; p.playing = true; renderPresentation(); }));
}

function sceneContent(id) {
  const daniel = clientById('client-lim'); const opp = state.presentationRecommendation || state.data.opportunities[0];
  if (id === 'opening') return `<section class="scene opening-scene"><p class="scene-label">08:30 · SINGAPORE</p><h1>What if every client need<br><em>arrived already understood?</em></h1><p>Meet John. 128 relationships. One intelligent workspace. Human judgement stays in control.</p><div class="scene-stats"><div><strong>128</strong><span>households</span></div><div><strong>S$184.6M</strong><span>assets under care</span></div><div><strong>4</strong><span>material signals</span></div></div></section>`;
  if (id === 'signals') return `<section class="scene signals-scene"><div><p class="scene-label">SOURCE CONVERGENCE</p><h1>Data, documents,<br><em>and client voice.</em></h1><p>Fabric Client 360, lifecycle events, past emails and meeting notes arrive as cited context before John starts his day.</p></div><div class="scene-signal-stack">${state.data.signals.map((signal, i) => `<article style="--delay:${i * 700}ms"><i>0${i + 1}</i><span><small>${i < 2 ? 'Fabric' : i === 2 ? 'Outlook' : 'SharePoint'}</small><strong>${signal.client}</strong><b>${signal.text}</b></span></article>`).join('')}</div></section>`;
  if (id === 'client') return `<section class="scene client-scene"><div class="scene-client-card"><span class="scene-avatar">DL</span><p class="scene-label">CLIENT 360 · 11:30 MEETING</p><h1>${daniel.name}</h1><p>${daniel.segment} · ${daniel.assets}</p><div class="scene-facts"><span><small>Risk</small>${daniel.riskProfile}</span><span><small>Profile</small>${daniel.kycStatus}</span><span><small>Contact</small>${daniel.contactPreference}</span></div></div><div class="scene-donut"><div><span><strong>S$4.8M</strong><small>relationship</small></span></div><p>Deposits <b>38%</b></p><p>Investments <b>31%</b></p><p>Lending <b>19%</b></p></div></section>`;
  if (id === 'reason') return `<section class="scene reason-scene"><div><p class="scene-label"><i></i> STAGE 1 · PREPARE BRIEFING</p><h1>Walk in already<br><em>briefed.</em></h1><div class="scene-reason-steps">${['Fabric Client 360', 'Past client emails', 'Meeting notes', 'Suitability boundaries'].map((label, i) => `<div style="--delay:${i * 900}ms"><i>✓</i><span><strong>${label}</strong><small>${opp.evidenceStages?.[i]?.detail || 'Resolved with a visible source reference.'}</small></span></div>`).join('')}</div></div><div class="scene-recommendation"><div class="scene-score">${opp.confidence}<small>% confidence</small></div><h2>${opp.title}</h2><p>${opp.summary}</p><blockquote>${opp.opening}</blockquote><span>${opp.provider === 'azure-openai' ? 'LIVE · gpt-4.1-mini' : 'PREPARING LIVE RESULT'}</span></div></section>`;
  if (id === 'govern') return `<section class="scene govern-scene"><p class="scene-label">STAGE 2 · CUSTOM RECOMMENDATIONS</p><div class="scene-chat"><div class="scene-user">Which fictional solution candidates fit Daniel's objectives and liquidity needs?</div><div class="scene-assistant"><b>F <span>Evidence-backed candidates</span></b><p>Keep a liquidity reserve, then compare a fictional liquidity fund and diversified balanced fund only after objectives, horizon, eligibility and suitability are confirmed.</p><footer>✓ Fabric Client 360 · Outlook correspondence · SharePoint product catalog</footer></div></div><div class="govern-pill">Why this? · Risks visible · Alternatives retained · Human review required</div></section>`;
  if (id === 'act') return `<section class="scene act-scene"><div class="action-check">✓</div><p class="scene-label">STAGE 3 · OPPORTUNITY DRAFT</p><h1>Drafted, not sent.</h1><p>Frontier prepares an editable client email and CRM opportunity record. John resolves placeholders, reviews the evidence and approves later use.</p><div class="action-ripple"><span>Email and CRM draft prepared</span><b>Nothing sent · Nothing committed</b></div></section>`;
  return `<section class="scene impact-scene"><p class="scene-label">17:45 · END-OF-DAY PULSE</p><h1>A day measured in<br><em>client outcomes.</em></h1><div class="impact-grid"><div><strong>4/4</strong><span>priority needs prepared</span></div><div><strong>5/5</strong><span>planned actions completed</span></div><div><strong>1h 45m</strong><span>time returned to John</span></div><div><strong>100%</strong><span>AI answers cited</span></div></div><p class="impact-close">Bank data, knowledge, applications and AI · working as one governed system.</p></section>`;
}

function bindGlobalActions() {
  document.querySelectorAll('[data-generate]').forEach((node) => node.addEventListener('click', () => { location.hash = 'opportunities'; setTimeout(() => runRecommendation(node.dataset.generate), 100); }));
  document.querySelectorAll('[data-open-client]').forEach((node) => node.addEventListener('click', () => { state.selectedClientId = node.dataset.openClient; location.hash = 'clients'; }));
  document.querySelectorAll('[data-start-story]').forEach((node) => node.addEventListener('click', startPresentation));
}

function render() {
  renderNav(); updateModeControl();
  const renderers = { today: renderToday, clients: renderClients, opportunities: renderOpportunities, sources: renderSources, operations: renderOperations, houseview: renderHouseview };
  (renderers[state.route] || renderToday)(); app.focus({ preventScroll: true });
  renderCopilot();
}

window.addEventListener('hashchange', () => { state.route = location.hash.slice(1) || 'today'; render(); });
copilotToggle.addEventListener('click', () => { if (state.copilotOpen) closeCopilot(); else openCopilot(); });
document.querySelector('#present-button').addEventListener('click', startPresentation);
document.querySelector('#mode-switch').addEventListener('click', () => { state.mode = state.mode === 'live' ? 'rehearsal' : 'live'; updateModeControl(); render(); showToast(state.mode === 'live' ? 'Live Azure AI enabled.' : 'Deterministic rehearsal mode enabled.'); });
window.addEventListener('keydown', (event) => {
  if (modalRoot.children.length) {
    if (event.key === 'Escape') closeModal();
    if (event.key === 'Tab') {
      const focusable = [...modalRoot.querySelectorAll('button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [href], [tabindex]:not([tabindex="-1"])')];
      if (!focusable.length) return;
      const first = focusable[0]; const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    return;
  }
  if (event.key === 'Escape' && state.copilotOpen) { closeCopilot(); return; }
  if (!state.presentation) return;
  if (event.key === 'Escape') closePresentation(); if (event.key === 'ArrowRight') movePresentation(1); if (event.key === 'ArrowLeft') movePresentation(-1); if (event.key === ' ') { event.preventDefault(); state.presentation.playing = !state.presentation.playing; renderPresentation(); }
});

try {
  const [dashboardResponse, healthResponse, agentsResponse, sourcesResponse] = await Promise.all([fetch('/api/dashboard'), fetch('/api/health'), fetch('/api/agents'), fetch('/api/sources')]);
  state.data = await dashboardResponse.json(); state.health = healthResponse.ok ? await healthResponse.json() : null;
  state.agentCatalog = agentsResponse.ok ? (await agentsResponse.json()).agents || [] : [];
  state.sources = sourcesResponse.ok ? (await sourcesResponse.json()).sources || [] : [];
  await loadAgentRun();
  state.mode = state.health?.provider === 'azure-openai' ? 'live' : 'rehearsal';
  render(); startTicker();
  const launch = new URLSearchParams(location.search);
  if (launch.get('settled') === '1') document.body.classList.add('capture-settled');
  if (launch.get('present') === '1') {
    window.setTimeout(() => startPresentation(launch.get('scene') || 0), 350);
  }
} catch (error) {
  app.innerHTML = `<div class="empty"><h2>Frontier RM could not start</h2><p>Check the API health endpoint and reload.</p></div>`;
  console.error(error);
}
