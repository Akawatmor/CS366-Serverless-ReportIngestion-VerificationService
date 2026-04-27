# fixed-doc.md — รายการสิ่งที่ต้องแก้ไขใน Template Service Purposal.htm

> เอกสารนี้สรุปความคลาดเคลื่อน (Discrepancy) ระหว่างเนื้อหาใน `Template Service Purposal.htm`  
> กับโค้ดและ Infrastructure ที่ถูก Implement จริงในโปรเจกต์ (ตรวจสอบ ณ วันที่ 22 เมษายน 2026)

---

## 1. ชื่อไฟล์และ Title — Typo (Purposal → Proposal)

| ตำแหน่ง | ค่าในเอกสาร | ค่าที่ถูกต้อง |
|---|---|---|
| ชื่อไฟล์ | `Template Service Purposal.htm` | `Template Service Proposal.htm` |
| `<title>` tag | — | — |
| หน้าปก | — | — |

**สิ่งที่ต้องแก้**: เปลี่ยนคำว่า "Purposal" เป็น "Proposal" ทุกที่ที่ปรากฏ

---

## 2. Gemini Model Chain — ข้อมูลไม่สม่ำเสมอและไม่ครบ

**ปัญหา**: เอกสารระบุชื่อโมเดลต่างกันในแต่ละส่วน และไม่ตรงกับ Config จริง

| ส่วนของเอกสาร | ค่าในเอกสาร |
|---|---|
| Service Purpose (ย่อหน้า 2) | `gemini-2.5-flash` หรือ `gemini-2.5-flash-lite` หรือ `gemini-2.0-flash` |
| API Contract #7 (Health Check) | `gemini-2.5-flash` หรือ `flash-lite` หรือ `gemini-2.0-flash` |

**ค่าจริงใน `src/config.py` และ `terraform/terraform.tfvars`**:
```
Default model   : gemini-2.5-flash-lite
Fallback chain  : gemini-2.5-flash-lite → gemini-2.0-flash → gemini-3.1-flash-lite
```

**สิ่งที่ต้องแก้**: ระบุ Default Model และ Fallback Chain อย่างชัดเจนในทุกส่วนที่กล่าวถึง โมเดลที่ใช้งานจริงลำดับคือ `gemini-2.5-flash-lite` (Default) → `gemini-2.0-flash` (Fallback 1) → `gemini-3.1-flash-lite` (Fallback 2)

---

## 3. Source Platform Enum ใน Data Schema — ค่าผิด

**ส่วนที่มีปัญหา**: ส่วน "Service Data > 1. Reports Data" (ตาราง field schema) ตัวอย่างค่าในคอลัมน์ Example

| ค่าในเอกสาร | ค่าที่ถูกต้อง (จาก `src/models/enums.py`) |
|---|---|
| `LINE_OFFICIAL` | `LINE` |
| `MOBILE_APP` | `OFFICIAL_APP` |

**Enum จริงใน `SourcePlatform`**: `TWITTER`, `FACEBOOK`, `LINE`, `OFFICIAL_APP`, `IOT_SENSOR`

**สิ่งที่ต้องแก้**: อัปเดตตาราง field schema และทุกที่ที่แสดงตัวอย่าง Enum ของ `source_platform`

---

## 4. Trust Score — ไม่ได้อธิบาย Composite Scoring ที่ใช้จริง

**ปัญหา**: เอกสารระบุว่า Gemini AI ทำ "Trust Scoring" โดยตรง แต่ implementation จริงใน `src/services/gemini_service.py` คือ Gemini ประเมินเพียง **content_score (0–30)** เท่านั้น แล้ว Python รวมคะแนนจากหลายส่วน:

| Component | แหล่งคำนวณ | คะแนนสูงสุด |
|---|---|---|
| `content_score` | Google Gemini AI | 0–30 |
| `source_score` | Source platform rule (config) | 0–20 |
| `history_score` | Reporter history (DynamoDB) | 0–15 |
| `image_score` | Gemini Vision (ถ้ามีรูป) | −10 ถึง +20 |

