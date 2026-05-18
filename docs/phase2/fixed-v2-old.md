# Report Ingestion & Verification Service
## CS366 Service Proposal — Version 2 (Fixed)

**Written by Akawat Moradsatian (6609681231)**  
**Course**: CS366 — Serverless Computing  
**Last Updated**: 22 April 2026

> เอกสารนี้คือ Proposal ฉบับแก้ไข (v2) ที่อัปเดตให้ตรงกับ Implementation จริง  
> การแก้ไขทั้งหมดมาจากการตรวจสอบโค้ดและ Terraform config  
> ดู `fixed-doc.md` สำหรับรายการ Issue ที่แก้ไข

---

## สารบัญ

1. [ภาพรวมของบริการ (Service Overview)](#1-ภาพรวมของบริการ-service-overview)
2. [Synchronous Function Contract](#2-synchronous-function-contract)
3. [Asynchronous Function Contract](#3-asynchronous-function-contract)
4. [Service Data](#4-service-data)
5. [Service Architecture](#5-service-architecture)
6. [Service Interaction](#6-service-interaction)
7. [Dependency Mapping](#7-dependency-mapping)

---

## 1. ภาพรวมของบริการ (Service Overview)

### 1.1 Service Owner

- **Akawat Moradsatian** (6609681231)

### 1.2 Service Purpose

บริการนี้ทำหน้าที่เป็น **Central Gateway** หลักในการรับข้อมูลเหตุภัยพิบัติจากแหล่งข้อมูลภายนอกที่หลากหลาย ไม่ว่าจะเป็น Social Media Scrapers, Mobile Apps หรือ Third-party APIs ผ่านมาตรฐาน API โดยมีกระบวนการจัดการข้อมูลอย่างเป็นระบบ ประกอบด้วย:

1. **Ingest** — รับ raw report ผ่าน REST API → คิวด้วย SQS
2. **Analyze** — ใช้ Google Gemini AI วิเคราะห์ **Composite Trust Score** (ดูรายละเอียดใน [§1.6](#16-autonomy--decision-logic))
3. **Deduplicate** — ตรวจจับรายงานซ้ำด้วย Haversine distance + Time Window
4. **Verify** — เจ้าหน้าที่กด Approve/Reject ผ่าน API
5. **Publish** — ส่ง Event ผ่าน EventBridge ไปสร้าง Incident

**Gemini AI Models ที่ใช้จริง** (ตาม `src/config.py` และ Terraform):

| ลำดับ | Model | บทบาท |
|---|---|---|
| 1 (Default) | `gemini-2.5-flash-lite` | Primary model |
| 2 (Fallback 1) | `gemini-2.0-flash` | Fallback เมื่อ default ติด Rate Limit |
| 3 (Fallback 2) | `gemini-3.1-flash-lite` | Last resort fallback |

### 1.3 Pain Points ที่แก้ไข

- **High Throughput** — รองรับปริมาณข้อมูลมหาศาลในสภาวะวิกฤต
- **Noise & Redundancy** — กรอง SPAM และ Duplicate ออกอัตโนมัติ
- **Unstructured Data** — Normalize ข้อมูลจากแหล่งต่างๆ ให้เป็นรูปแบบเดียว

### 1.4 Target User

- เจ้าหน้าที่ปฏิบัติการผู้รับผิดชอบด้านการตรวจสอบและยืนยันความถูกต้องของข้อมูล (Trust Officer)
- ระบบปฏิบัติการอัตโนมัติที่มีหน้าที่นำส่งข้อมูลเข้าสู่ API

### 1.5 Service Boundary

**In-scope:**
- RESTful API สำหรับรับ Raw JSON Payload
- Composite Trust Scoring ด้วย Gemini AI + Python rules
- Deduplication (External ID + Haversine + Time Window)
- Web Dashboard สำหรับเจ้าหน้าที่ Verify
- Asynchronous Event Publishing ผ่าน EventBridge
- Reverse Geocoding (ผ่าน `geocoding_service.py` — ขึ้นอยู่กับ `REVERSE_GEOCODING_ENABLED` config)

**Out-of-scope:**
- Bot/Scraper ดึงข้อมูลจากเว็บภายนอก
- ติดตาม Lifecycle ของ Incident (→ Incident Service)
- บริหารจัดการยานพาหนะกู้ภัย (→ Dispatch Service)

### 1.6 Autonomy / Decision Logic

ระบบตัดสินใจอัตโนมัติตาม **Composite Trust Score** ที่คำนวณจาก 4 ส่วน:

| Component | แหล่งคำนวณ | คะแนนสูงสุด |
|---|---|---|
| `content_score` | Google Gemini AI (ประเมินคุณภาพเนื้อหา) | 0–30 |
| `source_score` | Source platform rule (จาก config) | 0–20 |
| `history_score` | Reporter history (จาก DynamoDB) | 0–15 |
| `image_score` | Gemini Vision (เฉพาะกรณีมีรูปภาพ) | −10 ถึง +20 |

**เกณฑ์การตัดสินใจ:**

| เงื่อนไข | ผลลัพธ์ |
|---|---|
| Trust Score < 30% | → สถานะ **SPAM** (Auto-reject) |
| Trust Score ≥ 30% + ตรงเงื่อนไข Geo/Time | → สถานะ **DUPLICATE** |
| Trust Score ≥ 30% + ไม่ซ้ำ | → สถานะ **PENDING_REVIEW** |
| Trust Score ≥ 80% | → ถือว่า High Priority (ใช้ใน Future Priority Queue) |

ระบบยังคงต้องการการอนุมัติจากเจ้าหน้าที่ (Human-in-the-loop) ในขั้นตอน Verification สุดท้ายก่อนสร้าง Incident

### 1.7 Owned Data (รายการ Field สำคัญ)

ดูรายละเอียดเต็มใน [§4 Service Data](#4-service-data)

### 1.8 Linked Data (Reference Only)

- `incident_id` (Foreign Key — Reference Only): เก็บเฉพาะ ID อ้างอิงไปยัง Incident Service ไม่อนุญาตให้แก้ไขข้ามไปยัง Incident Service

### 1.9 Non-Functional Requirements

- **High Scalability** (สำคัญสูงสุด): รองรับ Write-Heavy Workload ระดับ 10,000 req/sec ผ่าน Serverless Queue
- **Data Integrity**: Zero Data Loss — ข้อมูลทุกชิ้นบันทึกลง DynamoDB แม้ส่วนอื่นขัดข้อง
- **Asynchronous Processing**: AI Analysis และ Dedup ทำงานใน Background เพื่อลด Latency

### 1.10 ลิงค์ที่เกี่ยวข้อง

- **GitHub**: https://github.com/Akawatmor/CS366-Serverless-ReportIngestion-VerificationService
- **API Endpoint**: `ingestverify-366-dev.akawatmor.com` (อาจมีการเปลี่ยนแปลง)

---

## 2. Synchronous Function Contract

**Base URL**: `ingestverify-366-dev.akawatmor.com/api/v1/`

> - Rate Limit: 50 req/s (Burst: 100 req/s)
> - Auth: `X-Api-Key` header สำหรับทุก Endpoint ยกเว้น `/health`
> - Response format: JSON

### สรุป Endpoints ทั้งหมด

| Method | Path | Description |
|---|---|---|
| `POST` | `/reports` | Submit raw report (202 Accepted) |
| `GET` | `/reports` | List reports with status/priority filter |
| `GET` | `/reports/stats` | Dashboard statistics |
| `GET` | `/reports/{id}` | Report detail + AI analysis |
| `PATCH` | `/reports/{id}` | Verify / Reject report |
| `DELETE` | `/reports/{id}` | Soft delete a report |
| `GET` | `/health` | Health check (No auth required) |
| `GET` | `/changelog.xml` | RSS feed สำหรับ API contract changes |
| `GET` | `/deprecation-info` | รายการ Deprecated endpoints |
| `GET` | `/reports/audit` | Audit log history |
| `GET` | `/reports/events` | Event history |
| `GET` | `/trace/{trace_id}` | Trace lookup via X-Trace-Id |
| `POST` | `/reports/upload-url` | Pre-signed S3 URL สำหรับ media upload |
| `POST` | `/report-incident` | Incident creation result callback (จาก Incident Tracking Service) |

---

### API Contract #1: Submit Raw Report (Ingest)

**Method**: `POST` | **Path**: `/reports` | **Type**: Synchronous (Fire and Forget)

**คำอธิบาย**: Lambda (`ingest_handler`) ตรวจสอบ Payload แล้วส่งเข้า SQS ตอบกลับทันที

**Request Body**:
```json
{
  "reporter_source": "TWITTER",
  "reporter_id": "@user123",
  "raw_content": "Fire reported near Central World! #BKKFire",
  "media_urls": ["https://img.host/fire123.jpg"],
  "geo_location": { "lat": 13.746123, "lon": 100.539123 },
  "timestamp": "2026-02-18T14:30:00Z"
}
```

**Validation**:
- `reporter_source` ∈ `[TWITTER, FACEBOOK, LINE, OFFICIAL_APP, IOT_SENSOR]`
- `raw_content` หรือ `media_urls` ต้องมีอย่างน้อย 1 อย่าง
- Payload ≤ 256KB

**Response 202 Accepted**:
```json
{
  "status": "QUEUED",
  "report_id": "r-550e8400-e29b-...",
  "message": "Report accepted and queued for processing."
}
```

**Errors**: 400, 401, 429, 500

---

### API Contract #2: List Reports

**Method**: `GET` | **Path**: `/reports`

**Query Parameters**:

| Parameter | Required | Default | Description |
|---|---|---|---|
| `status` | No | `PENDING_REVIEW` | Filter by ValidationStatus |
| `priority` | No | `all` | `all` \| `high` \| `normal` — กรองตาม Trust Score |
| `min_trust_score` | No | — | กรอง Trust Score ขั้นต่ำ |
| `limit` | No | `5` | จำนวนผลลัพธ์ต่อหน้า (Max: 100) |
| `last_evaluated_key` | No | — | Cursor-based Pagination |

**Response 200 OK**:
```json
{
  "data": [
    {
      "report_id": "r-550e8400-e29b-41d4-a716-446655440000",
      "content": "Fire near Central...",
      "trust_score": 85,
      "suggested_category": "FIRE",
      "time_ago": "5 mins"
    }
  ],
  "total_count": 1,
  "last_evaluated_key": "..."
}
```

---

### API Contract #3: Verify Report (Decision)

**Method**: `PATCH` | **Path**: `/reports/{report_id}`

**Request Body**:
```json
{
  "validation_status": "VERIFIED",
  "reviewer_id": "officer_007",
  "notes": "Confirmed via CCTV feed."
}
```

**Allowed Status Transitions**: `PENDING_REVIEW` → `VERIFIED` | `REJECTED` | `NEEDS_MORE_INFO`

**Response 200 OK**:
```json
{
  "report_id": "r-550e8400-e29b-41d4-a716-446655440000",
  "validation_status": "VERIFIED",
  "action_taken": "TRIGGER_NEW_INCIDENT",
  "updated_at": "2026-03-03T15:00:00Z"
}
```

> เมื่อตอบกลับ 200 แล้ว ระบบจะ Publish `ReportVerifiedEvent` ไปยัง EventBridge

**Errors**: 400, 404, 409 (Conflict — ถูกจัดการไปแล้วโดยผู้อื่น)

---

### API Contract #4: Get Report Detail

**Method**: `GET` | **Path**: `/reports/{report_id}`

**Response 200 OK**:
```json
{
  "report_id": "r-550e8400-e29b-41d4-a716-446655440000",
  "reporter_info": {
    "source": "TWITTER",
    "reporter_id": "@somchai_123",
    "source_external_id": "tweet-123456789"
  },
  "content": {
    "text": "ไฟไหม้ร้านทอง เยาวราช ตอนนี้เลย!",
    "images": ["https://s3.aws.../img1_hd.jpg"],
    "geo_location": { "lat": 13.746123, "lon": 100.539123 },
    "event_timestamp": "2026-03-03T10:00:00Z"
  },
  "analysis": {
    "trust_score": 88,
    "ai_reasoning": "Detected fire and smoke in image. Multiple users reporting same location.",
    "ai_analysis_tags": ["Fire", "Smoke", "High-Urgency"],
    "ai_analysis_failed": false,
    "suggested_category": "FIRE",
    "potential_duplicates": ["r-999", "r-888"]
  },
  "verification": {
    "status": "PENDING_REVIEW",
    "verified_by": "officer_007",
    "verification_notes": "Confirmed via CCTV feed.",
    "linked_incident_id": "inc-1234"
  },
  "created_at": "2026-03-03T10:05:00Z",
  "updated_at": "2026-03-03T10:10:00Z"
}
```

---

### API Contract #5: Get Dashboard Stats

**Method**: `GET` | **Path**: `/reports/stats`

**Query Parameters**:

| Parameter | Required | Values | หมายเหตุ |
|---|---|---|---|
| `timeframe` | No | `today` \| `last_24h` \| `last_7d` | — |
| `region` | No | `bkk` \| `central` \| `north` \| `northeast` \| `south` | ✅ Implemented แล้ว (ใช้ lat/lon boundaries) |

**Response 200 OK**:
```json
{
  "timestamp": "2026-03-03T12:00:00Z",
  "summary": {
    "total_received_today": 1500,
    "pending_review": 50,
    "verified_incidents": 120,
    "spam_rejected": 1330
  },
  "trending_keywords": [],
  "heatmap_data": []
}
```

> `heatmap_data` ยังเป็น Planned Feature (Future Enhancement)

---

### API Contract #6: Soft Delete / Archive

**Method**: `DELETE` | **Path**: `/reports/{report_id}`

**Request Body**:
```json
{
  "reason": "Contains sensitive PII",
  "deleted_by": "admin_001"
}
```

**Response 200 OK**:
```json
{
  "report_id": "r-550e8400-e29b-41d4-a716-446655440000",
  "status": "DELETED",
  "message": "Report has been archived and removed from public view."
}
```

> หมายเหตุ: ยังไม่ได้ Implement RBAC — ทุก Client ที่มี API Key ที่ถูกต้องสามารถลบได้

---

### API Contract #7: Health Check

**Method**: `GET` | **Path**: `/health` | **Auth**: ไม่ต้องใช้ API Key

**Response 200 OK (healthy)**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-03T14:30:00Z",
  "duration_ms": 123,
  "version": "1.0.0",
  "components": {
    "dynamodb": {
      "status": "healthy",
      "table": "report-verify-reports",
      "table_status": "ACTIVE"
    },
    "sqs": {
      "status": "healthy",
      "queue_url": "https://sqs.aws...",
      "approximate_messages": 5
    },
    "gemini": { "status": "healthy" },
    "eventbridge": { "status": "healthy" }
  }
}
```

**Status Logic**:
- `unhealthy` (503): DynamoDB หรือ SQS ขัดข้อง
- `degraded` (200): Gemini หรือ EventBridge ขัดข้อง แต่ส่วนหลักยังทำงานได้
- `healthy` (200): ทุกส่วนพร้อมใช้งาน

---

### API Contract #8: Changelog RSS Feed

**Method**: `GET` | **Path**: `/changelog.xml` | **Auth**: ไม่ต้องใช้ API Key

**คำอธิบาย**: RSS Feed รูปแบบ XML สำหรับ API Contract / Release changes ให้ Consumer Subscribe และรับแจ้งเตือนอัตโนมัติเมื่อ API เปลี่ยนแปลง

**Response**: `Content-Type: application/rss+xml`

---

### API Contract #9: Deprecation Info

**Method**: `GET` | **Path**: `/deprecation-info`

**คำอธิบาย**: แสดงรายการ Endpoint ที่ถูก Deprecated หรือมีกำหนด Sunset Date เพื่อให้ Consumer วางแผน Migration

---

### API Contract #10: Incident Creation Result Callback

**Method**: `POST` | **Path**: `/report-incident` | **Type**: Synchronous (Callback)

**คำอธิบาย**: รับผลการสร้าง Incident จาก **Incident Tracking Service** หลังจากที่ Service นี้ publish `ReportVerifiedEvent` ออกไป

- หาก `status = CREATED`: ระบบจะ auto-update `linked_incident_id` ลงใน Report ทันที พร้อมบันทึก Audit Log พร้อม Incident metadata ทั้งหมด  
- หาก `status = FAILED`: ระบบบันทึก Audit Log เพื่อให้ติดตามความผิดพลาดได้

> **หมายเหตุ**: รองรับทั้ง `original_report_ref_id` (field ของ Service นี้) และ `source_report_id` (field ของ Incident Tracking Service) เพื่ออ้างอิง Report — ใช้ `original_report_ref_id` เป็นหลัก หากไม่มีจึงใช้ `source_report_id`

**Request Body (CREATED)**:
```json
{
  "status": "CREATED",
  "incident_id": "inc-0001-2026",
  "original_report_ref_id": "r-550e8400-e29b-41d4-a716-446655440000",
  "incident_type": "FIRE",
  "incident_description": "Large fire at Central World, multiple units dispatched.",
  "exact_location": "13.7461,100.5391",
  "exact_location_description": "ห้างเซ็นทรัลเวิลด์ ชั้น 5",
  "impact_level": "HIGH",
  "priority": "1"
}
```

> `source_report_id` รองรับแทน `original_report_ref_id` ได้ หากฝั่งเพื่อนส่งมาในชื่อนั้น

**Request Body (FAILED)**:
```json
{
  "status": "FAILED",
  "original_report_ref_id": "r-550e8400-e29b-41d4-a716-446655440000",
  "error_code": "DUPLICATE_INCIDENT",
  "error_message": "An active incident already exists at this location."
}
```

**Field Definition**:

| Field | Type | Required | Description |
|---|---|---|---|
| `status` | String | YES | `CREATED` หรือ `FAILED` |
| `incident_id` | String | YES (CREATED เท่านั้น) | ID ของ Incident ที่สร้างสำเร็จ |
| `original_report_ref_id` | String | YES (ถ้าไม่มี `source_report_id`) | Report ID ของ Service นี้ (preferred) |
| `source_report_id` | String | YES (ถ้าไม่มี `original_report_ref_id`) | Report ID ที่ Incident Service เรียกว่า source — ใช้เป็น Fallback |
| `incident_type` | String | No | ประเภทเหตุการณ์ เช่น `FIRE`, `FLOOD` |
| `incident_description` | String | No | รายละเอียดเหตุการณ์ |
| `exact_location` | String | No | พิกัด `lat,lon` |
| `exact_location_description` | String | No | คำอธิบายสถานที่เป็นภาษาไทย |
| `impact_level` | String | No | `LOW` \| `MEDIUM` \| `HIGH` \| `CRITICAL` |
| `priority` | String/Int | No | ระดับ Priority ของ Incident |
| `error_code` | String | No | รหัสข้อผิดพลาด (กรณี FAILED) |
| `error_message` | String | No | รายละเอียดข้อผิดพลาด (กรณี FAILED) |

**Response 200 OK (CREATED)**:
```json
{
  "report_id": "r-550e8400-e29b-41d4-a716-446655440000",
  "linked_incident_id": "inc-0001-2026",
  "message": "Report successfully linked to incident."
}
```

**Response 200 OK (FAILED)**:
```json
{
  "report_id": "r-550e8400-e29b-41d4-a716-446655440000",
  "acknowledged": true,
  "message": "Failure notification recorded."
}
```

**Audit Log ที่บันทึก**:

| กรณี | `action_type` | `new_value` |
|---|---|---|
| CREATED | `INCIDENT_LINKED` | `linked_incident_id`, `incident_type`, `incident_description`, `exact_location`, `impact_level`, `priority` |
| FAILED | `INCIDENT_LINK_FAILED` | `error_code`, `error_message` |

**Errors**: 400 (validation error / missing required field), 404 (report not found)

---

## 3. Asynchronous Function Contract

### Message Contract #1: Report Verified Event

| ฟิลด์ | ค่า |
|---|---|
| **Message Name** | `ReportVerifiedEvent` |
| **Interaction Style** | Asynchronous (Publish/Subscribe) |
| **Producer** | Report Ingestion & Verification Service |
| **Consumer** | Incident Tracking Service |
| **Channel** | EventBridge Custom Bus: `report-verify-dev-disaster-event-bus` |
| **Detail-Type** | `ReportVerifiedEvent` |
| **Source** | `service.report-verify` |

**Message Body**:
```json
{
  "schemaVersion": "1.0",
  "report_ref_id": "r-550e8400-e29b-41d4-a716-446655440000",
  "suggested_incident_data": {
    "type": "FIRE",
    "description": "Fire reported at Central World, smoke visible from 5km away.",
    "severity_level": 3,
    "location": {
      "lat": 13.746,
      "lon": 100.539,
      "address_text": "ถนนราชดำริ กรุงเทพ"
    },
    "reporter_count": 1
  },
  "verified_by": "officer_007",
  "verification_notes": "Confirmed via traffic camera."
}
```

> - `severity_level`: ปัจจุบัน Hardcoded เป็น `3` (HIGH) — ยังไม่คำนวณแบบ Dynamic
> - `reporter_count`: ปัจจุบัน Hardcoded เป็น `1` — ยังไม่นับจากผู้แจ้งจริง
> - `address_text`: คำนวณจาก Reverse Geocoding Service — ขึ้นอยู่กับ `REVERSE_GEOCODING_ENABLED` config

**Field Definition**:

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| `schemaVersion` | String | YES | เวอร์ชันของ Schema | ปัจจุบัน: `"1.0"` |
| `report_ref_id` | UUID | YES | ID ของ Report ต้นทาง | Valid UUID v4 |
| `suggested_incident_data.type` | String | YES | ประเภทเหตุการณ์ | Enum: `FIRE`, `FLOOD`, `EARTHQUAKE`, `ACCIDENT`, `SOS`, `DAMAGE`, `OTHER` |
| `suggested_incident_data.description` | String | YES | รายละเอียดเหตุการณ์ | Max 500 chars, No HTML |
| `suggested_incident_data.severity_level` | Integer | YES | ระดับความรุนแรง (1–5) | 1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL, 5=CATASTROPHIC |
| `suggested_incident_data.location.lat` | Float | YES | ละติจูด | −90 ถึง 90 |
| `suggested_incident_data.location.lon` | Float | YES | ลองจิจูด | −180 ถึง 180 |
| `verified_by` | String | YES | ID ของเจ้าหน้าที่ | Non-empty string |

---

### Message Contract #2: Report Status Change Event

| ฟิลด์ | ค่า |
|---|---|
| **Message Name** | `ReportStatusChangedEvent` |
| **Interaction Style** | Asynchronous (Broadcast) |
| **Producer** | Report Ingestion & Verification Service |
| **Consumer** | Dashboard Service, Notification Service, Property Damage Service |
| **Channel** | EventBridge: `report-verify-dev-disaster-event-bus` |
| **Detail-Type** | `ReportStatusChangedEvent` |

**Message Body**:
```json
{
  "schemaVersion": "1.0",
  "report_id": "r-1234-5678-9012",
  "old_status": "PENDING_REVIEW",
  "new_status": "SPAM",
  "reason": "Auto-rejected by AI (Trust Score < 30%)",
  "changed_by": "SYSTEM_AI",
  "timestamp": "2026-03-03T11:15:00Z"
}
```

**Field Definition**:

| Field | Type | Required | Validation |
|---|---|---|---|
| `schemaVersion` | String | YES | ปัจจุบัน: `"1.0"` |
| `report_id` | UUID | YES | Valid UUID |
| `old_status` | String | YES | Enum: RECEIVED, PENDING_REVIEW, VERIFIED, SPAM, DUPLICATE, REJECTED, DELETED |
| `new_status` | String | YES | Enum: same as above |
| `reason` | String | NO | Max 255 chars |
| `changed_by` | String | YES | ID เจ้าหน้าที่ หรือ `"SYSTEM_AI"` |
| `timestamp` | String | YES | ISO 8601 format |

**Response**: None (Broadcast Event — ไม่มี callback จาก Consumer)

---

## 4. Service Data

### 4.1 Reports Table (Owned by this service)

| Field Name | Type | Required | Description |
|---|---|---|---|
| `report_id` (PK) | UUID | Yes | รหัสอ้างอิงของรายงาน |
| `source_platform` | Enum | Yes | `TWITTER`, `FACEBOOK`, `LINE`, `OFFICIAL_APP`, `IOT_SENSOR` |
| `source_external_id` | String | No | ID อ้างอิงจากต้นทาง (ใช้ทำ Idempotency) |
| `reporter_id` | String | Yes | User ID หรือเบอร์โทรของผู้แจ้ง |
| `raw_content` | Text | Yes | ข้อความดิบที่ได้รับ |
| `media_urls` | List | No | ลิงก์รูปภาพ/วิดีโอ |
| `geo_location` | JSON | Yes | `{ "lat": float, "lon": float }` |
| `ingested_at` | DateTime | Yes | เวลาที่บันทึกลงระบบ (System Time) |
| `trust_score` | Integer (0–100) | Yes | Composite Trust Score |
| `ai_analysis_tags` | List | No | Keywords ที่ AI ตรวจจับ |
| `ai_reasoning` | String | No | เหตุผลจาก AI สำหรับ Trust Score |
| `ai_analysis_failed` | Boolean | No | Flag ถ้า AI ขัดข้อง |
| `suggested_category` | Enum | No | `FIRE`, `FLOOD`, `EARTHQUAKE`, `ACCIDENT`, `SOS`, `DAMAGE`, `OTHER` |
| `validation_status` | Enum | Yes | `RECEIVED`, `PENDING_REVIEW`, `VERIFIED`, `SPAM`, `REJECTED`, `DUPLICATE`, `DELETED` |
| `verified_by` | String | No | ID ของเจ้าหน้าที่/ระบบที่เปลี่ยนสถานะ |
| `verification_notes` | Text | No | หมายเหตุจากการตรวจสอบ |
| `linked_incident_id` | UUID | No | Reference ID ของ Incident ที่เชื่อมโยง |
| `deleted_by` | String | No | ผู้ทำ Soft Delete |
| `deleted_reason` | String | No | เหตุผลในการลบ |
| `potential_duplicates` | List[UUID] | No | รายการ ID ที่อาจซ้ำซ้อน |
| `updated_at` | DateTime | Yes | เวลาอัปเดตล่าสุด |

> **หมายเหตุ**: `sentiment_score` ไม่ได้รับการ Implement จริง — ไม่มีใน data model

### 4.2 Report Audit Logs Table (Owned by this service)

| Field Name | Type | Required | Description |
|---|---|---|---|
| `log_id` (PK) | UUID | Yes | รหัสประจำรายการ Log |
| `report_ref_id` | UUID | Yes | (FK) อ้างอิงไปยัง Report |
| `actor_id` | String | Yes | ID ของผู้กระทำ หรือ `SYSTEM_AI` |
| `action_type` | Enum | Yes | `STATUS_CHANGE`, `DATA_EDIT`, `SOFT_DELETE`, `AI_ANALYSIS` |
| `previous_value` | JSON | No | ค่าเดิมก่อนแก้ไข |
| `new_value` | JSON | Yes | ค่าใหม่หลังแก้ไข |
| `timestamp` | DateTime | Yes | เวลาที่เกิดการกระทำ |

> GSI: `gsi_report_timestamp` (PK: `report_ref_id`, SK: `timestamp`) สำหรับ Query ประวัติรายรายงาน

### 4.3 StatsCounter Table (Atomic Counter)

| Field Name | Type | Required | Description |
|---|---|---|---|
| `stat_key` (PK) | String | Yes | รูปแบบ: `{date}#{stat_name}` เช่น `2026-03-03#total_received` |
| `stat_value` | Number | Yes | ค่านับสะสม (Atomic Increment) |

### 4.4 Idempotency & Audit Strategy

- **Idempotency**: ใช้ `source_external_id` ตรวจสอบผ่าน GSI `gsi_source_external_id` ก่อนสร้าง `report_id` ใหม่
- **Audit Logging**: ทุกการเปลี่ยนแปลงบันทึกลง Audit Logs ระบุ `action_type` ชัดเจน

---

## 5. Service Architecture

### 5.1 Components

```
External Client (Social Media / Mobile App / IoT)
        │
        ▼
┌─────────────────────────────────────────┐
│         API Gateway (REST)              │
│   X-Api-Key auth + Rate 50 req/s        │
└───┬──────────┬──────────┬──────────────┘
    │ POST      │ GET/PATCH/DELETE         │ GET
    ▼           ▼                          ▼
┌────────┐  ┌────────────────┐        ┌──────────┐
│ Ingest │  │  API Handler   │        │  Health  │
│Handler │  │   (Lambda)     │        │ Handler  │
└───┬────┘  └───┬────────┬───┘        └──────────┘
    │           │        │
    ▼           ▼        ▼
┌────────┐  ┌────────┐  ┌────────────┐
│  SQS   │  │DynamoDB│  │ EventBridge│
│ Queue  │  │Reports │  │ Bus        │
└───┬────┘  │Audit   │  └────────────┘
    │       │Stats   │
    ▼       └────────┘
┌────────────────────────┐
│  Ingestion Worker      │
│     (Lambda)           │
│ ┌──────────────────┐   │
│ │ Gemini AI        │   │
│ │ content_score    │   │
│ │ (0–30)           │   │
│ └──────────────────┘   │
│ ┌──────────────────┐   │
│ │ Python Assembler │   │
│ │ Composite Trust  │   │
│ │ Score (0–100)    │   │
│ └──────────────────┘   │
│ ┌──────────────────┐   │
│ │ Dedup Logic      │   │
│ │ Haversine ≤200m  │   │
│ │ Time ≤15min      │   │
│ └──────────────────┘   │
└────────────────────────┘
```

### 5.2 Trust Score Flow (Composite)

```
Raw Report
    │
    ▼
[Gemini AI]     → content_score (0–30)
[Source Rule]   → source_score (0–20, e.g. IOT_SENSOR=20, TWITTER=8)
[History Check] → history_score (0–15, +5 bonus if verified, −8 per spam)
[Vision (opt.)] → image_score (−10 ถึง +20)
    │
    ▼ Python assembles:
trust_score = content_score + source_score + history_score + image_score
    │
    ▼
< 30% → SPAM | ≥ 30% + Geo/Time match → DUPLICATE | ≥ 30% + unique → PENDING_REVIEW
```

### 5.3 Report Status Lifecycle

```
RECEIVED → PENDING_REVIEW → VERIFIED
    │              ↕
    │         NEEDS_MORE_INFO (via PATCH)
    │
    ├──→ SPAM (Auto — Trust Score < 30%)
    └──→ DUPLICATE (Auto — Geo + Time match)
              ↓
           REJECTED (Human)

ทุกสถานะ → DELETED (Soft delete)
```

---

## 6. Service Interaction

### 6.1 Upstream Services (เรียกใช้งาน Service นี้)

| Service | Method | Action |
|---|---|---|
| DisasterMonitoring Service (IoT) | HTTP POST | `POST /reports` |
| Operation Update Service (Dashboard) | HTTP GET | `GET /reports/stats`, `GET /reports?status=PENDING_REVIEW` |

### 6.2 Downstream Services (Service นี้ส่งข้อมูลไป)

| Service | Type | Event/Action | Filter |
|---|---|---|---|
| Incident Tracking Service | Async Event | `ReportVerifiedEvent` | ทุก VERIFIED report |
| Rescue Request Service | Async Event | `ReportVerifiedEvent` | filter: `type=SOS` หรือ `severity=CRITICAL` |
| Property Damage Service | Async Event | `ReportVerifiedEvent` | filter: `type=DAMAGE` |
| Incident Service | Sync GET (Optional) | `GET /incidents?active=true` | Dashboard ใช้ดู Active Incidents เพื่อ Link |

### 6.3 Technical Rationale

- **Fan-out Pattern**: Publish Event ครั้งเดียว → หลาย Service รับข้อมูลพร้อมกัน โดยไม่ต้อง Call API โดยตรง
- **Decoupling**: Service นี้ไม่รู้จัก Business Logic ของ Service อื่น
- **Resilience**: หาก RescueRequest ล่ม Service นี้ยังทำงานต่อได้โดยไม่เกิด Cascading Failure

---

## 7. Dependency Mapping

### 7.1 Incident Tracking Service

- **Type**: Microservice (External)
- **Interaction**: Synchronous (HTTP GET) — เรียกดู Active Incidents เพื่อ Link
- **Criticality**: Medium (ถ้าล่ม Feature "Link to Existing Incident" ใช้ไม่ได้ แต่ Service หลักยังทำงานได้)
- **Failure Handling**: Graceful Degradation — ปิดปุ่ม Link ชั่วคราว, fallback สร้าง New Incident

### 7.2 Amazon SQS

- **Queue Name**: `report-verify-{env}-ingestion-queue` (เช่น `report-verify-dev-ingestion-queue`)
- **DLQ Name**: `report-verify-{env}-ingestion-dlq`
- **Criticality**: Critical (ถ้าล่ม ข้อมูลขาเข้าสูญหาย)
- **Failure Handling**: Lambda Retry Policy → Dead Letter Queue → Developer Re-drive

### 7.3 Amazon EventBridge

- **Event Bus Name**: `report-verify-{env}-disaster-event-bus` (เช่น `report-verify-dev-disaster-event-bus`)
- **Criticality**: High (ถ้าส่ง Event ไม่ได้ Service อื่นไม่รู้ว่ามีเหตุเกิด)
- **Failure Handling**: Error Logging พร้อม Payload ลงใน Database (**Outbox Pattern — Planned, ยังไม่ Implement**)

### 7.4 Amazon DynamoDB

- **Tables**: `report-verify-reports`, `report-verify-audit-logs`, `report-verify-stats`
- **Criticality**: Critical (ระบบหยุดทันทีถ้า DynamoDB ล่ม)
- **Failure Handling**: Error 500 (Sync) หรือ SQS Retry + Exponential Backoff (Async)

### 7.5 Google Gemini API

- **Models**: `gemini-2.5-flash-lite` → `gemini-2.0-flash` → `gemini-3.1-flash-lite` (Fallback chain)
- **Multi-key Rotation**: รองรับ GEMINI_API_KEY1..N — หมุนเวียนอัตโนมัติเมื่อติด 429
- **Criticality**: Medium (ระบบยังทำงานได้แม้ Gemini ล่ม)
- **Failure Handling**: Trust Score fallback เป็น 50 (Unknown) + ติด Flag `ai_analysis_failed=true`

---

*Service Owner: Akawat Moradsatian (6609681231) — CS366 Serverless Computing*
