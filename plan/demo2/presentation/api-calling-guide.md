# API Calling Guide — Step-by-Step Demo

> **สำหรับ Demo 2 — 20 เมษายน 2026**  
> เอกสารนี้แยกการเรียก API แต่ละ endpoint อย่างชัดเจนพร้อมคำสั่ง curl ที่ copy-paste ได้ทันที

---

## ⚙️ ตั้งค่าตัวแปรก่อนเริ่ม

```bash
# ดึงค่าจาก Terraform
cd terraform/
export API_URL=$(terraform output -raw api_url)
export API_KEY=$(terraform output -raw api_key)

# หรือ set manual
export API_URL="https://d8a7ds12a2.execute-api.us-east-1.amazonaws.com/dev/v1"
export API_KEY="Hk3gkvihdf5scu0ZPJKGn1EsvX74Ny2m5gKDTxDe"

# ทดสอบว่า set ถูกต้อง
echo "URL: $API_URL"
echo "KEY: $API_KEY"
```

---

## 1. Health Check

**ทดสอบว่าระบบทำงานได้ครบทุก component**

```bash
curl -s "$API_URL/health" | python3 -m json.tool
```

**ดู X-Trace-Id header ด้วย:**
```bash
curl -v "$API_URL/health" 2>&1 | grep -i "x-trace-id"
```

**Expected:** status = "healthy", components ทุกตัว healthy  
**ถ้า degraded:** Gemini หรือ EventBridge มีปัญหา (ไม่กระทบหลัก)  
**ถ้า unhealthy (503):** DynamoDB หรือ SQS ล้ม

---

## 2. Submit Report (สร้าง report ใหม่)

**ส่ง report ข้อความล้วน:**
```bash
curl -s -X POST "$API_URL/reports" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reporter_source": "OFFICIAL_APP",
    "reporter_id": "demo-user-001",
    "raw_content": "ไฟไหม้ตลาดสดเยาวราช ควันดำเยอะมาก",
    "geo_location": { "lat": 13.7410, "lon": 100.5130 },
    "timestamp": "2026-04-20T10:00:00+07:00"
  }' | python3 -m json.tool
```

**ตัวอย่างจาก source อื่น ๆ:**

```bash
# จาก IOT Sensor (เซนเซอร์น้ำท่วม)
curl -s -X POST "$API_URL/reports" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reporter_source": "IOT_SENSOR",
    "reporter_id": "sensor-flood-bkk-001",
    "raw_content": "Water level exceeded threshold: 35cm. Alert triggered.",
    "geo_location": { "lat": 13.7200, "lon": 100.5850 }
  }' | python3 -m json.tool

# จาก Twitter
curl -s -X POST "$API_URL/reports" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reporter_source": "TWITTER",
    "reporter_id": "@emergency_bkk",
    "source_external_id": "tweet-1234567890",
    "raw_content": "#BKKFire ไฟไหม้ร้านทอง เยาวราช ตอนนี้เลย! ควันดำลอยมาเห็นจากไกล",
    "geo_location": { "lat": 13.7466, "lon": 100.5391 }
  }' | python3 -m json.tool

# จาก LINE
curl -s -X POST "$API_URL/reports" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reporter_source": "LINE",
    "reporter_id": "U1234567890abcdef",
    "raw_content": "แผ่นดินไหวที่เชียงใหม่ รู้สึกชัด ๆ",
    "geo_location": { "lat": 18.7883, "lon": 98.9853 }
  }' | python3 -m json.tool

# จาก Facebook
curl -s -X POST "$API_URL/reports" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reporter_source": "FACEBOOK",
    "reporter_id": "fb_user_12345",
    "source_external_id": "post_98765432",
    "raw_content": "พายุถล่มหนัก ต้นไม้ล้มขวางถนน สุขุมวิท 63",
    "geo_location": { "lat": 13.7308, "lon": 100.5827 }
  }' | python3 -m json.tool
```

**เก็บ report_id ไว้ใช้:**
```bash
export REPORT_ID=$(curl -s -X POST "$API_URL/reports" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reporter_source": "OFFICIAL_APP",
    "reporter_id": "demo-user-002",
    "raw_content": "น้ำท่วมซอยสุขุมวิท 71 สูงประมาณ 30 ซม.",
    "geo_location": { "lat": 13.7200, "lon": 100.5850 },
    "timestamp": "2026-04-20T10:05:00+07:00"
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['report_id'])")

echo "Created: $REPORT_ID"
```

