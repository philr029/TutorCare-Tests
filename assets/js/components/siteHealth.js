/** Alpine.js component for the Site Health & Diagnostics tool. */
function siteHealth() {
  return {
    url:       '',
    timeout:   '10',
    loading:   false,
    error:     null,
    result:    null,
    showRaw:   false,
    _sslChart: null,

    async submit() {
      const url = this.url.trim();
      if (!url) return;
      this.loading = true;
      this.error   = null;
      this.result  = null;
      this.showRaw = false;
      try {
        this.result = await api.siteHealth(url, this.timeout || null);
        this.$nextTick(() => this._renderSslChart());
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
      if (this._sslChart) { this._sslChart.destroy(); this._sslChart = null; }
    },

    get apiConfigured() { return !!api.baseUrl; },

    get httpBadge() {
      const code = this.result?.http?.status_code;
      if (!code) return null;
      if (code >= 200 && code < 300) return { text: `${code}`,          cls: 'badge-green'  };
      if (code >= 300 && code < 400) return { text: `${code} Redirect`, cls: 'badge-blue'   };
      if (code >= 400 && code < 500) return { text: `${code}`,          cls: 'badge-red'    };
      if (code >= 500)               return { text: `${code}`,          cls: 'badge-red'    };
      return                                { text: `${code}`,          cls: 'badge-gray'   };
    },

    get sslBadge() {
      const ssl = this.result?.ssl;
      if (!ssl) return null;
      if (ssl.error)   return { text: 'Error',   cls: 'badge-red'    };
      if (!ssl.valid)  return { text: 'Invalid', cls: 'badge-red'    };
      const days = ssl.days_until_expiry ?? 0;
      if (days <= 7)   return { text: `Expires in ${days}d`, cls: 'badge-red'    };
      if (days <= 30)  return { text: `Expires in ${days}d`, cls: 'badge-yellow' };
      return                  { text: `Valid · ${days}d`,    cls: 'badge-green'  };
    },

    get dnsEntries() {
      const dns = this.result?.dns;
      if (!dns) return [];
      return Object.entries(dns).map(([type, value]) => ({
        type,
        display: Array.isArray(value) ? value.join(', ') || '—' : (value || '—'),
      }));
    },

    get redirectChain() {
      return this.result?.http?.redirect_chain ?? [];
    },

    get pageLoadMs() {
      const ms = this.result?.http?.page_load_ms;
      return ms != null ? `${ms.toFixed(0)} ms` : '—';
    },

    _renderSslChart() {
      const canvas = document.getElementById('ssl-expiry-chart');
      if (!canvas || !this.result?.ssl) return;
      if (this._sslChart) { this._sslChart.destroy(); this._sslChart = null; }

      const days    = this.result.ssl.days_until_expiry ?? 0;
      const maxDays = 365;
      const elapsed = Math.max(0, maxDays - days);
      const color   = days <= 7 ? '#ef4444' : days <= 30 ? '#f59e0b' : '#22c55e';

      this._sslChart = new Chart(canvas, {
        type: 'bar',
        data: {
          labels:   ['SSL Certificate'],
          datasets: [
            {
              label:           `${days} days remaining`,
              data:            [Math.min(days, maxDays)],
              backgroundColor: color,
              borderRadius:    4,
            },
            {
              label:           'Time elapsed (capped at 365d)',
              data:            [elapsed],
              backgroundColor: '#e2e8f0',
              borderRadius:    4,
            },
          ],
        },
        options: {
          responsive:          true,
          maintainAspectRatio: false,
          indexAxis:           'y',
          scales: {
            x: {
              stacked: true,
              max:     maxDays,
              ticks:   { callback: v => `${v}d` },
              grid:    { color: '#f1f5f9' },
            },
            y: { stacked: true, display: false },
          },
          plugins: {
            legend: { position: 'bottom', labels: { font: { size: 12 }, padding: 12 } },
          },
        },
      });
    },

    jsonHtml(obj) { return syntaxHighlight(obj); },
  };
}
