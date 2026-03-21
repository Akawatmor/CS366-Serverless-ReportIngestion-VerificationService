# คู่มือเรียกใช้ API — Report Ingestion & Verification Service

> **สำหรับเพื่อน ๆ ที่ต้องการเรียกใช้ API ของ Service นี้**  
> **Updated:** 2026-03-09  
> **Service Owner:** CS366 Team

---

## การเข้าถึงระบบ

| รายการ | ค่า |
|--------|-----|
| **Base URL** | `https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1` |
| **API Key** | `bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ` |
| **Dashboard** | http://report-verify-dev-website-035136704221.s3-website-us-east-1.amazonaws.com/dashboard/ |
| **EventBridge Bus** | `report-verify-dev-disaster-event-bus` |
| **Region** | `us-east-1` |

> **หมายเหตุ:** API Key ต้องส่งผ่าน Header `X-Api-Key` ในทุก Request ที่เป็น POST (Ingest, Upload-URL)  
> GET Endpoints ไม่ต้องใช้ API Key

---

## ตั้งค่าตัวแปรก่อนเริ่ม

```bash
export API_URL="https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1"
export API_KEY="bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ"
```

---

## Synchronous API Contracts (REST)

### Contract #1: POST /reports — ส่งรายงานเข้าระบบ (Ingest)

**วัตถุประสงค์:** รับข้อมูลดิบจากภายนอก → ผ่าน SQS → AI วิเคราะห์ Trust Score → จัดสถานะอัตโนมัติ

```bash
curl -X POST "${API_URL}/reports" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${API_KEY}" \
  -d '{
    "reporter_source": "TWITTER",
    "reporter_id": "@your_user_id",
    "raw_content": "ไฟไหม้ร้านค้าตรงซอยสุขุมวิท 23 ควันเยอะมาก ช่วยด้วย!",
    "media_urls": ["https://example.com/evidence.jpg"],
    "geo_location": {
      "lat": 13.7366,
      "lon": 100.5608
    },
    "timestamp": "2026-03-09T10:00:00Z"
  }'
```

**Response (202 Accepted):**
```json
{
  "status": "QUEUED",
  "report_id": "r-550e8400-e29b",
  "message": "Report accepted and queued for processing.",
  "estimated_wait_time": "2s"
}
```

**ข้อจำกัด:**
- `reporter_source` ต้องเป็น: `TWITTER`, `FACEBOOK`, `LINE`, `OFFICIAL_APP`, `IOT_SENSOR`
- ต้องมี `raw_content` หรือ `media_urls` อย่างน้อย 1 อย่าง
- Payload ไม่เกิน 256KB

**หลังส่ง: ระบบจะประมวลผล Async ใน 5-20 วินาที:**
1. Gemini AI วิเคราะห์ Trust Score (0-100)
2. Trust < 30% → สถานะ **SPAM** อัตโนมัติ
3. ตรวจพบซ้ำ (GPS + เวลาใกล้กัน) → **DUPLICATE**
4. ผ่านเกณฑ์ → **PENDING_REVIEW** รอเจ้าหน้าที่ตรวจ

---

### Contract #2: GET /reports — ดูรายชื่อรายงาน (List)

```bash
# ดูรายงาน PENDING_REVIEW
curl "${API_URL}/reports?status=PENDING_REVIEW&limit=10"

# ดูรายงาน VERIFIED
curl "${API_URL}/reports?status=VERIFIED&limit=10"

# กรองด้วย Trust Score ขั้นต่ำ
curl "${API_URL}/reports?status=PENDING_REVIEW&min_trust_score=50&limit=20"
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "report_id": "r-620ae151dbd8",
      "content": "ไฟไหม้ตลาดนัดใกล้ Central World...",
      "trust_score": 60,
      "suggested_category": "FIRE",
      "time_ago": "5 mins"
    }
  ],
  "total_count": 1,
  "next_token": "eyJSZXBvcnRJZCI6..." 
}
```

