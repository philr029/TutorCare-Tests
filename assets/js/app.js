/**
 * Security Diagnostic Toolkit – Alpine.js application root.
 *
 * Provides:
 *   app()          – root component (sidebar navigation, tool switcher)
 *   settingsPanel() – settings form component
 *   syntaxHighlight() – JSON HTML highlighter used by tool components
 */

/** Milliseconds to show the "Saved ✅" confirmation before hiding it. */
const SAVE_CONFIRMATION_DURATION_MS = 3000;

/* ─── Root app component ────────────────────────────────────────────────── */
function app() {
  return {
    tool:        'ip',
    sidebarOpen: false,

    navItems: [
      /* Tools */
      { id: 'ip',       icon: '🛡️',  label: 'IP Reputation',     group: 'tools' },
      { id: 'domain',   icon: '🌐',  label: 'Domain Check',       group: 'tools' },
      { id: 'phone',    icon: '📱',  label: 'Phone Validation',   group: 'tools' },
      { id: 'site',     icon: '🌍',  label: 'Site Health',        group: 'tools' },
      /* Other */
      { id: 'settings', icon: '⚙️',  label: 'Settings',           group: 'other' },
      { id: 'docs',     icon: '📖',  label: 'Documentation',      group: 'other' },
    ],

    toolItems()  { return this.navItems.filter(n => n.group === 'tools'); },
    otherItems() { return this.navItems.filter(n => n.group === 'other'); },

    setTool(id) {
      this.tool        = id;
      this.sidebarOpen = false;
    },

    currentLabel() {
      return this.navItems.find(n => n.id === this.tool)?.label ?? 'Dashboard';
    },

    get apiConfigured() { return !!api.baseUrl; },
    get apiBaseUrl()    { return api.baseUrl;    },
  };
}

/* ─── Settings panel component ──────────────────────────────────────────── */
function settingsPanel() {
  return {
    baseUrl:  localStorage.getItem('apiBaseUrl') || '',
    apiKey:   localStorage.getItem('apiKey')     || '',
    showKey:  false,
    saved:    false,
    testMsg:  null,
    testing:  false,

    save() {
      api.updateSettings(this.baseUrl, this.apiKey);
      this.saved   = true;
      this.testMsg = null;
      setTimeout(() => { this.saved = false; }, SAVE_CONFIRMATION_DURATION_MS);
    },

    async testConnection() {
      if (!this.baseUrl.trim()) { this.testMsg = { ok: false, text: 'Enter a Base URL first.' }; return; }
      this.testing = true;
      this.testMsg = null;
      const url = this.baseUrl.replace(/\/$/, '') + '/health';
      try {
        const headers = {};
        if (this.apiKey) headers['X-API-Key'] = this.apiKey;
        const r = await fetch(url, { headers });
        if (r.ok) {
          this.testMsg = { ok: true,  text: `Connected! (HTTP ${r.status})` };
        } else {
          this.testMsg = { ok: false, text: `HTTP ${r.status} – check URL and API key.` };
        }
      } catch (e) {
        this.testMsg = { ok: false, text: `Connection failed: ${e.message}` };
      } finally {
        this.testing = false;
      }
    },

    get isConfigured() { return !!this.baseUrl.trim(); },
  };
}

/* ─── JSON syntax highlighter ───────────────────────────────────────────── */
function syntaxHighlight(obj) {
  let json = (typeof obj === 'string') ? obj : JSON.stringify(obj, null, 2);
  // Escape HTML special chars first
  json = json
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  // Colorise tokens
  return json.replace(
    /("(?:\\u[0-9a-fA-F]{4}|\\[^u]|[^\\"])*"(?:\s*:)?|\b(?:true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      let cls = 'json-number';
      if (/^"/.test(match)) {
        cls = /:$/.test(match) ? 'json-key' : 'json-string';
      } else if (/true|false/.test(match)) {
        cls = 'json-boolean';
      } else if (/null/.test(match)) {
        cls = 'json-null';
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}
