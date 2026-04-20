# Anti-Pattern Workshop - สรุปสิ่งที่ต้องแก้ไขและเพิ่มเติม

> **สรุปจากการตรวจสอบ Anti-Pattern Workshop ทั้ง 4 ไฟล์**  
> **Service:** Report Ingestion & Verification Service  

---

## 📊 สรุปผลการตรวจสอบ (Anti-Pattern Scorecard)

| Anti-Pattern | Status | Tier | Priority | Fixed? |
|---|---|---|---|---|
| #1 Distributed Monolith | ✅ PASS | CRITICAL | - | ✅ Yes |
| #2 Shared Database | ✅ PASS | CRITICAL | - | ✅ Yes |
| #3 Chatty Services | ✅ PASS | STANDARD | - | ✅ Yes |
| #4 Over-Microservices | ✅ PASS | STANDARD | - | ✅ Yes |
| #5 God Service | ✅ PASS | STANDARD | - | ✅ Yes |
| #6 Tight Coupling | ✅ PASS | STANDARD | - | ✅ Yes |
| **#7 Observability** | ⚠️ PARTIAL | STANDARD | 🔴 HIGH | ❌ Partial |
| **#8 Timeout** | ⚠️ PARTIAL | CRITICAL | 🔴 CRITICAL | ❌ Partial |
| **#9 Static Contract** | ⚠️ PARTIAL | STANDARD | 🟡 MEDIUM | ❌ Partial |

**Overall Score:** 6.5/9 (72%) - Well-architected แต่ต้องแก้ไข 3 gaps ก่อน production

---

## 🔴 CRITICAL - ต้องแก้ไขทันที

### 1. Anti-Pattern #8 - Timeout ไม่ถูก Enforce

**ปัญหา:**
- มี config `GEMINI_TIMEOUT=15` seconds ใน `src/config.py` line 35
- แต่ **ไม่ได้ใช้** ใน actual API call (`src/services/gemini_service.py` line 165-172)
- ถ้า Gemini API hang → Lambda จะรอเต็ม 60 seconds (worker) หรือ 30s (API handler)
- Consumer services ที่เรียกเราจะ timeout ตาม

**ตำแหน่งที่ต้องแก้:**
```python
# File: src/services/gemini_service.py
# Line: 165-172

# ❌ CURRENT (ไม่มี timeout):
response = client.generate_content(
    prompt,
    generation_config={
        "temperature": 0.1,
        "max_output_tokens": 512,
        "response_mime_type": "application/json",
        # ❌ NO TIMEOUT PARAMETER!
    },
)

# ✅ SHOULD BE:
response = client.generate_content(
    prompt,
    generation_config={
        "temperature": 0.1,
        "max_output_tokens": 512,
        "response_mime_type": "application/json",
    },
    request_options={
        "timeout": config.GEMINI_TIMEOUT,  # ✅ ADD THIS
    },
)
```

**Impact:**
- 🔴 CRITICAL - อาจทำให้ production hang
- Consumer services ที่พึ่งพาเราจะได้รับผลกระทบ

