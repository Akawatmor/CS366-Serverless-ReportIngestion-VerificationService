# CS366 — Report Ingestion & Verification Service

> Serverless Microservice สำหรับรับรายงานภัยพิบัติ (Disaster Reports) ประมวลผลด้วย AI แล้วให้เจ้าหน้าที่ Verify ก่อนสร้าง Incident

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Terraform](https://img.shields.io/badge/Terraform-1.5+-purple.svg)](https://www.terraform.io/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![Google Gemini](https://img.shields.io/badge/AI-Gemini-green.svg)](https://ai.google.dev/)

## 📋 Overview

ระบบนี้ทำหน้าที่เป็น **Central Gateway** สำหรับรับข้อมูลเหตุภัยพิบัติจากแหล่งต่างๆ (Social Media, Mobile Apps, IoT Sensors) แล้วทำการ:

1. **Ingest** — รับ raw report ผ่าน REST API → คิวด้วย SQS
2. **Analyze** — ใช้ Google Gemini AI วิเคราะห์ trust score
3. **Deduplicate** — ตรวจจับรายงานซ้ำด้วย Haversine distance + time window
4. **Verify** — เจ้าหน้าที่กด approve/reject ผ่าน API
5. **Publish** — ส่ง Event ผ่าน EventBridge ไปสร้าง Incident

### Service Owner
- **Akawat Moradsatian** (6609681231)

### Pain Points ที่แก้ไข
- ⚡ **Information Overload** — รองรับ High Throughput ในสภาวะวิกฤต
- 🔄 **Noise & Redundancy** — กรอง SPAM และ Duplicate ออกอัตโนมัติ
- 📝 **Unstructured Data** — Normalize ข้อมูลจากแหล่งต่างๆ ให้เป็นรูปแบบเดียว

## 🏗️ Architecture

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

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Runtime | Python 3.12 |
| Compute | AWS Lambda (4 functions) |
| API | API Gateway (REST) |
| Database | DynamoDB (3 tables: Reports, AuditLogs, Stats) |
| Queue | SQS + Dead Letter Queue |
| Events | EventBridge (custom bus) |
| AI | Google Gemini (gemini-2.0-flash) |
| IaC | Terraform |
| Auth | API Key (Usage Plan) |
| Frontend | S3 Static Website (Landing + Dashboard) |

## Prerequisites

- AWS Learner Lab — active session with credentials
- [Terraform](https://www.terraform.io/downloads) ≥ 1.5
- Python 3.12+
- Google Gemini API Key ([get one](https://aistudio.google.com/apikey))

## Quick Start

```bash
# 1. Clone repository
git clone <repo-url>
cd CS366-Serverless-RequestVerifyService

# 2. ตั้งค่า AWS Credentials (จาก Learner Lab)
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...

# 3. Deploy ทั้งหมดด้วยคำสั่งเดียว
chmod +x scripts/deploy.sh
./scripts/deploy.sh
#   → ระบบจะถาม Gemini API Key ระหว่าง terraform apply

# 4. ดู API URL + API Key
cd terraform
terraform output api_url
terraform output -raw api_key
```

## 📚 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/reports` | Submit raw report (202 Accepted) |
| `GET` | `/v1/reports` | List reports with status filter |
| `GET` | `/v1/reports/{id}` | Get report detail + AI analysis |
| `PATCH` | `/v1/reports/{id}` | Verify / Reject / Request more info |
| `DELETE` | `/v1/reports/{id}` | Soft delete a report |
| `GET` | `/v1/reports/stats` | Aggregated statistics |
| `GET` | `/v1/health` | System health check |

### Report Status Lifecycle

```
RECEIVED → PENDING_REVIEW → VERIFIED
    │              ↓↗
    │         NEEDS_MORE_INFO
    │              ↓
    ├──→ SPAM     REJECTED
    └──→ DUPLICATE

ทุกสถานะ → DELETED (Soft delete)
```

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
  "report_id": "r-550e8400-e29b-...",
  "message": "Report accepted and queued for processing."
}
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run unit + integration tests (no AWS needed)
pytest tests/unit/ tests/integration/ -v

# Run with coverage
pytest tests/unit/ tests/integration/ --cov=src --cov-report=term-missing

# Run E2E tests (requires deployed API)
API_URL=https://xxx.execute-api.../dev API_KEY=xxx pytest tests/e2e/ -v
```

### Test Coverage
- **Unit Tests**: Validators, Gemini Service, Dedup Service, API Handler
- **Integration Tests**: DynamoDB CRUD, SQS flow, EventBridge publish
- **E2E Tests**: Full API contract validation, Ingest flow, Verify flow

## 📁 Project Structure

```
src/
├── config.py                 # Environment config singleton
├── models/
│   ├── enums.py              # ValidationStatus, SourcePlatform, IncidentCategory
│   └── report.py             # Report, GeoLocation, AuditLog dataclasses
├── utils/
│   ├── logger.py             # Structured JSON logging
│   ├── response.py           # API Gateway response builders
│   └── validators.py         # Request validation + state machine
├── services/
│   ├── gemini_service.py     # Google Gemini AI trust scoring
│   ├── dedup_service.py      # Deduplication (Haversine + time window)
│   ├── audit_service.py      # Audit log writer
│   └── event_publisher.py    # EventBridge publisher
└── handlers/
    ├── ingest_handler.py     # POST /reports → SQS
    ├── ingestion_worker.py   # SQS → Process → DynamoDB
    ├── api_handler.py        # GET/PATCH/DELETE /reports
    └── health_handler.py     # GET /health

terraform/                    # All infrastructure-as-code (12 .tf files)
frontend/
├── index.html                # Landing page (/)
└── dashboard/
    └── index.html            # API Testing Dashboard (/dashboard/)
scripts/                      # deploy.sh, destroy.sh, seed_data.py
tests/
├── unit/                     # Pure logic tests (mocked)
├── integration/              # AWS-mocked tests (moto)
└── e2e/                      # Live API tests (httpx)
docs/                         # Service Proposal & Implementation docs
plan/                         # Original implementation plan
```

## 🗑️ Tear Down

```bash
./scripts/destroy.sh
```

## 🔄 EventBridge Events

| Event | Description | Consumer |
|-------|-------------|----------|
| `ReportVerifiedEvent` | เมื่อรายงานได้รับการยืนยัน | Incident Tracking Service |
| `ReportStatusChangedEvent` | เมื่อสถานะเปลี่ยน | Dashboard, Notification Services |

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [📋 Implementation Plan](docs/implement/implementation-plan.md) | **แผนการ Implement ตาม Phase พร้อมสรุปสิ่งที่ทำเสร็จ/ยังขาด** |
| [📄 Service Proposal (PDF)](docs/Service%20Proposal%206609681231%20WordVer2.pdf) | เอกสาร Proposal ฉบับเต็ม |
| [📝 Service Proposal (Text)](docs/others/reportingestion_proposal.txt) | เอกสาร Proposal รูปแบบ Text |
| [🔧 Original Plan](plan/implementation-plan.md) | แผนการ Implement ต้นฉบับ |
| [🔗 Integration Guide](docs/implement/integration-guide.md) | คู่มือ Integration กับ Services อื่น |

## 📊 Implementation Status

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1: Foundation & Infrastructure | ✅ Complete | 100% |
| Phase 2: Core Business Logic | ✅ Complete | ~95% |
| Phase 3: Integration & Enhancement | ✅ Complete | ~90% |

> ดูรายละเอียดเพิ่มเติมได้ที่ [Implementation Plan](docs/implement/implementation-plan.md)

## 🤝 Related Services

| Service | Interaction |
|---------|-------------|
| **Incident Tracking Service** | รับ ReportVerifiedEvent เพื่อสร้าง Incident |
| **Rescue Request Service** | รับ Event เฉพาะ severity=CRITICAL |
| **Operation Update Service** | เรียก GET /stats สำหรับ Dashboard |
| **Disaster Monitoring Service** | ส่ง POST /reports จาก IoT Sensors |

---

**Service Owner**: Akawat Moradsatian (6609681231)  
**Course**: CS366 — Serverless Computing  
**Version**: 1.0.0