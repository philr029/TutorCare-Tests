/**
 * Security Diagnostic Toolkit – API Client
 *
 * Connects the static dashboard to the hosted FastAPI backend.
 * The API base URL and key are persisted in localStorage so they
 * survive page refreshes.
 *
 * Endpoints consumed:
 *   POST /check-ip
 *   POST /check-domain
 *   POST /validate-phone
 *   POST /site-health
 */
class SecurityAPI {
  constructor() {
    this.baseUrl = (localStorage.getItem('apiBaseUrl') || '').replace(/\/$/, '');
    this.apiKey  = localStorage.getItem('apiKey') || '';
  }

  /** Persist new settings to localStorage and update this instance. */
  updateSettings(baseUrl, apiKey) {
    this.baseUrl = (baseUrl || '').replace(/\/$/, '');
    this.apiKey  = apiKey || '';
    localStorage.setItem('apiBaseUrl', this.baseUrl);
    localStorage.setItem('apiKey',     this.apiKey);
  }

  _headers() {
    const h = { 'Content-Type': 'application/json' };
    if (this.apiKey) h['X-API-Key'] = this.apiKey;
    return h;
  }

  async _post(path, body) {
    if (!this.baseUrl) {
      throw new Error(
        'API Base URL is not configured. Open ⚙️ Settings and enter your backend URL.'
      );
    }

    let response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        method:  'POST',
        headers: this._headers(),
        body:    JSON.stringify(body),
      });
    } catch (err) {
      throw new Error(
        `Network error: ${err.message}. ` +
        'Ensure the API is running and CORS is enabled for this origin.'
      );
    }

    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error(`HTTP ${response.status} – the response was not valid JSON.`);
    }

    if (!response.ok) {
      const detail = data?.detail ?? data?.message ?? `HTTP ${response.status}`;
      throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }

    return data;
  }

  /** POST /check-ip */
  checkIP(ip, dnsblZones) {
    const body = { ip };
    if (dnsblZones && dnsblZones.length) body.dnsbl_zones = dnsblZones;
    return this._post('/check-ip', body);
  }

  /** POST /check-domain */
  checkDomain(domain, dnsblHosts) {
    const body = { domain };
    if (dnsblHosts && dnsblHosts.length) body.dnsbl_hosts = dnsblHosts;
    return this._post('/check-domain', body);
  }

  /** POST /validate-phone */
  validatePhone(phone, region) {
    const body = { phone };
    if (region) body.region = region.toUpperCase();
    return this._post('/validate-phone', body);
  }

  /** POST /site-health */
  siteHealth(url, timeout) {
    const body = { url };
    if (timeout) body.timeout = Number(timeout);
    return this._post('/site-health', body);
  }
}

// Global singleton – referenced by all Alpine.js components
const api = new SecurityAPI();
