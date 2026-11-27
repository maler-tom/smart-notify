/*
 * Smart Notify – Seite in der Seitenleiste.
 *
 * Drei ein- und ausklappbare Abschnitte: Geräte, Personen, Lautsprecher.
 * Hinzufügen und Bearbeiten laufen über dieselben Untereintrag-Dialoge der
 * Integration (REST /api/config/config_entries/subentries/flow); die Formulare
 * zeichnet das eingebaute <ha-form> von Home Assistant.
 */

const DOMAIN = "smart_notify";
const STORAGE_KEY = "smart_notify_panel_open";

const SECTIONS = [
  { key: "devices", type: "device", title: "Geräte", add: "Gerät hinzufügen", empty: "Noch kein Gerät angelegt." },
  { key: "persons", type: "person", title: "Personen", add: "Person hinzufügen", empty: "Noch keine Person angelegt." },
  { key: "speakers", type: "speaker", title: "Lautsprecher", add: "Lautsprecher hinzufügen", empty: "Noch kein Lautsprecher angelegt." },
];

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const STYLE = `
  :host { display: block; min-height: 100vh; background: var(--primary-background-color); color: var(--primary-text-color); font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
  header { display: flex; align-items: center; gap: 8px; height: 56px; padding: 0 16px; background: var(--app-header-background-color, var(--primary-color)); color: var(--app-header-text-color, #fff); position: sticky; top: 0; z-index: 3; box-sizing: border-box; }
  header h1 { font-size: 20px; font-weight: 400; margin: 0; flex: 1; }
  header button { background: none; border: 0; color: inherit; cursor: pointer; padding: 8px; border-radius: 50%; display: inline-flex; }
  main { max-width: 760px; margin: 0 auto; padding: 16px; display: flex; flex-direction: column; gap: 16px; box-sizing: border-box; }
  .card { background: var(--card-background-color); border-radius: var(--ha-card-border-radius, 12px); border: 1px solid var(--divider-color); overflow: hidden; }
  .head { display: flex; align-items: center; gap: 12px; width: 100%; padding: 16px; background: none; border: 0; color: inherit; font: inherit; text-align: left; cursor: pointer; }
  .head:hover { background: var(--secondary-background-color); }
  .head .name { font-size: 18px; font-weight: 500; flex: 1; }
  .badge { min-width: 24px; padding: 2px 8px; text-align: center; border-radius: 12px; background: var(--primary-color); color: var(--text-primary-color, #fff); font-size: 13px; }
  .chev { transition: transform .2s; color: var(--secondary-text-color); display: inline-flex; }
  .card.open .chev { transform: rotate(180deg); }
  .body { display: none; border-top: 1px solid var(--divider-color); }
  .card.open .body { display: block; }
  .row { display: flex; align-items: center; gap: 8px; padding: 12px 8px 12px 16px; border-bottom: 1px solid var(--divider-color); }
  .row .text { flex: 1; min-width: 0; }
  .row .title { font-weight: 500; }
  .row .line { color: var(--secondary-text-color); font-size: 13px; margin-top: 2px; overflow-wrap: anywhere; }
  .icon { background: none; border: 0; cursor: pointer; padding: 8px; border-radius: 50%; color: var(--secondary-text-color); display: inline-flex; }
  .icon:hover { background: var(--secondary-background-color); color: var(--primary-text-color); }
  .empty { padding: 16px; color: var(--secondary-text-color); }
  .add { display: flex; align-items: center; gap: 8px; width: 100%; padding: 14px 16px; background: none; border: 0; color: var(--primary-color); font: inherit; font-weight: 500; cursor: pointer; text-align: left; }
  .add:hover { background: var(--secondary-background-color); }
  .msg { padding: 24px 16px; text-align: center; color: var(--secondary-text-color); }
  .msg.error { color: var(--error-color); }
  #dlg { position: fixed; inset: 0; z-index: 10; display: none; align-items: center; justify-content: center; background: rgba(0,0,0,.5); }
  #dlg.show { display: flex; }
  .dialog { background: var(--card-background-color); color: var(--primary-text-color); width: min(560px, 96vw); max-height: 92vh; display: flex; flex-direction: column; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,.4); }
  .dialog h2 { margin: 0; padding: 20px 24px 8px; font-size: 20px; font-weight: 500; }
  .dialog .content { padding: 8px 24px; overflow-y: auto; }
  .dialog .desc { color: var(--secondary-text-color); margin-bottom: 12px; white-space: pre-line; }
  .dialog .err { color: var(--error-color); margin: 8px 0; white-space: pre-line; }
  .dialog .actions { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 16px 16px; }
  .btn { background: none; border: 0; padding: 10px 16px; border-radius: 8px; font: inherit; font-weight: 500; color: var(--primary-color); cursor: pointer; }
  .btn:hover { background: var(--secondary-background-color); }
  .btn.primary { background: var(--primary-color); color: var(--text-primary-color, #fff); }
  .btn:disabled { opacity: .5; cursor: default; }
  .opt { display: block; width: 100%; text-align: left; padding: 14px 16px; margin-bottom: 8px; border: 1px solid var(--divider-color); border-radius: 10px; background: none; color: inherit; font: inherit; cursor: pointer; }
  .opt:hover { background: var(--secondary-background-color); border-color: var(--primary-color); }
`;

class SmartNotifyPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._data = null;
    this._error = null;
    this._flow = null;
    this._tr = {};
    this._trLang = null;
    this._entryId = null;
    this._started = false;
    try {
      this._open = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null") || { devices: true, persons: true, speakers: true };
    } catch (e) {
      this._open = { devices: true, persons: true, speakers: true };
    }
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <header><span id="menu"></span><h1>Smart Notify</h1>
        <button id="refresh" data-act="refresh" title="Aktualisieren"><ha-icon icon="mdi:refresh"></ha-icon></button></header>
      <main id="main"></main>
      <div id="dlg"></div>`;
    this.shadowRoot.addEventListener("click", (ev) => this._click(ev));
    window.addEventListener("focus", () => this._started && !this._flow && this._load());
  }

  set hass(hass) {
    this._hass = hass;
    if (this._menu) this._menu.hass = hass;
    if (!this._started) {
      this._started = true;
      this._load();
    }
  }

  set narrow(narrow) {
    this._narrow = narrow;
    this._ensureMenu();
    if (this._menu) this._menu.narrow = narrow;
  }

  set panel(panel) {
    this._entryId = panel?.config?.entry_id || null;
  }

  _ensureMenu() {
    if (this._menu || !customElements.get("ha-menu-button")) return;
    this._menu = document.createElement("ha-menu-button");
    this._menu.hass = this._hass;
    this.shadowRoot.getElementById("menu").appendChild(this._menu);
  }

  // ---------------------------------------------------------------- Daten
  async _load() {
    try {
      this._data = await this._hass.callWS({ type: `${DOMAIN}/overview` });
      this._entryId = this._data.entry_id;
      this._error = null;
    } catch (e) {
      this._error = e?.message || "Smart Notify konnte nicht geladen werden.";
    }
    this._render();
  }

  async _loadTranslations() {
    const language = this._hass.language || "de";
    if (this._trLang === language) return;
    this._tr = {};
    for (const category of ["config_subentries", "selector"]) {
      try {
        const res = await this._hass.callWS({ type: "frontend/get_translations", language, category, integration: [DOMAIN] });
        Object.assign(this._tr, res.resources || {});
      } catch (e) {
        /* ohne Übersetzung zeigt die Seite die technischen Namen */
      }
    }
    this._trLang = language;
  }

  _t(key, placeholders) {
    let text = this._tr[key];
    if (text === undefined) return undefined;
    for (const [name, value] of Object.entries(placeholders || {})) {
      text = text.replaceAll(`{${name}}`, value);
    }
    return text;
  }

  // ----------------------------------------------------------- Hauptseite
  _render() {
    const main = this.shadowRoot.getElementById("main");
    if (this._error && !this._data) {
      main.innerHTML = `<div class="msg error">${esc(this._error)}</div>`;
      return;
    }
    if (!this._data) {
      main.innerHTML = `<div class="msg">Lädt …</div>`;
      return;
    }
    main.innerHTML = SECTIONS.map((section) => {
      const items = this._data[section.key] || [];
      const open = this._open[section.key] !== false;
      const rows = items.length
        ? items.map((item) => `
            <div class="row">
              <div class="text">
                <div class="title">${esc(item.title)}</div>
                ${(item.lines || []).map((l) => `<div class="line">${esc(l)}</div>`).join("")}
              </div>
              <button class="icon" title="Bearbeiten" data-act="edit" data-type="${section.type}" data-id="${esc(item.id)}"><ha-icon icon="mdi:pencil"></ha-icon></button>
              <button class="icon" title="Löschen" data-act="del" data-type="${section.type}" data-id="${esc(item.id)}" data-name="${esc(item.title)}"><ha-icon icon="mdi:delete-outline"></ha-icon></button>
            </div>`).join("")
        : `<div class="empty">${section.empty}</div>`;
      return `
        <div class="card ${open ? "open" : ""}">
          <button class="head" data-act="toggle" data-key="${section.key}">
            <span class="name">${section.title}</span>
            <span class="badge">${items.length}</span>
            <span class="chev"><ha-icon icon="mdi:chevron-down"></ha-icon></span>
          </button>
          <div class="body">
            ${rows}
            <button class="add" data-act="add" data-type="${section.type}"><ha-icon icon="mdi:plus"></ha-icon>${section.add}</button>
          </div>
        </div>`;
    }).join("");
  }

  _click(ev) {
    const target = ev.target.closest("[data-act]");
    if (!target) {
      if (ev.target.id === "dlg") this._closeFlow(true);
      return;
    }
    const { act, key, type, id, name, option } = target.dataset;
    switch (act) {
      case "toggle":
        this._open[key] = !(this._open[key] !== false);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this._open));
        target.closest(".card").classList.toggle("open", this._open[key]);
        break;
      case "add":
        this._startFlow(type);
        break;
      case "edit":
        this._startFlow(type, id);
        break;
      case "del":
        this._delete(id, name);
        break;
      case "refresh":
        this._load();
        break;
      case "menu":
        this._submit({ next_step_id: option });
        break;
      case "cancel":
        this._closeFlow(true);
        break;
      case "save":
        this._submit(this._flow.data);
        break;
    }
  }

  async _delete(id, name) {
    if (!window.confirm(`„${name}“ wirklich löschen?`)) return;
    try {
      await this._hass.callWS({ type: "config_entries/subentries/delete", entry_id: this._entryId, subentry_id: id });
    } catch (e) {
      window.alert(e?.message || "Löschen hat nicht geklappt.");
    }
    this._load();
  }

  // ---------------------------------------------------------------- Dialog
  async _startFlow(type, subentryId) {
    this._flow = { type, reconfigure: !!subentryId, result: null, data: {}, busy: true, error: null };
    this._renderDialog();
    try {
      await this._loadTranslations();
      const body = { handler: [this._entryId, type] };
      if (subentryId) body.subentry_id = subentryId;
      this._handleResult(await this._hass.callApi("POST", "config/config_entries/subentries/flow", body));
    } catch (e) {
      this._flow.busy = false;
      this._flow.error = this._errorText(e);
      this._renderDialog();
    }
  }

  async _submit(payload) {
    const flow = this._flow;
    if (!flow?.result?.flow_id || flow.busy) return;
    flow.busy = true;
    flow.error = null;
    this._renderDialog(true);
    try {
      const result = await this._hass.callApi(
        "POST", `config/config_entries/subentries/flow/${flow.result.flow_id}`, payload
      );
      this._handleResult(result);
    } catch (e) {
      flow.busy = false;
      flow.error = this._errorText(e);
      this._renderDialog();
    }
  }

  _errorText(e) {
    return e?.message || e?.body?.message || (typeof e === "string" ? e : "Das hat nicht geklappt.");
  }

  _handleResult(result) {
    const flow = this._flow;
    if (!flow) return;
    flow.busy = false;
    if (result.type === "create_entry" || (result.type === "abort" && result.reason === "reconfigure_successful")) {
      this._closeFlow(false);
      this._load();
      return;
    }
    if (result.type === "form") {
      const previous = flow.result && flow.result.step_id === result.step_id ? flow.data : {};
      flow.data = { ...this._initialData(result.data_schema || []), ...previous };
    }
    flow.result = result;
    this._renderDialog();
  }

  _initialData(schema) {
    const data = {};
    for (const item of schema) {
      if (item.default !== undefined) data[item.name] = item.default;
      else if (item.description?.suggested_value !== undefined) data[item.name] = item.description.suggested_value;
    }
    return data;
  }

  _closeFlow(abort) {
    const flow = this._flow;
    this._flow = null;
    if (abort && flow?.result?.flow_id && !["create_entry", "abort"].includes(flow.result.type)) {
      this._hass.callApi("DELETE", `config/config_entries/subentries/flow/${flow.result.flow_id}`).catch(() => {});
    }
    const dlg = this.shadowRoot.getElementById("dlg");
    dlg.classList.remove("show");
    dlg.innerHTML = "";
  }

  _renderDialog() {
    const dlg = this.shadowRoot.getElementById("dlg");
    const flow = this._flow;
    if (!flow) {
      dlg.classList.remove("show");
      dlg.innerHTML = "";
      return;
    }
    dlg.classList.add("show");
    const result = flow.result;
    const base = `component.${DOMAIN}.config_subentries.${flow.type}`;
    const initiate = this._t(`${base}.initiate_flow.${flow.reconfigure ? "reconfigure" : "user"}`) || "Smart Notify";
    const errorBlock = flow.error ? `<div class="err">${esc(flow.error)}</div>` : "";

    if (!result) {
      dlg.innerHTML = `<div class="dialog"><h2>${esc(initiate)}</h2><div class="content">${errorBlock || "Lädt …"}</div>
        <div class="actions"><button class="btn" data-act="cancel">Schließen</button></div></div>`;
      return;
    }

    const step = `${base}.step.${result.step_id}`;
    const placeholders = result.description_placeholders || {};
    const title = this._t(`${step}.title`, placeholders) || initiate;
    const desc = this._t(`${step}.description`, placeholders) || "";

    if (result.type === "menu") {
      const options = result.menu_options || [];
      const list = (Array.isArray(options) ? options : Object.keys(options))
        .map((opt) => `<button class="opt" data-act="menu" data-option="${esc(opt)}">${esc(this._t(`${step}.menu_options.${opt}`) || opt)}</button>`)
        .join("");
      dlg.innerHTML = `<div class="dialog"><h2>${esc(title)}</h2>
        <div class="content">${desc ? `<div class="desc">${esc(desc)}</div>` : ""}${list}${errorBlock}</div>
        <div class="actions"><button class="btn" data-act="cancel">Abbrechen</button></div></div>`;
      return;
    }

    if (result.type === "form") {
      const baseError = result.errors?.base ? this._t(`${base}.error.${result.errors.base}`) || result.errors.base : "";
      dlg.innerHTML = `<div class="dialog"><h2>${esc(title)}</h2>
        <div class="content">${desc ? `<div class="desc">${esc(desc)}</div>` : ""}
          ${baseError ? `<div class="err">${esc(baseError)}</div>` : ""}<div id="form"></div>${errorBlock}</div>
        <div class="actions"><button class="btn" data-act="cancel">Abbrechen</button>
          <button class="btn primary" data-act="save" ${flow.busy ? "disabled" : ""}>Speichern</button></div></div>`;
      const form = document.createElement("ha-form");
      const fieldErrors = {};
      for (const [field, key] of Object.entries(result.errors || {})) {
        if (field !== "base") fieldErrors[field] = this._t(`${base}.error.${key}`) || key;
      }
      form.hass = this._hass;
      form.schema = result.data_schema || [];
      form.data = flow.data;
      form.error = fieldErrors;
      form.computeLabel = (item) => this._t(`${step}.data.${item.name}`) || item.name;
      form.computeHelper = (item) => this._t(`${step}.data_description.${item.name}`) || "";
      form.localizeValue = (key) => this._t(`component.${DOMAIN}.selector.${key}`) || key;
      form.addEventListener("value-changed", (ev) => {
        ev.stopPropagation();
        flow.data = ev.detail.value;
        form.data = flow.data;
      });
      dlg.querySelector("#form").appendChild(form);
      return;
    }

    // abort mit anderem Grund oder unbekannter Typ
    const reason = this._t(`${base}.abort.${result.reason}`) || result.reason || "Abgebrochen.";
    dlg.innerHTML = `<div class="dialog"><h2>${esc(title)}</h2><div class="content">${esc(reason)}</div>
      <div class="actions"><button class="btn" data-act="cancel">Schließen</button></div></div>`;
  }
}

customElements.define("smart-notify-panel", SmartNotifyPanel);