**Query Parameters:**
| Param | ค่าที่รับ | Default |
|-------|----------|---------|
| `status` | `PENDING_REVIEW`, `VERIFIED`, `SPAM`, `REJECTED`, `DUPLICATE`, `DELETED` | ไม่บังคับ |
| `limit` | 1-100 | 5 |
| `min_trust_score` | 0-100 | ไม่กรอง |
| `last_evaluated_key` | token จาก `next_token` | - |

---

### Contract #3: PATCH /reports/{report_id} — ยืนยัน/ปฏิเสธรายงาน (Verify)

**วัตถุประสงค์:** เจ้าหน้าที่ตรวจสอบแล้วเปลี่ยนสถานะ → ถ้า VERIFIED จะ trigger EventBridge Event

```bash
# ยืนยันรายงาน
curl -X PATCH "${API_URL}/reports/r-620ae151dbd8" \
  -H "Content-Type: application/json" \
  -d '{
    "validation_status": "VERIFIED",
    "reviewer_id": "officer_cs366",
    "reviewer_notes": "ยืนยันจากกล้อง CCTV แล้ว"
  }'

# ปฏิเสธเป็น SPAM
curl -X PATCH "${API_URL}/reports/r-620ae151dbd8" \
  -H "Content-Type: application/json" \
  -d '{
    "validation_status": "SPAM",
    "reviewer_id": "officer_cs366",
    "reviewer_notes": "ข่าวปลอม"
  }'
```

**Response (200 OK):**
```json
{
  "report_id": "r-620ae151dbd8",
  "validation_status": "VERIFIED",
  "action_taken": "TRIGGER_NEW_INCIDENT",
  "updated_at": "2026-03-09T08:24:11Z"
}
```

**State Transition Rules:**
| จาก (From) | ไป (To) ที่อนุญาต |
|------------|-------------------|
| `RECEIVED` | `PENDING_REVIEW`, `SPAM`, `REJECTED`, `DUPLICATE` |
| `PENDING_REVIEW` | `VERIFIED`, `SPAM`, `REJECTED`, `DUPLICATE` |
| `VERIFIED` | *(Terminal — เปลี่ยนไม่ได้ ยกเว้น DELETE)* |
| `SPAM` / `REJECTED` / `DUPLICATE` | *(Terminal)* |

> **สำคัญ:** ถ้า status = `VERIFIED` ต้องมี `reviewer_id` เสมอ

---

### Contract #4: GET /reports/{report_id} — ดูรายละเอียดรายงาน (Detail)

```bash
curl "${API_URL}/reports/r-620ae151dbd8"
```

**Response:** ข้อมูลครบถ้วนทุก field รวม AI Reasoning, Tags, Trust Score, GPS, Media URLs

---

### Contract #5: GET /reports/stats — สถิติภาพรวม (Dashboard Stats)

```bash
curl "${API_URL}/reports/stats?timeframe=today"
```

**Response (200 OK):**
```json
{
  "timestamp": "2026-03-09T08:24:18Z",
  "summary": {
    "total_received_today": 1,
    "pending_review": 0,
    "verified_incidents": 1,
    "spam_rejected": 0
  },
  "trending_keywords": [
    { "keyword": "ไฟไหม้", "count": 1, "category": "FIRE" },
    { "keyword": "Central World", "count": 1, "category": "FIRE" }
  ],
  "heatmap_data": []
}
```

---

### Contract #6: DELETE /reports/{report_id} — ลบรายงาน (Soft Delete)

```bash
curl -X DELETE "${API_URL}/reports/r-620ae151dbd8" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "ข้อมูลซ้ำ ลบออก",
    "deleted_by": "admin_001"
  }'
```

**ต้องใส่ `reason` และ `deleted_by` เสมอ** — ระบบจะบันทึกลง Audit Log

---

### Contract #7: GET /health — ตรวจสอบสถานะระบบ (Health Check)

```bash
curl "${API_URL}/health"
```

**Response:** แสดงสถานะ DynamoDB, SQS, Gemini AI, EventBridge (healthy / degraded / unhealthy)

---

### Contract เพิ่มเติม: GET /reports/audit — ดู Audit Logs

```bash
# ดู Audit Logs ทั้งหมด
curl "${API_URL}/reports/audit?limit=20"

# ดู Audit Logs เฉพาะรายงานหนึ่ง
curl "${API_URL}/reports/audit?report_id=r-620ae151dbd8"
```

