# should-fixed-doc.md — รายการที่ยังต้องแก้ใน fixed-v2-docs.md

> เอกสารนี้ลิสต์เฉพาะประเด็นที่ยังไม่สอดคล้องกับ implementation ปัจจุบันของโปรเจกต์ หลัง re-check เทียบกับ `src/`, `terraform/`, และ `frontend/` แล้ว
>
> รายการที่แก้ถูกแล้วจากรอบก่อนถูกลบออกหมดแล้ว เหลือเฉพาะสิ่งที่ยังควรกลับไปแก้ใน `fixed-v2-docs.md`

---

## 1. API Contract #1 ยังไม่อธิบาย `sensor_data` และ IOT ingest flow ให้ตรงของจริง

**ปัญหา**
- ตอนนี้เอกสารยังเขียนเหมือน ingest ต้องมีอย่างน้อย `raw_content` หรือ `media_urls`
- ยังไม่มี schema หรือตัวอย่างของ `sensor_data`
- ยังไม่อธิบายว่า `IOT_SENSOR` มี prompt logic แยกจาก citizen report

**ของจริงในระบบ**
- ingest รับอย่างน้อยหนึ่งใน `raw_content`, `media_urls`, หรือ `sensor_data`
- ถ้าไม่มี `raw_content` แต่มี `sensor_data` ระบบจะสร้าง fallback summary แล้วเข้าคิวต่อได้
- `sensor_data` ถูกเก็บใน model และถูกส่งกลับใน report detail

**ควรแก้เป็น**
- เพิ่ม `sensor_data` ใน request schema ของ Contract #1 และใน Owned Data
- เพิ่มหมายเหตุว่า `IOT_SENSOR` สามารถส่ง structured payload ได้โดยไม่ต้องใช้ narrative text
- อัปเดตตัวอย่าง response 202 ให้มี `estimated_wait_time` และ `traceId`

**ตัวอย่างข้อความที่ควรใช้**

```md
Validation: ระบบต้องได้รับอย่างน้อยหนึ่งใน `raw_content`, `media_urls`, หรือ `sensor_data`

หมายเหตุ: สำหรับ `reporter_source=IOT_SENSOR` สามารถส่ง `sensor_data` แบบ structured เช่น
`sensor_id`, `metric_name`, `metric_value`, `unit`, `threshold`, `status`, `observed_at`
ได้โดยไม่จำเป็นต้องมีข้อความบรรยายยาวแบบ citizen report
```

---

## 2. Scope ของ `X-Api-Key` ยังเขียนกว้างเกินจริง

**ปัญหา**
- หลาย contract ยังระบุว่าต้องใช้ `X-Api-Key` ทั้ง read endpoint, verify endpoint, stats, detail, delete
- Terraform ปัจจุบันไม่ได้บังคับ API key ทุก endpoint

**ของจริงในระบบ**
- API key ถูกบังคับเฉพาะ `POST /v1/reports` และ `POST /v1/reports/upload-url`
- read/admin endpoints อื่นใน environment ปัจจุบันเปิดผ่าน API Gateway โดยไม่บังคับ usage plan

**ควรแก้เป็น**
- แก้ auth note ส่วนต้นของ synchronous contract ใหม่
- ลบ `X-Api-Key` requirement ออกจาก contract ที่ไม่ได้ enforce จริงในตอนนี้
- ถ้าจะคงมุมมอง future production hardening ให้เขียนแยกเป็น planned hardening ไม่ใช่ current behavior

**ตัวอย่างข้อความที่ควรใช้**

```md
Current environment auth note:
- `POST /v1/reports` และ `POST /v1/reports/upload-url` ต้องใช้ `X-Api-Key`
- read/admin endpoints อื่นยังไม่บังคับ API key ใน API Gateway ของ environment ปัจจุบัน
```

---

## 3. API Contract #2: GET `/reports` ยังไม่ตรงทั้ง query และ response

**ปัญหา**
- ยังไม่อธิบาย `priority=all|high|normal` ให้ครบ
- ยังใช้ตัวอย่าง `status=PENDING` ในบางส่วน ทั้งที่ status จริงคือ `PENDING_REVIEW`
- เอกสารพูดถึง cursor pagination / `next_token` แต่ implementation ปัจจุบันยังไม่ได้คืน token กลับมา

**ของจริงในระบบ**
- query ที่รองรับจริงคือ `status`, `min_trust_score`, `priority`, `limit`
- summary item คืน `priority` เป็น `HIGH` หรือ `NORMAL`
- response ปัจจุบันมี `data` และ `total_count` เท่านั้น

**ควรแก้เป็น**
- เปลี่ยน `PENDING` ทุกจุดเป็น `PENDING_REVIEW`
- เพิ่ม `priority` filter และ response field `priority`
- เอา `next_token` / `last_evaluated_key` ออกจาก current contract ถ้ายังไม่ implement จริง

