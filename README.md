# Security Diagnostic Toolkit

A modular, non-intrusive security diagnostic toolkit for IP reputation, phone number validation, and website health checks. Built with Python, CLI-first design, and an optional web dashboard.

> ⚠️ **For authorized use only.** See [DISCLAIMER.md](DISCLAIMER.md) for full legal and ethical usage terms.

---

## Features

| Module | Description |
|---|---|
| **IP Reputation** | DNSBL lookups (Spamhaus, SURBL, Barracuda, SpamCop, SORBS), AbuseIPDB, VirusTotal |
| **Phone Validation** | libphonenumber parsing, country/carrier/line-type, Numverify & Twilio APIs |
| **Website Health** | HTTP status, redirect chains, SSL certificate details, DNS records (A, MX, TXT, SPF, DMARC) |
| **Web Dashboard** | Lightweight Flask UI at `http://localhost:5000/` |

---

## Installation

### Requirements
- Python 3.9+

```bash
git clone https://github.com/your-org/security-toolkit.git
cd security-toolkit
pip install -r requirements.txt
pip install -e .
```

---

## Configuration

Copy and edit `config/config.yaml`:

```yaml
api_keys:
  abuseipdb: "YOUR_KEY"      # https://www.abuseipdb.com/
  virustotal: "YOUR_KEY"     # https://www.virustotal.com/
  numverify: "YOUR_KEY"      # https://numverify.com/
  twilio_sid: "YOUR_SID"     # https://www.twilio.com/
  twilio_token: "YOUR_TOKEN"

settings:
  timeout: 10
  log_level: "INFO"
  log_file: "security_toolkit.log"
  redact_keys: true          # Redacts API keys from logs

dnsbl_sources:
  - name: "Spamhaus ZEN"
    host: "zen.spamhaus.org"
  # add/remove DNSBL sources as needed
```

All API keys are **optional** — the toolkit works without them using DNSBL lookups and libphonenumber.

---

## CLI Usage

```bash
# Show help
security-toolkit --help

# Use a custom config file
security-toolkit --config /path/to/config.yaml ip 8.8.8.8

# Save output to a file
security-toolkit --output result.json ip 1.2.3.4
```

### IP / Domain Reputation

```bash
security-toolkit ip 8.8.8.8
security-toolkit ip example.com
security-toolkit ip-bulk 1.1.1.1 8.8.8.8 evil.example.com
```

**Sample output:**
```json
{
  "input": "8.8.8.8",
  "resolved_ip": null,
  "listed": false,
  "sources": [
    {
      "name": "Spamhaus ZEN",
      "status": "clean",
      "details": "Not listed"
    },
    {
      "name": "SURBL",
      "status": "clean",
      "details": "Not listed"
    }
  ]
}
```

### Phone Number Validation

```bash
security-toolkit phone +14155552671
security-toolkit phone 02071234567 --region GB
```

**Sample output:**
```json
{
  "input": "+14155552671",
  "valid": true,
  "format": {
    "e164": "+14155552671",
    "international": "+1 415-555-2671",
    "national": "(415) 555-2671"
  },
  "country": "United States",
  "region": "US",
  "carrier": null,
  "line_type": "fixed_line_or_mobile",
  "timezones": ["America/Los_Angeles"],
  "sources": [],
  "error": null
}
```

### Website Health & Diagnostics

```bash
security-toolkit website https://example.com
security-toolkit website example.com
```

**Sample output:**
```json
{
  "input": "https://example.com",
  "hostname": "example.com",
  "http": {
    "status_code": 200,
    "final_url": "https://example.com/",
    "redirect_chain": [],
    "page_load_ms": 342.5,
    "error": null
  },
  "ssl": {
    "valid": true,
    "subject": {"commonName": "example.com"},
    "issuer": {"organizationName": "DigiCert Inc"},
    "not_after": "Mar  1 23:59:59 2025 GMT",
    "days_until_expiry": 120,
    "error": null
  },
  "dns": {
    "A": ["93.184.216.34"],
    "MX": [],
    "SPF": [],
    "DMARC": "No DMARC record found"
  },
  "checked_at": "2024-01-15T10:30:00Z"
}
```

### Web Dashboard

```bash
security-toolkit serve
# or with custom options:
security-toolkit serve --host 0.0.0.0 --port 8080
```

Open `http://127.0.0.1:5000/` in your browser.

**REST API endpoints:**
- `GET /api/ip?target=8.8.8.8`
- `GET /api/phone?number=+14155552671&region=US`
- `GET /api/website?url=https://example.com`

---

## Docker Usage

```bash
# Build
docker build -t security-toolkit .

# Run a check
docker run --rm security-toolkit ip 8.8.8.8

# Start the dashboard
docker run --rm -p 5000:5000 security-toolkit serve --host 0.0.0.0

# Mount a custom config
docker run --rm -v $(pwd)/config:/app/config security-toolkit ip 1.2.3.4
```

---

## Module Descriptions

### `security_toolkit/modules/ip_reputation.py`
- `check_reputation(target, config)` — single IP or domain check
- `check_reputation_bulk(targets, config)` — batch check for multiple targets
- Performs DNSBL lookups by reversing the IP and querying each configured blocklist
- Optionally enriches results with AbuseIPDB and VirusTotal when API keys are present

### `security_toolkit/modules/phone_validation.py`
- `validate_phone(phone_input, region, config)` — parse & validate using Google's libphonenumber
- Returns format variants (E.164, international, national), country, region, carrier, line type, and timezones
- No network calls are made unless Numverify or Twilio API keys are configured

