# Demo 2 - Anti-Pattern Workshop Fixes

**Owner:** Akawat Moradsatian (6609681231)  
**Service:** Report Ingestion & Verification Service  
**Date:** 2026-04-08

---

## 📊 สรุปสิ่งที่ต้องแก้ไข (จาก Anti-Pattern Workshop)

### Current Score: 6.5/9 (72%)
### Target Score: 9/9 (100%)

---

## 🎯 Anti-Patterns ที่ต้องแก้ไข (3 ข้อ)

| # | Anti-Pattern | Priority | Status |
|---|--------------|----------|--------|
| 8 | Timeout ไม่ถูก Enforce | 🔴 CRITICAL | ✅ Done |
| 7 | Observability ไม่สมบูรณ์ | 🔴 HIGH | ✅ Done |
| 9 | Static Contract ไม่สมบูรณ์ | 🟡 MEDIUM | ✅ Done |

---

## 📋 Tasks

### Task 1: Fix Anti-Pattern #8 - Timeout Enforcement (CRITICAL) ✅

**ไฟล์:** `src/services/gemini_service.py`

**แก้ไขแล้ว:**
- เพิ่ม `request_options={"timeout": config.GEMINI_TIMEOUT}` ใน `_call_gemini()` (บรรทัด ~310)
- เพิ่ม `request_options={"timeout": config.GEMINI_TIMEOUT}` ใน `health_check()` (บรรทัด ~565)
- เพิ่ม `request_options={"timeout": config.GEMINI_TIMEOUT + 15}` ใน `_call_gemini_with_images()` (บรรทัด ~390)

---

### Task 2: Fix Anti-Pattern #7 - Observability (HIGH) ✅

**ไฟล์ที่แก้ไข:**
- `src/utils/response.py` - เพิ่ม trace_id support และ deprecation headers
- `src/handlers/api_handler.py` - ส่ง request_id ไปที่ทุก response
- `src/handlers/ingest_handler.py` - ส่ง request_id ไปที่ทุก response
- `src/handlers/health_handler.py` - ส่ง request_id ไปที่ทุก response

**สิ่งที่เพิ่มเติม:**
- ✅ X-Trace-Id header ในทุก response
- ✅ X-Deprecated-Version, X-Sunset-Date headers (สำหรับ deprecation)
- ✅ traceId field ใน error response body
- ✅ errorCode field ใน error response (E400, E404, E500)
- ✅ timestamp field ใน error response

**CloudWatch Logs Insights Query:**
```
fields @timestamp, @message, request_id, level
| filter request_id = 'YOUR_TRACE_ID'
| sort @timestamp asc
```

---

### Task 3: Fix Anti-Pattern #9 - Static Contract (MEDIUM) ✅

**ไฟล์ที่แก้ไข:**
- `src/services/event_publisher.py` - เพิ่ม schemaVersion: "1.0" ในทุก event

**ไฟล์ที่สร้างใหม่:**
- `docs/VERSIONING_POLICY.md` - Versioning policy document

**Event Schema:**
```json
{
  "schemaVersion": "1.0",
  "report_ref_id": "...",
  ...
}
```

---

## 🔧 Additional Feature: Media Upload + AI Vision ✅

**ไฟล์ที่แก้ไข:** `src/services/gemini_service.py`

**สิ่งที่เพิ่มเติม:**

1. **S3 Image Download:**
   - `_get_s3_client()` - Lazy-load S3 client
   - `_download_image_from_s3(media_url)` - Download and validate image

2. **Gemini Vision Integration:**
   - `VISION_ANALYSIS_PROMPT` - Prompt สำหรับ image analysis
   - `_prepare_image_parts(media_urls)` - Convert images to Gemini format
   - `_call_gemini_with_images(prompt, image_parts)` - Multimodal API call

3. **Smart Analysis Flow:**
   - เมื่อ `media_urls` มี S3 images → ใช้ Vision API
   - เมื่อไม่มี images หรือ download ล้มเหลว → ใช้ text-only API

**Response Fields (เมื่อใช้ Vision):**
```json
{
  "trust_score": 75,
  "suggested_category": "FIRE",
  "keywords": ["ไฟไหม้", "อาคาร"],
  "reasoning": "...",
  "is_spam_likely": false,
  "vision_used": true,
  "image_analysis": "ภาพแสดงไฟไหม้ในอาคาร...",
  "image_authenticity": "real"
}
```

**Media Upload Flow:**
1. Client เรียก `POST /reports/upload-url` → ได้ presigned PUT URL
2. Client upload ไฟล์ไปที่ S3 โดยตรง
3. Client รวม `media_url` ใน `POST /reports`
4. Ingestion worker:
   - Download images จาก S3
   - Encode เป็น base64
   - ส่งไปให้ Gemini Vision วิเคราะห์

---

## 📁 Files Modified

| File | Changes |
|------|---------|
| `src/services/gemini_service.py` | Timeout, Vision API, S3 download |
| `src/utils/response.py` | trace_id support, deprecation headers |
| `src/handlers/api_handler.py` | Pass trace_id to responses |
| `src/handlers/ingest_handler.py` | Pass trace_id to responses |
| `src/handlers/health_handler.py` | Pass trace_id to responses |
| `src/services/event_publisher.py` | schemaVersion: "1.0" |

## 📁 Files Created

| File | Description |
|------|-------------|
| `docs/VERSIONING_POLICY.md` | API/Event versioning policy |

---

## 🧪 Testing

### Unit Tests
- [ ] Test timeout enforcement ใน Gemini service
- [ ] Test X-Trace-Id header ใน responses
- [ ] Test traceId field ใน error responses
- [ ] Test schemaVersion ใน events
- [ ] Test Vision API with sample image

### Integration Tests (AWS)
- [ ] Call API และตรวจสอบ X-Trace-Id header
- [ ] Trigger error และตรวจสอบ traceId ใน response body
- [ ] Upload image และตรวจสอบ Vision analysis
- [ ] Query CloudWatch Logs by trace_id
- [ ] Check schemaVersion ใน CloudWatch Events

---

**Status:** ✅ Code Complete - Ready for Testing
