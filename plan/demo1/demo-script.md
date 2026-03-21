# Demo Script — บทพูด + ขั้นตอน Demo

> เวลารวม: ~12-15 นาที  
> รูปแบบ: สไลด์ 5-6 นาที → Demo 5-6 นาที → Q&A 3-4 นาที

---

## ก่อน Demo: เตรียมตัว (Checklist)

- [ ] เปิด Terminal พร้อม `curl` หรือ Postman/Insomnia/Thunder Client
- [ ] เปิด Browser → Dashboard page
- [ ] ตรวจสอบ API ทำงานอยู่: `curl https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/health`
- [ ] เตรียม JSON payload สำหรับ POST (copy ไว้ใน clipboard)
- [ ] เตรียม report_id ที่เป็น PENDING_REVIEW ไว้ 1 ตัว (สำหรับ Verify demo)
- [ ] เปิด AWS Console → CloudWatch Logs (optional, ถ้าจะแสดง log)

### Pre-created Payloads

**Payload 1 — ข้อมูลภัยพิบัติจริง** (ควรได้ trust_score สูง):
```bash
curl -X POST "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  -d '{
    "reporter_source": "OFFICIAL_APP",
    "reporter_id": "demo_officer_01",
    "raw_content": "น้ำท่วมหนักบริเวณถนนพหลโยธิน ซอย 15 น้ำสูงประมาณ 50 เซนติเมตร รถยนต์ไม่สามารถสัญจรได้ มีประชาชนติดอยู่ในบ้านหลายหลัง ขอความช่วยเหลือด่วน",
    "geo_location": {"lat": 13.8361, "lon": 100.5614},
    "timestamp": "2026-03-07T10:30:00Z"
  }'
```

**Payload 2 — ข้อมูล Spam** (ควรได้ trust_score ต่ำ):
```bash
curl -X POST "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  -d '{
    "reporter_source": "TWITTER",
    "reporter_id": "@random_user_999",
    "raw_content": "lol check out my new mixtape fire fire fire 🔥🔥🔥 click here www.spam-link.com free iphone giveaway",
    "geo_location": {"lat": 0.0, "lon": 0.0}
  }'
```

**Payload 3 — Verify (PATCH)**:
```bash
curl -X PATCH "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports/{REPORT_ID}" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  -d '{
    "validation_status": "VERIFIED",
    "reviewer_id": "officer_demo",
    "reviewer_notes": "ยืนยันแล้วจากกล้อง CCTV และรายงานจากเจ้าหน้าที่ภาคสนาม"
  }'
```

**Payload 4 — List Reports (GET)**:
```bash
# ดูรายงาน PENDING_REVIEW
curl -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports?status=PENDING_REVIEW&limit=10"

# ดูรายงาน VERIFIED
curl -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports?status=VERIFIED&limit=10"

# ดูรายงาน SPAM
curl -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports?status=SPAM&limit=10"
```

**Payload 5 — Get Report Detail (GET)**:
```bash
curl -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports/{REPORT_ID}"
```

**Payload 6 — Soft Delete (DELETE)**:
```bash
curl -X DELETE "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports/{REPORT_ID}" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  -d '{
    "reason": "ข้อมูลทดสอบ ลบออกหลัง demo",
    "deleted_by": "officer_demo"
  }'
```

**Payload 7 — Audit Logs (GET)**:
```bash
# ดู Audit Logs ทั้งหมด
curl -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports/audit?limit=10"

# ดู Audit Log เฉพาะ report หนึ่ง
curl -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports/audit?report_id={REPORT_ID}"
```

**Payload 8 — EventBridge Events (GET)**:
```bash
curl -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports/events?type=all&limit=10"
```

---

## Part 1: สไลด์ (~5-6 นาที)

### Slide 1-2: เปิดเรื่อง + Pain Point (~1 นาที)

