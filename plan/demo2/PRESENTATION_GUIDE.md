# CS366 Demo 2 — Presentation Guide
### Report Ingestion & Verification Service

> **วันนำเสนอ:** 20 เมษายน 2026  
> **API Base URL:** `https://d8a7ds12a2.execute-api.us-east-1.amazonaws.com/dev/v1`  
> **API Key:** `Hk3gkvihdf5scu0ZPJKGn1EsvX74Ny2m5gKDTxDe`  
> **Region:** `us-east-1`

---

## 📋 สารบัญ

1. [วิธีหาค่า API URL และ API Key](#1-วิธีหาค่า-api-url-และ-api-key)
2. [Endpoint ทั้งหมด (Sync)](#2-sync-endpoints)
3. [Async Pipeline (EventBridge)](#3-async-pipeline)
4. [Feature ใหม่ที่เพิ่มใน Demo 2](#4-feature-ใหม่)
5. [Anti-Pattern Fix Status](#5-anti-pattern-fix-status)
6. [Frontend API Tester](#6-frontend-api-tester)
7. [20 คำถามที่อาจถามในการนำเสนอ](#7-20-คำถาม)

---

## 1. วิธีหาค่า API URL และ API Key

### วิธีที่ 1 — terraform output (แนะนำ)
```bash
cd terraform/
terraform output api_url          # → https://xxxx.execute-api.us-east-1.amazonaws.com/dev/v1
terraform output -raw api_key     # → Hk3gkvihdf5scu0ZPJKGn1EsvX74Ny2m5gKDTxDe
```

### วิธีที่ 2 — อ่านจาก terraform.tfstate
```bash
cat terraform/terraform.tfstate | python3 -c "
import json, sys
s = json.load(sys.stdin)
for r in s['resources']:
    if r['type'] == 'aws_api_gateway_stage':
        print('invoke_url:', r['instances'][0]['attributes']['invoke_url'])
"
```

### วิธีที่ 3 — AWS CLI
```bash
aws apigateway get-rest-apis --region us-east-1
aws apigateway get-api-keys --include-values --region us-east-1
```

### วิธีที่ 4 — deploy.sh output
```bash
./scripts/deploy.sh --auto-approve
# ดูในบรรทัดสุดท้าย: Outputs → api_url, api_key
```

> **หมายเหตุ:** API_KEY ต้องส่งใน header `x-api-key` เฉพาะ endpoint ที่เป็น `api_key_required = true`  
> ดูว่า endpoint ไหนต้องการ Key ได้จาก `terraform/api_gateway.tf` บรรทัด `api_key_required = true`

---

## 2. Sync Endpoints

Base: `https://d8a7ds12a2.execute-api.us-east-1.amazonaws.com/dev/v1`

> ทุก Response มี header `X-Trace-Id` และ body มี `traceId` ให้ track ได้ (Anti-Pattern #7)

### 2.1 Health Check
```
GET /v1/health
```
- **Auth:** ไม่ต้องใช้ API Key
- **Lambda:** `health_handler.py → handler()`
- **Returns:** สถานะ DynamoDB, SQS, Gemini AI, EventBridge แบบ component-level
- **HTTP 200** = healthy/degraded | **HTTP 503** = unhealthy (DynamoDB/SQS ล้ม)

```bash
curl https://d8a7ds12a2.execute-api.us-east-1.amazonaws.com/dev/v1/health
```

**Response ตัวอย่าง:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-20T10:00:00+00:00",
  "duration_ms": 245,
  "traceId": "abc-123",
  "version": "1.0.0",
  "components": {
    "dynamodb": { "status": "healthy", "table": "report-verify-dev-reports" },
    "sqs":      { "status": "healthy", "approximate_messages": 0 },
    "gemini":   { "status": "healthy", "model": "gemini-2.5-flash-lite", "available_keys": 6 },
    "eventbridge": { "status": "healthy" }
  }
}
```

---

### 2.2 Submit Report (Async Trigger)
```
POST /v1/reports
Header: x-api-key: <API_KEY>
```
- **Auth:** ต้องใช้ API Key
- **Lambda:** `ingest_handler.py → handler()` → ส่ง SQS → Worker ประมวลผล async
- **Pattern:** Fire-and-forget → Response 202 ทันที, AI วิเคราะห์ใน background
- **Source file:** `src/handlers/ingest_handler.py`

**Required Body:**
```json
{
  "reporter_source": "citizen_app",
  "reporter_id": "user-001",
  "raw_content": "ไฟไหม้บ้านเลขที่ 10",
  "geo_location": { "lat": 13.7466, "lon": 100.5391 },
  "timestamp": "2026-04-20T10:00:00+00:00"
}
```

**Optional Fields:**
```json
{
  "media_urls": ["https://bucket.s3.amazonaws.com/media/temp/m-xxx_file.jpg"],
  "source_external_id": "ext-12345"
}
```

**Response 202:**
```json
{
  "report_id": "r-f0744deff05b",
  "status": "RECEIVED",
  "message": "Report accepted for processing.",
  "traceId": "abc-def-123"
}
```

---

### 2.3 Upload Media (Presigned S3 URL)
```
POST /v1/reports/upload-url
Header: x-api-key: <API_KEY>
```
- **Auth:** ต้องใช้ API Key
- **Lambda:** `api_handler.py → _handle_upload_url()`
- **Flow:** รับ presigned PUT URL แล้วค่อย PUT ไฟล์ตรงไป S3
- **Bucket:** `report-verify-dev-media-533267353075`
- **Source file:** `src/handlers/api_handler.py` ฟังก์ชัน `_handle_upload_url()`

**Body:**
```json
{
  "filename": "photo.jpg",
  "content_type": "image/jpeg",
  "file_size_bytes": 102400
}
```

**Response:**
```json
{
  "upload_url": "https://s3.amazonaws.com/...?X-Amz-Signature=...",
  "media_id": "m-abc123def456",
  "media_url": "https://report-verify-dev-media-533267353075.s3.us-east-1.amazonaws.com/media/temp/m-abc_photo.jpg",
  "expires_in": 900,
  "method": "PUT"
}
```

**Step 2 — Upload ไฟล์:**
```bash
curl -X PUT "<upload_url>" \
  -H "Content-Type: image/jpeg" \
  --data-binary @photo.jpg
```

**Step 3 — ส่ง report พร้อม media_url ที่ได้:**
```json
{ "media_urls": ["<media_url>"] }
```

---

### 2.4 Get Report Detail
```
GET /v1/reports/{report_id}
```
- **Auth:** ไม่ต้องใช้ API Key
- **Lambda:** `api_handler.py → _handle_get_detail()`
- **ใช้ติดตาม:** สถานะ AI analysis, trust_score, final status

```bash
curl https://d8a7ds12a2.execute-api.us-east-1.amazonaws.com/dev/v1/reports/r-f0744deff05b
```

**Response สำคัญ:**
```json
{
  "report_id": "r-f0744deff05b",
  "validation_status": "DUPLICATE",
  "trust_score": 85,
  "ai_reasoning": "The image clearly depicts a house engulfed in flames...",
  "suggested_category": "FIRE",
  "ai_analysis_tags": ["house fire", "fire", "smoke"],
  "traceId": "abc-def-123"
}
```

---

### 2.5 List Reports
```
GET /v1/reports?status=PENDING_REVIEW&limit=10&min_trust_score=50
```
- **Auth:** ไม่ต้องใช้ API Key
- **Lambda:** `api_handler.py → _handle_list_reports()`
- **Query params:**
  - `status` = RECEIVED | PENDING_REVIEW | VERIFIED | SPAM | REJECTED | DUPLICATE
  - `limit` = จำนวน (max 100)
  - `min_trust_score` = กรอง score ขั้นต่ำ
  - `priority` = all | high | normal

---

### 2.6 Verify / Reject Report
```
PATCH /v1/reports/{report_id}
```
- **Auth:** ไม่ต้องใช้ API Key (ปรับได้)
- **Lambda:** `api_handler.py → _handle_verify()`
- **Trigger Async:** ถ้า status = VERIFIED → ส่ง `ReportVerifiedEvent` ไป EventBridge

**Body:**
```json
{
  "validation_status": "VERIFIED",
  "reviewer_id": "officer-001",
  "reviewer_notes": "ยืนยันจากกล้อง CCTV"
}
```

**Optimistic Locking:** ใช้ DynamoDB `ConditionExpression` ป้องกัน race condition  
**Source:** `src/handlers/api_handler.py` บรรทัด `ConditionExpression="validation_status = :expected_status"`

---

### 2.7 Dashboard Statistics
```
GET /v1/reports/stats?timeframe=today&region=bkk
```
- **Auth:** ไม่ต้องใช้ API Key
- **Lambda:** `api_handler.py → _handle_get_stats()`
- **Cache:** ผล cache ใน Lambda memory (TTL กำหนดใน `config.STATS_CACHE_TTL_SECONDS`)
- **Query params:**
  - `timeframe` = today | last_24h | last_7d
  - `region` = bkk | central | north | northeast | south

**Response:**
```json
{
  "timeframe": "today",
  "region": "bkk",
  "summary": {
    "total_received_today": 25,
    "pending_review": 5,
    "verified_incidents": 10,
    "spam_rejected": 10
  },
  "trending_keywords": [{"keyword": "flood", "count": 8}],
  "heatmap_data": [{"lat": 13.75, "lon": 100.54, "count": 3}]
}
```

---

### 2.8 Audit Logs
```
GET /v1/reports/audit?report_id=r-xxx&limit=20
```
- **Auth:** ไม่ต้องใช้ API Key
- **Lambda:** `api_handler.py → _handle_get_audit_logs()`
- **Source:** DynamoDB `report-verify-dev-audit-logs` table
- **ดูได้:** ทุก status change, ใครเปลี่ยน, เวลา

---

### 2.9 EventBridge Events (Debug)
```
GET /v1/reports/events?type=all&limit=10
GET /v1/reports/events?type=verified
GET /v1/reports/events?type=status-changed
```
- **Auth:** ไม่ต้องใช้ API Key
- **Lambda:** `api_handler.py → _handle_get_events()`
- **Source:** อ่านจาก CloudWatch Logs `/events/{prefix}/report-verified` และ `/events/{prefix}/status-changed`

---

### 2.10 Soft Delete
```
DELETE /v1/reports/{report_id}
```
- **Body:** `{ "deleted_by": "admin", "reason": "test data" }`
- **Note:** Soft delete เท่านั้น — ข้อมูลยังอยู่ใน DynamoDB แต่ status = DELETED, GET จะ 404

---

### 2.11 Changelog (Version XML/RSS)
```
GET /v1/changelog.xml
```
- **Auth:** ไม่ต้องใช้ API Key
- **Returns:** RSS/XML feed ของการเปลี่ยนแปลง API (Anti-Pattern #9)
- **Lambda:** `api_handler.py → _handle_changelog_rss()` + `_build_changelog_rss_xml()`
- **Source:** ข้อมูลมาจาก `CHANGELOG_ENTRIES` array ที่บรรทัดต้นของ `api_handler.py`

```bash
curl https://d8a7ds12a2.execute-api.us-east-1.amazonaws.com/dev/v1/changelog.xml
```

**Response (XML):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Report Ingestion &amp; Verification Service — API Changelog</title>
    <item>
      <title>Added OpenAPI specification and RSS changelog endpoint — v1.1.0</title>
      <pubDate>Sat, 19 Apr 2026 10:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Improved response observability — v1.0.2</title>
      <pubDate>Wed, 08 Apr 2026 09:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>
```

---

## 3. Async Pipeline

```
POST /v1/reports  →  ingest_handler  →  SQS Queue  →  ingestion_worker
                                                              │
                                               ┌──────────────┼──────────────┐
                                               ▼              ▼              ▼
                                          Gemini AI      Dedup Check    DynamoDB
                                          (Vision)       (Geo+Time)    (store)
                                               │
                                               ▼ (if VERIFIED via PATCH)
                                          EventBridge
                                         ┌──────┴──────┐
                                         ▼              ▼
                               ReportVerifiedEvent  ReportStatusChangedEvent
                               (→ Incident Service) (→ Dashboard/Notification)
```

### Event Schema (schemaVersion: "1.0") — Anti-Pattern #9
**ReportVerifiedEvent** (EventBridge detail-type):
```json
{
  "schemaVersion": "1.0",
  "report_ref_id": "r-xxx",
  "suggested_incident_data": {
    "type": "FIRE",
    "severity_level": 3,
    "location": { "lat": 13.7466, "lon": 100.5391 }
  },
  "verified_by": "officer-001"
}
```

**ReportStatusChangedEvent:**
```json
{
  "schemaVersion": "1.0",
  "report_id": "r-xxx",
  "old_status": "PENDING_REVIEW",
  "new_status": "VERIFIED",
  "changed_by": "officer-001",
  "timestamp": "2026-04-20T10:00:00+00:00"
}
```

**Source file:** `src/services/event_publisher.py`

---

## 4. Feature ใหม่

### 4.1 Traceable Response (Anti-Pattern #7)

**หาได้จาก:** `src/utils/response.py`

ทุก response มี:
- **HTTP Header:** `X-Trace-Id: <uuid>` ← ดูในหัว HTTP Response
- **Body JSON:** `"traceId": "<uuid>"` ← ดูในทุก success และ error response
- **Body Error:** `"errorCode": "E400"` (E400, E401, E403, E404, E409, E429, E500)

```python
# response.py
def _build_headers(trace_id=None, deprecated=False, sunset_date=None):
    headers["X-Trace-Id"] = trace_id          # ← ทุก response
    headers["X-Deprecated-Version"] = "true"  # ← เฉพาะ deprecated endpoint
    headers["X-Sunset-Date"] = sunset_date     # ← เฉพาะ deprecated endpoint

def error(..., error_code=None):
    body["traceId"] = trace_id    # ← ทุก error
    body["errorCode"] = error_code # ← E400, E404, E500, etc.
    body["timestamp"] = "..."
```

**วิธีทดสอบ:**
```bash
curl -v https://d8a7ds12a2.execute-api.us-east-1.amazonaws.com/dev/v1/health
# ดู: < X-Trace-Id: 4b96bc3c-bbff-40e7-a57f-9281d5b90875
```

---

### 4.2 Deprecation Response (Anti-Pattern #9 / Versioning)

**หาได้จาก:** `src/utils/response.py` ฟังก์ชัน `_build_headers()`  
**ใช้งาน:** ถ้า endpoint เก่าถูกเรียก จะได้ headers เพิ่มมา

```http
X-Deprecated-Version: true
X-Sunset-Date: 2026-07-01
```

**ตัวอย่างใน code:**
```python
return response.success(body, trace_id=trace_id, deprecated=True, sunset_date="2026-07-01")
```

**Policy:** ดูได้ที่ `docs/VERSIONING_POLICY.md`

---

### 4.3 Version XML / RSS Changelog (Anti-Pattern #9)

**Endpoint:** `GET /v1/changelog.xml`  
**หาได้จาก code:**
- `CHANGELOG_ENTRIES` array ใน `src/handlers/api_handler.py` บรรทัดประมาณ 70-100
- ฟังก์ชัน `_build_changelog_rss_xml()` และ `_handle_changelog_rss()`
- `src/utils/response.py` ฟังก์ชัน `xml()` และ `raw()`

**Content-Type:** `application/rss+xml; charset=utf-8`

**เพิ่ม entry ใหม่:**
```python
CHANGELOG_ENTRIES.append({
    "id": "2026-05-01-new-feature",
    "title": "Added new endpoint",
    "description": "...",
    "version": "1.2.0",
    "published_at": "2026-05-01T00:00:00+00:00",
})
```

---

### 4.4 Gemini Vision API (AI Image Analysis)

**หาได้จาก:** `src/services/gemini_service.py`  
**ทำงานใน:** `src/handlers/ingestion_worker.py`

**Flow:**
1. Worker ดาวน์โหลดภาพจาก S3
2. แปลงเป็น base64
3. ส่งไปให้ Gemini Vision พร้อม prompt
4. ได้กลับ: `trust_score`, `ai_reasoning`, `suggested_category`, `ai_analysis_tags`

**Multi-key rotation:** 6 keys (KEY1-KEY6) หมุนเวียนกัน  
**Model chain:** `gemini-2.5-flash-lite` → `gemini-2.0-flash` → fallback

**ตรวจ Gemini health:**
```bash
curl https://d8a7ds12a2.execute-api.us-east-1.amazonaws.com/dev/v1/health
# ดูใน components.gemini
```

---

## 5. Anti-Pattern Fix Status

| # | Anti-Pattern | Status | หลักฐาน |
|---|---|---|---|
| #1 | Distributed Monolith | ✅ ไม่มี | แต่ละ Lambda แยก responsibility, EventBridge ใช้แทน direct call |
| #2 | Shared Database | ✅ ไม่มี | มี DynamoDB table แยก: reports, audit, stats |
| #3 | Chatty Services | ✅ ไม่มี | SQS batch, DynamoDB batch_get_item |
| #4 | Over-Microservices | ✅ ไม่มี | 3 Lambda เท่านั้น: api, ingest, worker |
| #5 | God Service | ✅ ไม่มี | แต่ละ handler มี scope ชัดเจน |
| #6 | Tight Coupling | ✅ ไม่มี | EventBridge async, ไม่ call Incident Service ตรง |
| **#7** | **Observability** | **✅ แก้แล้ว** | **X-Trace-Id header, traceId+errorCode ใน body ทุก response** |
| **#8** | **Timeout** | **✅ แก้แล้ว** | **`request_options={"timeout": 15}` ใน gemini_service.py** |
| **#9** | **Static Contract** | **✅ แก้แล้ว** | **schemaVersion="1.0" ใน EventBridge, changelog.xml, deprecation headers** |

### Health Check Anti-Pattern Status ✅

**ตรวจ:** `src/handlers/health_handler.py`

```python
body = {
    "status": overall,          # "healthy" | "degraded" | "unhealthy"
    "traceId": request_id,      # ← Anti-Pattern #7: traceable ✅
    "version": "1.0.0",         # ← Anti-Pattern #9: versioned ✅
    "components": components,   # ← ระบุ component breakdown ✅
    "duration_ms": duration_ms, # ← observability ✅
}
status_code = 200 if overall != "unhealthy" else 503  # ← 503 เมื่อ critical fail ✅
return response.success(body, status_code=status_code, trace_id=request_id)
# → เพิ่ม X-Trace-Id header อัตโนมัติ ✅
```

- **Critical components** (ล้มแล้ว unhealthy): DynamoDB, SQS
- **Non-critical** (ล้มแล้ว degraded): Gemini, EventBridge

---

## 6. Frontend API Tester

### URLs (S3 Static Website)

| หน้า | URL |
|---|---|
| **Dashboard / API Tester** | `http://report-verify-dev-website-533267353075.s3-website-us-east-1.amazonaws.com/dashboard/` |
| Landing Page | `http://report-verify-dev-website-533267353075.s3-website-us-east-1.amazonaws.com` |
| OpenAPI Spec (JSON) | `http://report-verify-dev-website-533267353075.s3-website-us-east-1.amazonaws.com/openapi.json` |

> หา URL ได้จาก: `terraform output dashboard_url` หรือ `terraform output website_url`

### ขั้นตอนหลังเปิด Dashboard:
1. ไปที่ **API Settings** (เมนูซ้าย)
2. กรอก **API URL:** `https://d8a7ds12a2.execute-api.us-east-1.amazonaws.com/dev/v1`
3. กรอก **API Key:** `Hk3gkvihdf5scu0ZPJKGn1EsvX74Ny2m5gKDTxDe`
4. กด **Save**
5. เลือก endpoint จากเมนูซ้าย แล้วกด **Send**

### หน้าหลัก (Landing page)
```bash
# เปิด
file:///home/skoadmin/git-repository/CS366-Serverless-RequestVerifyService/frontend/index.html
```

---

## 7. Twenty Q&A

### กลุ่ม 1: Architecture & Design

**Q1: ทำไมใช้ SQS คั่นกลางระหว่าง API กับ Worker ไม่รับ-ประมวลผลตรงเลย?**  
A: เพราะ Gemini Vision API ใช้เวลาหลายวินาที ถ้าประมวลผลใน Lambda ที่รับ request จะทำให้ client ต้องรอนาน (หรือ timeout) SQS ทำให้รับ request ได้เร็ว (202 ทันที) แล้ว Worker ค่อยประมวลผล async ถ้า Worker ล้มก็ retry ได้จาก SQS โดยไม่ต้อง client ส่งใหม่

**Q2: ทำไม EventBridge ไม่ call Incident Service ตรง?**  
A: ป้องกัน Tight Coupling (Anti-Pattern #6) — ถ้า Incident Service ล้ม Report Service ก็ยังทำงานได้ นอกจากนี้ฝั่ง consumer สามารถ subscribe event ได้เองโดยไม่ต้อง modify Report Service

**Q3: ทำไม DELETE ถึงเป็น Soft Delete ไม่ลบจริง?**  
A: เพื่อ audit trail — ยังต้องพิสูจน์ได้ว่าเคยมี report นี้ ป้องกันการแก้ไขหลังยืนยัน และข้อมูล geo/ai_analysis ยังอาจมีประโยชน์สำหรับ stats

**Q4: Deduplication ทำงานยังไง?**  
A: Worker เช็คใน DynamoDB ว่ามี report อื่นที่ `geo_location` ใกล้กัน (radius ~500m) และ `ingested_at` ภายใน window เดียวกันหรือไม่ ถ้าใช่จะ set status = DUPLICATE และ link `potential_duplicates`

**Q5: trust_score คำนวณยังไง?**  
A: Gemini Vision วิเคราะห์ภาพ (ถ้ามี) + เนื้อหา report แล้ว return score 0-100  
- 0-30 = SPAM (auto-reject)  
- 31-49 = PENDING_REVIEW (รอเจ้าหน้าที่)  
- 50-100 = PENDING_REVIEW (ความน่าเชื่อถือสูง)  

---

### กลุ่ม 2: Anti-Pattern Fixes

**Q6: X-Trace-Id มาจากไหน และใช้ทำอะไร?**  
A: มาจาก `context.aws_request_id` ของ Lambda (UUID ที่ AWS generate ต่อ request) ส่งผ่าน `response.py` เป็น HTTP header `X-Trace-Id` และใน JSON body เป็น `traceId` ทำให้ correlate logs ใน CloudWatch ได้โดยใช้ request_id เดียวกัน — หาใน `src/utils/response.py` และ `src/handlers/*.py`

**Q7: errorCode เช่น E404, E500 มาจากไหน?**  
A: กำหนดใน `src/utils/response.py` ฟังก์ชัน `bad_request()`, `not_found()`, `internal_error()` ฯลฯ ทุก error function ส่ง `error_code` เข้าไปให้ `error()` ที่เพิ่มลงใน JSON body อัตโนมัติ

**Q8: schemaVersion ใน EventBridge ใช้ทำอะไร?**  
A: ป้องกัน Static Contract (Anti-Pattern #9) — consumer check `schemaVersion` ก่อนประมวลผล ถ้า version เปลี่ยน consumer รู้ว่า schema อาจต่างออกไป ช่วยให้ backward compatible — หาใน `src/services/event_publisher.py`

**Q9: Timeout ถูก Enforce ที่ไหน?**  
A: `src/services/gemini_service.py` มี `request_options={"timeout": 15}` เมื่อเรียก Gemini API ทำให้ถ้า Gemini ไม่ตอบใน 15 วินาที จะ raise exception และ Worker จะ fail message กลับไป SQS เพื่อ retry แทนที่จะค้างไปเรื่อย ๆ

**Q10: deprecation header ทำงานยังไง?**  
A: เมื่อเรียก endpoint ที่ deprecated จะได้ headers `X-Deprecated-Version: true` และ `X-Sunset-Date: <date>` ซึ่งบอก consumer ว่า endpoint นี้จะถูกปิดวันไหน ให้ migrate ก่อน — กำหนดใน `src/utils/response.py` ฟังก์ชัน `_build_headers()`

---

### กลุ่ม 3: AWS Infrastructure

**Q11: Lambda Functions มีกี่ตัว ทำอะไร?**  
A:
- `ingest_handler` — รับ POST /reports, validate, ส่ง SQS (sync, เร็ว)
- `ingestion_worker` — SQS trigger, AI + dedup + store DynamoDB (async, ช้า)
- `api_handler` — ทุก endpoint อื่น (list, detail, verify, stats, audit, events)
- `health_handler` — GET /health เท่านั้น

**Q12: DynamoDB มี Table อะไรบ้าง?**  
A:
- `report-verify-dev-reports` — reports ทั้งหมด
- `report-verify-dev-audit-logs` — ทุก status change
- `report-verify-dev-stats` — aggregate counters (pending, verified, spam)

**Q13: ทำไม stats ต้องมี table แยก ไม่ count จาก reports ทุกครั้ง?**  
A: DynamoDB Scan ทั้ง table ช้าและแพง ถ้า report มีล้านรายการ stats จะช้า table แยกเก็บ counter แบบ atomic increment ทำให้ stats เร็ว O(1)

**Q14: S3 Media Bucket ใช้ทำอะไร เข้าถึงยังไง?**  
A: เก็บไฟล์ภาพ/วิดีโอ ที่ reporter upload มา ไม่ public โดยตรง — เข้าถึงผ่าน presigned URL จาก `POST /v1/reports/upload-url` (มีอายุ 15 นาที) Worker ดาวน์โหลดจาก S3 เองด้วย IAM role

---

### กลุ่ม 4: Testing & Quality

**Q15: ทดสอบมีกี่ประเภท ผ่านทั้งหมดไหม?**  
A:
- Unit Tests: **87/87 passed** — ทดสอบ service, model, validator แยก mock
- Integration Tests: **13/13 passed** — ทดสอบ handler กับ DynamoDB จริง (LocalStack)
- E2E Tests: **25/25 passed** — ทดสอบผ่าน live API URL ใน AWS
- Image Tests: **4/4 passed** — ทดสอบ Gemini Vision กับภาพจริงจาก tests/media/

**Q16: Image Test ได้ผลยังไงบ้าง?**  
A:
- `housefire.jpg` → Gemini: FIRE, trust=85 ✅ (ระบุถูก)
- `flood.jpg` → Gemini: FLOOD, trust=85 ✅ (ระบุถูก)
- `forestfire.jpg` → Gemini: FIRE, trust=85 ✅ (ระบุถูก)
- `campfire.jpg` → Gemini: OTHER, trust=10 → auto-SPAM ✅ (Reject ถูก)

**Q17: E2E Test ตรวจสอบอะไรบ้าง?**  
A: ทดสอบ flow ทั้งระบบ: submit report → wait → check AI result → verify → check EventBridge event ครบ 25 test cases ใน `tests/e2e/` รวม edge cases เช่น invalid payload, duplicate detection, permission checks

---

### กลุ่ม 5: Operations & Scaling

**Q18: ถ้า Gemini API Key หมด limit จะเกิดอะไร?**  
A: `gemini_service.py` มี multi-key rotation — rotate ไป KEY2, KEY3 ... KEY6 อัตโนมัติ ถ้าทุก key หมดจะ fallback ไป model ถัดไปใน chain (`gemini-2.0-flash`, `gemini-3.1-flash-lite`) ถ้า fail ทั้งหมดจะ mark `ai_analysis_failed=true` และ report เป็น PENDING_REVIEW แทน

**Q19: Deploy ใหม่ทำยังไง destroy ของเก่าก่อนไหม?**  
A:
```bash
./scripts/destroy.sh --auto-approve   # ลบทุก resource (108 resources)
./scripts/deploy.sh --auto-approve    # สร้างใหม่ทั้งหมด (11+ resources)
```
ปกติไม่ต้อง destroy ถ้าแค่ update code — `deploy.sh` จะ `terraform apply` ซึ่ง update เฉพาะที่เปลี่ยน

**Q20: ระบบ scale ยังไงถ้า report เข้ามาพร้อมกัน 10,000 รายการ?**  
A:
- API Gateway: scale อัตโนมัติ (managed)
- Lambda: scale concurrent ตาม traffic (default limit 1000 concurrent/region)
- SQS: buffer และ batch processing — Worker รับ batch สูงสุด 10 messages ต่อครั้ง
- DynamoDB: On-demand mode scale อัตโนมัติ ไม่ต้อง provision capacity
- Bottleneck: Gemini API rate limit — แก้ด้วย multi-key rotation และ SQS retry

---

## 🔗 ไฟล์อ้างอิงสำคัญ

| เรื่อง | ไฟล์ |
|---|---|
| Response builder (X-Trace-Id, errorCode, deprecation) | `src/utils/response.py` |
| Health Check handler | `src/handlers/health_handler.py` |
| Ingest (sync POST) | `src/handlers/ingest_handler.py` |
| Worker (async AI+dedup) | `src/handlers/ingestion_worker.py` |
| API Routes (list/verify/stats/upload) | `src/handlers/api_handler.py` |
| EventBridge publisher (schemaVersion) | `src/services/event_publisher.py` |
| Gemini Vision + timeout | `src/services/gemini_service.py` |
| Versioning Policy | `docs/VERSIONING_POLICY.md` |
| API Gateway Terraform | `terraform/api_gateway.tf` |
| All Endpoints OpenAPI | `docs/openapi/` |
| Anti-Pattern Self-Review | `docs/anti-pattern-workshop/AI-rechecked-fixed-needed.md` |
| Test Results | `plan/demo2/TEST_RESULTS.md` |
| Frontend Dashboard | `frontend/dashboard/index.html` |