**Evidence:**
- Consumer Review (consumer_review_sheet.docx.md line 20)
- Peer Review (peer_review_sheet.docx.md line 27)
- Remediation Log (remediation_log.docx.md Anti-Pattern #8)

---

## 🔴 HIGH - ควรแก้ไขก่อน Production

### 2. Anti-Pattern #7 - Observability ไม่สมบูรณ์

**ปัญหา:**
1. ❌ **ไม่มี X-Trace-Id** ในทุก response headers
2. ❌ **Error responses ไม่มี traceId** field
3. ✅ มี structured JSON logging (ดีอยู่แล้ว)

**ตำแหน่งที่ต้องแก้:**

#### 2.1 เพิ่ม X-Trace-Id Header
```python
# File: src/utils/response.py
# Lines: 9-14

# ❌ CURRENT:
CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Api-Key",
}

# ✅ SHOULD BE:
def _build_headers(trace_id: str | None = None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Api-Key",
    }
    if trace_id:
        headers["X-Trace-Id"] = trace_id  # ✅ ADD THIS
    return headers

def success(body: Any, status_code: int = 200, trace_id: str | None = None) -> dict:
    return {
        "statusCode": status_code,
        "headers": _build_headers(trace_id),  # ✅ PASS trace_id
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }
```

#### 2.2 Restructure Error Responses
```python
# File: src/utils/response.py
# Lines: 31-43

# ❌ CURRENT:
def error(status_code: int, message: str, detail: str | None = None) -> dict:
    body: dict[str, Any] = {
        "error": True,
        "message": message,
    }
    if detail:
        body["detail"] = detail
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }

# ✅ SHOULD BE:
def error(
    status_code: int, 
    message: str, 
    detail: str | None = None,
    trace_id: str | None = None,
    error_code: str | None = None
) -> dict:
    body: dict[str, Any] = {
        "error": True,
        "message": message,
    }
    if trace_id:
        body["traceId"] = trace_id  # ✅ ADD THIS
    if error_code:
        body["errorCode"] = error_code  # ✅ ADD THIS (e.g., "E404", "E500")
    if detail:
        body["detail"] = detail
    body["timestamp"] = datetime.now(timezone.utc).isoformat()  # ✅ ADD THIS
    
    return {
        "statusCode": status_code,
        "headers": _build_headers(trace_id),
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }
```

#### 2.3 แก้ไขทุก Handler ให้ส่ง trace_id
```python
# File: src/handlers/api_handler.py
# File: src/handlers/ingest_handler.py
# File: src/handlers/health_handler.py

# ✅ ทุก handler ต้องแก้ไขให้:
def handler(event: dict, context) -> dict:
    request_id = context.aws_request_id if context else str(uuid.uuid4())
    
    # ... logic ...
    
    # เมื่อ return success:
    return response.success(data, trace_id=request_id)
    
    # เมื่อ return error:
    return response.error(400, "Bad Request", trace_id=request_id, error_code="E400")
```

**Impact:**
- 🔴 HIGH - ทำให้ debug production issues ยากมาก
- ไม่สามารถ trace requests ข้าม services ได้
- Consumer Review ระบุว่าต้องการฟีเจอร์นี้ก่อน integrate

**Evidence:**
- Peer Review (peer_review_sheet.docx.md line 21)
- Remediation Log (remediation_log.docx.md Anti-Pattern #7)
- Consumer Review (consumer_review_sheet.docx.md line 23)

---

## 🟡 MEDIUM - ควรทำให้ครบถ้วน

### 3. Anti-Pattern #9 - Static Contract ไม่สมบูรณ์

**ปัญหา:**
1. ✅ ใช้ `/v1/` ใน URL แล้ว (ดีอยู่แล้ว)
2. ❌ **EventBridge events ไม่มี schemaVersion**
3. ❌ **ไม่มี Versioning Policy document**

#### 3.1 เพิ่ม schemaVersion ใน Events

**ตำแหน่งที่ต้องแก้:**
```python
# File: src/services/event_publisher.py
# Lines: 52-64 (ReportVerifiedEvent)

# ❌ CURRENT:
detail = {
    "report_ref_id": report_id,
    "suggested_incident_data": suggested_incident_data,
    "verified_by": verified_by,
    "verification_notes": verification_notes,
}

# ✅ SHOULD BE:
detail = {
    "schemaVersion": "1.0",  # ✅ ADD THIS
    "report_ref_id": report_id,
    "suggested_incident_data": suggested_incident_data,
    "verified_by": verified_by,
    "verification_notes": verification_notes,
}
```

**ทำเช่นเดียวกันกับ:**
- `ReportStatusChangedEvent` (lines 85-92)
- ทุก events ที่ publish ผ่าน EventBridge

#### 3.2 สร้าง Versioning Policy Document

**สร้างไฟล์ใหม่:**
```bash
docs/VERSIONING_POLICY.md
```

**เนื้อหาที่ควรมี:**

```markdown
# API & Event Versioning Policy

## Breaking Changes Definition

A change is considered **breaking** if it:
1. Removes or renames a field in request/response
2. Changes the data type of an existing field
3. Removes or changes enum values
4. Makes a previously optional field required
5. Changes error response structure
6. Removes or renames an endpoint

## Non-Breaking Changes

These changes are safe and won't break existing consumers:
1. Adding a new optional field to response
2. Adding a new enum value
3. Adding a new endpoint
4. Adding a new optional query parameter
5. Improving error messages

## Deprecation Process

1. **Announcement** (30 days before):
   - Add `X-Deprecated-Version: true` header to deprecated endpoints
   - Update API documentation with deprecation notice
   - Notify all known consumers via email

2. **Grace Period** (30-60 days):
   - Keep old version running alongside new version
   - Monitor usage metrics
   - Assist consumers with migration

3. **Sunset**:
   - Remove deprecated version
   - Return HTTP 410 Gone with migration instructions

## Versioning Strategy

### API Endpoints
- Use `/v1/`, `/v2/` in URL path
- Increment major version only for breaking changes
- Keep at least 2 versions active during transition

### EventBridge Events
- All events MUST include `schemaVersion` field
- Format: `"schemaVersion": "1.0"`
- Increment version for breaking schema changes
- Consumers MUST check schemaVersion before processing

### Example Event Evolution

**Version 1.0:**
```json
{
  "schemaVersion": "1.0",
  "report_ref_id": "r-123",
  "suggested_incident_data": {...}
}
```

**Version 2.0 (breaking - renamed field):**
```json
{
  "schemaVersion": "2.0",
  "reportId": "r-123",  // renamed from report_ref_id
  "incidentData": {...} // renamed from suggested_incident_data
}
```

## Consumer Notification

1. **Subscribe to changelog**: RSS feed at `/api/changelog.xml`
2. **Webhook notifications**: Register webhook for breaking changes
3. **Release notes**: Published 30 days before deployment
4. **Test environment**: Always available at `https://api-staging.example.com`

## Contact

For versioning questions or migration support:
- **Owner**: Akawat Moradsatian
- **Email**: akawat.m@student.chula.ac.th
- **Slack**: #report-verify-service
```

**Impact:**
- 🟡 MEDIUM - ไม่ได้ block production แต่จำเป็นสำหรับ long-term maintainability
- Consumer services ต้องการความชัดเจนในการจัดการ breaking changes

**Evidence:**
- Consumer Review (consumer_review_sheet.docx.md lines 21-22)
- Peer Review (peer_review_sheet.docx.md line 28)
- Remediation Log (remediation_log.docx.md Anti-Pattern #9)

---

## ✅ สิ่งที่ทำได้ดีอยู่แล้ว (ไม่ต้องแก้)

### 1. ✅ Anti-Pattern #1 (Distributed Monolith)
- **PASS** - Service สามารถ deploy standalone ได้
- ใช้ SQS buffer, async EventBridge
- มี graceful degradation สำหรับทุก dependency
- **Evidence:** self_review_session1_6609681231.docx.md line 17

### 2. ✅ Anti-Pattern #2 (Shared Database)
- **PASS** - มี exclusive database ownership
- DynamoDB tables: Reports, AuditLogs, Stats
- ไม่มี service อื่นเข้าถึง database โดยตรง
- **Evidence:** terraform/dynamodb.tf

### 3. ✅ Anti-Pattern #3 (Chatty Services)
- **PASS** - Rich composite payloads
- List endpoint คืนข้อมูลครบใน 1 call
- ไม่ต้อง follow-up calls
- **Evidence:** src/models/report.py `to_api_detail()` method

### 4. ✅ Anti-Pattern #4 (Over-Microservices)
- **PASS** - มี genuine standalone value
- Clear single responsibility
- **Evidence:** Proposal หัวข้อ Service Boundary

### 5. ✅ Anti-Pattern #5 (God Service)
- **PASS** - มี explicit out-of-scope
- ไม่ก้าวก่าย responsibilities ของ service อื่น
- **Evidence:** Proposal หัวข้อ 5 Service Boundary

### 6. ✅ Anti-Pattern #6 (Tight Coupling)
- **PASS** - มี comprehensive fallback
- Multi-key rotation, model fallback chain
- Gemini fail → trust_score=50
- **Evidence:** src/services/gemini_service.py lines 293-302

---

## 📋 Action Items Checklist

### CRITICAL (ทำก่อน integrate กับ consumer services)
- [x] แก้ไข Gemini timeout enforcement (gemini_service.py line 165)
- [x] เพิ่ม X-Trace-Id header (response.py)
- [x] เพิ่ม traceId ใน error responses (response.py)

### HIGH (ทำก่อน production deployment)
- [x] แก้ไขทุก handler ให้ส่ง trace_id ไปที่ response builders
- [x] เพิ่ม error codes (E400, E404, E500, etc.)
- [x] เพิ่ม timestamp ใน error responses

### MEDIUM (ทำเพื่อ long-term maintainability)
- [x] เพิ่ม schemaVersion ใน EventBridge events (event_publisher.py)
- [x] สร้าง docs/VERSIONING_POLICY.md
- [x] Setup changelog RSS feed
- [ ] สร้าง staging environment สำหรับ consumer testing

### NICE TO HAVE (Optional improvements)
- [x] Implement X-Deprecated-Version header mechanism
- [ ] Setup webhook notifications for breaking changes
- [x] Create OpenAPI 3.x specification
- [x] Add health check endpoint with dependency status

## 📚 References

**Workshop Files:**
1. `self_review_session1_6609681231.docx.md` - Session 1 self-review
2. `peer_review_sheet.docx.md` - Session 2 & 3 peer review
3. `consumer_review_sheet.docx.md` - Session 3 consumer review
4. `remediation_log.docx.md` - Complete remediation plan

**Source Files:**
- `src/services/gemini_service.py` - Gemini API integration
- `src/utils/response.py` - API response builders
- `src/utils/logger.py` - Structured logging
- `src/handlers/*.py` - Lambda handlers
- `terraform/*.tf` - Infrastructure as Code

**Documentation:**
- [Implementation Plan](../implement/implementation-plan.md)
- [Service Proposal](../others/reportingestion_proposal.txt)
- [README.md](../../README.md)