---

### Contract เพิ่มเติม: GET /reports/events — ดู EventBridge Events

```bash
# ดู Events ทั้งหมด
curl "${API_URL}/reports/events?type=all&limit=20"

# ดูเฉพาะ Verified Events
curl "${API_URL}/reports/events?type=verified&limit=10"

# ดูเฉพาะ Status Changed Events
curl "${API_URL}/reports/events?type=status-changed&limit=10"
```

---

### Contract เพิ่มเติม: POST /reports/upload-url — อัปโหลดไฟล์หลักฐาน

```bash
# ขั้นตอน 1: ขอ Presigned URL
curl -X POST "${API_URL}/reports/upload-url" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${API_KEY}" \
  -d '{
    "filename": "fire_evidence.jpg",
    "content_type": "image/jpeg",
    "report_id": "r-620ae151dbd8"
  }'

# ขั้นตอน 2: อัปโหลดไฟล์ไปยัง S3 (ใช้ upload_url ที่ได้รับ)
curl -X PUT "${UPLOAD_URL}" \
  -H "Content-Type: image/jpeg" \
  --data-binary @fire_evidence.jpg

# ขั้นตอน 3: ใช้ media_url ที่ได้ ใส่ใน POST /reports
```

**ไฟล์ที่รองรับ:** JPEG, PNG, GIF, WebP, MP4, MOV, AVI, PDF

---

## Asynchronous Event Contracts (EventBridge)

### วิธีเชื่อมต่อ

EventBridge Custom Bus: `report-verify-dev-disaster-event-bus`  
Source: `service.report-verify`

**ข้อจำกัด Learner Lab:** ไม่สามารถสร้าง IAM Role ใหม่ได้ ดังนั้นให้ใช้ LabRole ที่มีอยู่

---

### Event #1: ReportVerifiedEvent

**เกิดเมื่อ:** เจ้าหน้าที่ PATCH status → VERIFIED  
**Consumer เป้าหมาย:** Incident Tracking Service

```json
{
  "source": "service.report-verify",
  "detail-type": "ReportVerifiedEvent",
  "detail": {
    "report_ref_id": "r-620ae151dbd8",
    "suggested_incident_data": {
      "type": "FIRE",
      "description": "ไฟไหม้ตลาดนัด...",
      "severity_level": 3,
      "location": { "lat": "13.7466", "lon": "100.5391" },
      "reporter_count": 1,
      "media_evidence": ["https://s3.../img1.jpg"]
    },
    "verified_by": "officer_cs366",
    "verification_notes": "ยืนยันจากกล้อง CCTV ไฟไหม้จริง"
  }
}
```

---

### Event #2: ReportStatusChangedEvent

**เกิดเมื่อ:** ทุกครั้งที่สถานะเปลี่ยน (เช่น PENDING→SPAM, PENDING→VERIFIED)  
**Consumer เป้าหมาย:** Dashboard Service, Notification Service, Property Damage Service

```json
{
  "source": "service.report-verify",
  "detail-type": "ReportStatusChangedEvent",
  "detail": {
    "report_id": "r-620ae151dbd8",
    "old_status": "PENDING_REVIEW",
    "new_status": "VERIFIED",
    "reason": "ยืนยันจากกล้อง CCTV",
    "changed_by": "officer_cs366",
    "timestamp": "2026-03-09T08:24:11Z"
  }
}
```

---

### วิธี Subscribe ด้วย Terraform (สำหรับเพื่อน Service อื่น)

```hcl
# อ้างอิง Event Bus ที่มีอยู่แล้ว
data "aws_cloudwatch_event_bus" "disaster_bus" {
  name = "report-verify-dev-disaster-event-bus"
}

# สร้าง Rule เพื่อ subscribe ReportVerifiedEvent
resource "aws_cloudwatch_event_rule" "on_verified" {
  name           = "my-service-on-verified"
  event_bus_name = data.aws_cloudwatch_event_bus.disaster_bus.name

  event_pattern = jsonencode({
    source      = ["service.report-verify"]
    detail-type = ["ReportVerifiedEvent"]
  })
}

# Route event ไปที่ Lambda ของคุณ
resource "aws_cloudwatch_event_target" "my_lambda" {
  rule           = aws_cloudwatch_event_rule.on_verified.name
  event_bus_name = data.aws_cloudwatch_event_bus.disaster_bus.name
  arn            = aws_lambda_function.my_handler.arn
}
```

