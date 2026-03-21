# Slides Outline — Demo 1

> จำนวนสไลด์แนะนำ: 12-15 หน้า | เวลา: ~10-12 นาที (เพื่อเหลือเวลา Demo + Q&A)

---

## Slide 1: Title Slide
**หัวข้อ**: Report Ingestion & Verification Service  
**รอง**: Serverless Disaster Response Microservice  
**ข้อมูล**: ชื่อนักศึกษา, รหัส, CS366 Serverless Computing  

---

## Slide 2: Pain Point — ปัญหาที่แก้ไข
**เนื้อหา**:
- ในสถานการณ์ภัยพิบัติ ข้อมูลหลั่งไหลเข้ามามหาศาล (High Throughput)
- 80%+ เป็นข้อมูลซ้ำ / ข่าวปลอม / Spam
- เจ้าหน้าที่ไม่สามารถคัดกรองทันด้วยมือ
- ข้อมูลจากหลายแหล่งไม่มีโครงสร้างเดียวกัน

**Visual**: ภาพแสดง bottleneck — ข้อมูลจาก Twitter, LINE, App หลายทาง → เจ้าหน้าที่คนเดียว

---

## Slide 3: Solution Overview — ภาพรวมระบบ
**เนื้อหา**:
- Serverless Microservice บน AWS
- รับข้อมูลดิบ → AI วิเคราะห์อัตโนมัติ → เจ้าหน้าที่ยืนยัน → ส่งต่อ Incident Service
- AI ช่วยคัดกรอง: Trust Score < 30% → SPAM อัตโนมัติ, ตำแหน่งซ้ำ → DUPLICATE

**Visual**: Architecture Diagram แบบง่าย
```
Client → API Gateway → Lambda (Ingest) → SQS → Lambda (Worker) → DynamoDB
                                                    ↓
                                              Gemini AI (Trust Score)
                                                    ↓
                                              EventBridge → Incident Service
```

---

## Slide 4: Architecture — Tech Stack Detail
**เนื้อหา**:

| Component | Service | หน้าที่ |
|-----------|---------|---------|
| API Gateway | REST API + Usage Plan | Rate Limit, API Key Auth |
| Lambda ×4 | Python 3.12 | Ingest, Worker, API, Health |
| DynamoDB ×3 | Reports + Audit + Stats | NoSQL Storage |
| SQS + DLQ | Standard Queue | Async Decouple |
| EventBridge | Custom Bus | Async Events |
| Gemini AI | External API | Trust Scoring |
| Terraform | IaC | Reproducible Deployment |

---

## Slide 5: API Contracts — ฟังก์ชัน Synchronous (7 Contracts)
**เนื้อหา**:

| # | Method | Path | หน้าที่ |
|---|--------|------|---------|
| 1 | POST | /reports | รับข้อมูลดิบ → 202 Accepted |
| 2 | GET | /reports | ดึงรายการรายงาน (Filter, Pagination) |
| 3 | **PATCH** | **/reports/{id}** | **Verify/Reject (Demo!)** |
| 4 | GET | /reports/{id} | รายละเอียดเชิงลึก + AI Analysis |
| 5 | GET | /reports/stats | Dashboard สรุปสถิติ |
| 6 | DELETE | /reports/{id} | Soft Delete + Audit |
| 7 | GET | /health | Deep Health Check |

**เน้น**: Contract #3 (Verify) — จะ Demo ให้ดู

---

## Slide 6: API Contracts — ฟังก์ชัน Asynchronous (2 Message Contracts)
**เนื้อหา**:

| # | Event Name | Channel | Consumer |
|---|-----------|---------|----------|
| 1 | **ReportVerifiedEvent** | EventBridge | Incident Service **(Mock)** |
| 2 | ReportStatusChangedEvent | EventBridge | Dashboard, Notification |

**เน้น**: Message Contract #1 → เรียกใช้ Service ของเพื่อน (Incident) แต่ตอนนี้ใช้ Mock

**Visual**: Flow diagram: PATCH Verify → 200 OK → (background) EventBridge → Incident Service

---

## Slide 7: Autonomy — Decision Logic ที่ AI ตัดสินใจเอง
**เนื้อหา**:

```
ข้อมูลเข้า → Gemini AI วิเคราะห์
  ├── Trust Score < 30% → SPAM (อัตโนมัติ)
  ├── ตำแหน่ง/เวลาซ้ำ (200m, 15min) → DUPLICATE (อัตโนมัติ)
  └── Trust Score ≥ 30% + ไม่ซ้ำ → PENDING_REVIEW (รอเจ้าหน้าที่)
```

- AI ใช้ Gemini 2.5-flash-lite → fallback 2.0-flash → 3.1-flash-lite
- Multi-key rotation (2 API keys) ป้องกัน rate limit
- Dedup ใช้ Haversine Formula คำนวณระยะจาก GPS