**Expected:** HTTP 202, ได้ report_id กลับมา  
**หมายเหตุ:** AI ประมวลผล async ผ่าน SQS → Worker, รอ ~5-15 วินาทีก่อน GET detail

---

## 3. Upload Media (ส่งรูปภาพ)

### Step 3.1 — ขอ presigned URL
```bash
UPLOAD_RESP=$(curl -s -X POST "$API_URL/reports/upload-url" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "fire_evidence.jpg",
    "content_type": "image/jpeg",
    "file_size_bytes": 102400
  }')

echo "$UPLOAD_RESP" | python3 -m json.tool

# ดึง URL สำหรับ upload
UPLOAD_URL=$(echo "$UPLOAD_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['upload_url'])")
MEDIA_URL=$(echo "$UPLOAD_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['media_url'])")
```

### Step 3.2 — Upload ไฟล์ไป S3
```bash
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: image/jpeg" \
  --data-binary @tests/media/housefire.jpg
```

### Step 3.3 — ส่ง report พร้อม media
```bash
curl -s -X POST "$API_URL/reports" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"reporter_source\": \"OFFICIAL_APP\",
    \"reporter_id\": \"demo-user-003\",
    \"raw_content\": \"ไฟไหม้บ้าน มีภาพหลักฐาน\",
    \"geo_location\": { \"lat\": 13.7466, \"lon\": 100.5391 },
    \"media_urls\": [\"$MEDIA_URL\"]
  }" | python3 -m json.tool
```

---

## 4. List Reports (ดูรายการ report)

**ดู report ที่รอตรวจสอบ:**
```bash
curl -s "$API_URL/reports?status=PENDING_REVIEW&limit=10" | python3 -m json.tool
```

**ดูเฉพาะ high priority:**
```bash
curl -s "$API_URL/reports?status=PENDING_REVIEW&priority=high&limit=5" | python3 -m json.tool
```

**กรองด้วย trust score ขั้นต่ำ:**
```bash
curl -s "$API_URL/reports?status=PENDING_REVIEW&min_trust_score=50&limit=10" | python3 -m json.tool
```

**ดู report ที่ verified แล้ว:**
```bash
curl -s "$API_URL/reports?status=VERIFIED&limit=10" | python3 -m json.tool
```

**ดู SPAM:**
```bash
curl -s "$API_URL/reports?status=SPAM&limit=5" | python3 -m json.tool
```

---

## 5. Get Report Detail (ดูรายละเอียด)

```bash
# ใช้ report_id ที่ได้จากขั้นตอน 2 หรือ 4
curl -s "$API_URL/reports/$REPORT_ID" | python3 -m json.tool
```

**สิ่งที่ควรดู:**
- `status` — สถานะปัจจุบัน (RECEIVED → PENDING_REVIEW หลัง AI วิเคราะห์เสร็จ)
- `analysis.trust_score` — คะแนนจาก Gemini AI (0-100)
- `analysis.ai_reasoning` — เหตุผลจาก AI
- `analysis.suggested_category` — ประเภทเหตุการณ์ (FIRE, FLOOD, etc.)
- `analysis.ai_analysis_tags` — tags จาก AI
- `analysis.potential_duplicates` — report ID ของรายงานที่อาจซ้ำกัน
- `priority` — ระดับความสำคัญ (HIGH, NORMAL)

---

## 6. Verify Report (อนุมัติ/ปฏิเสธ)

### 6.1 Verify (อนุมัติ → สร้าง Incident)
```bash
curl -s -X PATCH "$API_URL/reports/$REPORT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "validation_status": "VERIFIED",
    "reviewer_id": "officer-001",
    "reviewer_notes": "ยืนยันจากกล้อง CCTV ในพื้นที่"
  }' | python3 -m json.tool
```

**Expected:** `action_taken` = "TRIGGER_NEW_INCIDENT"  
→ EventBridge จะ publish `ReportVerifiedEvent`

### 6.2 Reject (ปฏิเสธ)
```bash
curl -s -X PATCH "$API_URL/reports/$REPORT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "validation_status": "REJECTED",
    "reviewer_id": "officer-001",
    "reviewer_notes": "ข้อมูลไม่ตรงกับสถานการณ์จริง"
  }' | python3 -m json.tool
```

