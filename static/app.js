/**
 * SaaSOptimizer AI — Google Antigravity Dashboard
 * Orchestrates Matter.js rigid-body physics, DOM synchronizer,
 * WebSockets live event stream, and Human-in-the-Loop approval workflows.
 */

(function () {
  'use strict';

  // --- State & DOM References ---
  const state = {
    subscriptions: [],
    auditLogs: [],
    activeProposal: null,
    physicsEnabled: true,
    gravityMode: 'normal', // 'normal', 'zero', 'reverse'
    ws: null,
    bodiesMap: new Map(), // DOM Element -> Matter.Body
  };

  // UI Elements
  const worldContainer = document.getElementById('antigravity-world');
  const cardsContainer = document.getElementById('saas-cards-container');
  const hitlModal = document.getElementById('hitl-modal');
  const auditTerminal = document.getElementById('audit-terminal');
  const terminalBody = document.getElementById('terminal-body');
  const detailDrawer = document.getElementById('detail-drawer');
  const archModal = document.getElementById('arch-modal');

  // Matter.js Module Aliases
  const { Engine, World, Bodies, Body, Vector, Runner, Events, Mouse, MouseConstraint } = Matter;

  let engine;
  let runner;
  let ground, leftWall, rightWall, ceiling;
  let mouseConstraint;

  // ==========================================================================
  // 1. Matter.js Physics Engine Initialization
  // ==========================================================================
  function initPhysics() {
    engine = Engine.create({
      gravity: { x: 0, y: 0.9, scale: 0.001 },
      enableSleeping: false,
    });

    runner = Runner.create();
    Runner.run(runner, engine);

    createBoundaries();

    // Mouse control for grabbing and tossing DOM elements
    const mouse = Mouse.create(document.body);
    mouseConstraint = MouseConstraint.create(engine, {
      mouse: mouse,
      constraint: {
        stiffness: 0.15,
        render: { visible: false },
      },
    });

    World.add(engine.world, mouseConstraint);

    // Sync DOM positions on every physics step
    Events.on(engine, 'afterUpdate', syncDomWithPhysics);

    window.addEventListener('resize', handleResize);
  }

  function createBoundaries() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const thickness = 100;

    if (ground) World.remove(engine.world, [ground, leftWall, rightWall, ceiling]);

    // Floor (sits right above bottom live HUD)
    ground = Bodies.rectangle(width / 2, height - 52 + thickness / 2, width * 2, thickness, {
      isStatic: true,
      friction: 0.8,
      restitution: 0.4,
    });

    // Ceiling (sits below top nav)
    ceiling = Bodies.rectangle(width / 2, 60 - thickness / 2, width * 2, thickness, {
      isStatic: true,
      restitution: 0.4,
    });

    // Left Wall
    leftWall = Bodies.rectangle(-thickness / 2, height / 2, thickness, height * 2, {
      isStatic: true,
      restitution: 0.4,
    });

    // Right Wall
    rightWall = Bodies.rectangle(width + thickness / 2, height / 2, thickness, height * 2, {
      isStatic: true,
      restitution: 0.4,
    });

    World.add(engine.world, [ground, ceiling, leftWall, rightWall]);
  }

  function handleResize() {
    createBoundaries();
  }

  // Register an HTML element with the physics world
  function registerPhysicsElement(el, initialPos = null) {
    if (!el || state.bodiesMap.has(el)) return;

    const rect = el.getBoundingClientRect();
    const w = rect.width || 300;
    const h = rect.height || 100;
    const x = initialPos ? initialPos.x : rect.left + w / 2;
    const y = initialPos ? initialPos.y : rect.top + h / 2;

    const body = Bodies.rectangle(x, y, w, h, {
      chamfer: { radius: 10 },
      friction: 0.1,
      frictionAir: 0.02,
      restitution: 0.45,
      density: 0.002,
    });

    body.domElement = el;
    state.bodiesMap.set(el, body);
    World.add(engine.world, body);

    // Prevent default touch/click drag collision
    el.style.position = 'absolute';
    el.style.left = '0px';
    el.style.top = '0px';
  }

  function syncDomWithPhysics() {
    state.bodiesMap.forEach((body, el) => {
      const rect = el.getBoundingClientRect();
      const hw = (rect.width || 300) / 2;
      const hh = (rect.height || 100) / 2;

      const px = body.position.x - hw;
      const py = body.position.y - hh;
      const angle = body.angle;

      el.style.transform = `translate3d(${px.toFixed(2)}px, ${py.toFixed(2)}px, 0px) rotate(${angle.toFixed(4)}rad)`;
    });
  }

  // Setup core Google Centerpiece elements as physics bodies
  function registerCenterpiecePhysics() {
    const ids = [
      'elem-logo-group',
      'elem-search-box',
      'elem-search-btns',
      'elem-scenario-chips',
    ];

    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (el) {
        registerPhysicsElement(el);
      }
    });
  }

  // Physics Control Modes
  function setGravity(mode) {
    state.gravityMode = mode;
    document.querySelectorAll('.dock-btn').forEach((btn) => btn.classList.remove('active'));

    if (mode === 'normal') {
      engine.gravity.x = 0;
      engine.gravity.y = 0.9;
      document.getElementById('btn-gravity-normal').classList.add('active');
    } else if (mode === 'zero') {
      engine.gravity.x = 0;
      engine.gravity.y = 0;
      document.getElementById('btn-gravity-zero').classList.add('active');
      // Give gentle drift impulse
      state.bodiesMap.forEach((body) => {
        Body.setVelocity(body, {
          x: (Math.random() - 0.5) * 2,
          y: (Math.random() - 0.5) * 2,
        });
      });
    } else if (mode === 'reverse') {
      engine.gravity.x = 0;
      engine.gravity.y = -0.9;
      document.getElementById('btn-gravity-reverse').classList.add('active');
    }
  }

  function applyExplosionImpulse() {
    const cx = window.innerWidth / 2;
    const cy = window.innerHeight / 2;

    state.bodiesMap.forEach((body) => {
      const forceVec = Vector.sub(body.position, { x: cx, y: cy });
      const dist = Math.max(Vector.magnitude(forceVec), 80);
      const normal = Vector.normalise(forceVec);
      const forceMag = (1500 / dist) * 0.04;

      Body.applyForce(body, body.position, {
        x: normal.x * forceMag,
        y: normal.y * forceMag - 0.02,
      });
      Body.setAngularVelocity(body, (Math.random() - 0.5) * 0.2);
    });
  }

  function reassembleElements() {
    setGravity('zero');
    const width = window.innerWidth;

    // Default target spots
    const targets = [
      { id: 'elem-logo-group', x: width / 2, y: 130 },
      { id: 'elem-search-box', x: width / 2, y: 240 },
      { id: 'elem-search-btns', x: width / 2, y: 310 },
      { id: 'elem-scenario-chips', x: width / 2, y: 380 },
    ];

    targets.forEach((t) => {
      const el = document.getElementById(t.id);
      if (el && state.bodiesMap.has(el)) {
        const body = state.bodiesMap.get(el);
        Body.setPosition(body, { x: t.x, y: t.y });
        Body.setVelocity(body, { x: 0, y: 0 });
        Body.setAngle(body, 0);
        Body.setAngularVelocity(body, 0);
      }
    });

    // Reassemble SaaS cards into balanced bottom grid
    let cardIdx = 0;
    const cards = Array.from(cardsContainer.children);
    const startX = Math.max(120, (width - (cards.length * 340)) / 2 + 160);

    cards.forEach((cardEl) => {
      if (state.bodiesMap.has(cardEl)) {
        const body = state.bodiesMap.get(cardEl);
        const tx = startX + cardIdx * 340;
        const ty = window.innerHeight - 200;
        Body.setPosition(body, { x: Math.min(tx, width - 180), y: ty });
        Body.setVelocity(body, { x: 0, y: 0 });
        Body.setAngle(body, 0);
        Body.setAngularVelocity(body, 0);
        cardIdx++;
      }
    });
  }

  // ==========================================================================
  // 2. SaaS Cards Rendering & Real-time Synchronization
  // ==========================================================================
  function renderSaaSCards(subscriptions) {
    state.subscriptions = subscriptions;
    cardsContainer.innerHTML = '';

    const width = window.innerWidth;
    const height = window.innerHeight;
    const count = subscriptions.length;
    const spacing = Math.min(340, (width - 100) / count);

    subscriptions.forEach((sub, idx) => {
      const card = createCardElement(sub);
      cardsContainer.appendChild(card);

      // Initial position spread across screen
      const initX = (width / 2) - ((count - 1) * spacing) / 2 + (idx * spacing);
      const initY = height - 260 + (idx % 2 === 0 ? -30 : 20);

      registerPhysicsElement(card, { x: initX, y: initY });
    });

    updateHudMetrics();
  }

  function createCardElement(sub) {
    const card = document.createElement('div');
    card.className = 'saas-card physics-element';
    card.id = `card-${sub.id}`;
    card.dataset.subId = sub.id;

    // Status pill determination
    let statusClass = 'pill-optimal';
    let statusText = 'HEALTHY';
    let isCritical = false;

    if (sub.days_until_renewal <= 14) {
      statusClass = 'pill-critical';
      statusText = `RENEWAL ${sub.days_until_renewal}D`;
      isCritical = true;
    } else if (sub.contract_terms && sub.contract_terms.has_mid_term_lock && sub.days_until_renewal > 30) {
      statusClass = 'pill-locked';
      statusText = 'MID-TERM LOCK';
    } else if (sub.idle_user_count > 0) {
      statusClass = 'pill-warning';
      statusText = `${sub.idle_user_count} IDLE SEATS`;
    }

    if (isCritical) {
      card.classList.add('has-critical-alert');
    }

    const iconMap = {
      slack: '💬',
      jira: '🔷',
      google: '🌐',
      github: '🐙',
    };
    const icon = iconMap[sub.icon_slug] || '💼';

    card.innerHTML = `
      <div class="card-header">
        <div class="tool-identity">
          <div class="tool-icon">${icon}</div>
          <div class="tool-name-wrap">
            <h4>${sub.name}</h4>
            <span class="tool-category">${sub.category}</span>
          </div>
        </div>
        <span class="status-pill ${statusClass}">${statusText}</span>
      </div>

      <div class="card-stats-grid">
        <div class="stat-col">
          <span class="stat-label">Total Seats</span>
          <span class="stat-number" id="card-total-${sub.id}">${sub.total_seats}</span>
        </div>
        <div class="stat-col">
          <span class="stat-label">Active</span>
          <span class="stat-number success">${sub.active_user_count}</span>
        </div>
        <div class="stat-col">
          <span class="stat-label">Idle (≥90d)</span>
          <span class="stat-number ${sub.idle_user_count > 0 ? 'danger' : ''}">${sub.idle_user_count}</span>
        </div>
      </div>

      <div class="utilization-bar-wrap">
        <div class="util-header">
          <span>Utilization</span>
          <strong>${sub.utilization_pct}%</strong>
        </div>
        <div class="bar-track">
          <div class="bar-fill ${sub.utilization_pct < 85 ? 'danger' : ''}" style="width: ${sub.utilization_pct}%;"></div>
        </div>
      </div>

      <div class="card-actions">
        <button class="card-btn secondary" data-action="inspect" data-sub-id="${sub.id}">
          🔍 Inspect
        </button>
        <button class="card-btn primary" data-action="optimize" data-sub-id="${sub.id}">
          ⚡ Optimize
        </button>
      </div>
    `;

    // Click handler for buttons inside card (stop propagation to prevent physics fling on click)
    card.addEventListener('click', (e) => {
      const btn = e.target.closest('.card-btn');
      if (!btn) return;
      e.stopPropagation();

      const action = btn.dataset.action;
      const subId = btn.dataset.subId;

      if (action === 'inspect') {
        openInspectionDrawer(subId);
      } else if (action === 'optimize') {
        runOptimizationForSubscription(subId);
      }
    });

    return card;
  }

  function updateHudMetrics() {
    let totalSeats = 0;
    let totalIdle = 0;
    let totalAnnualWaste = 0;

    state.subscriptions.forEach((sub) => {
      totalSeats += sub.total_seats;
      totalIdle += sub.idle_user_count;
      totalAnnualWaste += sub.idle_user_count * sub.cost_per_seat_monthly * 12;
    });

    document.getElementById('hud-sub-count').textContent = `${state.subscriptions.length} Applications`;
    document.getElementById('hud-total-seats').textContent = `${totalSeats} Seats`;
    document.getElementById('hud-idle-seats').textContent = `${totalIdle} Idle`;
    document.getElementById('hud-savings').textContent = `$${totalAnnualWaste.toLocaleString()} / yr`;
  }

  // ==========================================================================
  // 3. WebSocket Real-time Event Streaming
  // ==========================================================================
  function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
      logToTerminal('SYSTEM', 'WebSocket connection established with FastAPI Agent Engine.', 'green');
    };

    state.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleServerMessage(msg);
      } catch (err) {
        console.error('Error parsing WS message:', err);
      }
    };

    state.ws.onclose = () => {
      logToTerminal('SYSTEM', 'WebSocket disconnected. Retrying in 3s...', 'yellow');
      setTimeout(initWebSocket, 3000);
    };
  }

  function handleServerMessage(msg) {
    const { type, payload } = msg;

    if (type === 'initial_state') {
      renderSaaSCards(payload.subscriptions);
      if (payload.audit_logs) {
        payload.audit_logs.reverse().forEach((log) => appendAuditEntry(log));
      }
    } else if (type === 'subscriptions_updated') {
      renderSaaSCards(payload);
    } else if (type === 'audit_event') {
      appendAuditEntry(payload);
    } else if (type === 'hitl_prompt') {
      if (payload.proposal) {
        openHitlModal(payload.proposal);
      }
    } else if (type === 'system_reset') {
      renderSaaSCards(payload.subscriptions);
      terminalBody.innerHTML = '';
      logToTerminal('SYSTEM', 'Mock consoles and state store reset to baseline.', 'green');
    }
  }

  function appendAuditEntry(log) {
    const entry = document.createElement('div');
    entry.className = 'log-entry';

    const timeStr = new Date(log.timestamp).toLocaleTimeString();
    entry.innerHTML = `
      <span class="log-time">[${timeStr}]</span>
      <span class="log-badge ${log.event_type}">${log.event_type}</span>
      <span class="log-msg"><strong>${escapeHtml(log.title)}:</strong> ${escapeHtml(log.message)}</span>
    `;

    terminalBody.appendChild(entry);
    terminalBody.scrollTop = terminalBody.scrollHeight;

    if (log.event_type === 'VERIFICATION_SUCCESS') {
      document.getElementById('hud-verified-count').textContent = 'Verified (100%)';
    }
  }

  function logToTerminal(badge, text, color = 'blue') {
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    const timeStr = new Date().toLocaleTimeString();
    entry.innerHTML = `
      <span class="log-time">[${timeStr}]</span>
      <span class="log-badge ${badge}" style="color: ${color}">[${badge}]</span>
      <span class="log-msg">${escapeHtml(text)}</span>
    `;
    terminalBody.appendChild(entry);
    terminalBody.scrollTop = terminalBody.scrollHeight;
  }

  // ==========================================================================
  // 4. Scenario Runners & Action Gate Handlers
  // ==========================================================================
  async function runScenario(scenarioId) {
    logToTerminal('SCENARIO', `Triggering scenario ${scenarioId}...`, 'yellow');

    try {
      const resp = await fetch(`/api/scenarios/${scenarioId}/run`, { method: 'POST' });
      const data = await resp.json();

      if (!resp.ok) {
        logToTerminal('ERROR', data.detail || 'Scenario execution failed.', 'red');
        return;
      }

      if (data.proposal && data.proposal.status === 'AWAITING_APPROVAL') {
        openHitlModal(data.proposal);
      } else if (data.scenario === 'TC1') {
        logToTerminal('TC1_PASS', `Slack Enterprise 14-day renewal alert triggered! Utilization: ${data.renewal_alert?.utilization_pct}%.`, '#34d399');
      } else if (data.scenario === 'TC2') {
        logToTerminal('TC2_PASS', `Flagged ${data.idle_users_count} idle users including dev_user_04 (94d inactive).`, '#34d399');
      } else if (data.scenario === 'TC3') {
        logToTerminal('TC3_PASS', `Google Workspace mid-term contract lock verified. Action DEFERRED successfully.`, '#c084fc');
      }
    } catch (err) {
      logToTerminal('ERROR', `Network failure triggering ${scenarioId}: ${err.message}`, 'red');
    }
  }

  async function runOptimizationForSubscription(subId) {
    let scenario = 'TC1';
    if (subId.includes('jira')) scenario = 'TC4';
    else if (subId.includes('google')) scenario = 'TC3';
    await runScenario(scenario);
  }

  // HITL Action Gate Modal Logic
  function openHitlModal(proposal) {
    state.activeProposal = proposal;

    document.getElementById('modal-title').textContent = `Review Rightsizing: ${proposal.subscription_name}`;
    document.getElementById('prop-curr-seats').textContent = proposal.current_seats;
    document.getElementById('prop-target-seats').textContent = proposal.proposed_seats;
    document.getElementById('prop-diff-seats').textContent = `-${proposal.seats_to_remove}`;
    document.getElementById('prop-savings-mo').textContent = `$${proposal.monthly_savings_usd.toFixed(2)}`;

    // Render flagged users list
    const listEl = document.getElementById('modal-user-list');
    listEl.innerHTML = '';
    proposal.idle_user_ids.forEach((id) => {
      const tag = document.createElement('span');
      tag.className = 'user-tag';
      tag.innerHTML = `<span>👤</span> ${id} (≥90d inactive)`;
      listEl.appendChild(tag);
    });

    hitlModal.classList.remove('hidden');
  }

  function closeHitlModal() {
    hitlModal.classList.add('hidden');
    state.activeProposal = null;
  }

  async function approveProposal() {
    if (!state.activeProposal) return;
    const propId = state.activeProposal.proposal_id;
    closeHitlModal();

    logToTerminal('HITL_AUTH', `Operator approved proposal ${propId}. Dispatching API downscaling call...`, '#34d399');

    try {
      const resp = await fetch(`/api/proposals/${propId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'ops_lead_admin', notes: 'Approved via Antigravity UI' }),
      });
      const data = await resp.json();

      if (resp.ok) {
        logToTerminal(
          'VERIFIED',
          `Console mutation verified! Target: ${data.verification.target_seats} == Observed: ${data.verification.observed_seats}. SHA256: ${data.verification.verification_hash.slice(0, 16)}...`,
          '#22d3ee'
        );
      } else {
        logToTerminal('ERROR', data.detail || 'Approval failed.', 'red');
      }
    } catch (err) {
      logToTerminal('ERROR', `Approval request failed: ${err.message}`, 'red');
    }
  }

  async function rejectProposal() {
    if (!state.activeProposal) return;
    const propId = state.activeProposal.proposal_id;
    closeHitlModal();

    logToTerminal('HITL_REJECT', `Operator rejected proposal ${propId}. Action deferred.`, '#f87171');

    try {
      await fetch(`/api/proposals/${propId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'ops_lead_admin', reason: 'Rejected from Antigravity UI' }),
      });
    } catch (err) {
      console.error(err);
    }
  }

  // Inspection Drawer
  function openInspectionDrawer(subId) {
    const sub = state.subscriptions.find((s) => s.id === subId);
    if (!sub) return;

    document.getElementById('drawer-sub-name').textContent = sub.name;
    const content = document.getElementById('drawer-content');

    const usersHtml = sub.users
      .map((u) => {
        const isIdle = u.last_active_days_ago >= 90;
        return `
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; margin-bottom: 6px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid ${isIdle ? 'rgba(234,67,53,0.3)' : 'rgba(255,255,255,0.05)'}">
            <div>
              <div style="font-size: 13px; font-weight: 600; color: #fff;">${escapeHtml(u.name)} <span style="font-size: 11px; color: #94a3b8;">(${escapeHtml(u.user_id)})</span></div>
              <div style="font-size: 11px; color: #64748b;">${escapeHtml(u.email)} · ${escapeHtml(u.role)}</div>
            </div>
            <div style="text-align: right;">
              <span style="font-size: 11px; font-weight: 700; color: ${isIdle ? '#f87171' : '#34d399'};">
                ${u.last_active_days_ago}d ago
              </span>
              <div style="font-size: 10px; color: #64748b;">${isIdle ? 'IDLE' : 'ACTIVE'}</div>
            </div>
          </div>
        `;
      })
      .join('');

    content.innerHTML = `
      <div style="margin-bottom: 20px;">
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase;">Contract Overview</div>
        <div style="font-size: 14px; margin-top: 4px;">Renewal in <strong>${sub.days_until_renewal} days</strong> · Cost: <strong>$${sub.cost_per_seat_monthly}/mo/seat</strong></div>
        <div style="font-size: 13px; color: #60a5fa; margin-top: 2px;">Mid-Term Lock: ${sub.contract_terms.has_mid_term_lock ? 'Enforced' : 'Flexible'} (Window: ${sub.contract_terms.reduction_window_days_before_renewal}d prior)</div>
      </div>
      <h4 style="font-size: 13px; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px;">User Seat Assignments (${sub.users.length})</h4>
      <div style="max-height: 480px; overflow-y: auto;">
        ${usersHtml}
      </div>
    `;

    detailDrawer.classList.remove('hidden');
  }

  function closeInspectionDrawer() {
    detailDrawer.classList.add('hidden');
  }

  // Utilities
  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[m]);
  }

  // ==========================================================================
  // 5. DOM Event Binding & Initialization
  // ==========================================================================
  function bindDomEvents() {
    // Gravity Dock buttons
    document.getElementById('btn-gravity-normal').addEventListener('click', () => setGravity('normal'));
    document.getElementById('btn-gravity-zero').addEventListener('click', () => setGravity('zero'));
    document.getElementById('btn-gravity-reverse').addEventListener('click', () => setGravity('reverse'));
    document.getElementById('btn-physics-explode').addEventListener('click', applyExplosionImpulse);
    document.getElementById('btn-physics-gather').addEventListener('click', reassembleElements);

    // Scenario Trigger Chips
    document.getElementById('chip-tc1').addEventListener('click', () => runScenario('TC1'));
    document.getElementById('chip-tc2').addEventListener('click', () => runScenario('TC2'));
    document.getElementById('chip-tc3').addEventListener('click', () => runScenario('TC3'));
    document.getElementById('chip-tc4').addEventListener('click', () => runScenario('TC4'));

    document.getElementById('chip-reset').addEventListener('click', async () => {
      await fetch('/api/reset', { method: 'POST' });
    });

    // Google Buttons
    document.getElementById('btn-run-all').addEventListener('click', async () => {
      await runScenario('TC1');
      setTimeout(() => runScenario('TC4'), 800);
    });

    document.getElementById('btn-feeling-lucky').addEventListener('click', () => {
      applyExplosionImpulse();
      runScenario('TC4');
    });

    // HITL Modal Buttons
    document.getElementById('btn-hitl-approve').addEventListener('click', approveProposal);
    document.getElementById('btn-hitl-reject').addEventListener('click', rejectProposal);
    document.getElementById('modal-close-btn').addEventListener('click', closeHitlModal);

    // Drawers & Modals
    document.getElementById('drawer-close-btn').addEventListener('click', closeInspectionDrawer);
    document.getElementById('btn-docs').addEventListener('click', () => archModal.classList.remove('hidden'));
    document.getElementById('arch-modal-close').addEventListener('click', () => archModal.classList.add('hidden'));

    // Terminal controls
    const toggleTerminal = () => auditTerminal.classList.toggle('hidden');
    document.getElementById('btn-toggle-terminal').addEventListener('click', toggleTerminal);
    document.getElementById('hud-terminal-btn').addEventListener('click', toggleTerminal);
    document.getElementById('btn-close-terminal').addEventListener('click', () => auditTerminal.classList.add('hidden'));
    document.getElementById('btn-clear-terminal').addEventListener('click', () => {
      terminalBody.innerHTML = '';
      logToTerminal('SYSTEM', 'Terminal log cleared.', 'yellow');
    });
  }

  // --- Bootstrapping on DOM Load ---
  document.addEventListener('DOMContentLoaded', () => {
    initPhysics();
    registerCenterpiecePhysics();
    bindDomEvents();
    initWebSocket();
  });
})();