### `security_toolkit/modules/website_health.py`
- `check_website(url, config)` — comprehensive non-intrusive health check
- HTTP: status code, response headers, redirect chain, page load time
- SSL: certificate validity, subject/issuer, expiry countdown
- DNS: A, MX, TXT records with automatic SPF and DMARC extraction

### `security_toolkit/utils/logging_utils.py`
- `get_logger(name, log_file, level)` — returns a logger with `RedactingFormatter`
- Automatically redacts API keys, tokens, passwords from all log output

### `security_toolkit/utils/config_loader.py`
- `load_config(config_path)` — loads YAML config with safe fallback defaults

---

## Running Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

---

## Project Structure

```
security_toolkit/               # Production package (installable via pip/setup.py)
├── cli.py                      # Click CLI: ip, ip-bulk, phone, website, serve
├── modules/
│   ├── ip_reputation.py        # IP/domain reputation (DNSBL, AbuseIPDB, VirusTotal)
│   ├── phone_validation.py     # Phone number validation
│   └── website_health.py       # Website health diagnostics
├── utils/
│   ├── config_loader.py        # YAML config loader
│   └── logging_utils.py        # Redacting log formatter
└── web/
    ├── dashboard.py            # Flask web dashboard
    └── templates/
        └── index.html          # Dashboard UI

src/                            # Modular scaffold (granular per-feature files)
├── ip_reputation/
│   ├── check_rbl.py            # DNSBL / RBL lookup
│   └── check_abuseipdb.py      # AbuseIPDB API check
├── domain_reputation/
│   └── check_dnsbl.py          # Domain DNSBL + Spamhaus DBL
├── phone_validation/
│   └── validate_number.py      # libphonenumber + Numverify/Twilio enrichment
├── site_diagnostics/
│   ├── http_status.py          # HTTP status, headers, redirect chain
│   ├── ssl_check.py            # SSL/TLS certificate inspection
│   └── dns_records.py          # DNS records (A, MX, TXT, SPF, DMARC)
└── utils/
    ├── http_client.py          # Shared HTTP client with logging
    ├── logger.py               # Redacting logger wrapper
    └── config_loader.py        # JSON config loader

cli.py                          # Top-level CLI (check-ip, check-domain,
                                #   validate-phone, site-health)
config/
├── config.yaml                 # YAML configuration (production)
└── config.example.json         # JSON configuration template
dashboard/                      # Optional web dashboard (placeholder)
docs/                           # Supplementary documentation
tests/                          # pytest unit tests (103 tests)
Dockerfile
requirements.txt
setup.py
```

---

## `src/` Scaffold CLI

A second CLI entry point (`cli.py` at the project root) uses the granular `src/`
module layout and exposes four commands:

```bash
# Check IP reputation (DNSBL + AbuseIPDB)
python cli.py check-ip 8.8.8.8
python cli.py check-ip 1.2.3.4 --dnsbl zen.spamhaus.org --dnsbl bl.spamcop.net

# Check domain reputation (Spamhaus DBL + IP-based DNSBLs)
python cli.py check-domain example.com

# Validate a phone number
python cli.py validate-phone "+14155552671"
python cli.py validate-phone "02071234567" --region GB

# Full site-health diagnostics (HTTP + SSL + DNS)
python cli.py site-health https://example.com
python cli.py --output result.json site-health example.com
```

**Sample `check-ip` output:**
```json
{
  "ip": "8.8.8.8",
  "dnsbl_results": [
    {"ip": "8.8.8.8", "dnsbl": "zen.spamhaus.org", "listed": false, "details": "Not listed"},
    {"ip": "8.8.8.8", "dnsbl": "multi.surbl.org",  "listed": false, "details": "Not listed"}
  ],
  "abuseipdb": null
}
```

**Sample `validate-phone` output:**
```json
{
  "input": "+14155552671",
  "valid": true,
  "format": {
    "e164": "+14155552671",
    "international": "+1 415-555-2671",
    "national": "(415) 555-2671"
  },
  "country": "United States",
  "region": "US",
  "line_type": "fixed_line_or_mobile",
  "timezones": ["America/Los_Angeles"],
  "sources": [],
  "error": null
}
```

**Sample `site-health` output:**
```json
{
  "hostname": "example.com",
  "http": {"status_code": 200, "page_load_ms": 342.5, "error": null},
  "ssl":  {"valid": true, "days_until_expiry": 120, "error": null},
  "dns":  {"A": ["93.184.216.34"], "SPF": [], "DMARC": "No DMARC record found"},
  "checked_at": "2024-01-15T10:30:00+00:00"
}
```

### API Key Setup

Copy `config/config.example.json` to `config/config.json` and fill in your keys:

| Key | Provider | Free tier |
|---|---|---|
| `abuseipdb` | https://www.abuseipdb.com/ | ✅ 1 000 checks/day |
| `virustotal` | https://www.virustotal.com/ | ✅ 4 req/min |
| `numverify` | https://numverify.com/ | ✅ 100 req/month |
| `twilio_sid` + `twilio_token` | https://www.twilio.com/ | ✅ trial credits |

All keys are **optional** – the toolkit performs DNSBL lookups and phone
parsing entirely without API calls.

---

## Legal

This toolkit performs **non-intrusive, passive checks only**:
- DNS queries (standard resolution)
- HTTP GET requests with a clearly identified User-Agent
- SSL certificate inspection via standard TLS handshake
- Phone number parsing entirely offline (libphonenumber)

See [DISCLAIMER.md](DISCLAIMER.md) for full terms.
