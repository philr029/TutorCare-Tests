/** Alpine.js component for the Domain Reputation Check tool. */
function domainCheck() {
  return {
    domain:     '',
    dnsblHosts: '',
    loading:    false,
    error:      null,
    result:     null,
    showRaw:    false,

    async submit() {
      const domain = this.domain.trim();
      if (!domain) return;
      this.loading = true;
      this.error   = null;
      this.result  = null;
      this.showRaw = false;
      try {
        const hosts = this.dnsblHosts
          ? this.dnsblHosts.split(',').map(h => h.trim()).filter(Boolean)
          : [];
        this.result = await api.checkDomain(domain, hosts);
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },

    clear() {
      this.result  = null;
      this.error   = null;
      this.showRaw = false;
    },

    get apiConfigured() { return !!api.baseUrl; },

    get statusBadge() {
      if (!this.result) return null;
      return this.result.listed
        ? { text: 'Listed', cls: 'badge-red'   }
        : { text: 'Clean',  cls: 'badge-green' };
    },

    get resolvedIPs() {
      return this.result?.resolved_ips ?? [];
    },

    get sources() {
      return this.result?.sources ?? [];
    },

    jsonHtml(obj) { return syntaxHighlight(obj); },
  };
}