> **บทพูด**:  
> "สวัสดีครับ วันนี้ผมจะนำเสนอ Report Ingestion & Verification Service ซึ่งเป็น Serverless Microservice สำหรับระบบจัดการภัยพิบัติครับ"
>
> "ลองนึกภาพว่าเกิดน้ำท่วมใหญ่ในกรุงเทพ — คนหลายพันคนโพสต์ใน Twitter, แจ้งผ่านแอป, ส่งรูปเข้ามา — ข้อมูลเข้ามาเป็นหมื่นต่อชั่วโมง แต่กว่า 80% เป็นข่าวซ้ำ ข่าวปลอม หรือ spam เจ้าหน้าที่ไม่มีทางกรองทันด้วยมือครับ"
>
> "Service นี้จึงทำหน้าที่เป็น Central Gateway ที่ใช้ AI คัดกรองอัตโนมัติ แล้วส่งต่อให้เจ้าหน้าที่ยืนยันเฉพาะรายงานที่น่าเชื่อถือครับ"

### Slide 3-4: Architecture (~1.5 นาที)

> **บทพูด**:  
> "Architecture ของระบบเป็น fully serverless บน AWS ครับ ใช้ API Gateway เป็นทางเข้า, Lambda 4 ตัวทำงานแยกกัน, SQS เป็นตัวกลาง decouple ระหว่าง API กับ Worker"
>
> "เมื่อข้อมูลเข้ามา Lambda ตัวแรกจะ validate แล้วส่งเข้า SQS ทันที ตอบ 202 Accepted กลับภายใน 500ms ส่วน Lambda Worker จะดึงจาก SQS ไปวิเคราะห์กับ Gemini AI แล้วเก็บลง DynamoDB"
>
> "AI จะให้ Trust Score 0-100 ถ้าต่ำกว่า 30 จะเป็น SPAM อัตโนมัติ ถ้าตำแหน่งซ้ำภายใน 200 เมตรและ 15 นาที จะเป็น DUPLICATE ที่เหลือจะเป็น PENDING_REVIEW รอเจ้าหน้าที่ครับ"

### Slide 5-6: API Contracts (~1.5 นาที)

> **บทพูด**:  
> "ระบบมี 7 Synchronous API Contracts และ 2 Asynchronous Message Contracts ครับ"
>
> "วันนี้ผมจะ demo 2 ฟังก์ชันหลัก:"
> - "ฟังก์ชันแรก — **Asynchronous**: POST /reports ส่งข้อมูลเข้า → ระบบ process เบื้องหลังด้วย SQS + Gemini AI"
> - "ฟังก์ชันที่สอง — **Synchronous**: PATCH /reports/{id} ให้เจ้าหน้าที่ verify รายงาน → ระบบเปลี่ยนสถานะ + ส่ง event ไปยัง EventBridge"
>
> "ส่วน EventBridge event ที่ publish ออกไป จะเป็น mock สำหรับ Incident Service ของเพื่อน — event ถูกส่งจริงบน AWS แต่ยังไม่มี consumer ฝั่งปลายทางครับ"

### Slide 7: Decision Logic (~1 นาที)

> **บทพูด**:  
> "สิ่งที่ทำให้ service นี้มี autonomy คือ AI ตัดสินใจได้เองโดยไม่ต้องรอคน — ถ้า trust score ต่ำกว่า 30% ก็ reject เป็น spam เลย ถ้าตำแหน่งและเวลาซ้ำกับรายงานเดิมก็ mark เป็น duplicate"
>
> "Gemini API ใช้ multi-key rotation — มี 2 API keys สลับกัน ถ้า key แรกโดน rate limit ก็เปลี่ยน key ถ้า model ไม่พร้อมก็ fallback ไป model อื่น เพื่อให้ระบบไม่ล่มครับ"

---

## Part 2: Live Demo (~5-6 นาที)

### Demo 2A: Async Function — Submit Report (POST /reports) (~3 นาที)

> **บทพูด**:  
> "มาดู demo กันครับ เริ่มจากฟังก์ชัน Asynchronous — การส่งรายงานเข้าระบบ"

**ขั้นตอน**:

1. **ส่ง POST request** (Payload 1 — ข้อมูลน้ำท่วม):

> "ผมจะส่งรายงานน้ำท่วมเข้าระบบครับ"  
> *(รัน curl Payload 1)*

