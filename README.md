# CS366 — Report Ingestion & Verification Service

> Serverless intake and human-verification layer สำหรับ disaster reports: รับข้อมูลดิบ, วิเคราะห์ด้วย AI, คัดซ้ำ, ให้เจ้าหน้าที่ verify, แล้ว publish ต่อให้ service downstream ใช้งานได้จริง

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Terraform](https://img.shields.io/badge/Terraform-1.5+-purple.svg)](https://www.terraform.io/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![Google Gemini](https://img.shields.io/badge/AI-Gemini-green.svg)](https://ai.google.dev/)

## 📋 Overview

ระบบนี้ทำหน้าที่เป็น verified-intake gateway สำหรับข้อมูลเหตุภัยพิบัติจากหลายแหล่ง เช่น social posts, mobile app reports, และ IoT sensor alerts โดย flow ปัจจุบันคือ:

1. **Ingest** — รับ report ผ่าน `POST /v1/reports` หรืออัปโหลด media แยกผ่าน `POST /v1/reports/upload-url`
2. **Queue & Persist** — บันทึก placeholder report ลง DynamoDB แล้วส่งงานต่อเข้า SQS
3. **Analyze** — ใช้ Gemini วิเคราะห์ trust score, suggested category, tags และทำ graceful fallback ได้ถ้า AI ใช้งานไม่ได้
4. **Deduplicate** — ตรวจซ้ำจาก `source_external_id`, geo/time proximity, และ content similarity
5. **Verify** — เจ้าหน้าที่ review ผ่าน API หรือหน้า `admin-verify` แล้วเลือก verify/reject/spam/duplicate
6. **Publish & Link Back** — ส่ง EventBridge events ไป downstream และรองรับ callback ที่ `POST /v1/report-incident` เพื่อ link incident กลับเข้ารายงาน

### Service Owner
- **Akawat Moradsatian** (6609681231)

### Current Snapshot
- ✅ 4 Lambda functions, 3 DynamoDB tables, 1 SQS queue + DLQ, 1 custom EventBridge bus
- ✅ Frontend มีทั้ง landing page, API dashboard, และ admin verification console
- ✅ Observability ครบกว่าช่วงต้นโปรเจกต์: `X-Trace-Id`, audit log, recent events, trace lookup, RSS changelog, deprecation metadata
- ✅ AI resilience รองรับ multi-key rotation + model fallback และถ้า AI ล้มเหลวจะตั้ง `ai_analysis_failed=true` เพื่อให้ manual review ทำงานต่อได้
- ✅ Media evidence upload ผ่าน S3 presigned URL สูงสุด 20 MB ตาม config ปัจจุบัน

### Pain Points ที่แก้ไข
- ⚡ **Information Overload** — write path แยก async ผ่าน SQS เพื่อรองรับ traffic ช่วงวิกฤต
- 🔄 **Noise & Redundancy** — กรอง spam/duplicate ด้วย rules + AI-assisted analysis
- 📝 **Unstructured Data** — normalize ข้อมูลจากหลาย source ให้อยู่ใน workflow เดียวกันก่อนส่งต่อ downstream

## 🏗️ Architecture

```
External Client / Dashboard / Admin Verify
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│              API Gateway (REST /v1)            │
│  API key required: POST /reports, /upload-url  │
│  Demo/admin routes: GET/PATCH/DELETE/trace/etc │
└───────┬───────────────────────┬─────────────────┘
        │                       │
        ▼                       ▼
┌──────────────┐        ┌─────────────────────┐
│Ingest Handler│        │ API / Health Lambda │
└──────┬───────┘        └───────┬─────────────┘
       │                        │
       ▼                        ├──────────────► DynamoDB (Reports / Audit / Stats)
┌──────────────┐                ├──────────────► EventBridge
│ SQS + DLQ    │                ├──────────────► S3 Media (presigned upload URL)
└──────┬───────┘                └──────────────► CloudWatch Logs / trace lookup
       │
       ▼
┌─────────────────────────────────────────────────┐
│              Ingestion Worker Lambda           │
│  - Gemini trust scoring + fallback            │
│  - Dedup: external_id + geo/time + content    │
│  - Async processing and report enrichment      │
└─────────────────────────────────────────────────┘

Static UI: S3 Website hosting `/`, `/dashboard/`, `/admin-verify/`
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Runtime | Python 3.12 |
| Compute | AWS Lambda (4 functions) |
| API | API Gateway (REST) |
| Database | DynamoDB (Reports, AuditLogs, Stats) |
| Queue | SQS + Dead Letter Queue |
| Events | EventBridge (custom bus) |
| AI | Google Gemini with configurable model fallback chain |
| Storage | S3 Static Website + S3 Media Bucket |
| IaC | Terraform |
| Auth | API Key for ingest and media upload endpoints |
| Observability | CloudWatch Logs, `X-Trace-Id`, RSS changelog, deprecation metadata |

## Prerequisites

- AWS Learner Lab session with valid credentials
- [Terraform](https://www.terraform.io/downloads) >= 1.5
- Python 3.12+
- `pip`
- At least 1 Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- Optional: Incident Service base URL for live validation of `link_to_incident_id`

## Quick Start

```bash
# 1. Clone repository
git clone <repo-url>
cd CS366-Serverless-RequestVerifyService

# 2. (Optional but recommended) install local dev dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# 3. Set AWS credentials from Learner Lab
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...

# 4. Create .env for deploy.sh
cat > .env <<'EOF'
GEMINI_API_KEY1=your-first-gemini-key
# Optional when verifying and linking to existing incidents
INCIDENT_SERVICE_BASE_URL=https://incident-service.example/api/v1
EOF

# 5. Deploy everything
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 6. Read important outputs
cd terraform
terraform output -raw api_url
terraform output -raw api_key
terraform output -raw website_url
terraform output -raw dashboard_url
terraform output -raw openapi_spec_url
```

### Deploy Notes

- `scripts/deploy.sh` อ่านค่าจาก `.env` หรือ environment variables แล้ว generate `terraform/terraform.tfvars` ให้อัตโนมัติ
- รองรับ `GEMINI_API_KEY1..N` และ model fallback chain สำหรับ Gemini
- ถ้าไม่ตั้ง `INCIDENT_SERVICE_BASE_URL` ระบบยังทำงานได้ แต่ verify flow จะไม่สามารถ validate incident reference แบบ live ได้
- หน้า admin console ใช้ URL เดียวกับ `website_url` แล้วต่อท้าย `/admin-verify/`

## 📚 API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/v1/reports` | API Key | Submit raw report for async ingestion (`202 Accepted`) |
| `POST` | `/v1/reports/upload-url` | API Key | Generate presigned S3 PUT URL for media evidence |
| `GET` | `/v1/reports` | None | List reports with status, trust score, priority, and limit filters |
| `GET` | `/v1/reports/{id}` | None | Get full report detail with AI analysis and linked incident info |
| `PATCH` | `/v1/reports/{id}` | None | Verify, reject, spam, or mark duplicate; optional incident linking when verified |
| `DELETE` | `/v1/reports/{id}` | None | Soft delete a report with audit reason |
| `GET` | `/v1/reports/stats` | None | Aggregated statistics, trending keywords, and heatmap data |
| `GET` | `/v1/reports/audit` | None | Audit log history |
| `GET` | `/v1/reports/events` | None | Recent EventBridge event mirror from CloudWatch logs |
| `GET` | `/v1/reports/trace/{trace_id}` | None | Cross-Lambda trace lookup by `X-Trace-Id` |
| `POST` | `/v1/report-incident` | None | Callback from Incident Tracking Service to link incident result back |
| `GET` | `/v1/health` | None | Dependency-aware health check |
| `GET` | `/v1/changelog.xml` | None | RSS feed for release and contract changes |
| `GET` | `/v1/deprecation-info` | None | Deprecated/sunset endpoint metadata |

### Query Parameters ที่ใช้บ่อย

- `GET /v1/reports?status=PENDING_REVIEW&priority=high&min_trust_score=80&limit=10`
- `GET /v1/reports/stats?timeframe=today|last_24h|last_7d&region=bkk|central|north|northeast|south`
- `GET /v1/reports/audit?report_id=<report_id>&limit=20`
- `GET /v1/reports/events?type=all|verified|status-changed&limit=20`

### Report Status Lifecycle

```
RECEIVED → PENDING_REVIEW → VERIFIED
    │             ├──→ REJECTED
    │             ├──→ SPAM
    │             └──→ DUPLICATE
    └──────────────────────────────► DELETED
```

ถ้า downstream Incident Tracking Service สร้าง incident สำเร็จ callback ที่ `POST /v1/report-incident` จะเติม `linked_incident_id` และเขียน audit log เพิ่มให้อัตโนมัติ

### Example — Submit a report

```bash
API_URL="https://xxx.execute-api.us-east-1.amazonaws.com/dev/v1"
API_KEY="your-api-key"

curl -X POST "$API_URL/reports" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $API_KEY" \
  -d '{
    "reporter_source": "TWITTER",
    "reporter_id": "@somchai",
    "raw_content": "ไฟไหม้ร้านทอง เยาวราช ตอนนี้เลย!",
    "geo_location": {"lat": 13.7422, "lon": 100.5108}
  }'
```

Response:

```json
{
  "status": "QUEUED",
  "report_id": "r-550e8400e29b",
  "message": "Report accepted and queued for processing.",
  "estimated_wait_time": "2s",
  "traceId": "2c4f7f1d-..."
}
```

### Example — Media Upload Flow

1. Call `POST /v1/reports/upload-url` with `filename`, `content_type`, and optional `report_id` / `file_size_bytes`
2. `PUT` the file body to the returned `upload_url`
3. Include returned `media_url` in `POST /v1/reports` under `media_urls`

## 🖥️ Frontend

| Page | Path | Purpose |
|------|------|---------|
| Landing Page | `/` | Project overview and entry point |
| Dashboard | `/dashboard/` | API tester for health, reports, stats, events, upload URL, and trace lookup |
| Admin Verify | `/admin-verify/` | Pending report queue, detailed review, verify/reject/delete actions, audit trail, and incident linking |

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run unit + integration tests
pytest tests/unit/ tests/integration/ -v

# Run with coverage
pytest tests/unit/ tests/integration/ --cov=src --cov-report=term-missing

# Run E2E tests against deployed API
API_URL=https://xxx.execute-api.../dev API_KEY=xxx pytest tests/e2e/ -v
```

### Test Coverage

- **Unit Tests**: config, validators, ingest handler, ingestion worker, API handler, Gemini service, dedup service
- **Integration Tests**: DynamoDB operations, SQS flow, EventBridge publish
- **E2E Tests**: API contract validation, ingest flow, verify flow
- `pytest` ถูกตั้งค่าไว้ใน `pyproject.toml` และ E2E จะ auto-skip ถ้าไม่ได้ตั้ง `API_URL`

## 📁 Project Structure

```text
src/
├── config.py                 # Environment and feature flags
├── models/
│   ├── enums.py              # ValidationStatus, SourcePlatform, IncidentType, etc.
│   └── report.py             # Report, GeoLocation, AuditLog dataclasses
├── utils/
│   ├── logger.py             # Structured JSON logging
│   ├── response.py           # API Gateway response helpers + trace/deprecation headers
│   └── validators.py         # Payload and state transition validation
├── services/
│   ├── gemini_service.py     # Gemini integration, key rotation, model fallback
│   ├── dedup_service.py      # External ID, geo/time, and content similarity dedup
│   ├── geocoding_service.py  # Reverse geocoding enrichment
│   ├── audit_service.py      # Audit log writer
│   └── event_publisher.py    # EventBridge publisher
└── handlers/
    ├── ingest_handler.py     # POST /reports -> DynamoDB placeholder -> SQS
    ├── ingestion_worker.py   # SQS -> AI/dedup/process -> DynamoDB
    ├── api_handler.py        # Report read/review/admin/trace/callback endpoints
    └── health_handler.py     # GET /health

frontend/
├── index.html                # Landing page
├── dashboard/
│   └── index.html            # API testing dashboard
└── admin-verify/
    └── index.html            # Admin verification console

terraform/                    # Infrastructure as code and outputs
scripts/                      # deploy.sh, destroy.sh, seed_data.py
tests/                        # unit, integration, e2e suites
docs/                         # OpenAPI, phase notes, versioning policy, implementation docs
plan/                         # Original project planning documents
```

## 🔄 EventBridge Events

| Event | Description | Consumer |
|-------|-------------|----------|
| `ReportVerifiedEvent` | Fired after verification with `schemaVersion`, action, suggested incident data, severity, reporter count, location, media evidence, and optional address text | Incident Tracking Service and downstream consumers |
| `ReportStatusChangedEvent` | Fired on status transitions with `schemaVersion`, old/new status, actor, reason, and timestamp | Dashboard, Notification, and monitoring consumers |

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [📋 Implementation Plan](docs/implement/implementation-plan.md) | Phase-based implementation snapshot from March 2026; useful as historical context but not the latest source of truth |
| [🧩 OpenAPI 3.0 Spec](docs/openapi/openapi.json) | Machine-readable contract for the primary REST endpoints |
| [🗂️ Versioning Policy](docs/VERSIONING_POLICY.md) | REST and event versioning/deprecation policy |
| [🎤 Demo Scope Mapping](docs/phase2/demoday.md) | อธิบายว่า service นี้อยู่ตรงไหนใน simulator และ integration flow |
| [🔗 Integration Guide](docs/implement/integration-guide.md) | คู่มือ integration กับ services อื่น |
| [📄 Service Proposal (PDF)](docs/Service%20Proposal%206609681231%20WordVer2.pdf) | Proposal ฉบับเต็ม |
| [📝 Service Proposal (Text)](docs/others/reportingestion_proposal.txt) | Proposal แบบ text |
| [🔧 Original Plan](plan/implementation-plan.md) | แผน implementation ฉบับตั้งต้น |

## 🚀 หลังเดโม ถ้าจะปรับต่อ

- **ปิดช่องโหว่ด้าน auth/admin flow**: แยก public ingest ออกจาก admin/reviewer/trace/callback endpoints และใส่ RBAC หรือ Lambda authorizer ให้ชัดเจน
- **รวม contract ให้เหลือ source of truth เดียว**: ขยาย OpenAPI ให้ครอบคลุม `audit`, `events`, `trace`, `deprecation-info`, และ `report-incident` ด้วย เพื่อลด drift ระหว่าง docs กับ code
- **ทำ operational hardening จริงจัง**: เพิ่ม CloudWatch dashboard, alarms, DLQ redrive workflow, load testing, และ retry/outbox strategy สำหรับ downstream event delivery
- **เก็บ repo ให้ production-friendly กว่าเดโม**: เพิ่ม `.env.example`, เอา generated artifacts/state ออกจาก version control, และใส่ CI สำหรับ test + lint + docs checks
- **ยกระดับ data quality loop**: ใช้ reviewer feedback ย้อนกลับไปปรับ scoring, เพิ่ม multilingual similarity/dedup, และทำ source reputation/history ให้มีน้ำหนักมากขึ้น
- **เพิ่ม staging/integration ergonomics**: มี test environment, custom domain, และ callback contract testing กับ Incident Service แบบอัตโนมัติ

## 🗑️ Tear Down

```bash
./scripts/destroy.sh
```

## 🤝 Related Services

| Service | Interaction |
|---------|-------------|
| **Incident Tracking Service** | รับ `ReportVerifiedEvent` เพื่อสร้างหรือ merge incident และ callback กลับที่ `POST /v1/report-incident` |
| **Rescue Request Service** | ใช้ verified events ที่มี severity สูงเป็น trigger หรือ context |
| **Operation Update Service** | เรียก `GET /v1/reports/stats` สำหรับ dashboard/summary |
| **Disaster Monitoring Service** | ส่ง `POST /v1/reports` จาก sensor หรือ field updates |

---

**Service Owner**: Akawat Moradsatian (6609681231)  
**Course**: CS366 — Serverless Computing  
**API Version**: `/v1`