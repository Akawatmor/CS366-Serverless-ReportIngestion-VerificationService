# Implementation Plan — Report Ingestion & Verification Service

> **เอกสารนี้เป็นแผนการ Implement ที่เปลี่ยนจาก Service Proposal ให้เป็นระบบที่ทำงานจริงบน AWS Learner Lab**
> 
> อัปเดตล่าสุด: 2025-01

---

## 1. Gap Analysis จาก Service Proposal

### 1.1 สิ่งที่ Proposal กำหนดไว้แล้ว ✅
| หัวข้อ | รายละเอียด |
|--------|-----------|
| Service Purpose | Central Gateway สำหรับ Disaster Reports |
| Pain Points | Information Overload, Noise & Redundancy, Unstructured Data |
| API Contracts | POST /reports, GET /reports, PATCH /reports/{id}, GET /reports/{id} |
| Async Contract | ReportVerifiedEvent, ReportStatusChangedEvent (EventBridge) |
| Owned Data | report_id, source_metadata, content_payload, analysis_result, verification_status |
| Non-Functional | High Scalability, Data Integrity, Async Processing |

### 1.2 สิ่งที่ต้องเพิ่มเติมและตัดสินใจ ❗
| หัวข้อ | จาก Proposal | Implementation Decision |
|--------|-------------|----------------------|
| AI Engine | Amazon Comprehend | **Google Gemini** (gemini-2.0-flash) — ยืดหยุ่นกว่าและไม่จำกัดใน Learner Lab |
| Authentication | JWT / Cognito | **API Key** (AWS API Gateway Usage Plan) — ง่ายขึ้นสำหรับ Lab |
| IaC Tool | ไม่ได้ระบุ | **Terraform** (~> 5.0, AWS Provider) |
| Language | ไม่ได้ระบุ | **Python 3.12** (Lambda Runtime) |
| DELETE endpoint | ไม่มี | เพิ่ม **DELETE /reports/{id}** (Soft delete) |
| Stats endpoint | ไม่มี | เพิ่ม **GET /reports/stats** (Atomic counter) |
| Health check | ไม่มี | เพิ่ม **GET /health** |
| Logging | ไม่มี | Structured JSON logging → CloudWatch |
| Test strategy | ไม่ได้ระบุ | pytest + moto (Unit/Integration) + httpx (E2E) |
| Deploy script | ไม่มี | `deploy.sh` — one-command build & deploy |

---

## 2. Architecture Overview

```
External Client
      │
      ▼
┌─────────────────────────────────────┐
│         API Gateway (REST)          │
│   X-Api-Key auth + Usage Plan      │
│   Rate: 50 req/s, Burst: 100       │
└───┬──────────┬──────────┬──────────┘
    │          │          │
    ▼ POST     ▼ GET/PATCH/DELETE    ▼ GET
┌────────┐  ┌────────────────┐  ┌──────────┐
│ Ingest │  │  API Handler   │  │  Health  │
│Handler │  │   (Lambda)     │  │ Handler  │
└───┬────┘  └───┬────────┬───┘  └──────────┘
    │           │        │
    ▼           ▼        ▼
┌────────┐  ┌────────┐  ┌────────────┐
│  SQS   │  │DynamoDB│  │ EventBridge│
│ Queue  │  │Reports │  │ Custom Bus │
└───┬────┘  │Audit   │  └────────────┘
    │       │Stats   │
    ▼       └────────┘
┌────────────────────┐
│ Ingestion Worker   │
│    (Lambda)        │
│ ┌──────────────┐   │
│ │ Gemini AI    │   │
│ │ Trust Scoring│   │
│ └──────────────┘   │
│ ┌──────────────┐   │
│ │ Dedup Logic  │   │
│ │ Haversine    │   │
│ └──────────────┘   │
└────────────────────┘
```

### 2.1 Lambda Functions (4 ตัว)
| Function | Trigger | หน้าที่ |
|----------|---------|--------|
| `ingest-handler` | API Gateway POST /reports | รับ raw report → validate → ส่ง SQS → ตอบ 202 |
| `ingestion-worker` | SQS Event Source | Gemini AI → Dedup → Write DynamoDB → Publish Event |
| `api-handler` | API Gateway GET/PATCH/DELETE | List, Detail, Verify, Delete reports |
| `health-handler` | API Gateway GET /health | ตรวจสอบ DynamoDB, SQS, Gemini, EventBridge |

### 2.2 DynamoDB Tables (3 ตาราง)
| Table | PK | GSI | Mode |
|-------|----|-----|------|
| `Reports` | report_id | gsi_status_ingested, gsi_source_external_id | PAY_PER_REQUEST |
| `AuditLogs` | log_id | gsi_report_timestamp | PAY_PER_REQUEST |
| `Stats` | stat_key | - | PAY_PER_REQUEST |

### 2.3 Event Bus
- Custom EventBridge Bus: `disaster-events`
- Events: `ReportVerifiedEvent`, `ReportStatusChangedEvent`
- Target: CloudWatch Logs (สำหรับ debugging)