**สิ่งที่ต้องแก้**: เพิ่มอธิบาย Composite Trust Score Breakdown ในส่วน "6. Autonomy / Decision Logic" และ "Service Architecture > Explanation"

---

## 5. API Endpoints ที่ขาดหายจาก Synchronous Function Contract

เอกสารระบุเพียง 7 API Contract แต่โค้ดจริงใน `src/handlers/api_handler.py` มี Endpoint เพิ่มเติมที่ยังไม่ได้บรรยาย:

| Endpoint | Method | สถานะในเอกสาร | สถานะใน Code |
|---|---|---|---|
| `/v1/changelog.xml` | GET | ✅ กล่าวถึงใน README แต่ **ไม่มี Contract** ใน Proposal | ✅ Implemented |
| `/v1/deprecation-info` | GET | ❌ ไม่มีในเอกสารเลย | ✅ Implemented |
| `/v1/reports/audit` | GET | ❌ ไม่มีในเอกสารเลย | ✅ Implemented |
| `/v1/reports/events` | GET | ❌ ไม่มีในเอกสารเลย | ✅ Implemented |
| `/v1/trace/{trace_id}` | GET | ❌ ไม่มีในเอกสารเลย | ✅ Implemented |
| `/v1/reports/upload-url` | POST | ❌ ไม่มีในเอกสารเลย | ✅ Implemented |

**สิ่งที่ต้องแก้**: เพิ่ม API Contract สำหรับ Endpoint ข้างต้นทั้งหมด หรืออย่างน้อยระบุในตาราง Endpoint Summary

---

## 6. `priority` Query Parameter ใน GET /reports — ไม่ได้ระบุใน Contract #2

**ปัญหา**: README.md ระบุชัดว่า `GET /v1/reports?priority=all|high|normal` แต่ API Contract #2 (List Pending Reports) ไม่ได้กล่าวถึง parameter `priority` เลย

**สิ่งที่ต้องแก้**: เพิ่ม `priority` (Optional: `all` | `high` | `normal`) ใน Path/Query Parameters ของ API Contract #2

---

## 7. Region Filter ใน GET /reports/stats — ระบุว่าไม่ Implement แต่จริงๆ ทำแล้ว

**ปัญหา**: API Contract #5 ระบุว่า:
> "มีการรับ Parameter นี้ไว้ แต่ปัจจุบันยังไม่ได้ Implement ระบบกรองตามพื้นที่จริง"

**แต่ใน `src/handlers/api_handler.py`** มี `REGION_BOUNDARIES` dict ครบทั้ง 5 region (bkk, central, north, northeast, south) และ Logic การกรองตาม lat/lon ถูก Implement จริงแล้ว

**สิ่งที่ต้องแก้**: ลบข้อความ "(หมายเหตุ: ยังไม่ได้ Implement)" และอัปเดตเป็น Region ที่รองรับ: `bkk` | `central` | `north` | `northeast` | `south`

---

## 8. Reverse Geocoding — ระบุว่าไม่รองรับ แต่จริงๆ มีแล้ว

**ปัญหา**: ใน ReportVerifiedEvent Contract ระบุว่า:
> "ไม่รวม address_text เนื่องจากระบบยังไม่รองรับ Reverse Geocoding"

**แต่** โปรเจกต์มี `src/services/geocoding_service.py` ที่ Implement `ReverseGeocodingService` แบบเต็มรูปแบบ รองรับ provider Nominatim และมี caching

**สิ่งที่ต้องแก้**: อัปเดต comment ใน Message Contract #1 ให้ระบุว่า Reverse Geocoding รองรับแล้ว (ขึ้นอยู่กับ `REVERSE_GEOCODING_ENABLED` config)

---

## 9. `schemaVersion` Field ขาดหายจาก Event Contracts

**ปัญหา**: ทั้ง `ReportVerifiedEvent` และ `ReportStatusChangedEvent` ใน `src/services/event_publisher.py` ส่ง field `schemaVersion: "1.0"` ออกไปด้วย แต่เอกสารไม่ได้ระบุ field นี้ในตาราง Field Definition

**สิ่งที่ต้องแก้**: เพิ่ม field `schemaVersion` (String, Required, "ค่าปัจจุบัน: 1.0") ในตาราง Field Definition ของทั้งสอง Message Contract

