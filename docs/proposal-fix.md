# Proposal Fix v2 — ตรวจสอบ Proposal (ฉบับอัปเดต) เทียบกับ Codebase + Learner Lab Limits

> อัปเดตล่าสุด: 2026-03-05
>
> เอกสารฉบับนี้ตรวจสอบ `reportingestion_proposal.txt` (ฉบับอัปเดตแล้ว) เทียบกับ Codebase ที่ Implement จริง **และ** ข้อจำกัดของ AWS Learner Lab
>
> สัญลักษณ์:
> - 🔴 **ผิด/ไม่ตรง** — ต้องแก้ไข
> - 🟡 **ยังขาดรายละเอียด** — ควรเพิ่มเติม
> - 🟢 **ขาดหายไปจาก Proposal** — ต้องเขียนเพิ่ม
> - ✅ **แก้ไขแล้ว** — จากเวอร์ชันก่อนหน้า

---

## ✅ สิ่งที่แก้ไขแล้ว (จาก Proposal v1 → v2)

Proposal ฉบับอัปเดต (v2) ได้แก้ไขปัญหาที่พบในเวอร์ชันก่อนหน้าเกือบทั้งหมด:

| # | ปัญหาเดิม | สถานะ |
|---|-----------|-------|
| 1 | Auth JWT → X-Api-Key ทุก Contract | ✅ แก้ไขแล้ว (Contract #1-#7 ใช้ X-Api-Key ครบ) |
| 2 | Error Format `{success, type, reason}` → `{error, message, detail}` | ✅ แก้ไขแล้วเกือบทั้งหมด (ยกเว้น Contract #3) |
| 3 | Contract #1 คำอธิบาย "ไม่ผ่าน Lambda" | ✅ แก้ไขแล้ว (ระบุ Lambda ingest_handler ชัดเจน) |
| 4 | Contract #1 Dependency ระบุ SQS | ✅ แก้ไขแล้ว |
| 5 | Contract #2 Pagination (last_evaluated_key) | ✅ แก้ไขแล้ว |
| 6 | Contract #2 total_count อธิบายเป็น Current Page Count | ✅ แก้ไขแล้ว |
| 7 | Contract #2 GSI details | ✅ แก้ไขแล้ว (gsi_status_ingested, PK/SK/Projection) |
| 8 | Contract #3 State Transitions | ✅ แก้ไขแล้ว (From → To table) |
| 9 | Contract #3 Optimistic Locking ConditionExpression | ✅ แก้ไขแล้ว |
| 10 | Contract #3 action_taken values | ✅ แก้ไขแล้ว (3 ค่า documented) |
| 11 | Contract #3 EventBridge publish หลัง 200 | ✅ แก้ไขแล้ว |
| 12 | Contract #3 Sequential ไม่ใช่ Transaction | ✅ แก้ไขแล้ว (ระบุ update_item + put_item + put_events) |
| 13 | Contract #3 NEEDS_MORE_INFO ไม่รองรับ | ✅ แก้ไขแล้ว |
| 14 | Contract #4 reporter_id / source_external_id / AI fields | ✅ แก้ไขแล้ว |
| 15 | Contract #4 followers_count/account_age ลบแล้ว | ✅ แก้ไขแล้ว (noted as not supported) |
| 16 | Contract #5 region parameter ยังไม่ implement | ✅ แก้ไขแล้ว (noted) |
| 17 | Contract #5 trending_keywords/heatmap_data planned | ✅ แก้ไขแล้ว (noted as Future Enhancement) |
| 18 | Contract #5 Atomic Counter details | ✅ แก้ไขแล้ว (Key Pattern + Increment + BatchGetItem) |
| 19 | Contract #6 RBAC ยังไม่ implement | ✅ แก้ไขแล้ว (noted) |
| 20 | Contract #6 Copy-paste Validation | ✅ แก้ไขแล้ว (reason/deleted_by) |
| 21 | Contract #6 404 สำหรับ deleted report | ✅ แก้ไขแล้ว (noted in response) |
| 22 | Contract #7 Auth เป็น Public | ✅ แก้ไขแล้ว (None, No Auth) |
| 23 | Contract #7 Response Format ตรง Implementation | ✅ แก้ไขแล้ว (healthy/degraded/unhealthy, components, 4 ตัว) |
| 24 | Contract #7 Deep Health Check details | ✅ แก้ไขแล้ว (DescribeTable, GetQueueAttributes, etc.) |
| 25 | Owned Data validation_status 7 สถานะ | ✅ แก้ไขแล้ว (RECEIVED→DELETED ครบ 7 ค่า) |
| 26 | Owned Data extra fields ครบ | ✅ แก้ไขแล้ว (ai_reasoning, suggested_category, etc.) |
| 27 | StatsCounter Table | ✅ แก้ไขแล้ว (documented in Owned Data) |
| 28 | Audit Log 4 action_types | ✅ แก้ไขแล้ว |
| 29 | Audit Log GSI gsi_report_timestamp | ✅ แก้ไขแล้ว |
| 30 | Message Contract #1 EventBridge Native Fields | ✅ แก้ไขแล้ว (Source, Detail-Type, EventBusName) |
| 31 | Message Contract #1 hardcoded values noted | ✅ แก้ไขแล้ว (severity_level=3, reporter_count=1) |
| 32 | Message Contract #2 SYSTEM_AI uppercase | ✅ แก้ไขแล้ว (noted in example) |
| 33 | Architecture/Dependency/Interaction sections removed | ✅ ถูกลบออก (ลดความซ้ำซ้อน) |
| 34 | BaseURL + CNAME explanation | ✅ แก้ไขแล้ว |
| 35 | Service Data Reports fields ครบ | ✅ แก้ไขแล้ว (ai_analysis_tags, deleted_by, etc.) |

---

## 🔴 สิ่งที่ยังต้องแก้ไข (Critical — ต้องแก้ก่อน Implement)

### 1. Service Purpose (บรรทัดที่ 7) — Amazon Comprehend ❌

> **บรรทัดที่ 7**: "เริ่มต้นจากการใช้ **Amazon Comprehend** เพื่อทำการจำแนกกลุ่มข้อความเบื้องต้น"

- **ปัญหา**: Amazon Comprehend **ใช้ไม่ได้**ใน AWS Learner Lab (ตรวจสอบจาก learnerlab-limit.txt แล้วไม่มีในรายชื่อ Allowed Services)
- **ใน Codebase**: ใช้ **Google Gemini API เพียวๆ** (gemini-2.0-flash) สำหรับทั้ง Text Classification และ Trust Scoring
- **ต้องแก้**: เปลี่ยนจาก "Amazon Comprehend" เป็น "Google Gemini API" ในบรรทัดนี้

**แก้ไขที่แนะนำ**:
```
// AS-IS (บรรทัดที่ 7)
"เริ่มต้นจากการใช้ Amazon Comprehend เพื่อทำการจำแนกกลุ่มข้อความเบื้องต้นให้เป็นหมวดหมู่ที่ชัดเจน"

// TO-BE
"เริ่มต้นจากการใช้ Google Gemini API เพื่อทำการจำแนกกลุ่มข้อความเบื้องต้นให้เป็นหมวดหมู่ที่ชัดเจน"
```

### 2. Contract #3 Error Format (บรรทัดที่ ~275-280) — ยังเป็น Format เก่า ❌

```json
// AS-IS (ยังอยู่ใน Proposal)
{
  "success": False,
  "type": "400",
  "reason": "validate_status is invalid!" 
}

// TO-BE (ควรเปลี่ยนให้ตรงกับ Contract อื่นๆ)
{
  "error": true,
  "message": "Bad Request",
  "detail": "validation_status is invalid!"
}
```

- **ปัญหา**: Contract #1, #2, #4, #5, #6 ใช้ format `{error, message, detail}` แล้ว แต่ Contract #3 ยังใช้ format เก่า `{success, type, reason}`
- **ต้องแก้**: ทำให้ Error format เป็นมาตรฐานเดียวกันทุก Contract

### 3. Gemini Model Version — ไม่ตรงกับ Codebase

> **บรรทัดที่ 8**: "gemini-2.5-flash หรือ gemini-2.5-flash-lite"
> **บรรทัดที่ ~535 (Health Check Contract #7)**: "gemini-2.5-flash หรือ flash-lite"

- **ใน Codebase**: ใช้ `gemini-2.0-flash` (ตั้งค่าผ่าน `GEMINI_MODEL` env variable, default = `gemini-2.0-flash`)
- **ต้องเลือก**: เปลี่ยน Proposal ให้ตรง หรืออัปเดต Code ให้ใช้ 2.5-flash
- **แนะนำ**: ใช้คำว่า "gemini-2.0-flash (ค่าเริ่มต้น, สามารถเปลี่ยนได้ผ่าน Environment Variable)"

---

## 🟡 สิ่งที่ควรเพิ่มเติม (Minor — ไม่กระทบ Functionality)

### 4. Message Contract #2 Field Definition — old_status/new_status ENUM ขาด 2 ค่า

> **Field Definition Table** ใน Message Contract #2 ระบุ:
> - `old_status` Enum: RECEIVED, PENDING_REVIEW, VERIFIED, SPAM, DUPLICATE
> - `new_status` Enum: RECEIVED, PENDING_REVIEW, VERIFIED, SPAM, DUPLICATE

- **ขาด**: `REJECTED` และ `DELETED`
- ระบบมี 7 สถานะ (ระบุไว้ถูกต้องใน Owned Data ข้อ 7) แต่ Field Definition table ไม่ครบ
- **ต้องแก้**: เพิ่ม REJECTED และ DELETED ใน ENUM ของทั้ง old_status และ new_status

### 5. Message Contract #2 changed_by — Lowercase ใน Validation

> **Field Definition Table**: `changed_by` → Validation Rules: "ID ของเจ้าหน้าที่ หรือ **'system_ai'**"
> **ตัวอย่าง Message Body**: `"changed_by": "SYSTEM_AI"` (Uppercase)

- **ไม่ consistent**: ตัวอย่างใช้ Uppercase แต่ Validation Rules เขียน lowercase
- **Implementation**: ใช้ `SYSTEM_AI` (Uppercase)
- **ต้องแก้**: เปลี่ยน Validation Rules เป็น `'SYSTEM_AI'` ให้ตรงกัน

### 6. Service Data Reports — validation_status ENUM ขาด DELETED

> **Service Data ข้อ 1** (Reports Data table): `validation_status` ระบุ ENUM เป็น
> "RECEIVED, PENDING_REVIEW, VERIFIED, SPAM, REJECTED, DUPLICATE"

- **ขาด**: `DELETED` (มี 6 ค่า แทนที่จะเป็น 7 ค่า)
- ในขณะที่ Owned Data ข้อ 7 ระบุครบ 7 ค่ารวม DELETED — แต่ Service Data table ลืม
- **ต้องแก้**: เพิ่ม DELETED ใน ENUM

### 7. Service Data Reports — ai_analysis_tags ซ้ำ

> **Service Data ข้อ 1** มี field `ai_analysis_tags` ปรากฏ **2 ครั้ง** ในตาราง (บรรทัดที่ ~679 และ ~693)

- **ต้องแก้**: ลบ duplicate row ออก 1 รายการ

---

## 🟢 สิ่งที่ยังไม่มีใน Proposal (แต่มีใน Implementation — ไม่จำเป็นต้องเพิ่มทุกข้อ)

> หัวข้อเหล่านี้ไม่ได้ถูกระบุไว้ใน Proposal แต่มีอยู่ใน Codebase จริง
> เป็น "bonus" ที่สามารถเพิ่มเข้า Proposal ได้ถ้าต้องการความสมบูรณ์

### 8. CORS Configuration
- Implementation มี CORS headers ทุก endpoint:
  ```
  Access-Control-Allow-Origin: *
  Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
  Access-Control-Allow-Headers: Content-Type, Authorization, X-Api-Key
  ```
- ทุก endpoint มี OPTIONS method สำหรับ CORS preflight

### 9. Rate Limiting Details
- Proposal ระบุ error 429 Too Many Requests แต่ไม่ได้ระบุ limit เท่าไหร่
- Implementation: API Gateway Usage Plan — **50 requests/second, burst 100**

### 10. Logging Strategy
- Implementation มี Structured JSON Logging ผ่าน CloudWatch:
  ```json
  {"timestamp": "...", "level": "INFO", "name": "module", "message": "...", "data": {...}}
  ```

### 11. Lambda Architecture
- Implementation มี **4 Lambda functions** (Proposal ไม่ได้ระบุจำนวน):
  1. `ingest-handler` — POST /reports → SQS
  2. `ingestion-worker` — SQS → Process → DynamoDB
  3. `api-handler` — GET/PATCH/DELETE /reports
  4. `health-handler` — GET /health
- มี **Lambda Layer** สำหรับ shared dependencies (google-generativeai, etc.)
- มี **Dead Letter Queue (DLQ)** สำหรับ message ที่ fail 3 ครั้ง
- Worker รองรับ **Partial Batch Failure** (return เฉพาะ message ที่ fail)

### 12. Deployment / IaC
- ใช้ **Terraform (~> 5.0)** สำหรับ Infrastructure as Code
- Region: `us-east-1` (Learner Lab default)
- Deploy: `scripts/deploy.sh` (5-step: clean → layer → src → init → apply)

### 13. Testing Strategy
- **Unit Tests**: pytest + mock (4 files)
- **Integration Tests**: moto (3 files)
- **E2E Tests**: httpx (3 files)

### 14. Static Website (/ + /dashboard)
- Proposal ระบุไว้ใน Base URL note: "/ (root domain) สำหรับเป็นเว็บหน้าหลัก" + "/dashboard สำหรับเป็นเว็บให้บริการตัวอย่าง"
- จะ host บน **S3 Static Website Hosting** (S3 เป็น Allowed Service ใน Learner Lab ✅)

---

## 🏫 Learner Lab Compatibility Check

| AWS Service ที่ใช้ | อยู่ใน Learner Lab? | หมายเหตุ |
|-------------------|-------------------|----------|
| Amazon API Gateway | ✅ Yes | REST API + Usage Plan |
| AWS Lambda | ✅ Yes | 4 functions, Python 3.12 |
| Amazon DynamoDB | ✅ Yes | 3 tables + 2 GSIs |
| Amazon SQS | ✅ Yes | Main Queue + DLQ |
| Amazon EventBridge | ✅ Yes | Custom Bus |
| Amazon S3 | ✅ Yes | Static Website Hosting |
| Amazon CloudWatch | ✅ Yes | Logs + Monitoring |
| AWS IAM (LabRole) | ✅ Yes | Pre-configured role |
| **Amazon Comprehend** | **❌ NOT Available** | ⚠️ ต้องลบออกจาก Proposal |
| Google Gemini API | ✅ N/A (External) | ไม่ใช่ AWS — ไม่ถูกจำกัด |

**สรุป**: ทุก AWS Service ที่ใช้ใน Implementation อยู่ใน Learner Lab ✅ **ยกเว้น Amazon Comprehend** ซึ่งต้องลบออกจาก Proposal แล้วใช้ **Gemini เพียวๆ** แทน

---

## สรุป: Priority ในการแก้ไข (เฉพาะสิ่งที่เหลือ)

| Priority | # | หัวข้อ | ประเภท |
|----------|---|-------|-------|
| 🔴 P0 | 1 | Service Purpose — ลบ Amazon Comprehend → ใช้ Gemini เพียว | แก้ไข |
| 🔴 P0 | 2 | Contract #3 Error Format — แก้เป็น `{error, message, detail}` | แก้ไข |
| 🔴 P0 | 3 | Gemini Model Version — 2.5-flash vs 2.0-flash ทำให้ตรงกัน | แก้ไข |
| 🟡 P1 | 4 | Message Contract #2 ENUMs — เพิ่ม REJECTED + DELETED | เพิ่มเติม |
| 🟡 P1 | 5 | Message Contract #2 changed_by — uppercase consistency | เพิ่มเติม |
| 🟡 P1 | 6 | Service Data validation_status — เพิ่ม DELETED | เพิ่มเติม |
| 🟡 P2 | 7 | Service Data ai_analysis_tags — ลบ duplicate row | เพิ่มเติม |
| 🟢 P3 | 8-14 | เพิ่ม CORS, Rate Limit, Lambda Architecture, etc. | Optional |