### 2.4 S3 Static Website
- Bucket: `{prefix}-website-{account_id}` (public read)
- `/` → Landing page (index.html) — Project info, architecture overview, API docs
- `/dashboard/` → API Testing Dashboard (dashboard/index.html) — Interactive API tester
- CORS enabled, Website hosting configuration
- Files managed by Terraform (`aws_s3_object` with etag for auto-updates)

---

## 3. State Machine — Report Lifecycle

```
RECEIVED → PENDING_REVIEW → VERIFIED
    │              ↓↗
    │         NEEDS_MORE_INFO
    │              ↓
    ├──→ SPAM     REJECTED
    └──→ DUPLICATE

ทุกสถานะ → DELETED (Soft delete)
```

### Valid Transitions
| From | Allowed To |
|------|-----------|
| RECEIVED | PENDING_REVIEW, SPAM, DUPLICATE |
| PENDING_REVIEW | VERIFIED, REJECTED, NEEDS_MORE_INFO, SPAM, DUPLICATE |
| NEEDS_MORE_INFO | PENDING_REVIEW, REJECTED |
| VERIFIED | (terminal — ยกเว้น soft delete) |
| REJECTED | (terminal) |
| SPAM | (terminal) |
| DUPLICATE | (terminal) |

---

## 4. API Endpoints — Final Spec

### 4.1 POST /v1/reports (Async Ingestion)
- **Auth:** X-Api-Key
- **Body:** reporter_source, reporter_id, raw_content, media_urls?, geo_location?, timestamp?
- **Response:** 202 `{ status: "QUEUED", report_id: "r-...", message: "..." }`
- **Flow:** Validate → Generate UUID → SendMessage SQS → Return 202

### 4.2 GET /v1/reports (List)
- **Auth:** X-Api-Key
- **Query:** status (required filter), limit (1-100), last_evaluated_key
- **Response:** 200 `{ items: [...], last_evaluated_key?: "..." }`

### 4.3 GET /v1/reports/{report_id} (Detail)
- **Auth:** X-Api-Key
- **Response:** 200 `{ report_id, status, trust_score, ai_analysis, ... }`

### 4.4 PATCH /v1/reports/{report_id} (Verify/Reject)
- **Auth:** X-Api-Key
- **Body:** action (VERIFY|REJECT|NEEDS_MORE_INFO), reviewer_id, comment?
- **Response:** 200 `{ report_id, status, verified_by, updated_at }`
- **Optimistic Locking:** ConditionExpression ป้องกัน race condition

### 4.5 DELETE /v1/reports/{report_id} (Soft Delete)
- **Auth:** X-Api-Key
- **Body:** deleted_by, reason
- **Response:** 200 `{ report_id, status: "DELETED" }`

### 4.6 GET /v1/reports/stats (Statistics)
- **Response:** 200 `{ period, total, by_status: {...}, by_category: {...} }`

### 4.7 GET /v1/health (Health Check)
- **Response:** 200/503 `{ status, components: { dynamodb, sqs, gemini, eventbridge } }`

---

## 5. Gemini AI Integration

### 5.1 ใช้ที่ไหน
- **Ingestion Worker เท่านั้น** — วิเคราะห์ raw_content เพื่อให้ Trust Score

### 5.2 Prompt Structure
```text
Analyze this disaster report and return JSON:
- trust_score (0-100)
- suggested_category (FLOOD, FIRE, EARTHQUAKE, ...)
- keywords []
- reasoning (string)
- is_spam_likely (bool)
```

### 5.3 Fallback Strategy
- หาก Gemini API ล่ม → return trust_score=50, ai_analysis_failed=true
- ระบบไม่หยุดทำงาน, แค่ flag ว่า AI วิเคราะห์ไม่สำเร็จ

---

## 6. Deduplication Logic

### 6.1 External ID Check
- ใช้ GSI `gsi_source_external_id` ตรวจสอบว่ามี report จาก source+reporter_id เดิมหรือไม่

### 6.2 Geo-Temporal Matching
- **Distance:** Haversine formula, ≤ 200m
- **Time window:** ≤ 15 นาที
- ถ้าตรงทั้ง 2 เงื่อนไข → mark เป็น `DUPLICATE`

---

## 7. Testing Strategy

### 7.1 Unit Tests (`tests/unit/`)
- Validator functions (all edge cases)
- Gemini service (mock API response)
- Dedup service (Haversine math, time windows)
- API handler (routing, verify logic)

### 7.2 Integration Tests (`tests/integration/`)
- DynamoDB CRUD via **moto** library
- SQS send/receive + Worker processing
- EventBridge publish events

### 7.3 E2E Tests (`tests/e2e/`)
- ต้องมี deployed API (set `API_URL` env var)
- Full ingest flow: POST → SQS → Worker → DynamoDB
- Verify flow: PATCH → status change → EventBridge
- All API contract shapes

### 7.4 Coverage Target
- Minimum: 60% (enforced ใน pyproject.toml)