### วิธี Subscribe ด้วย AWS CLI

```bash
# สร้าง Rule
aws events put-rule \
  --name "my-service-on-verified" \
  --event-bus-name "report-verify-dev-disaster-event-bus" \
  --event-pattern '{"source":["service.report-verify"],"detail-type":["ReportVerifiedEvent"]}' \
  --region us-east-1

# เพิ่ม Target (Lambda ARN ของคุณ)
aws events put-targets \
  --rule "my-service-on-verified" \
  --event-bus-name "report-verify-dev-disaster-event-bus" \
  --targets "Id=MyLambda,Arn=arn:aws:lambda:us-east-1:035136704221:function:YOUR-FUNCTION-NAME" \
  --region us-east-1
```

---

## ตัวอย่าง Flow สมบูรณ์ (End-to-End)

```bash
# 1. ตรวจสอบระบบ
curl "${API_URL}/health"

# 2. ส่งรายงานเข้าระบบ
RESPONSE=$(curl -s -X POST "${API_URL}/reports" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${API_KEY}" \
  -d '{
    "reporter_source": "OFFICIAL_APP",
    "reporter_id": "user-test-001",
    "raw_content": "อุบัติเหตุรถชนกัน 5 คัน ถนนวิภาวดี กม.15",
    "geo_location": {"lat": 13.8456, "lon": 100.5650},
    "timestamp": "2026-03-09T10:00:00Z"
  }')
echo "$RESPONSE"
REPORT_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['report_id'])")

# 3. รอ AI ประมวลผล (~10-20 วินาที)
sleep 15

# 4. ดูรายละเอียดผลวิเคราะห์
curl -s "${API_URL}/reports/${REPORT_ID}" | python3 -m json.tool

# 5. ดูรายงาน PENDING ทั้งหมด
curl -s "${API_URL}/reports?status=PENDING_REVIEW"

# 6. ยืนยันรายงาน (triggers EventBridge → Incident Service)
curl -X PATCH "${API_URL}/reports/${REPORT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "validation_status": "VERIFIED",
    "reviewer_id": "officer_demo",
    "reviewer_notes": "ตรวจสอบแล้ว อุบัติเหตุจริง"
  }'

# 7. ดูสถิติ
curl -s "${API_URL}/reports/stats"

# 8. ดู Audit Trail
curl -s "${API_URL}/reports/audit?report_id=${REPORT_ID}"

# 9. ดู Events ที่ถูก publish
curl -s "${API_URL}/reports/events?type=all"
```

---

## Error Codes

| HTTP Code | ความหมาย |
|-----------|----------|
| `200` | สำเร็จ |
| `202` | รับแล้ว (กำลังประมวลผล Async) |
| `400` | ข้อมูลไม่ถูกต้อง |
| `403` | ไม่มีสิทธิ์ (API Key ผิด) |
| `404` | ไม่พบข้อมูล |
| `409` | ขัดแย้ง (รายงานถูกจัดการไปแล้ว) |
| `429` | เกิน Rate Limit (50 req/s) |
| `500` | ระบบขัดข้อง |

---

## การใช้งานผ่าน Dashboard (GUI)

1. เปิด Dashboard URL ในเบราว์เซอร์
2. ใส่ Base URL + API Key ในแท็บ **Config**
3. ใช้แท็บต่าง ๆ ทดลองเรียก API ได้ทันที:
   - **POST /reports** — ส่งรายงาน
   - **GET /reports** — ดูรายชื่อ
   - **PATCH** — ยืนยัน/ปฏิเสธ
   - **Stats** — ดูสถิติ + trending keywords
   - **Audit** — ดูประวัติการเปลี่ยนแปลง
   - **Events** — ดู EventBridge events
   - **Media Upload** — อัปโหลดไฟล์หลักฐาน
