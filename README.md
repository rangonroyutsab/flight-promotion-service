# Flight Promotion Service

A Django-based microservice that automatically generates AI-powered flight promotion content by querying Elasticsearch for eligible flights, producing marketing copy via the Gemini API, and exposing the results through a REST API.

---

## Overview

The service solves a single problem: **every day, surface the 5 best available flights to US destinations and generate compelling promotional copy for each one**.

It does this through a fully automated pipeline:

1. **Elasticsearch** — Queries the `kibana_sample_data_flights` index for non-cancelled, non-delayed flights to the US with an average ticket price above $500.
2. **Gemini AI** — Each flight's data is formatted into a strict prompt and sent to the Gemini API, which returns a structured JSON promotional title + content.
3. **MinIO (S3-compatible storage)** — The generated promotion objects and a daily run manifest are stored as JSON files.
4. **PostgreSQL** — Stores a `PromotionPrompt` audit record for each generated promotion, linking the promotion UUID to its MinIO object key.
5. **REST API** — A Django REST Framework API exposes the promotions for consumption.
6. **APScheduler** — A dedicated Django management command runs the pipeline automatically every midnight.

---

### Tech Stack

| Component | Technology |
|---|---|
| API Framework | Django 5.1 + Django REST Framework |
| Database | PostgreSQL 16 |
| Object Storage | MinIO (S3-compatible) |
| Search / Data Source | Elasticsearch 8.15 |
| AI Provider | Google Gemini (via REST API) |
| Scheduler | APScheduler 3.x (blocking, in-process) |
| Containerization | Docker + Docker Compose |
| Data Validation | Pydantic v2 |
| Retry Logic | Tenacity |

---

## Project Architecture

### Directory Structure

```
flight-promotion-service/
├── config/             # Django project configuration (settings, root URLs)
├── promotions/         # Core application containing all business logic
│   ├── api/            # HTTP layer (endpoints and responses)
│   ├── clients/        # External service adapters (Elasticsearch, MinIO, Gemini)
│   ├── management/     # CLI commands (manual generation, scheduler)
│   ├── schemas/        # Pydantic models for data validation
│   └── services/       # Core business logic (pipeline orchestration, prompt building)
├── docker/             # Initialization scripts for MinIO and Elasticsearch
├── docker-compose.yml  # Orchestrates all services (Postgres, ES, MinIO, API, Scheduler)
└── manage.py           # Django CLI entrypoint
```

### Data Flow

```
Elasticsearch (Flight Data) ──► Generation Pipeline (Gemini AI)
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
         MinIO (JSON)                                PostgreSQL (Audit)
  (Promotions & Manifests)                         (PromotionPrompt Logs)
               │
               ▼
          REST API
   GET /api/v1/promotions/
```

---

## Project Setup

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd flight-promotion-service
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   Add your API keys to `.env` (or leave `AI_PROVIDER=mock` for testing).

2. **Start all services:**
   ```bash
   docker-compose up --build -d
   ```

---

## API Endpoints

Base URL: `http://localhost:8000/api/v1/promotions/`

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness check (returns 200 OK). |
| `/` | GET | Returns the latest generated promotions. Accepts optional `?date=YYYY-MM-DD`. |
| `/{id}` | GET | Returns full details of a specific promotion. |

---

## Testing Commands

Generate promotions manually (runs the pipeline immediately):
```bash
docker-compose exec web python manage.py generate_flight_promotions
```

Test the API:
```bash
# Health check
curl http://localhost:8000/health

# Latest promotions
curl http://localhost:8000/api/v1/promotions/

# Promotions for a specific date
curl "http://localhost:8000/api/v1/promotions/?date=2026-08-07"

# Promotion detail
curl "http://localhost:8000/api/v1/promotions/<promotion-uuid>"
```

Run Django system checks:
```bash
docker-compose exec web python manage.py check
```

---

## Key Design Decisions

### 1. APScheduler over system cron
The scheduler runs as a standard Django management command (`run_scheduler`) using APScheduler's `BlockingScheduler`. This means:
- No cron daemon or root privileges required
- Full access to Django settings and environment variables natively
- Scheduler timezone is controlled by `settings.TIME_ZONE`

### 2. MinIO as the promotion store (not Postgres)
Generated promotion content and manifests are stored as JSON objects in MinIO rather than Postgres columns. This keeps the relational DB lean (it only holds audit/audit-pointer records) and allows large promotion payloads to be fetched concurrently without DB query pressure.

### 3. Idempotent daily runs
The pipeline checks for an existing manifest before generating. If today's manifest already exists in MinIO, the run exits immediately with a log message. Promotion UUIDs are derived deterministically via `uuid5(date:flight_id)`, so re-running on the same day produces identical IDs and `update_or_create` prevents Postgres duplicates.


### 4. Concurrent MinIO reads
When listing promotions, the service fetches individual promotion JSON objects from MinIO concurrently using `ThreadPoolExecutor` (max 5 workers — matching the ES result limit). This prevents sequential latency from degrading the list API response time.

### 5. Centralised retry configuration
All external clients (MinIO, Elasticsearch, Gemini) use `settings.DEFAULT_MAX_RETRIES` for their tenacity retry count. The Gemini client applies the retry decorator lazily (as an inner function) to avoid reading settings at class-definition/import time — a subtle Django app registry coupling issue.