**ตัวอย่างข้อความที่ควรใช้**

```json
{
	"data": [
		{
			"report_id": "r-550e8400-e29b-41d4-a716-446655440000",
			"content": "Fire near Central...",
			"trust_score": 85,
			"suggested_category": "FIRE",
			"priority": "HIGH",
			"time_ago": "5 mins"
		}
	],
	"total_count": 1
}
```

---

## 4. API Contract #4: GET `/reports/{report_id}` ยังไม่ตรงกับ schema ที่ API คืนจริง

**ปัญหา**
- เอกสารยังวาง `geo_location` ไว้ใต้ `content` และมี nested `verification` object
- ยังไม่มี `sensor_data` ใน detail payload
- มี `updated_at` ในตัวอย่าง แต่ current API detail ใช้ `created_at` และ `event_timestamp`

**ของจริงในระบบ**
- `geo_location`, `status`, `verified_by`, `verification_notes`, `linked_incident_id` อยู่ top-level
- `content` มี `text`, `images`, `video`, `sensor_data`
- มี `priority` top-level

**ควรแก้เป็น**
- ปรับตัวอย่าง response ใหม่ให้ตรงกับ `Report.to_api_detail()`

**ตัวอย่างข้อความที่ควรใช้**

```json
{
	"report_id": "r-...",
	"reporter_info": {
		"source": "IOT_SENSOR",
		"reporter_id": "sensor-station-01",
		"source_external_id": ""
	},
	"content": {
		"text": "Sensor alert for water_level: 2.8 m, threshold 2.0, status CRITICAL",
		"images": [],
		"video": null,
		"sensor_data": {
			"sensor_id": "wl-01",
			"metric_name": "water_level",
			"metric_value": 2.8,
			"unit": "m"
		}
	},
	"analysis": {
		"trust_score": 88,
		"ai_reasoning": "...",
		"suggested_category": "FLOOD",
		"ai_analysis_tags": ["water_level", "threshold_breach"],
		"ai_analysis_failed": false,
		"potential_duplicates": []
	},
	"priority": "HIGH",
	"geo_location": {"lat": 13.7563, "lon": 100.5018},
	"status": "PENDING_REVIEW",
	"verified_by": null,
	"verification_notes": null,
	"linked_incident_id": null,
	"created_at": "2026-05-14T10:30:00Z",
	"event_timestamp": "2026-05-14T10:29:30Z"
}
```

---

## 5. API Contract #5: GET `/reports/stats` ยังล้าหลายจุด

**ปัญหา**
- ยังเขียนว่า region filter ยังไม่ implement
- ยังอธิบายเหมือน endpoint นี้อ่านจาก pre-aggregated stats table เป็นหลัก
- ยังเขียน `trending_keywords` และ `heatmap_data` เหมือนเป็น future feature
- ยังไม่ใส่ `supported_regions`, `timeframe`, `region` ใน response body

**ของจริงในระบบ**
- region filter ใช้งานจริงแล้วสำหรับ `bkk`, `central`, `north`, `northeast`, `south`
- response คืน `timeframe`, `region`, `supported_regions`, `summary`, `trending_keywords`, `heatmap_data`
- current implementation คำนวณจาก report items พร้อม cache ชั่วคราว ไม่ใช่แค่อ่าน counter table อย่างเดียว

**ควรแก้เป็น**
- ลบ note ว่า region ยังไม่พร้อม
- เปลี่ยนคำอธิบายให้ตรงกับ current implementation
- ปรับ response example ใหม่

**ตัวอย่างข้อความที่ควรใช้**

```md
GET `/reports/stats` รองรับ query `timeframe=today|last_24h|last_7d` และ `region=bkk|central|north|northeast|south`

Response ปัจจุบันคืนทั้ง `summary`, `trending_keywords`, `heatmap_data`, `timeframe`, `region` และ `supported_regions`
โดยใช้การคำนวณจากชุดรายงานล่าสุดร่วมกับ in-memory cache ระยะสั้น
```

---

## 6. Contract ของ `/reports/audit`, `/reports/events`, `/reports/upload-url`, `/reports/trace/{trace_id}` ยังเป็น placeholder หรือ method/path ไม่ตรง

**ปัญหา**
- บาง section ยังว่าง
- บาง sectionยกคำอธิบายมาจาก health check ผิด endpoint
- `/reports/trace/{trace_id}` ยังเขียน method/path ไม่ตรงของจริง
- `/reports/upload-url` ยังไม่อธิบาย request/response ที่ใช้จริง

