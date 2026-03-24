'use strict';

const WS_URL = 'ws://localhost:8765';
const RECONNECT_DELAY_MS = 3000;

const elHealth = document.getElementById('health');
const elCounter = document.getElementById('counter');
const elActiveList = document.getElementById('active-list');
const elHistoryList = document.getElementById('history-list');
const tabs = document.querySelectorAll('.tab');

let socket = null;

// --- Tab switching ---
tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((t) => t.classList.remove('tab--active'));
    tab.classList.add('tab--active');
    const target = tab.dataset.tab;
    document.getElementById('view-active').classList.toggle(
      'view--hidden', target !== 'active'
    );
    document.getElementById('view-history').classList.toggle(
      'view--hidden', target !== 'history'
    );
  });
});

// --- WebSocket connection ---
function connect() {
  socket = new WebSocket(WS_URL);

  socket.addEventListener('open', () => {
    setHealth(true);
  });

  socket.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'state') {
      renderActive(data.active || []);
      renderHistory(data.history || []);
      updateCounter(data.stats?.active_count ?? 0);
    }
  });

  socket.addEventListener('close', () => {
    setHealth(false);
    setTimeout(connect, RECONNECT_DELAY_MS);
  });

  socket.addEventListener('error', () => {
    setHealth(false);
  });
}

function setHealth(online) {
  elHealth.classList.toggle('health--online', online);
  elHealth.classList.toggle('health--offline', !online);
}

function updateCounter(count) {
  elCounter.textContent = `${count} лимиток`;
}

// --- Rendering ---
function renderActive(orders) {
  if (!orders.length) {
    elActiveList.innerHTML = '<p class="empty">Нет активных лимиток</p>';
    return;
  }
  elActiveList.innerHTML = orders.map(buildActiveCard).join('');
}

function buildActiveCard(o) {
  const sideClass = o.side === 'buy' ? 'card--buy' : 'card--sell';
  const time = new Date(o.time).toLocaleTimeString();
  return `
    <div class="card ${sideClass}">
      <div class="card__header">
        <span class="card__token">${o.token}</span>
        <span class="card__side">${o.side.toUpperCase()}</span>
      </div>
      <div class="card__row">
        <span>Цена:</span><span>${o.px}</span>
      </div>
      <div class="card__row">
        <span>Размер:</span><span>${o.sz}</span>
      </div>
      <div class="card__row">
        <span>USDC:</span><span>$${o.usdc.toLocaleString()}</span>
      </div>
      <div class="card__footer">
        <span class="card__time">${time}</span>
        <span class="card__hash">${o.tx_hash ? o.tx_hash.slice(0, 10) + '...' : ''}</span>
      </div>
    </div>`;
}

function renderHistory(records) {
  if (!records.length) {
    elHistoryList.innerHTML = '<p class="empty">История пуста</p>';
    return;
  }
  elHistoryList.innerHTML = records
    .slice()
    .reverse()
    .map(buildHistoryCard)
    .join('');
}

function buildHistoryCard(rec) {
  const o = rec.order;
  const appeared = new Date(rec.appeared_at).toLocaleTimeString();
  const disappeared = new Date(rec.disappeared_at).toLocaleTimeString();
  const reasonClass = `reason--${rec.reason}`;
  return `
    <div class="card card--history">
      <div class="card__header">
        <span class="card__token">${o.token}</span>
        <span class="card__reason ${reasonClass}">${rec.reason}</span>
      </div>
      <div class="card__row">
        <span>Цена:</span><span>${o.px}</span>
      </div>
      <div class="card__row">
        <span>USDC:</span><span>$${o.usdc.toLocaleString()}</span>
      </div>
      <div class="card__row">
        <span>Появилась:</span><span>${appeared}</span>
      </div>
      <div class="card__row">
        <span>Исчезла:</span><span>${disappeared}</span>
      </div>
    </div>`;
}

// --- Init ---
if (window.Telegram?.WebApp) {
  window.Telegram.WebApp.ready();
}
connect();
