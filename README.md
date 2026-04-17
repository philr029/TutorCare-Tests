# Security Diagnostic Toolkit

A modular, non-intrusive security diagnostic toolkit for IP reputation, phone number validation, and website health checks. Built with Python, with a CLI, web dashboard, and a **production-ready FastAPI REST API**.

> ⚠️ **For authorized use only.** See [DISCLAIMER.md](DISCLAIMER.md) for full legal and ethical usage terms.

---

## Features

| Module | Description |
|---|---|
| **IP Reputation** | DNSBL lookups (Spamhaus, SURBL, Barracuda, SpamCop, SORBS), AbuseIPDB, VirusTotal |
| **Phone Validation** | libphonenumber parsing, country/carrier/line-type, Numverify & Twilio APIs |
| **Website Health** | HTTP status, redirect chains, SSL certificate details, DNS records (A, MX, TXT, SPF, DMARC) |
| **REST API** | FastAPI service with auth, rate limiting, CORS, Pydantic validation, Swagger UI |
| **Web Dashboard** | Lightweight Flask UI at `http://localhost:5000/` |

---

## REST API

### Quick Start

```bash
# Install API dependencies
pip install -r requirements.txt -r requirements-api.txt
pip install -e .

# Start the API server (listens on http://localhost:8000)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive docs are available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/metrics` | Prometheus-format metrics |
| `POST` | `/check-ip` | DNSBL + AbuseIPDB check for an IPv4 address |
| `POST` | `/check-domain` | DNSBL check for a domain name |
| `POST` | `/validate-phone` | Parse and validate a phone number |
| `POST` | `/site-health` | HTTP + SSL + DNS diagnostics for a URL |

### Authentication

Pass your API key in the `X-API-Key` request header:

```bash
curl -H "X-API-Key: your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{"ip": "8.8.8.8"}' \
     http://localhost:8000/check-ip
```

Authentication is disabled when `API_KEYS` is empty or `AUTH_DISABLED=true`.

### Example Requests & Responses

#### `POST /check-ip`

```bash
curl -X POST http://localhost:8000/check-ip \
  -H "Content-Type: application/json" \
  -d '{"ip": "8.8.8.8"}'
```

```json
{
  "ip": "8.8.8.8",
  "dnsbl_results": [
    {"ip": "8.8.8.8", "dnsbl": "zen.spamhaus.org", "listed": false, "details": "Not listed"}
  ],
  "abuseipdb": null
}
```

#### `POST /check-domain`

```bash
curl -X POST http://localhost:8000/check-domain \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com"}'
```

```json
{
  "domain": "example.com",
  "resolved_ips": ["93.184.216.34"],
  "listed": false,
  "sources": []
}
```

#### `POST /validate-phone`

```bash
curl -X POST http://localhost:8000/validate-phone \
  -H "Content-Type: application/json" \
  -d '{"phone": "+14155552671"}'
```

```json
{
  "input": "+14155552671",
  "valid": true,
  "possible": true,
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

#### `POST /site-health`

```bash
curl -X POST http://localhost:8000/site-health \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "timeout": 10}'
```

```json
{
  "hostname": "example.com",
  "http": {"status_code": 200, "page_load_ms": 342.5, "error": null},
  "ssl":  {"valid": true, "days_until_expiry": 120, "error": null},
  "dns":  {"A": ["93.184.216.34"], "SPF": [], "DMARC": "No DMARC record found"},
  "checked_at": "2024-01-15T10:30:00+00:00"
}
```

### Rate Limiting

Default: **60 requests/minute per IP** (configurable via `RATE_LIMIT_DEFAULT`).  
Exceeding the limit returns `HTTP 429 Too Many Requests`.  
Uses Redis for distributed rate limiting when `REDIS_URL` is set, otherwise in-memory.

---

## Deployment

### Docker (single container)

```bash
# Build the API image
docker build -f Dockerfile.api -t security-toolkit-api .

# Run with environment variables
docker run --rm -p 8000:8000 \
  -e API_KEYS="your-secret-key" \
  -e LOG_JSON=true \
  security-toolkit-api
