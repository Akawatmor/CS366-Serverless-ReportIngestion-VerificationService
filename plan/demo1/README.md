# Demo 1 — Report Ingestion & Verification Service

> วันนำเสนอ: TBD | ผู้นำเสนอ: (ชื่อ) | เวลาประมาณ: 10-15 นาที

---

## 1. สรุปภาพรวม Service

**ชื่อบริการ**: Report Ingestion & Verification Service  
**หน้าที่หลัก**: เป็น Central Gateway รับข้อมูลเหตุภัยพิบัติจากแหล่งภายนอก (Twitter, App, IoT) → AI วิเคราะห์ความน่าเชื่อถือ → เจ้าหน้าที่ Verify → ส่งต่อ Incident Service

**Tech Stack**: AWS Lambda (Python 3.12) + API Gateway + DynamoDB + SQS + EventBridge + Google Gemini AI  
**IaC**: Terraform  
**Tests**: 107 tests ทั้งหมด (Unit 69 + Integration 13 + E2E 25) — ผ่าน 100%

---

## 2. ฟังก์ชันที่จะ Demo (ขั้นต่ำ 2 ฟังก์ชัน — Sync + Async)

### ฟังก์ชันที่ 1: Synchronous — Contract #3: Verify Report (PATCH /reports/{id})
- **ทำไมเลือก**: เป็นหัวใจหลักของระบบ — เจ้าหน้าที่ทำการตัดสินใจ (Human-in-the-loop)
- **แสดงอะไร**: State Machine Transition + Optimistic Locking + Audit Log
- **จุดเด่น**: สถานะเปลี่ยนแบบ Atomic, มี ConditionExpression ป้องกัน Race Condition, เขียน Audit Trail ทุกครั้ง

### ฟังก์ชันที่ 2: Asynchronous — Contract #1 + Worker: Submit Report (POST /reports → SQS → Worker)
- **ทำไมเลือก**: แสดง Async Pattern (Fire-and-Forget + Background Processing) + Gemini AI
- **แสดงอะไร**: POST ตอบ 202 ทันที → SQS Queue → Worker Lambda → Gemini AI วิเคราะห์ → DynamoDB + EventBridge
- **จุดเด่น**: ระบบรับโหลดได้ไม่จำกัด (decouple), AI ให้ Trust Score + Category อัตโนมัติ, Dedup ด้วย Haversine + Time Window

### ฟังก์ชันเสริม (ถ้ามีเวลา): Contract #7: Health Check + Contract #5: Stats
- **Health Check**: Deep check ทุก component (DynamoDB, SQS, Gemini, EventBridge)
- **Stats Dashboard**: Atomic Counter + BatchGetItem — ไม่ Scan ตาราง, ตอบภายใน ms

---

## 3. Mock Function — การเรียก Service ของเพื่อน

เมื่อเจ้าหน้าที่ Verify รายงาน (PATCH → VERIFIED) ระบบจะ publish `ReportVerifiedEvent` ไปยัง **EventBridge** ซึ่งเป็น Async Message ตาม Message Contract #1

**Consumer**: Incident Tracking Service (ของเพื่อน)  
**สถานะ**: ใช้ Mock — event ถูก publish จริงบน EventBridge แต่ยังไม่มี Rule/Target ที่ฝั่ง Consumer

```json
{
  "Source": "service.report-verify",
  "DetailType": "ReportVerifiedEvent",
  "Detail": {
    "report_ref_id": "r-550e8400e29b",
    "suggested_incident_data": {
      "type": "FIRE",
      "description": "ไฟไหม้ร้านค้าตลาดน้อย",
      "severity_level": 3,
      "location": { "lat": 13.746, "lon": 100.539 },
      "reporter_count": 1,
      "media_evidence": ["https://s3.../img1.jpg"]
    },
    "verified_by": "officer_007",
    "verification_notes": "ยืนยันจากกล้อง CCTV"
  }
}
```

---

## 4. ลำดับไฟล์ในโฟลเดอร์นี้

| ไฟล์ | เนื้อหา |
|------|---------|
| [README.md](README.md) | สรุปภาพรวม (ไฟล์นี้) |
| [slides-outline.md](slides-outline.md) | โครงสร้างสไลด์ + เนื้อหาแต่ละหน้า |
| [demo-script.md](demo-script.md) | บทพูด + ขั้นตอน Demo ละเอียด (STAR) |
| [qa-preparation.md](qa-preparation.md) | 15 คำถามที่อาจถูกถาม + คำตอบ |

---

## 5. Demo Endpoints (Live)

| Endpoint | URL |
|----------|-----|
| API Base | `https://s4favly0y4.execute-api.us-east-1.amazonaws.com/dev/v1` |
| Website | `http://report-verify-dev-website-035136704221.s3-website-us-east-1.amazonaws.com` |
| Dashboard | เดียวกัน + `/dashboard/` |
| API Key | `Et5NVu8sSb5omOGpznV4ZaluCUO9YBuP8kEV9ATE` (Header: `X-Api-Key`) |
