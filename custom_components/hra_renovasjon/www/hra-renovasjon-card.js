const HRA_ASSET_URL = "/api/hra_renovasjon/assets";

const HRA_TYPES = {
  Restavfall: { icon: "mdi:trash-can-outline", asset: "waste-new.png", color: "#69717a" },
  Matavfall: { icon: "mdi:food-apple-outline", asset: "organic-new.png", color: "#7b9e4b" },
  Plastemballasje: { icon: "mdi:bottle-soda-outline", asset: "plastic-new.png", color: "#d9a441" },
  "Papir, papp og kartong": { icon: "mdi:file-document-outline", asset: "paper_carton.png", color: "#4b79a8" },
  "Glass- og metallemballasje": { icon: "mdi:glass-fragile", asset: "glass_metal.png", color: "#4e9b94" },
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function isSummaryState(state) {
  const attributes = state?.attributes || {};
  return Boolean(
    attributes.agreement_guid &&
      Array.isArray(attributes.upcoming) &&
      attributes.upcoming.some((item) => item && typeof item === "object"),
  );
}

class HraRenovasjonCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = { max_dates: 4, title: "HRA hentedager", ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 5;
  }

  static getConfigElement() {
    return document.createElement("hra-renovasjon-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  _summaryCandidates() {
    if (!this._hass?.states) return [];
    return Object.entries(this._hass.states)
      .filter(([entityId, state]) => entityId.startsWith("sensor.") && isSummaryState(state))
      .map(([entityId]) => entityId)
      .sort();
  }

  _resolvedEntityId() {
    if (this._config.entity) return this._config.entity;
    const candidates = this._summaryCandidates();
    return candidates.length === 1 ? candidates[0] : null;
  }

  _state() {
    const entityId = this._resolvedEntityId();
    return entityId ? this._hass?.states?.[entityId] : undefined;
  }

  _resolvedCalendarId(summaryEntityId) {
    if (this._config.calendar) return this._config.calendar;
    if (!this._hass || !summaryEntityId) return null;
    const summaryEntry = this._hass.entities?.[summaryEntityId];
    if (summaryEntry?.device_id) {
      const relatedCalendar = Object.values(this._hass.entities || {}).find(
        (entry) => entry.device_id === summaryEntry.device_id && entry.entity_id.startsWith("calendar."),
      );
      if (relatedCalendar) return relatedCalendar.entity_id;
    }
    const objectId = summaryEntityId.replace(/^sensor\./, "").replace(/_hra_neste_henting$/, "");
    const fallback = `calendar.${objectId}_hra_hentedager`;
    return this._hass.states?.[fallback] ? fallback : null;
  }

  _events() {
    const attributes = this._state()?.attributes || {};
    const rawEvents = Array.isArray(attributes.upcoming) ? attributes.upcoming : [];
    const events = rawEvents
      .map((event) => ({ waste_type: event?.waste_type, date: event?.date }))
      .filter((event) => event.waste_type && /^\d{4}-\d{2}-\d{2}$/.test(event.date));
    if (!events.length && attributes.waste_type && attributes.next_collection) {
      events.push({ waste_type: attributes.waste_type, date: attributes.next_collection });
    }
    const grouped = new Map();
    for (const event of events) {
      if (!grouped.has(event.date)) grouped.set(event.date, new Set());
      grouped.get(event.date).add(event.waste_type);
    }
    return [...grouped.entries()]
      .map(([date, wasteTypes]) => ({ date, wasteTypes: [...wasteTypes] }))
      .sort((a, b) => a.date.localeCompare(b.date));
  }

  _daysUntil(dateString) {
    const target = new Date(`${dateString}T00:00:00`);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return Math.round((target - today) / 86400000);
  }

  _relativeDate(dateString) {
    const days = this._daysUntil(dateString);
    if (days <= 0) return "I dag";
    if (days === 1) return "I morgen";
    return `Om ${days} dager`;
  }

  _formatDate(dateString) {
    const language = this._hass?.locale?.language || "nb-NO";
    return new Intl.DateTimeFormat(language, { day: "numeric", month: "long" }).format(new Date(`${dateString}T00:00:00`));
  }

  _typeInfo(type) {
    return HRA_TYPES[type] || { icon: "mdi:recycle", asset: null, color: "#8a6aa8" };
  }

  _typeLabel(type) {
    return type.replace("Papir, papp og kartong", "Papir/papp").replace("Glass- og metallemballasje", "Glass/metall");
  }

  _typeMarkup(type) {
    const info = this._typeInfo(type);
    const icon = info.asset
      ? `<img src="${HRA_ASSET_URL}/${info.asset}" alt="" />`
      : `<ha-icon icon="${info.icon}"></ha-icon>`;
    return `<span class="type" style="--type-color:${info.color}" title="${escapeHtml(type)}"><span class="type-icon">${icon}</span><span class="type-label">${escapeHtml(this._typeLabel(type))}</span></span>`;
  }

  _openMoreInfo(entityId) {
    if (!entityId) return;
    this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
  }

  _renderDiscoveryError() {
    const candidates = this._summaryCandidates();
    const message = candidates.length > 1
      ? "Flere HRA-avtaler funnet. Velg en sammendragssensor i kortkonfigurasjonen."
      : "Fant ingen HRA-sammendragssensor ennå.";
    this.shadowRoot.innerHTML = `<style>${this._styles()}</style><ha-card><div class="shell empty-state"><ha-icon icon="mdi:trash-can-outline"></ha-icon><div><strong>HRA hentedager</strong><p>${message}</p></div></div></ha-card>`;
  }

  _render() {
    if (!this.shadowRoot) return;
    const entityId = this._resolvedEntityId();
    const state = this._state();
    if (!entityId || !state) {
      this._renderDiscoveryError();
      return;
    }
    const attributes = state.attributes || {};
    const events = this._events();
    const first = events[0];
    const maxDates = Math.max(1, Number(this._config.max_dates) || 4);
    const days = first ? this._daysUntil(first.date) : null;
    const urgency = first ? (days <= 0 ? "today" : days === 1 ? "tomorrow" : "normal") : "empty";
    const title = escapeHtml(this._config.title || "HRA hentedager");
    const address = escapeHtml(attributes.address || "Adresse ikke tilgjengelig");
    const statusText = first ? this._relativeDate(first.date) : "Ingen kommende henting";
    const summaryTypes = first ? first.wasteTypes.map((type) => this._typeMarkup(type)).join("") : `<span class="empty-text">Sjekk HRA-avtalen eller oppdater integrasjonen.</span>`;
    const calendarId = this._resolvedCalendarId(entityId);
    const calendarButton = calendarId
      ? `<button class="calendar-button" type="button" aria-label="Åpne HRA-kalenderen" data-action="calendar"><ha-icon icon="mdi:calendar-month-outline"></ha-icon></button>`
      : "";
    const upcomingRows = events.slice(1, maxDates).map((event) => `<div class="timeline-row"><div class="timeline-date"><strong>${this._formatDate(event.date)}</strong><span>${this._relativeDate(event.date)}</span></div><div class="timeline-types">${event.wasteTypes.map((type) => this._typeMarkup(type)).join("")}</div></div>`).join("");

    this.shadowRoot.innerHTML = `<style>${this._styles()}</style><ha-card><div class="shell"><div class="header"><div class="heading"><ha-icon icon="mdi:trash-can-outline"></ha-icon><div><div>${title}</div><span class="address">${address}</span></div></div>${calendarButton}</div><div class="hero ${urgency}" data-action="summary" role="button" tabindex="0" aria-label="Vis neste henting"><div class="hero-copy"><div class="eyebrow">Neste henting</div><div class="hero-date">${first ? this._formatDate(first.date) : statusText}</div><div class="type-list">${summaryTypes}</div>${first ? `<div class="status-line"><span class="hero-status">${statusText}</span></div>` : ""}</div><ha-icon class="hero-icon" icon="mdi:truck-outline"></ha-icon></div>${upcomingRows ? `<div class="timeline"><div class="section-label">Deretter</div>${upcomingRows}</div>` : ""}<div class="footer"><span>${events.length > maxDates ? `Viser ${maxDates} av ${events.length} datoer` : "Kommende hentedager"}</span><span>HRA</span></div></div></ha-card>`;

    this.shadowRoot.querySelectorAll("[data-action]").forEach((element) => {
      const action = () => this._openMoreInfo(element.dataset.action === "calendar" ? calendarId : entityId);
      element.addEventListener("click", action);
      element.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); action(); }
      });
    });
  }

  _styles() {
    return `:host { --hra-surface: var(--ha-card-background, var(--card-background-color, #fff)); --hra-text: var(--primary-text-color, #202124); --hra-secondary: var(--secondary-text-color, #6b7280); --hra-divider: var(--divider-color, rgba(127,127,127,.18)); display:block; } ha-card { overflow:hidden; color:var(--hra-text); background:var(--hra-surface); } .shell { padding:18px 18px 14px; } .header, .hero, .timeline-row, .footer { display:flex; align-items:center; } .header { justify-content:space-between; gap:12px; margin-bottom:16px; } .heading { display:flex; align-items:center; gap:10px; font-weight:600; } .heading > ha-icon { color:var(--primary-color, #5078a0); } .address { display:block; color:var(--hra-secondary); font-size:.76rem; font-weight:400; margin-top:3px; } button { color:inherit; font:inherit; } .calendar-button { border:0; background:transparent; padding:7px; border-radius:50%; cursor:pointer; color:var(--hra-secondary); } .calendar-button:hover, .calendar-button:focus-visible { background:var(--ha-card-border-color, rgba(127,127,127,.12)); color:var(--hra-text); outline:none; } .hero { border-radius:16px; padding:16px; background:color-mix(in srgb, var(--primary-color, #5078a0) 10%, var(--hra-surface)); border-left:4px solid var(--primary-color, #5078a0); cursor:pointer; } .hero.today { background:color-mix(in srgb, #e06a4f 13%, var(--hra-surface)); border-left-color:#d45b42; } .hero.tomorrow { background:color-mix(in srgb, #d4a43a 13%, var(--hra-surface)); border-left-color:#c38e24; } .hero.empty { background:color-mix(in srgb, var(--hra-secondary) 9%, var(--hra-surface)); border-left-color:var(--hra-secondary); } .hero-copy { flex:1; min-width:0; } .eyebrow, .section-label { color:var(--hra-secondary); font-size:.72rem; text-transform:uppercase; letter-spacing:.1em; } .eyebrow { margin-bottom:4px; } .hero-date { font-size:1.08rem; font-weight:600; margin-bottom:10px; } .hero-icon { color:var(--primary-color, #5078a0); opacity:.85; } .today .hero-icon { color:#d45b42; } .type-list, .timeline-types { display:flex; flex-wrap:wrap; gap:7px; } .type { display:inline-flex; align-items:center; gap:6px; min-height:28px; padding:3px 9px 3px 4px; border-radius:15px; background:color-mix(in srgb, var(--type-color) 12%, var(--hra-surface)); color:var(--hra-text); font-size:.83rem; } .type-icon { display:grid; place-items:center; width:22px; height:22px; color:var(--type-color); } .type-icon img { width:22px; height:22px; object-fit:contain; border-radius:50%; } .type-icon ha-icon { --mdc-icon-size:20px; } .status-line { margin-top:11px; } .hero-status { display:inline-flex; align-items:center; padding:4px 9px; border-radius:10px; background:var(--primary-color, #5078a0); color:var(--text-primary-color, #fff); font-size:.78rem; font-weight:600; } .today .hero-status { background:#d45b42; } .tomorrow .hero-status { background:#c38e24; } .timeline { margin-top:18px; } .section-label { margin:0 0 8px 2px; } .timeline-row { justify-content:space-between; gap:12px; padding:10px 2px; border-top:1px solid var(--hra-divider); } .timeline-date { display:flex; flex-direction:column; gap:2px; min-width:112px; } .timeline-date strong { font-size:.88rem; font-weight:600; } .timeline-date span { color:var(--hra-secondary); font-size:.75rem; } .timeline-types { justify-content:flex-end; } .timeline-types .type { font-size:.76rem; padding-right:7px; } .timeline-types .type-icon, .timeline-types .type-icon img { width:19px; height:19px; } .timeline-types .type-icon ha-icon { --mdc-icon-size:17px; } .empty-text, .empty-state p { color:var(--hra-secondary); font-size:.84rem; } .footer { justify-content:space-between; margin-top:12px; color:var(--hra-secondary); font-size:.72rem; } .empty-state { display:flex; align-items:center; gap:12px; padding:18px; } .empty-state > ha-icon { color:var(--primary-color, #5078a0); } .empty-state p { margin:4px 0 0; } @media (max-width:420px) { .shell { padding:15px; } .timeline-row { align-items:flex-start; flex-direction:column; gap:6px; } .timeline-types { justify-content:flex-start; } }`;
  }
}

class HraRenovasjonCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _summaryCandidates() {
    return Object.entries(this._hass?.states || {})
      .filter(([entityId, state]) => entityId.startsWith("sensor.") && isSummaryState(state))
      .map(([entityId]) => entityId)
      .sort();
  }

  _calendarCandidates(entityId) {
    const registryEntry = this._hass?.entities?.[entityId];
    const related = registryEntry?.device_id
      ? Object.values(this._hass.entities || {}).filter((entry) => entry.device_id === registryEntry.device_id && entry.entity_id.startsWith("calendar."))
      : [];
    return related.length ? related.map((entry) => entry.entity_id).sort() : Object.keys(this._hass?.states || {}).filter((id) => id.startsWith("calendar.") && id.includes("hra_hentedager")).sort();
  }

  _selectedSummary() {
    if (this._config.entity) return this._config.entity;
    const candidates = this._summaryCandidates();
    return candidates.length === 1 ? candidates[0] : "";
  }

  _fireConfig(config) {
    this._config = { ...config };
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
  }

  _render() {
    if (!this.shadowRoot) return;
    const summaryCandidates = this._summaryCandidates();
    const selectedSummary = this._selectedSummary();
    const calendarCandidates = this._calendarCandidates(selectedSummary);
    const state = selectedSummary ? this._hass?.states?.[selectedSummary] : undefined;
    const address = escapeHtml(state?.attributes?.address || "Sensor velges automatisk når det bare finnes én HRA-avtale.");
    const summaryOptions = [`<option value="">Automatisk oppdagelse</option>`, ...summaryCandidates.map((entityId) => `<option value="${escapeHtml(entityId)}">${escapeHtml(this._hass.states[entityId]?.attributes?.address || entityId)}</option>`)].join("");
    const calendarOptions = [`<option value="">Automatisk oppdagelse</option>`, ...calendarCandidates.map((entityId) => `<option value="${escapeHtml(entityId)}">${escapeHtml(entityId)}</option>`)].join("");
    this.shadowRoot.innerHTML = `<style>:host { display:block; color:var(--primary-text-color); } .row { display:grid; gap:6px; margin:12px 0; } label { color:var(--primary-text-color); font-size:14px; } select, input { box-sizing:border-box; width:100%; min-height:40px; padding:8px; color:var(--primary-text-color); background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:4px; font:inherit; } .hint { color:var(--secondary-text-color); font-size:12px; line-height:1.4; }</style><div class="row"><label for="summary">HRA-avtale / adresse</label><select id="summary">${summaryOptions}</select><div class="hint">${address}</div></div><div class="row"><label for="calendar">Kalender</label><select id="calendar">${calendarOptions}</select></div><div class="row"><label for="max_dates">Antall datoer</label><input id="max_dates" type="number" min="1" max="12" step="1" value="${escapeHtml(this._config.max_dates ?? 4)}" /></div>`;
    this.shadowRoot.querySelector("#summary").value = this._config.entity || "";
    this.shadowRoot.querySelector("#calendar").value = this._config.calendar || "";
    this.shadowRoot.querySelector("#summary").addEventListener("change", (event) => {
      const config = { ...this._config };
      if (event.target.value) config.entity = event.target.value; else delete config.entity;
      delete config.calendar;
      this._fireConfig(config);
      this._render();
    });
    this.shadowRoot.querySelector("#calendar").addEventListener("change", (event) => {
      const config = { ...this._config };
      if (event.target.value) config.calendar = event.target.value; else delete config.calendar;
      this._fireConfig(config);
    });
    this.shadowRoot.querySelector("#max_dates").addEventListener("change", (event) => this._fireConfig({ ...this._config, max_dates: Number(event.target.value) || 4 }));
  }
}

if (!customElements.get("hra-renovasjon-card-editor")) customElements.define("hra-renovasjon-card-editor", HraRenovasjonCardEditor);
if (!customElements.get("hra-renovasjon-card")) customElements.define("hra-renovasjon-card", HraRenovasjonCard);

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "hra-renovasjon-card")) {
  window.customCards.push({ type: "hra-renovasjon-card", name: "HRA hentedager", description: "Oversikt over neste og kommende avfallshentinger fra HRA.", preview: true });
}