```

### Docker Compose (API + Redis)

```bash
# Copy and edit .env
cp .env.example .env

# Start services
docker-compose up --build

# Stop services
docker-compose down
```

The API will be available at http://localhost:8000.

### Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_PORT` | `8000` | Port |
| `API_WORKERS` | `1` | Uvicorn worker count |
| `DEBUG` | `false` | Reload on code changes |
| `API_KEYS` | *(empty)* | Comma-separated valid API keys |
| `AUTH_DISABLED` | `false` | Disable auth (dev only) |
| `RATE_LIMIT_DEFAULT` | `60/minute` | Rate limit per IP |
| `REDIS_URL` | *(none)* | Redis URL for distributed rate limiting |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `LOG_LEVEL` | `INFO` | Log level |
| `LOG_JSON` | `true` | JSON-structured log output |
| `REQUEST_TIMEOUT` | `10` | Network timeout (seconds) |
| `ABUSEIPDB_KEY` | *(empty)* | AbuseIPDB API key |
| `VIRUSTOTAL_KEY` | *(empty)* | VirusTotal API key |
| `NUMVERIFY_KEY` | *(empty)* | Numverify API key |
| `TWILIO_SID` | *(empty)* | Twilio Account SID |
| `TWILIO_TOKEN` | *(empty)* | Twilio Auth Token |

### Cloud Deployment

Deployment templates are in the `deploy/` folder:

| Template | File | Provider |
|----------|------|----------|
| Azure App Service | `deploy/azure-app-service.yml` | Azure |
| AWS ECS Fargate | `deploy/aws-ecs-fargate.json` | AWS |
| Google Cloud Run | `deploy/gcp-cloud-run.yml` | GCP |

Each template includes build commands, environment variable mapping, port configuration, and health check setup.

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

### With API support

```bash
pip install -r requirements.txt -r requirements-api.txt
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
# Core tests only
pip install -r requirements.txt
python -m pytest tests/ -v

# Including API tests
pip install -r requirements.txt -r requirements-api.txt
python -m pytest tests/ -v
```

---

## Project Structure

```
api/                            # FastAPI REST API layer
├── main.py                     # App factory + uvicorn entry point
├── config.py                   # Settings (env vars / .env)
├── routes/
│   ├── health.py               # GET /health, GET /metrics
│   ├── ip.py                   # POST /check-ip
│   ├── domain.py               # POST /check-domain
│   ├── phone.py                # POST /validate-phone
│   └── site.py                 # POST /site-health
├── controllers/
│   ├── ip_controller.py
│   ├── domain_controller.py
│   ├── phone_controller.py
│   └── site_controller.py
├── middleware/
│   ├── auth.py                 # API key authentication
│   ├── rate_limit.py           # SlowAPI rate limiter
│   └── logging.py              # Structured JSON request logging
├── schemas/
│   ├── ip_schemas.py           # Pydantic models (IP endpoints)
│   ├── domain_schemas.py
│   ├── phone_schemas.py
│   └── site_schemas.py
└── services/
    ├── ip_service.py           # Wrapper around src/ip_reputation
    ├── domain_service.py       # Wrapper around src/domain_reputation
    ├── phone_service.py        # Wrapper around src/phone_validation
    └── site_service.py         # Wrapper around src/site_diagnostics

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

deploy/
├── azure-app-service.yml       # Azure App Service + ACR deployment
├── aws-ecs-fargate.json        # AWS ECS Fargate task definition
└── gcp-cloud-run.yml           # Google Cloud Run + Cloud Build config

cli.py                          # Top-level CLI (check-ip, check-domain,
                                #   validate-phone, site-health)
config/
├── config.yaml                 # YAML configuration (production)
└── config.example.json         # JSON configuration template
Dockerfile                      # CLI / dashboard Docker image
Dockerfile.api                  # FastAPI service Docker image
docker-compose.yml              # API + Redis compose stack
.env.example                    # Environment variable template
requirements.txt                # Core dependencies
requirements-api.txt            # API-layer dependencies
tests/                          # pytest unit tests (123 tests)
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