2. **แสดง Response**:
```json
{
  "status": "QUEUED",
  "report_id": "r-xxxxxxxxxxxx",
  "message": "Report accepted and queued for processing.",
  "estimated_wait_time": "2s"
}
```

> "ได้ 202 Accepted ทันทีครับ ใช้เวลาไม่ถึง 500ms ระบบยังไม่ได้วิเคราะห์ — แค่ validate แล้วส่งเข้า SQS เท่านั้น นี่คือ Fire-and-Forget pattern ครับ"
>
> "ตอนนี้ Lambda Worker กำลัง process อยู่เบื้องหลัง — ดึงจาก SQS → ส่งไป Gemini AI → เขียนลง DynamoDB"

3. **รอ ~10 วินาที** แล้ว GET detail:

> "รอสักครู่ให้ AI วิเคราะห์เสร็จ..."  
> *(รัน `curl -H "X-Api-Key: ..." GET /v1/reports/{report_id}`)*

4. **แสดง AI Analysis Result**:

> "ตอนนี้เห็นผลแล้วครับ — AI ให้ trust_score 85 จาก 100, category เป็น FLOOD, สถานะเปลี่ยนเป็น PENDING_REVIEW รอเจ้าหน้าที่ยืนยัน"
>
> "ลอง note ด้วยว่า ai_reasoning บอกว่า 'Detected flooding keywords, specific location mentioned, urgent tone' — AI อ่านแล้ววิเคราะห์ให้เราเลย"

5. **(ถ้ามีเวลา) ส่ง Spam Payload**:

> "ลองส่งข้อมูล spam เข้าไปดูครับ"  
> *(รัน curl Payload 2)*  
> *(รอ 10 วินาที แล้ว GET)*

> "เห็นไหมครับ trust_score ได้แค่ 12 — ระบบ auto-reject เป็น SPAM เลย ไม่ต้องรอเจ้าหน้าที่มาดู ประหยัดเวลามากครับ"

---

### Demo 2B: Sync Function — Verify Report (PATCH /reports/{id}) (~2.5 นาที)

> **บทพูด**:  
> "ทีนี้มาดูฟังก์ชัน Synchronous — การยืนยันรายงานโดยเจ้าหน้าที่ครับ"

**ขั้นตอน**:

1. **ใช้ report_id ที่เป็น PENDING_REVIEW** (จาก Demo 2A):

> "ผมจะเอา report_id ที่เพิ่งส่งเข้ามาเมื่อกี้ ซึ่งตอนนี้เป็น PENDING_REVIEW มา verify ครับ"
> *(รัน curl Payload 3 — PATCH verify)*

2. **แสดง Response**:
```json
{
  "report_id": "r-xxxxxxxxxxxx",
  "validation_status": "VERIFIED",
  "action_taken": "TRIGGER_NEW_INCIDENT",
  "updated_at": "2026-03-07T10:35:00Z"
}
```

> "ได้ 200 OK ครับ สถานะเปลี่ยนเป็น VERIFIED แล้ว action_taken บอกว่า TRIGGER_NEW_INCIDENT — หมายความว่าระบบได้ publish event ไปยัง EventBridge แล้ว เพื่อให้ Incident Service ของเพื่อนไปสร้าง Incident ต่อ"

3. **อธิบาย Optimistic Locking**:

> "จุดสำคัญคือ — ระบบใช้ ConditionExpression ของ DynamoDB ป้องกัน race condition ครับ สมมติเจ้าหน้าที่ 2 คนกด verify พร้อมกัน คนแรกสำเร็จ คนที่สองจะได้ 409 Conflict"

4. **(Demo ยืนยัน)** ลอง PATCH อีกครั้ง:

> "ลอง verify ซ้ำอีกครั้ง..."  
> *(รัน PATCH เดิมอีกรอบ)*

```json
{
  "error": true,
  "message": "Report with status 'VERIFIED' cannot be updated."
}
```

> "ได้ 409 Conflict ครับ — VERIFIED เป็น Terminal State เปลี่ยนไม่ได้แล้ว ระบบปลอดภัย"

5. **อธิบาย Mock Integration**:

> "ตรงนี้เบื้องหลังระบบได้ publish ReportVerifiedEvent ไปยัง EventBridge ตาม Message Contract #1 แล้วครับ Incident Service ของเพื่อนจะรับ event นี้ไปสร้าง Incident — ตอนนี้ใช้ mock คือ event ถูกส่งจริงบน AWS แต่ยังไม่มี consumer เมื่อเพื่อนพร้อมก็แค่เพิ่ม EventBridge Rule ก็ integrate ได้เลยครับ"

---

### Demo 2C (ถ้ามีเวลา): Health Check + Stats (~1 นาที)

```bash
# Health Check
curl "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/health"

# Dashboard Stats
curl -H "X-Api-Key: bLXlrW1I9f34khMEw1ZZoa7iVvIy1rrH9raK3bcZ" \
  "https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1/reports/stats"
```

> "เสริมอีกนิดครับ — Health Check endpoint ตรวจสอบ DynamoDB, SQS, Gemini, EventBridge ทุกตัว ถ้า component หลักล่มจะเป็น unhealthy, ถ้า component รองล่มจะเป็น degraded"
>
> "ส่วน Stats endpoint ใช้ Atomic Counter — ดึงค่าจาก StatsCounter table ด้วย BatchGetItem ตอบภายไม่กี่ millisecond ไม่ต้อง scan ตาราง reports ทั้งหมด"

---

## Part 3: STAR Summary + ปิด (~1 นาที)

> **บทพูด** (กลับมาที่ Slide 11):
>
> "สรุปตามแนว STAR ครับ:"
>
> "**Situation** — สถานการณ์ภัยพิบัติ ข้อมูลเข้ามาเยอะมาก เจ้าหน้าที่กรองไม่ทัน"
>
> "**Task** — สร้าง Serverless Microservice ที่รับข้อมูลดิบ วิเคราะห์ด้วย AI และให้เจ้าหน้าที่ verify"
>
> "**Action** — พัฒนา 7 REST APIs + 2 Async Events บน AWS Lambda, DynamoDB, SQS, EventBridge ใช้ Gemini AI วิเคราะห์ trust score ทำ IaC ด้วย Terraform และเขียน test 107 ตัว"
>
> "**Result** — ระบบ deploy บน AWS จริง, ทำงานได้ครบ, AI คัดกรอง spam/duplicate อัตโนมัติ ลดภาระเจ้าหน้าที่ได้มาก tests ผ่าน 100% ทั้ง unit, integration และ end-to-end ครับ"

---

## Part 4: Slide สุดท้าย — Q&A

> "สำหรับการปรับปรุงในอนาคต — ยังมี Priority Queue, RBAC, Region Filter, Trending Keywords, Heatmap ที่วางแผนไว้ครับ"
>
> "ขอบคุณครับ มีคำถามไหมครับ?"

---

## Timing Guide

| ช่วง | เวลา | สไลด์ |
|------|------|-------|
| เปิดเรื่อง + Pain Point | 1:00 | 1-2 |
| Architecture | 1:30 | 3-4 |
| API Contracts + Decision | 2:30 | 5-7 |
| Demo: Async (POST + AI) | 3:00 | 8-9 |
| Demo: Sync (PATCH Verify) | 2:30 | 8-9 |
| STAR + Improvement | 1:00 | 11-13 |
| Q&A | 3:00 | 14 |
| **รวม** | **~14:30** | |

---

## Backup Plan — ถ้า Live Demo ล่ม

ถ้า API ไม่ตอบ (AWS Learner Lab หมดเวลา / Lambda cold start นานเกิน):

1. **มี Screenshot/Recording ไว้สำรอง** — ถ่ายภาพหน้าจอ response จาก Postman
2. **Run Unit + Integration Tests ให้ดู** — `python -m pytest tests/unit/ tests/integration/ -v` (ใช้ mock ไม่ต้องต่อ AWS)
3. **เปิด Code ให้ดู** — อธิบาย logic ตรงๆ จาก source code

### Pre-recorded Results (เก็บไว้เผื่อ):
```
# Unit Tests
69 passed in 0.31s ✅

# Integration Tests  
13 passed in 1.50s ✅

# E2E Tests
25 passed (0 failed, 0 skipped) in 120s ✅
```