**ของจริงในระบบ**
- `GET /reports/audit` รองรับ `report_id` และ `limit`
- `GET /reports/events` รองรับ `type=all|verified|status-changed` และ `limit`
- `POST /reports/upload-url` ต้องใช้ API key และคืน presigned PUT URL
- `GET /reports/trace/{trace_id}` ค้น CloudWatch Logs ตาม trace ID

**ควรแก้เป็น**
- เติม contract ให้ครบทั้ง 4 endpoint โดยใช้ behavior จริงจาก handler และ dashboard

**ตัวอย่างข้อความที่ควรใช้**
- `/reports/audit`: ใช้ดึง audit logs ล่าสุด หรือ filter ตาม `report_id`; response คืน `data[]` และ `total_count`
- `/reports/events`: ใช้ดึง recent event mirror จาก CloudWatch Logs; response คืน `data[]`, `total_count`, `log_groups`
- `/reports/upload-url`: request body ควรมี `filename` และ optional `content_type`, `report_id`, `file_size_bytes`; response คืน `upload_url`, `media_url`, `expires_in`, `instructions`
- `/reports/trace/{trace_id}`: method ต้องเป็น `GET`; response คืน `target_trace_id`, `results`, `cloudwatch_insights_query`, `how_to_trace`

---

## 7. `POST /report-incident` callback contract ยังหายไป

**ปัญหา**
- fixed-v2-docs ยังไม่มี contract ของ callback endpoint นี้ ทั้งที่ implementation มีจริงและสำคัญต่อ incident handoff loop

**ของจริงในระบบ**
- รับได้ทั้ง flat payload และ envelope แบบ `{ eventType, data: {...} }`
- ใช้ `original_report_ref_id > source_report_id > report_id` ในการจับคู่ report ต้นทาง
- รองรับ `status=CREATED` และ `status=FAILED`
- ถ้า `CREATED` จะอัปเดต `linked_incident_id` และเขียน audit log `INCIDENT_LINKED`
- ถ้า `FAILED` จะเขียน audit log `INCIDENT_LINK_FAILED`

**ควรแก้เป็น**
- เพิ่ม API Contract ใหม่สำหรับ callback endpoint นี้โดยตรง

**ตัวอย่างข้อความที่ควรใช้**

```md
API Contract: `POST /report-incident`

Purpose:
- รับผลลัพธ์จาก Incident Tracking Service หลังจาก service นี้ publish `ReportVerifiedEvent`
- ถ้า `status=CREATED` จะ auto-link `linked_incident_id` กลับเข้า report
- ถ้า `status=FAILED` จะบันทึกเหตุผลไว้ใน audit log เพื่อ trace ปัญหา

Reference resolution:
- ใช้ `original_report_ref_id` เป็นหลัก
- fallback ไป `source_report_id` หรือ `report_id` ได้
```

---

## 8. Service Interaction และ verify flow ของ `link_to_incident_id` ยังอธิบายผิด

**ปัญหา**
- ยังเขียนเหมือน frontend จะไปดึง active incidents ผ่าน `GET /incidents?active=true`
- ยังไม่บอกเงื่อนไขว่า `link_to_incident_id` ใช้ได้เฉพาะตอน verify เป็น `VERIFIED`
- ยังไม่บอก error behavior ตอน incident reference ไม่ผ่าน validation

**ของจริงในระบบ**
- frontend ปัจจุบันเป็นช่องกรอก `link_to_incident_id` ตรง ๆ
- backend จะ validate ตอน `PATCH /reports/{report_id}`
- path ที่ใช้จริงคือ `GET {INCIDENT_SERVICE_BASE_URL}/incidents/{incident_id}`
- ถ้าไม่พบ incident จะตอบ `400`
- ถ้า Incident Service ใช้ไม่ได้หรือไม่ได้ตั้งค่า จะตอบ `503`

**ควรแก้เป็น**
- เปลี่ยนคำอธิบายจาก list-based flow เป็น backend validation flow

**ตัวอย่างข้อความที่ควรใช้**

```md
When `validation_status=VERIFIED` and caller provides `link_to_incident_id`,
the API handler validates that incident reference against
`GET {INCIDENT_SERVICE_BASE_URL}/incidents/{incident_id}` before writing `linked_incident_id`.

- not found -> `400 Bad Request`
- incident service unavailable or not configured -> `503 Service Unavailable`
```

---

## 9. Asynchronous contract ยังไม่สะท้อน payload ปัจจุบันของ event publisher

**ปัญหา**
- `ReportVerifiedEvent` ยังไม่ใส่ `schemaVersion`, `action`, `target_incident_id`
- ยังมี comment ว่า `severity_level`, `reporter_count`, `address_text` เป็น hardcoded หรือยังไม่รองรับ
- `ReportStatusChangedEvent` ก็ยังไม่ใส่ `schemaVersion`
- บางจุดยังใช้ชื่อ event bus แบบ generic แทน naming ปัจจุบัน