### 6.3 Mark as SPAM
```bash
curl -s -X PATCH "$API_URL/reports/$REPORT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "validation_status": "SPAM",
    "reviewer_id": "officer-001",
    "reviewer_notes": "โฆษณา spam"
  }' | python3 -m json.tool
```

### 6.4 Merge เข้า Incident ที่มีอยู่แล้ว
```bash
curl -s -X PATCH "$API_URL/reports/$REPORT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "validation_status": "VERIFIED",
    "reviewer_id": "officer-001",
    "reviewer_notes": "รวมกับ incident เดิม",
    "link_to_incident_id": "inc-existing-001"
  }' | python3 -m json.tool
```

**Expected:** `action_taken` = "MERGED_EXISTING_INCIDENT"

---

## 7. Soft Delete

```bash
curl -s -X DELETE "$API_URL/reports/$REPORT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "deleted_by": "admin-001",
    "reason": "ข้อมูลทดสอบ ลบหลัง demo"
  }' | python3 -m json.tool
```

**หมายเหตุ:** Soft delete เท่านั้น — ข้อมูลยังอยู่ใน DynamoDB แต่ GET จะ return 404

---

## 8. Dashboard Statistics

**วันนี้ ทุกพื้นที่:**
```bash
curl -s "$API_URL/reports/stats?timeframe=today" | python3 -m json.tool
```

**24 ชั่วโมงล่าสุด เฉพาะกรุงเทพ:**
```bash
curl -s "$API_URL/reports/stats?timeframe=last_24h&region=bkk" | python3 -m json.tool
```

**7 วันล่าสุด ภาคเหนือ:**
```bash
curl -s "$API_URL/reports/stats?timeframe=last_7d&region=north" | python3 -m json.tool
```

**สิ่งที่ได้กลับมา:**
- `summary` — จำนวน total, pending, verified, spam
- `trending_keywords` — keyword ยอดนิยม พร้อมจำนวนและ category
- `heatmap_data` — พิกัด GPS ที่มี report เยอะ (สำหรับแสดงแผนที่)
- `supported_regions` — รายชื่อ region ที่ filter ได้ (bkk, central, north, northeast, south)

---

## 9. Audit Logs

**ดู audit log ทั้งหมด:**
```bash
curl -s "$API_URL/reports/audit?limit=20" | python3 -m json.tool
```

**ดูเฉพาะ report ตัวเดียว:**
```bash
curl -s "$API_URL/reports/audit?report_id=$REPORT_ID&limit=10" | python3 -m json.tool
```

---

## 10. EventBridge Events

**ดูทุก event:**
```bash
curl -s "$API_URL/reports/events?type=all&limit=10" | python3 -m json.tool
```

**ดูเฉพาะ verified events:**
```bash
curl -s "$API_URL/reports/events?type=verified&limit=10" | python3 -m json.tool
```

**ดูเฉพาะ status changed:**
```bash
curl -s "$API_URL/reports/events?type=status-changed&limit=10" | python3 -m json.tool
```

---

## 11. Changelog (RSS)

```bash
curl -s "$API_URL/changelog.xml"
```

**Content-Type:** `application/rss+xml; charset=utf-8`

---

## 12. Deprecation Info (NEW)

**ดู endpoint ที่ deprecated หรือจะ sunset:**
```bash
curl -s "$API_URL/deprecation-info" | python3 -m json.tool
```

**สิ่งที่ได้:**
- `active_deprecations` — endpoint ที่ deprecated แต่ยังใช้ได้
- `sunset_endpoints` — endpoint ที่ปิดแล้ว
- Headers ที่เกี่ยวข้อง: `X-Deprecated-Version`, `X-Sunset-Date`

---

## 13. Trace Lookup (NEW)

**ค้นหา request ใน CloudWatch Logs ด้วย traceId:**

```bash
# Step 1: เรียก API ใดก็ได้ แล้วเก็บ traceId
TRACE_ID=$(curl -s "$API_URL/health" | python3 -c "import json,sys; print(json.load(sys.stdin).get('traceId',''))")
echo "Trace ID: $TRACE_ID"

# Step 2: ค้นหาด้วย trace endpoint
curl -s "$API_URL/reports/trace/$TRACE_ID" | python3 -m json.tool
```

**สิ่งที่ได้:**
- `results` — log entries จากทุก Lambda function ที่เจอ traceId นี้
- `cloudwatch_insights_query` — query สำหรับ copy ไปใช้ใน AWS Console
- `how_to_trace` — ขั้นตอนการ trace แบบ step-by-step

---