---

## Slide 8: Demo — Synchronous Function (Contract #3: Verify Report)

> **🔴 LIVE DEMO**

**สิ่งที่จะแสดง**:
1. เปิด Dashboard → เห็นรายงานสถานะ PENDING_REVIEW
2. เลือกรายงาน → ดูผล AI (Trust Score, Category, Reasoning)
3. กด Verify → PATCH request → สถานะเปลี่ยนเป็น VERIFIED
4. ดู Response: `action_taken: TRIGGER_NEW_INCIDENT`
5. อธิบาย Optimistic Locking (ConditionExpression)

**ผล**: สถานะเปลี่ยน Atomic + Audit Log ถูกบันทึก + EventBridge Event ถูก publish

---

## Slide 9: Demo — Asynchronous Function (Contract #1: Submit Report → SQS → Worker)

> **🔴 LIVE DEMO**

**สิ่งที่จะแสดง**:
1. ส่ง POST /reports ด้วยข้อมูลภัยพิบัติ
2. ได้ 202 Accepted ทันที (< 500ms) → `report_id`
3. รอ ~5-10 วินาที (SQS → Worker → Gemini AI)
4. GET /reports/{id} → เห็นผล AI วิเคราะห์:
   - `trust_score: 85`
   - `suggested_category: FLOOD`
   - `ai_reasoning: "Detected flooding keywords..."`
   - `validation_status: PENDING_REVIEW`
5. ลองส่งข้อมูล Spam → ได้ trust_score < 30 → สถานะ SPAM อัตโนมัติ

**ผล**: ระบบ decouple สมบูรณ์ — API ตอบเร็ว, AI ทำงานเบื้องหลัง

---

## Slide 10: Mock Integration — เรียก Service ของเพื่อน
**เนื้อหา**:
- เมื่อ Verify → publish `ReportVerifiedEvent` ไปยัง EventBridge
- Incident Service (ของเพื่อน) จะรับ event นี้ไปสร้าง Incident
- ตอนนี้ใช้ Mock — event ถูก publish จริงบน EventBridge แต่ยังไม่มี Consumer
- Ready to integrate: แค่เพื่อนสร้าง EventBridge Rule + Target

**Visual**: แสดง JSON payload ของ ReportVerifiedEvent

---

## Slide 11: STAR Summary — ผลลัพธ์
**เนื้อหา**:

| STAR | รายละเอียด |
|------|-----------|
| **S**ituation | ภัยพิบัติ → ข้อมูลมหาศาล เจ้าหน้าที่คัดกรองไม่ทัน |
| **T**ask | สร้าง Serverless Service รับ-วิเคราะห์-ยืนยัน ข้อมูลภัยพิบัติ |
| **A**ction | 7 Sync APIs + 2 Async Events, Gemini AI, Terraform IaC, 107 Tests |
| **R**esult | ระบบทำงานบน AWS จริง, AI คัดกรอง SPAM/DUPLICATE อัตโนมัติ, ลดภาระเจ้าหน้าที่ |

---

## Slide 12: Testing & Quality
**เนื้อหา**:

| Layer | จำนวน | ครอบคลุม |
|-------|-------|---------|
| Unit Tests | 69 | Validators, Handlers, Gemini Service, Dedup |
| Integration Tests | 13 | DynamoDB CRUD, SQS Flow, EventBridge |
| E2E Tests | 25 | Live API (CORS, Contracts, Flows) |
| **Total** | **107** | **100% Passed** |

- ใช้ `pytest` + `moto` (AWS mock) + `httpx` (HTTP client)  
- E2E ทดสอบกับ AWS จริง (ไม่ใช่ mock)

---

## Slide 13: ปรับปรุงในอนาคต (Improvement / Feedback)
**เนื้อหา**:
1. **Priority Queue**: ใช้ `TRUST_HIGH_PRIORITY=80` จัดลำดับ urgent reports
2. **RBAC**: Role-based access control (Admin vs Officer)
3. **Region Filter**: กรองตามพื้นที่ใน Stats endpoint
4. **Trending Keywords**: วิเคราะห์คำที่ถูกรายงานบ่อย
5. **Heatmap**: แสดง density ของเหตุการณ์บนแผนที่
6. **Reverse Geocoding**: แปลง GPS → ที่อยู่ (address_text)
7. **Consumer Integration**: เชื่อมต่อ Incident Service จริง

---

## Slide 14: ขอบคุณ & Q&A
**เนื้อหา**:
- GitHub: `github.com/Akawatmor/CS366-Serverless-ReportIngestion-VerificationService`
- Live API: `https://s73yua5br2.execute-api.us-east-1.amazonaws.com/dev/v1`
- Dashboard: S3 Static Website
- "ขอบคุณครับ มีคำถามไหมครับ?"
