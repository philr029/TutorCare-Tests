/** Alpine.js component for the IP Reputation Check tool. */
function ipCheck() {
  return {
    ip:         '',
    dnsblZones: '',
    loading:    false,
    error:      null,
    result:     null,
    showRaw:    false,
    _chart:     null,

    async submit() {
      const ip = this.ip.trim();
      if (!ip) return;
      this.loading = true;
      this.error   = null;
      this.result  = null;
      this.showRaw = false;
      try {
        const zones = this.dnsblZones
          ? this.dnsblZones.split(',').map(z => z.trim()).filter(Boolean)
          : [];
        this.result = await api.checkIP(ip, zones);
        this.$nextTick(() => this._renderChart());
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
      if (this._chart) { this._chart.destroy(); this._chart = null; }
    },

    get apiConfigured() { return !!api.baseUrl; },

    get listedCount() {
      return this.result?.dnsbl_results?.filter(r => r.listed).length ?? 0;
    },

    get statusBadge() {
      if (!this.result) return null;
      return this.listedCount > 0
        ? { text: 'Listed',  cls: 'badge-red'   }
        : { text: 'Clean',   cls: 'badge-green' };
    },

    rowCls(row) {
      return row.listed
        ? 'bg-red-50 hover:bg-red-100'
        : 'hover:bg-gray-50';
    },

    _renderChart() {
      const canvas = document.getElementById('ip-dnsbl-chart');
      if (!canvas || !this.result?.dnsbl_results?.length) return;
      if (this._chart) { this._chart.destroy(); this._chart = null; }

      const listed = this.listedCount;
      const clean  = this.result.dnsbl_results.length - listed;

      this._chart = new Chart(canvas, {
        type: 'doughnut',
        data: {
          labels:   ['Listed', 'Clean'],
          datasets: [{
            data:            [listed, clean],
            backgroundColor: ['#ef4444', '#22c55e'],
            borderWidth:     0,
          }],
        },
        options: {
          responsive:          true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { font: { size: 12 }, padding: 12 } },
          },
          cutout: '65%',
        },
      });
    },

    jsonHtml(obj) { return syntaxHighlight(obj); },
  };
}
