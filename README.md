# Flight Promotion Service

A Django-based microservice that automatically generates AI-powered flight promotion content by querying Elasticsearch for eligible flights, producing marketing copy via the Gemini API, and exposing the results through a REST API.

---

## Overview

The service solves a single problem: **every day, surface the 5 best available flights to US destinations and generate compelling promotional copy for each one**.

It does this through a fully automated pipeline:

1. **Elasticsearch** — Queries the `kibana_sample_data_flights` index for non-cancelled, non-delayed flights to the US with an average ticket price above $500.
2. **Gemini AI** — Each flight's data is formatted into a strict prompt and sent to the Gemini API, which returns a structured JSON promotional title + content.
3. **MinIO (S3-compatible storage)** — Stores generated flight promotions (`outputs/{date}/{date}.json`) and generation inputs (`inputs/{date}/{date}.json`) as single JSON files per date, along with run manifests.
4. **REST API** — A Django REST Framework API exposes the promotions for consumption.
5. **APScheduler** — A dedicated Django management command runs the pipeline automatically every midnight.

---

### Tech Stack

| Component | Technology |
|---|---|
| API Framework | Django 5.1 + Django REST Framework |
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
├── apps/               # Applications directory
│   └── promotions/     # Core flight promotion domain application
│       ├── api/        # HTTP layer (endpoints and responses)
│       ├── clients/    # External service adapters (Elasticsearch, MinIO, Gemini)
│       ├── management/ # CLI commands (manual generation, scheduler)
│       ├── schemas/    # Pydantic models for data validation
│       └── services/   # Business logic (pipeline orchestration, prompt building)
├── config/             # Django project configuration (settings, root URLs)
├── docker/             # Initialization scripts for MinIO and Elasticsearch
├── docker-compose.yml  # Orchestrates all services (ES, MinIO, API, Scheduler)
└── manage.py           # Django CLI entrypoint
```

### Data Flow

```
Elasticsearch (Flight Data) ──► Generation Pipeline (Gemini AI)
                                      │
                                      ▼
                                MinIO Bucket
                       (flight-promotions/)
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
             outputs/{date}/                     inputs/{date}/
             {date}.json                         {date}.json
             (All 5 Promotion Contents)          (Prompts & Flight Inputs)
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

3. **Start all services:**
   ```bash
   docker-compose up --build -d
   ```

---

## API Endpoints

Base URL: `http://localhost:8000/api/v1/promotions/`

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness check (returns 200 OK). |
| `/` | GET | Returns the latest generated promotions list. Accepts optional `?date=YYYY-MM-DD`. |

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
```

Run Django system checks and tests:
```bash
docker-compose exec web python manage.py check
docker-compose exec web python manage.py test apps.promotions
```

---

## Key Design Decisions

### 1. Single JSON File per Date in MinIO
All 5 generated flight promotion contents for a given date are stored together in a single JSON file at `outputs/{date}/{date}.json`. Similarly, all prompt inputs and raw flight details are stored in `inputs/{date}/{date}.json`. This simplifies MinIO object management and enables single-request retrieval.

### 2. Elimination of Relational Database Prompts
Prompts and generation inputs are preserved in MinIO object storage (`inputs/{date}/{date}.json`) rather than PostgreSQL columns, keeping external database dependencies minimal and audit records co-located with output assets.

### 3. APScheduler over system cron
The scheduler runs as a standard Django management command (`run_scheduler`) using APScheduler's `BlockingScheduler`. This means:
- No cron daemon or root privileges required
- Full access to Django settings and environment variables natively
- Scheduler timezone is controlled by `settings.TIME_ZONE`

### 4. Idempotent daily runs
The pipeline checks for existing output/manifest before generating. If today's run already exists in MinIO, the generation step exits gracefully.

### 5. Centralised retry configuration
All external clients (MinIO, Elasticsearch, Gemini) use `settings.DEFAULT_MAX_RETRIES` for their tenacity retry count.
