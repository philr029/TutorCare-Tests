/** Alpine.js component for the Phone Number Validation tool. */
function phoneCheck() {
  return {
    phone:   '',
    region:  '',
    loading: false,
    error:   null,
    result:  null,
    showRaw: false,

    async submit() {
      const phone = this.phone.trim();
      if (!phone) return;
      this.loading = true;
      this.error   = null;
      this.result  = null;
      this.showRaw = false;
      try {
        this.result = await api.validatePhone(phone, this.region.trim() || null);
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

    get validBadge() {
      if (!this.result) return null;
      if (this.result.error)  return { text: 'Error',   cls: 'badge-red'    };
      if (this.result.valid)  return { text: 'Valid',   cls: 'badge-green'  };
      return                         { text: 'Invalid', cls: 'badge-red'    };
    },

    get possibleBadge() {
      if (!this.result) return null;
      return this.result.possible
        ? { text: 'Possible',     cls: 'badge-blue' }
        : { text: 'Not possible', cls: 'badge-gray' };
    },

    get lineTypeBadge() {
      const t = this.result?.line_type;
      if (!t) return null;
      const clsMap = {
        fixed_line:             'badge-blue',
        mobile:                 'badge-green',
        fixed_line_or_mobile:   'badge-blue',
        voip:                   'badge-yellow',
        premium_rate:           'badge-red',
        toll_free:              'badge-gray',
        shared_cost:            'badge-gray',
        pager:                  'badge-gray',
        unknown:                'badge-gray',
      };
      return { text: t.replace(/_/g, ' '), cls: clsMap[t] ?? 'badge-gray' };
    },

    get formats() {
      const f = this.result?.format;
      if (!f) return [];
      return [
        { label: 'E.164',         value: f.e164          },
        { label: 'International', value: f.international  },
        { label: 'National',      value: f.national       },
      ].filter(row => row.value);
    },

    get timezones() {
      return this.result?.timezones ?? [];
    },

    jsonHtml(obj) { return syntaxHighlight(obj); },
  };
}