---

## 10. Event Bus Name และ SQS Queue Name — ไม่ตรงกับที่ Deploy จริง

| ส่วนในเอกสาร | ชื่อในเอกสาร | ชื่อจริงจาก Terraform (prefix = report-verify-dev) |
|---|---|---|
| Dependency Mapping (EventBridge) | `disaster.event.bus.v1` | `report-verify-dev-disaster-event-bus` |
| Dependency Mapping (SQS) | `report.ingestion.queue.v1` | `report-verify-dev-ingestion-queue` |
| Async Contract Header | `disaster-event-bus` | `report-verify-dev-disaster-event-bus` |

**สิ่งที่ต้องแก้**: แก้ชื่อตามที่ Terraform กำหนด หรืออธิบายว่าชื่อจริงคือ `{project_name}-{environment}-disaster-event-bus` และ `{project_name}-{environment}-ingestion-queue`

---

## 11. IncidentType Enum — ขาด 3 ค่า

**ปัญหา**: ตาราง Field Definition ใน Message Contract #1 ระบุ Enum สำหรับ `suggested_incident_data.type` ไว้ 4 ค่า: `FIRE`, `FLOOD`, `EARTHQUAKE`, `ACCIDENT`

**แต่ใน `src/models/enums.py`** มี `IncidentType` ครบ 7 ค่า: `FIRE`, `FLOOD`, `EARTHQUAKE`, `ACCIDENT`, **`SOS`**, **`DAMAGE`**, **`OTHER`**

**สิ่งที่ต้องแก้**: อัปเดต Enum list ใน Field Definition ให้ครบทั้ง 7 ค่า

---

## 12. Health Check Response — ชื่อ DynamoDB Table ผิด

**ปัญหา**: ตัวอย่าง Response ของ API Contract #7 แสดง:
```json
"dynamodb": { "table": "DisasterReports" }
```

**แต่** ชื่อ Table จริงจาก `src/config.py` คือ `report-verify-reports` (กำหนดโดย `REPORTS_TABLE` env var)

**สิ่งที่ต้องแก้**: อัปเดตตัวอย่าง Response ให้ใช้ชื่อ Table ที่ถูกต้อง

---

## 13. `sentiment_score` — Field ที่ไม่มีในโค้ด

**ปัญหา**: ส่วน "7. Owned Data > analysis_result" กล่าวถึง field `sentiment_score` แต่ใน `src/services/gemini_service.py` และ `src/models/report.py` ไม่มี field นี้ในผลลัพธ์จาก Gemini หรือใน data model

**สิ่งที่ต้องแก้**: ลบ `sentiment_score` ออกจากรายการ fields ใน analysis_result หรือ mark ว่าเป็น Planned (Future Enhancement)

---

## 14. Outbox Pattern Retry — ระบุว่า Implement แต่ยังเป็นแค่ TODO

**ปัญหา**: ส่วน "Dependency Mapping > Amazon EventBridge" ระบุว่า:
> "มีระบบ Scheduled Retry Task ที่จะคอยกวาด Event ที่ส่งไม่ผ่านใน Database เพื่อทำการส่งใหม่"

**แต่ใน `src/services/event_publisher.py`** log message ระบุว่า `"Failed to publish event — consider Outbox pattern retry"` ซึ่งหมายความว่า Outbox Pattern ยังไม่ได้ Implement จริง มีเพียง Error Log เท่านั้น

**สิ่งที่ต้องแก้**: แก้เป็น "วางแผนใช้ Outbox Pattern (Future Enhancement)" และระบุว่า Current Behavior เป็น Error Logging เท่านั้น

---

## สรุปจำนวน Issues

| ระดับความรุนแรง | จำนวน |
|---|---|
| 🔴 ข้อมูลผิดพลาด (Incorrect) | 6 (Issues #3, #6, #7, #8, #11, #12) |
| 🟡 ข้อมูลไม่ครบ (Incomplete) | 6 (Issues #4, #5, #9, #10, #13, #14) |
| 🟢 Typo / Formatting | 2 (Issues #1, #2) |
| **รวม** | **14 issues** |