**ของจริงในระบบ**
- `ReportVerifiedEvent` ส่ง `schemaVersion`, `action`, และ optional `target_incident_id`
- `severity_level` คำนวณจาก category/keywords/trust score
- `reporter_count` คำนวณจาก unique reporters ของ report ปัจจุบันกับ duplicate candidates
- `address_text` ได้จาก reverse geocoding เมื่อ feature เปิดใช้งาน
- `ReportStatusChangedEvent` ส่ง `schemaVersion` ด้วย

**ควรแก้เป็น**
- อัปเดตทั้ง field definition และ example payload ของ async contracts ใหม่

**ตัวอย่างข้อความที่ควรใช้**

```json
{
	"schemaVersion": "1.0",
	"report_ref_id": "r-...",
	"suggested_incident_data": {
		"type": "FIRE",
		"description": "...",
		"severity_level": 4,
		"location": {
			"lat": 13.746,
			"lon": 100.539,
			"address_text": "Ratchadamri, Bangkok"
		},
		"reporter_count": 2
	},
	"verified_by": "officer_007",
	"verification_notes": "Confirmed via CCTV",
	"action": "MERGED_EXISTING_INCIDENT",
	"target_incident_id": "inc-1234"
}
```

---

## 10. Health Check example ยังไม่ตรงกับ response structure ปัจจุบัน

**ปัญหา**
- ตัวอย่างยังไม่มี `traceId`
- ยังใช้ชื่อตาราง generic
- ยังไม่ใส่ Gemini `model_chain`
- ยังไม่อธิบายว่าค่า overall status เป็น `healthy | degraded | unhealthy`

**ของจริงในระบบ**
- response body คืน `status`, `timestamp`, `duration_ms`, `components`, `version`, `traceId`
- Gemini health คืน `model`, `available_keys`, `model_chain`
- DynamoDB และ SQS เป็น critical dependency; ถ้าพัง overall จะเป็น `unhealthy`

**ควรแก้เป็น**
- เปลี่ยน response example ให้ตรงกับ health handler ปัจจุบัน

**ตัวอย่างข้อความที่ควรใช้**

```json
{
	"status": "healthy",
	"timestamp": "2026-05-17T05:30:00Z",
	"duration_ms": 123,
	"components": {
		"dynamodb": {
			"status": "healthy",
			"table": "report-verify-dev-reports",
			"table_status": "ACTIVE"
		},
		"gemini": {
			"status": "healthy",
			"model": "gemini-3.1-flash-lite",
			"available_keys": 2,
			"model_chain": [
				"gemini-3.1-flash-lite",
				"gemini-3-flash-preview",
				"gemma-4-26b-a4b-it",
				"gemini-2.5-flash",
				"gemini-2.5-flash-lite",
				"gemma-4-31b-it"
			]
		}
	},
	"version": "1.0.0",
	"traceId": "..."
}
```

---

## 11. Owned Data และ Dependency Mapping ยังมี claim ที่ไม่จริงหรือยังไม่ implement

**ปัญหา**
- ยังมี `sentiment_score` ทั้งที่ไม่มีใน model หรือ Gemini result
- ยังใช้ชื่อ resource แบบ generic หลายจุด
- ยังเขียนเหมือน outbox / scheduled retry สำหรับ EventBridge ทำงานแล้ว

**ของจริงในระบบ**
- field ที่มีจริงคือ `sensor_data`, `ai_reasoning`, `ai_analysis_tags`, `ai_analysis_failed`, `linked_incident_id`, `potential_duplicates`
- naming ปัจจุบันใช้ pattern `${project_name}-${environment}-...`
- Event publish failure ตอนนี้ยังเป็น error logging; ยังไม่มี outbox table, replay scheduler, หรือ retry worker จริง

**ควรแก้เป็น**
- ลบ `sentiment_score`
- เปลี่ยนชื่อตัวอย่าง resource หรืออธิบาย naming convention ให้ชัด
- เปลี่ยน outbox section ให้เป็น future enhancement

**ตัวอย่างข้อความที่ควรใช้**

```md
Current EventBridge failure behavior:
- ถ้า publish event ไม่สำเร็จ ระบบจะ log error พร้อม payload สำหรับการตรวจสอบย้อนหลัง
- Outbox / replay retry เป็น planned enhancement และยังไม่ได้ implement ใน revision ปัจจุบัน
```

---

## สรุป

| หมวด | จำนวนประเด็นหลัก |
|---|---:|
| Ingest / sync contracts | 6 |
| Incident linking / async contracts | 3 |
| Health / data / dependency notes | 2 |
| **รวม** | **11** |
