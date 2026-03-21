# Implementation Plan — Report Ingestion & Verification Service

> **เอกสารนี้สรุปการ Implement ตาม Phase และเปรียบเทียบกับ Service Proposal**
>
> อัปเดตล่าสุด: 2026-03-21

---

## สารบัญ (Table of Contents)

1. [ภาพรวมโปรเจค](#1-ภาพรวมโปรเจค)
2. [Phase 1: Foundation & Infrastructure](#phase-1-foundation--infrastructure)
3. [Phase 2: Core Business Logic](#phase-2-core-business-logic)
4. [Phase 3: Integration & Enhancement](#phase-3-integration--enhancement)
5. [สรุปสิ่งที่ทำเสร็จแล้วและสิ่งที่ยังขาด](#4-สรุปสิ่งที่ทำเสร็จแล้วและสิ่งที่ยังขาด)
6. [เอกสารที่เกี่ยวข้อง](#5-เอกสารที่เกี่ยวข้อง)

---

## 1. ภาพรวมโปรเจค

**Report Ingestion & Verification Service** เป็น Serverless Microservice สำหรับรับรายงานภัยพิบัติจากแหล่งต่างๆ ประมวลผลด้วย AI และให้เจ้าหน้าที่ Verify ก่อนสร้าง Incident

### Tech Stack ที่ใช้
| Component | Technology |
|-----------|-----------|
| Runtime | Python 3.12 |
| Compute | AWS Lambda (4 functions) |
| API | API Gateway (REST) |
| Database | DynamoDB (3 tables) |
| Queue | SQS + Dead Letter Queue |
| Events | EventBridge (custom bus) |
| AI | Google Gemini (gemini-2.0-flash) |
| IaC | Terraform |
| Auth | API Key (Usage Plan) |

---

## Phase 1: Foundation & Infrastructure

### 🎯 เป้าหมาย
สร้างโครงสร้างพื้นฐานบน AWS และ Project Structure ที่พร้อมสำหรับการพัฒนา

### ✅ Tasks ที่ทำเสร็จแล้ว

| Task | สถานะ | รายละเอียด |
|------|-------|------------|
| **1.1 Project Structure Setup** | ✅ Done | สร้างโครงสร้างโปรเจค src/, tests/, terraform/, scripts/, docs/ |
| **1.2 Terraform Infrastructure** | ✅ Done | เขียน IaC ครบ 12 ไฟล์ (main.tf, variables.tf, outputs.tf, dynamodb.tf, sqs.tf, eventbridge.tf, iam.tf, lambda.tf, api_gateway.tf, s3.tf, s3_media.tf, cloudfront.tf) |
| **1.3 DynamoDB Tables** | ✅ Done | สร้าง 3 tables: Reports, AuditLogs, Stats พร้อม GSI |
| **1.4 SQS Queue** | ✅ Done | สร้าง report-ingestion-queue + Dead Letter Queue (DLQ) |
| **1.5 EventBridge Custom Bus** | ✅ Done | สร้าง disaster-events bus พร้อม Rule |
| **1.6 IAM Roles & Policies** | ✅ Done | Lambda execution roles พร้อม DynamoDB, SQS, EventBridge permissions |
| **1.7 API Gateway Setup** | ✅ Done | REST API พร้อม Usage Plan, API Key, Rate Limiting |
| **1.8 S3 Static Website** | ✅ Done | Landing page และ Dashboard hosting |
| **1.9 Deploy Scripts** | ✅ Done | deploy.sh, destroy.sh สำหรับ one-command deployment |
| **1.10 Python Config Module** | ✅ Done | src/config.py — Environment config singleton |
| **1.11 Logging Utility** | ✅ Done | src/utils/logger.py — Structured JSON logging |
| **1.12 Response Builder** | ✅ Done | src/utils/response.py — API Gateway response helpers |

### ❌ Tasks ที่ยังไม่ได้ทำ

| Task | ความสำคัญ | หมายเหตุ |
|------|----------|----------|
| **1.13 CloudWatch Dashboard** | Medium | ยังไม่มี Dashboard สำหรับ monitoring metrics |
| **1.14 CloudWatch Alarms** | Medium | ยังไม่มี Alarms สำหรับ error rate, latency |

---

## Phase 2: Core Business Logic

### 🎯 เป้าหมาย
Implement ตาม API Contracts และ Business Logic ตาม Proposal

### ✅ Tasks ที่ทำเสร็จแล้ว

#### API Contracts (Synchronous)

| API Contract | สถานะ | Handler | Path |
|--------------|-------|---------|------|
| **#1 Submit Raw Report (Ingest)** | ✅ Done | `ingest_handler.py` | POST /v1/reports |
| **#2 List Pending Reports** | ✅ Done | `api_handler.py` | GET /v1/reports |
| **#3 Verify Report (Decision)** | ✅ Done | `api_handler.py` | PATCH /v1/reports/{id} |
| **#4 Get Report Detail** | ✅ Done | `api_handler.py` | GET /v1/reports/{id} |
| **#5 Get Dashboard Stats** | ✅ Done | `api_handler.py` | GET /v1/reports/stats |
| **#6 Soft Delete / Archive** | ✅ Done | `api_handler.py` | DELETE /v1/reports/{id} |
| **#7 Health Check** | ✅ Done | `health_handler.py` | GET /v1/health |

#### Message Contracts (Asynchronous)

| Message Contract | สถานะ | Publisher | รายละเอียด |
|-----------------|-------|-----------|------------|
| **#1 ReportVerifiedEvent** | ✅ Done | `event_publisher.py` | ส่งไป Incident Tracking Service |
| **#2 ReportStatusChangedEvent** | ✅ Done | `event_publisher.py` | Broadcast เมื่อสถานะเปลี่ยน |

#### Core Services

| Service | สถานะ | รายละเอียด |
|---------|-------|------------|
| **Gemini AI Service** | ✅ Done | `gemini_service.py` — Trust Scoring, Category Suggestion |
| **Deduplication Service** | ✅ Done | `dedup_service.py` — Haversine + Time Window + External ID Check |
| **Audit Service** | ✅ Done | `audit_service.py` — Log all actions to AuditLogs table |
| **Event Publisher** | ✅ Done | `event_publisher.py` — EventBridge integration |

#### Business Logic

| Logic | สถานะ | รายละเอียด |
|-------|-------|------------|
| **Validation Status State Machine** | ✅ Done | RECEIVED → PENDING_REVIEW → VERIFIED/REJECTED/SPAM/DUPLICATE → DELETED |
| **Auto-SPAM Detection** | ✅ Done | trust_score < 30% → SPAM |
| **Auto-DUPLICATE Detection** | ✅ Done | Geo (200m) + Time (15 min) match |
| **Reporter History Analysis** | ✅ Done | GSI gsi_reporter สำหรับ historical context |
| **Optimistic Locking** | ✅ Done | ConditionExpression ใน PATCH |
| **Stats Atomic Counter** | ✅ Done | DynamoDB ADD operation |

#### Data Models & Validators

| Component | สถานะ | File |
|-----------|-------|------|
| **Enums** | ✅ Done | `models/enums.py` — ValidationStatus, SourcePlatform, IncidentCategory |
| **Report Dataclass** | ✅ Done | `models/report.py` — Report, GeoLocation, AuditLog |
| **Request Validators** | ✅ Done | `utils/validators.py` — All API payloads |

### ❌ Tasks ที่ยังไม่ได้ทำ (ตาม Proposal)

| Task | ความสำคัญ | หมายเหตุ (จาก Proposal) |
|------|----------|------------------------|
| **2.1 Media Upload (Pre-signed URL)** | Medium | POST /upload-url — ระบุไว้ใน Proposal แต่ Handler ว่างเปล่า |
| **2.2 Priority Queue** | Low | TRUST_HIGH_PRIORITY=80 ระบุไว้ แต่ยังไม่ได้ใช้จัดลำดับการแสดงผล |
| **2.3 Reverse Geocoding** | Low | ไม่รวม address_text ใน suggested_incident_data |
| **2.4 Reporter Count** | Low | Hardcoded เป็น 1 ยังไม่ได้นับจริง |
| **2.5 Severity Level Calculation** | Low | Hardcoded เป็น 3 ยังไม่ได้คำนวณจาก AI Tags |
| **2.6 Region Filtering** | Low | Parameter region ใน /stats รับไว้แต่ยังไม่ได้ Implement |
| **2.7 trending_keywords / heatmap_data** | Low | ยังเป็น empty array ใน /stats response |
| **2.8 Content Similarity** | Low | ระบุใน Proposal แต่ปัจจุบันใช้แค่ Geo+Time |

---

## Phase 3: Integration & Enhancement

### 🎯 เป้าหมาย
Testing, Frontend, Documentation และการ Integration กับ External Services

### ✅ Tasks ที่ทำเสร็จแล้ว

#### Testing

| Test Type | สถานะ | Files |
|-----------|-------|-------|
| **Unit Tests** | ✅ Done | `test_validators.py`, `test_gemini_service.py`, `test_dedup_service.py`, `test_api_handler.py` |
| **Integration Tests** | ✅ Done | `test_dynamodb_ops.py`, `test_sqs_flow.py`, `test_eventbridge.py` |
| **E2E Tests** | ✅ Done | `test_api_contracts.py`, `test_ingest_flow.py`, `test_verify_flow.py` |
| **Test Config (pytest)** | ✅ Done | `pyproject.toml`, `conftest.py` |

#### Frontend

| Component | สถานะ | File |
|-----------|-------|------|
| **Landing Page** | ✅ Done | `frontend/index.html` — Project info, Architecture overview |
| **API Testing Dashboard** | ✅ Done | `frontend/dashboard/index.html` — Interactive API tester |

#### Documentation

| Document | สถานะ | Location |
|----------|-------|----------|
| **README.md** | ✅ Done | Quick start, API endpoints, Testing guide |
| **Implementation Plan (Original)** | ✅ Done | `plan/implementation-plan.md` |
| **Integration Guide** | ✅ Done | `docs/implement/integration-guide.md` |

### ❌ Tasks ที่ยังไม่ได้ทำ

| Task | ความสำคัญ | หมายเหตุ |
|------|----------|----------|
| **3.1 RBAC (Role-Based Access Control)** | Medium | ระบุใน Proposal ว่ายังไม่ได้ Implement — ทุก API Key เข้าถึงได้เท่ากัน |
| **3.2 Custom Domain + CNAME** | Low | ปัจจุบันใช้ CloudFront URL ตรง ๆ |
| **3.3 API Versioning Path Prefix** | Low | ระบุ /api/v1 แต่ปัจจุบันใช้ /v1 |
| **3.4 Incident Service Integration (GET)** | Low | เรียก GET /incidents?active=true สำหรับ Dropdown — Optional |
| **3.5 Performance Load Testing** | Medium | ยังไม่ได้ทดสอบ 10,000 req/sec |
| **3.6 Error Retry with Outbox Pattern** | Low | มี comment ใน code แต่ยังไม่ได้ Implement |

---

## 4. สรุปสิ่งที่ทำเสร็จแล้วและสิ่งที่ยังขาด

### ✅ สิ่งที่ Implement แล้วตาม Proposal (ครบถ้วน)

| Category | Completion |
|----------|------------|
| **API Contracts (7 endpoints)** | 100% ✅ |
| **Message Contracts (2 events)** | 100% ✅ |
| **Core Services (AI, Dedup, Audit, Events)** | 100% ✅ |
| **State Machine (7 statuses)** | 100% ✅ |
| **DynamoDB Tables (3 tables + GSI)** | 100% ✅ |
| **Infrastructure (Lambda, SQS, EventBridge, API GW)** | 100% ✅ |
| **Testing (Unit, Integration, E2E)** | 100% ✅ |
| **Frontend (Landing + Dashboard)** | 100% ✅ |
| **Deploy Scripts** | 100% ✅ |

### ❌ สิ่งที่ยังไม่ได้ทำ / Future Enhancements

| Item | Priority | Notes |
|------|----------|-------|
| Media Upload (Pre-signed URL) | Medium | POST /upload-url handler ว่าง |
| RBAC | Medium | ทุก API Key เท่าเทียมกัน |
| CloudWatch Dashboard + Alarms | Medium | Monitoring/Alerting |
| Load Testing | Medium | 10K req/sec benchmark |
| Priority Queue | Low | High trust_score ยังไม่ได้จัดลำดับ |
| trending_keywords / heatmap_data | Low | Stats response ยังเป็น empty array |
| Reverse Geocoding | Low | ไม่มี address_text |
| Content Similarity | Low | ใช้แค่ Geo+Time dedup |
| Severity Dynamic Calc | Low | Hardcoded = 3 |
| Region Filtering | Low | Parameter รับแต่ยังไม่ทำงาน |
| Custom Domain | Low | ใช้ CloudFront URL |
| Outbox Pattern Retry | Low | EventBridge retry logic |

---

## 5. เอกสารที่เกี่ยวข้อง

| Document | Path | Description |
|----------|------|-------------|
| **Service Proposal (Word)** | [`docs/Service Proposal 6609681231 WordVer2.pdf`](../Service%20Proposal%206609681231%20WordVer2.pdf) | เอกสาร Proposal ฉบับเต็ม (PDF) |
| **Service Proposal (Text)** | [`docs/others/reportingestion_proposal.txt`](../others/reportingestion_proposal.txt) | เอกสาร Proposal (Text format) |
| **Original Implementation Plan** | [`plan/implementation-plan.md`](../../plan/implementation-plan.md) | แผนการ Implement ต้นฉบับ |
| **Integration Guide** | [`docs/implement/integration-guide.md`](./integration-guide.md) | คู่มือ Integration กับ Services อื่น |
| **README** | [`README.md`](../../README.md) | Quick Start และ API Usage |

---

## Appendix: API Contract Quick Reference

### Synchronous APIs

```
POST   /v1/reports              # Submit raw report (202 Accepted)
GET    /v1/reports              # List reports with status filter
GET    /v1/reports/{id}         # Get report detail + AI analysis
PATCH  /v1/reports/{id}         # Verify / Reject / Request more info
DELETE /v1/reports/{id}         # Soft delete a report
GET    /v1/reports/stats        # Aggregated statistics
GET    /v1/health               # System health check
```

### Asynchronous Events (EventBridge)

```
ReportVerifiedEvent      → Incident Tracking Service
ReportStatusChangedEvent → Dashboard, Notification Services
```

---

*Generated: 2026-03-21 | Service Version: 1.0.0*