## 🔄 Demo Flow แนะนำ (End-to-End)

ลำดับการ demo ที่แนะนำเพื่อแสดงให้เห็น flow ทั้งระบบ:

```bash
# 1. ตรวจสอบระบบ
curl -s "$API_URL/health" | python3 -m json.tool

# 2. ส่ง report ใหม่
REPORT_ID=$(curl -s -X POST "$API_URL/reports" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reporter_source": "OFFICIAL_APP",
    "reporter_id": "demo-presenter",
    "raw_content": "ไฟไหม้อาคารพาณิชย์ ซอยเจริญกรุง ควันดำหนาแน่น",
    "geo_location": { "lat": 13.7280, "lon": 100.5140 }
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['report_id'])")
echo "Created: $REPORT_ID"

# 3. รอ AI วิเคราะห์ (~10 วินาที)
echo "Waiting for AI analysis..."
sleep 15

# 4. ดูผลลัพธ์ AI
curl -s "$API_URL/reports/$REPORT_ID" | python3 -m json.tool

# 5. ดูรายการ pending
curl -s "$API_URL/reports?status=PENDING_REVIEW&limit=5" | python3 -m json.tool

# 6. อนุมัติ report
curl -s -X PATCH "$API_URL/reports/$REPORT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "validation_status": "VERIFIED",
    "reviewer_id": "demo-officer",
    "reviewer_notes": "Live demo verification"
  }' | python3 -m json.tool

# 7. ดู EventBridge event
curl -s "$API_URL/reports/events?type=verified&limit=3" | python3 -m json.tool

# 8. ดู audit trail
curl -s "$API_URL/reports/audit?report_id=$REPORT_ID&limit=5" | python3 -m json.tool

# 9. ดู stats
curl -s "$API_URL/reports/stats?timeframe=today&region=bkk" | python3 -m json.tool

# 10. Trace request (ใช้ traceId จาก PATCH response)
TRACE_ID=$(curl -s -X PATCH "$API_URL/reports/$REPORT_ID" \
  -H "Content-Type: application/json" \
  -d '{"validation_status":"VERIFIED","reviewer_id":"demo-officer"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin).get('traceId',''))")
curl -s "$API_URL/reports/trace/$TRACE_ID" | python3 -m json.tool
```

---

## ⚠️ Error Scenarios สำหรับ Demo

**Invalid JSON:**
```bash
curl -s -X POST "$API_URL/reports" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d 'not valid json'
```
→ Expected: 400 + errorCode: E400

**Missing API Key:**
```bash
curl -s -X POST "$API_URL/reports" \
  -H "Content-Type: application/json" \
  -d '{"reporter_source":"test","reporter_id":"x","raw_content":"test"}'
```
→ Expected: 403 Forbidden

**Report Not Found:**
```bash
curl -s "$API_URL/reports/r-nonexistent-id"
```
→ Expected: 404 + errorCode: E404

**Invalid Status Transition (Optimistic Locking):**
```bash
# ลอง verify report ที่เป็น SPAM แล้ว
curl -s -X PATCH "$API_URL/reports/$REPORT_ID" \
  -H "Content-Type: application/json" \
  -d '{"validation_status":"VERIFIED","reviewer_id":"test"}'
```
→ Expected: 409 Conflict + errorCode: E409

---

## 📌 หมายเหตุสำคัญ

| หัวข้อ | รายละเอียด |
|--------|------------|
| **API Key** | ต้องใช้เฉพาะ POST /reports และ POST /reports/upload-url |
| **X-Trace-Id** | ทุก response มี header นี้ ใช้ trace ใน CloudWatch |
| **traceId** | Error responses, PATCH, health endpoint มี field นี้ (เหมือน X-Trace-Id) |
| **reporter_source** | ต้องเป็น OFFICIAL_APP, TWITTER, FACEBOOK, LINE, หรือ IOT_SENSOR เท่านั้น |
| **errorCode** | ทุก error response มี E400, E401, E403, E404, E409, E429, E500 |
| **AI Processing** | async ผ่าน SQS, ใช้เวลา ~5-15 วินาทีหลัง POST |
| **Dedup** | Worker ตรวจ report ซ้ำใกล้เคียง (radius 200m, time window 15 นาที) |
| **Soft Delete** | DELETE ไม่ลบจริง, เปลี่ยน status เป็น DELETED |
| **Optimistic Lock** | PATCH ใช้ ConditionExpression ป้องกัน race condition |