---

## 8. Deployment

### 8.1 Prerequisites
- AWS Learner Lab session (active credentials)
- Terraform ≥ 1.5
- Python 3.12
- Google Gemini API Key

### 8.2 One-Command Deploy
```bash
# ตั้งค่า credentials
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...

# Deploy ทั้งหมด
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 8.3 deploy.sh ทำอะไรบ้าง
1. Clean build artifacts
2. Build Lambda Layer (pip install → zip)
3. Package source code (src/ → zip)
4. `terraform init`
5. `terraform apply -auto-approve` (prompt ให้ใส่ Gemini API Key)

### 8.4 Destroy
```bash
./scripts/destroy.sh
```

---

## 9. Project Structure

```
├── src/
│   ├── config.py              # Environment config singleton
│   ├── models/
│   │   ├── enums.py           # All enums (Status, Source, Incident, Severity)
│   │   └── report.py          # Report, GeoLocation, AuditLog dataclasses
│   ├── utils/
│   │   ├── logger.py          # Structured JSON logging
│   │   ├── response.py        # API Gateway response builders
│   │   └── validators.py      # Request validation + state machine
│   ├── services/
│   │   ├── gemini_service.py  # Google Gemini AI trust scoring
│   │   ├── dedup_service.py   # Deduplication (Haversine + time window)
│   │   ├── audit_service.py   # Audit log writer
│   │   └── event_publisher.py # EventBridge publisher
│   └── handlers/
│       ├── ingest_handler.py  # POST /reports → SQS
│       ├── ingestion_worker.py# SQS → Process → DynamoDB
│       ├── api_handler.py     # GET/PATCH/DELETE /reports
│       └── health_handler.py  # GET /health
├── terraform/
│   ├── main.tf, variables.tf, outputs.tf
│   ├── dynamodb.tf, sqs.tf, eventbridge.tf
│   ├── iam.tf, lambda.tf, api_gateway.tf
│   ├── s3.tf                  # S3 static website hosting
│   └── modules/cors/          # Reusable CORS OPTIONS module
├── frontend/
│   ├── index.html             # Landing page (/)
│   └── dashboard/
│       └── index.html         # API Testing Dashboard (/dashboard/)
├── scripts/
│   ├── deploy.sh              # One-command deploy
│   ├── destroy.sh             # Terraform destroy
│   └── seed_data.py           # Sample data seeder
├── tests/
│   ├── conftest.py            # Shared fixtures
│   ├── unit/                  # Pure logic tests (mocked)
│   ├── integration/           # AWS-mocked tests (moto)
│   └── e2e/                   # Live API tests (httpx)
├── docs/
│   └── Service Proposal.md
├── plan/
│   └── implementation-plan.md # ← เอกสารนี้
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml             # pytest config
└── .gitignore
```

---

## 10. Design Decisions — เหตุผลที่เลือก

| Decision | Why |
|----------|-----|
| Gemini แทน Comprehend | Learner Lab จำกัด service access; Gemini API ยืดหยุ่นกว่า |
| API Key แทน JWT/Cognito | ลด complexity สำหรับ Lab; API Gateway Usage Plan เพียงพอ |
| SQS + Worker แทน Direct-to-DB | Decouple ingestion จาก processing; Zero data loss (SQS retention 14d) |
| Stats Counter Table | หลีกเลี่ยง Table Scan ที่แพง; Atomic increment ใน DynamoDB |
| Soft Delete แทน Hard Delete | เก็บข้อมูลไว้สำหรับ audit trail; flag DELETED + timestamp |
| EventBridge แทน SNS | Richer event routing, schema flexibility, built-in archive |
| Lambda Layer | แยก dependencies (boto3, gemini SDK) จากโค้ด; ลดขนาด zip |
| Optimistic Locking | ConditionExpression ป้องกัน 2 เจ้าหน้าที่ verify พร้อมกัน |

---

## 11. Verification Checklist

- [ ] `deploy.sh` สำเร็จโดยไม่มี error
- [ ] POST /v1/reports → ได้ 202 + report_id
- [ ] GET /v1/reports?status=PENDING_REVIEW → เห็นรายงานที่ส่งเข้ามา
- [ ] GET /v1/reports/{id} → เห็นรายละเอียด + trust_score จาก Gemini
- [ ] PATCH /v1/reports/{id} verify → สถานะเปลี่ยนเป็น VERIFIED
- [ ] EventBridge CloudWatch Logs → เห็น ReportVerifiedEvent
- [ ] GET /v1/health → status "healthy"
- [ ] DELETE /v1/reports/{id} → soft delete สำเร็จ
- [ ] GET /v1/reports/stats → เห็นสถิติ
- [ ] Website → Landing page แสดงผลถูกต้อง
- [ ] Dashboard → API Tester ทำงานได้ (ตั้ง API URL + API Key → ส่ง request)
- [ ] Unit tests pass: `pytest tests/unit/ -v`
- [ ] Integration tests pass: `pytest tests/integration/ -v`
