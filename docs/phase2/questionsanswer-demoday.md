# คำตอบคำถามสำหรับ Demoday ของ Request Verify Service

> เอกสารนี้อ้างอิงจาก implementation จริงใน `src/`, `terraform/`, `frontend/`, `tests/` เป็นหลัก และใช้เอกสารใน `docs/` เฉพาะส่วนที่สอดคล้องกับโค้ดหรือใช้เป็นบริบทของ cluster เท่านั้น เพราะมีบางเอกสารที่ล้าหลังกว่า implementation ปัจจุบัน

## บทนำ: ระบบนี้คืออะไร และไม่ใช่อะไร

Repository นี้ไม่ได้เป็น "ระบบจัดการภัยพิบัติทั้งก้อน" แต่เป็น **Request Verify Service** ที่ทำหน้าที่เป็นจุดรับข้อมูลภาคสนาม, คัดกรองความน่าเชื่อถือ, ตรวจ duplicate, ให้เจ้าหน้าที่ verify, แล้วส่ง event ที่เชื่อถือได้ต่อไปยังบริการปลายทาง เช่น Incident Tracking หรือ service อื่นใน cluster

ถ้าจะพูดสั้น ๆ บนเวที ควรพูดว่า:

> "บริการของเราเป็นประตูรับข้อมูลเหตุภัยและคำร้องจากหลายแหล่งแบบ asynchronous จากนั้นช่วยเจ้าหน้าที่คัดกรองด้วย AI + rule-based scoring + duplicate detection ก่อนให้คนตัดสินใจ verify แล้วค่อย publish ต่อเป็นเหตุการณ์ที่ระบบอื่นนำไปใช้ได้อย่างปลอดภัย"

เหตุผลที่นิยามแบบนี้ เพราะโค้ดจริงแสดงชัดว่า:

1. `POST /v1/reports` ไม่ได้สร้าง incident โดยตรง แต่ enqueue เข้าคิว SQS ก่อน
2. Worker จะวิเคราะห์ข้อความ/รูป, คำนวณ trust score, ตรวจ duplicate, แล้วตั้งสถานะเริ่มต้นเป็น `PENDING_REVIEW`, `SPAM`, หรือ `DUPLICATE`
3. การสร้างหรือ merge incident จะเกิดตอนเจ้าหน้าที่ `PATCH /v1/reports/{id}` เป็น `VERIFIED` เท่านั้น
4. หลัง verify แล้วจึง publish `ReportVerifiedEvent` และ `ReportStatusChangedEvent` ผ่าน EventBridge

ดังนั้นจุดแข็งของ service นี้คือ **ทำข้อมูลดิบให้กลายเป็นข้อมูลที่ downstream ไว้ใจได้** ไม่ใช่การจัดรถกู้ภัย, บริหารเตียงโรงพยาบาล, จองศูนย์พักพิง, จัด donation, หรือค้นหาคนหายโดยตรง

---

## Section I: System Setup (10 นาที)

ส่วนนี้ควรนำเสนอในฐานะ "การเตรียมระบบให้พร้อมสำหรับใช้งานจริง" ไม่ใช่แค่เปิดหน้าเว็บแล้วจบ ควรทำให้กรรมการเห็นว่าเรารู้ dependency ของระบบและรู้ว่าจะเช็กความพร้อมอย่างไรจาก implementation จริง

### 1. สิ่งที่ต้องเตรียมก่อนขึ้นเดโม

ควรเตรียมอย่างน้อย 2 หน้าจอหรือ 2 tab พร้อมกัน:

1. หน้า `dashboard` สำหรับยิง API, ดู health, stats, events, upload URL, verify/delete แบบตรงไปตรงมา
2. หน้า `admin-verify` สำหรับให้เจ้าหน้าที่ดูรายการ pending report, อ่าน AI analysis, กด verify/reject/delete, ดู audit trail, และใส่ `link_to_incident_id` เพื่อ merge เข้ากับ incident เดิม

เหตุผลที่ควรเปิดทั้งสองหน้า เพราะ frontend ที่มีอยู่ใน repo แบ่งบทบาทชัดเจน:

1. `frontend/dashboard/index.html` เหมาะกับการอธิบายมุมมองระบบและ endpoint
2. `frontend/admin-verify/index.html` เหมาะกับการสาธิต human-in-the-loop verification ซึ่งเป็นหัวใจของระบบนี้

นอกจากนี้ควรเตรียมข้อมูลต่อไปนี้ล่วงหน้า:

1. `API base URL` ของระบบ
2. `API key` สำหรับ `POST /v1/reports` และ `POST /v1/reports/upload-url`
3. URL ของหน้า `dashboard` และ `admin-verify`
4. ถ้าจะเดโมรูปภาพ ควรเตรียมไฟล์รูปและทดสอบ flow upload ล่วงหน้า
5. ถ้าจะเดโมการ merge เข้ากับ incident เดิม ควรมี `incident_id` ตัวอย่างเตรียมไว้ หรือเตรียมสร้าง incident แรกก่อนแล้วค่อยเดโม report ตัวถัดไปด้วย `link_to_incident_id`

### 2. สิ่งที่ควรตรวจเช็กก่อนเริ่มเดโม

#### 2.1 ตรวจ health ก่อนเสมอ

เริ่มจาก `GET /v1/health` แล้วอธิบายว่า endpoint นี้ไม่ได้เช็กแค่ "Lambda ตอบได้" แต่เช็ก dependency หลักของระบบด้วย ได้แก่:

1. DynamoDB
2. SQS
3. Gemini AI
4. EventBridge

`health_handler.py` ทำ dependency checks แบบ concurrent ทำให้หน้าจอนี้มีน้ำหนักเชิงวิศวกรรม ไม่ใช่แค่ endpoint สำหรับโชว์เฉย ๆ

สิ่งที่ควรพูดคือ:

> "ถ้า health เป็น healthy แปลว่าระบบรับงาน, คิวงาน, การเก็บข้อมูล, และการ publish event พร้อมใช้งาน ถ้า Gemini มีปัญหา ระบบยังพอทำงานได้แต่จะลดระดับเป็น manual review มากขึ้น"

ประโยคนี้พูดได้อย่างมั่นใจ เพราะ `gemini_service.py` มี fallback ชัดเจน: ถ้าไม่มี key หรือ AI call ล้มเหลว ระบบจะคืนค่า default พร้อม `ai_analysis_failed=True` และให้ manual review ตัดสินต่อ

#### 2.2 ยืนยัน write path ที่ต้องใช้ API key

จาก Terraform ของ API Gateway ตอนนี้ **ไม่ได้บังคับ API key ทุก endpoint** แต่บังคับเฉพาะ:

1. `POST /v1/reports`
2. `POST /v1/reports/upload-url`

ดังนั้นในวันเดโม ควรอธิบายให้ชัดว่า:

> "ใน environment นี้ เรา focus เรื่อง demo convenience จึงล็อก API key เฉพาะ write endpoints ที่รับข้อมูลใหม่และรับ upload URL ส่วน read/admin endpoints ยังเปิดไว้เพื่อให้สาธิต flow ได้เร็ว แต่ถ้า harden สำหรับ production ควรเพิ่ม auth/authorizer เพิ่มเติม"

การพูดแบบนี้ดีกว่าพยายามแกล้งทำเหมือนระบบ secure ครบทุกมิติ ทั้งที่ Terraform ปัจจุบันยังไม่ได้บังคับ auth ทุก endpoint

#### 2.3 เตรียม demo payload ให้ไม่ชน dedup โดยไม่จำเป็น

ระบบนี้มี dedup จริง ไม่ใช่แค่พูดในเอกสาร โดยตรวจอย่างน้อย 3 แบบ:

1. `external_id` ซ้ำ
2. พิกัดใกล้กันในรัศมีประมาณ 200 เมตร ภายในช่วงเวลาประมาณ 15 นาที
3. เนื้อหาคล้ายกันตาม content similarity threshold ประมาณ 0.65

ดังนั้นถ้าจะยิงหลายเคสที่มีข้อความคล้ายกันในช่วงเดโม ควรทำอย่างน้อยหนึ่งอย่างต่อไปนี้:

1. เปลี่ยน `reporter_id`
2. เปลี่ยน timestamp
3. เปลี่ยนพิกัดเล็กน้อยตามสถานการณ์จริง
4. เปลี่ยนถ้อยคำบางส่วนให้สะท้อนคนละเหตุการณ์จริง
5. ถ้ามี `external_id` ให้ใช้คนละค่า

เหตุผลคือถ้าไม่เตรียมดี ๆ ระบบอาจ mark เคสหลังเป็น `DUPLICATE` ซึ่งไม่ใช่ bug แต่เป็น behavior ที่ถูกต้องตาม design

#### 2.4 เตรียม expectation เรื่อง asynchronous flow

`POST /v1/reports` จะตอบกลับ `202 Accepted` ทันที และใน handler ยังคืน `estimated_wait_time: "2s"` มาให้ด้วย เพราะระบบใช้แนวคิด fire-and-forget ส่งงานเข้า SQS ก่อน

ดังนั้นตอนเดโมควรพูดนำผู้ชมไว้ก่อนว่า:

> "เมื่อผู้ใช้แจ้งเหตุ ระบบจะตอบรับทันทีว่าได้รับคำขอแล้ว จากนั้น worker จะประมวลผลเบื้องหลังอีกเล็กน้อยก่อนที่เจ้าหน้าที่จะเห็นรายการในหน้า review"

คำอธิบายนี้ทำให้ delay 2-5 วินาทีบนหน้าจอดูเป็น design decision ไม่ใช่อาการระบบช้า

#### 2.5 ถ้าจะเดโมรูปภาพ ให้ทดสอบ upload URL ล่วงหน้า

ระบบรองรับ media evidence จริงผ่าน `POST /v1/reports/upload-url` และเก็บไฟล์ใน S3 media bucket โดยมีขนาดไฟล์สูงสุดประมาณ 20 MB ตาม config ปัจจุบัน

จุดนี้ควรเตรียมล่วงหน้า เพราะถ้าจะโชว์ multimodal analysis ของ Gemini แล้วติดที่ upload จะเสียจังหวะเดโมทันที

#### 2.6 เตรียม incident merge flow ถ้าจะเล่าเหตุการณ์ต่อเนื่อง

ทั้ง `dashboard` และ `admin-verify` มีช่องให้ใส่ `link_to_incident_id` ตอน verify ได้จริง

สิ่งนี้สำคัญมากสำหรับเคสประเภท:

1. มี report ใหม่เข้ามาเพื่ออัปเดต incident เดิม
2. น้ำเริ่มลดแล้ว
3. มีถนนอีกสายถูกตัดขาดในเหตุการณ์เดิม
4. มี shelter เปิดเพิ่มในพื้นที่เดิม

ถ้าต้องการโชว์ว่า architecture รองรับ "incident lifecycle" มากกว่าแค่สร้าง incident ใหม่ทุกครั้ง ควรใช้ field นี้

### 3. ลำดับการโชว์ setup ที่แนะนำ

ภายใน 10 นาที แนะนำให้เรียงตามนี้:

1. เปิด `dashboard` แล้วเรียก `GET /v1/health`
2. อธิบาย dependency หลัก 4 ตัว: DynamoDB, SQS, Gemini, EventBridge
3. เปิด `admin-verify` ให้เห็นว่ามีหน้ารวม report queue, suggested incident, verify action, audit trail
4. เปิด stats สั้น ๆ เพื่อยืนยันว่าระบบมี monitoring ระดับ business metrics ไม่ใช่แค่รับ-ส่งข้อมูล
5. ถ้าจะใช้รูป ให้โชว์ว่า service ขอ presigned upload URL ได้จริง

### 4. ประเด็นที่ควรพูดเองก่อนกรรมการถาม

1. ระบบนี้รับ natural-language report ได้โดย design เพราะ validation ของ ingest บังคับเพียง `reporter_source`, `reporter_id`, และอย่างน้อยหนึ่งใน `raw_content` หรือ `media_urls`
2. ถ้าไม่มีพิกัด ระบบยังรับได้ แต่ trust score จะไม่เต็มและ dedup/geospatial analytics จะแม่นน้อยลง
3. ถ้า AI ใช้งานไม่ได้ ระบบยังรับงานได้ แต่จะ fallback ไป manual review มากขึ้น
4. environment ปัจจุบันเหมาะสำหรับเดโมและ internal integration มากกว่า production hardening เต็มรูปแบบ

---

## Section II: System Overview (15 นาที)

ส่วนนี้ควรตอบคำถาม 3 เรื่องพร้อมกัน:

1. ระบบนี้แก้ปัญหาอะไร
2. มันทำงานอย่างไรแบบ end-to-end
3. มันเชื่อมกับ service อื่นใน cluster ตรงไหน และไม่เชื่อมตรงไหนเพราะอะไร

### 1. ปัญหาที่ระบบนี้แก้

ในระบบรับมือภัยพิบัติ ปัญหาใหญ่ไม่ใช่แค่ "ข้อมูลมีน้อย" แต่คือ **ข้อมูลเข้ามาเยอะ, มาจากหลายแหล่ง, คุณภาพไม่เท่ากัน, ซ้ำกันง่าย, และถ้าปล่อยให้ข้อมูลที่ยังไม่ยืนยันไหลเข้าระบบอื่นเร็วเกินไปจะทำให้ทั้ง cluster ตัดสินใจผิด**

service นี้จึงถูกออกแบบมาเพื่อเป็นชั้นกลางที่ทำ 5 อย่าง:

1. รับข้อมูลจากหลายแหล่งโดยไม่ต้องบังคับ schema ที่แข็งเกินไป
2. ช่วยคัดกรองความน่าเชื่อถือด้วย AI และ deterministic rules
3. ตรวจ duplicate ทั้งเชิงเวลา, พื้นที่, และเนื้อหา
4. ให้เจ้าหน้าที่เป็นคนตัดสินใจสุดท้าย
5. ส่งต่อเฉพาะข้อมูลที่ verify แล้วไปยังระบบปลายทางผ่าน event

นี่คือเหตุผลว่าทำไม service นี้ถึงมี leverage สูงมากใน cluster: ถ้าชั้น verify แข็งแรง downstream ทุกตัวจะได้ข้อมูลที่สะอาดขึ้นทันที

### 2. องค์ประกอบหลักของระบบจาก implementation จริง

| องค์ประกอบ | ทำหน้าที่อะไร | เหตุผลที่มีอยู่ใน architecture |
| --- | --- | --- |
| API Gateway | รับ HTTP requests จาก client | เป็นทางเข้าหลักของระบบและแยก route ไป Lambda แต่ละตัว |
| `ingest_handler` | รับ report ใหม่แล้ว enqueue SQS | ทำให้ client ได้ `202 Accepted` เร็วและไม่ต้องรอ AI/DB ครบทุกขั้น |
| SQS + DLQ | buffer งาน ingestion | รับ burst traffic ได้ดีและแยก failure/retry ออกจาก user-facing path |
| `ingestion_worker` | ประมวลผล report จาก SQS | เป็นจุดรวม logic สำคัญ: trust score, dedup, initial status, stats |
| DynamoDB reports table | เก็บ report หลัก | เหมาะกับ access pattern แบบ key-based และ scale ใน serverless |
| DynamoDB audit table | เก็บ audit log | ทำให้ตรวจย้อนกลับได้ว่าใครเปลี่ยนสถานะอะไร เมื่อไร |
| DynamoDB stats table | เก็บ counter และสถิติภาพรวม | ใช้ตอบ dashboard/stats โดยไม่ต้องคำนวณใหม่ทุกครั้ง |
| `api_handler` | ให้ admin/client query, verify, delete, stats, events, upload-url, callback | รวม synchronous operations ที่เกี่ยวกับ human review และ reporting |
| `health_handler` | health check dependencies | ใช้ยืนยัน readiness ก่อนเดโมและก่อนปล่อยจริง |
| `gemini_service` | วิเคราะห์ข้อความและรูปภาพ | ช่วยเพิ่มสัญญาณให้เจ้าหน้าที่ตัดสินใจเร็วขึ้น |
| `dedup_service` | ตรวจ duplicate | ลด noise และลดโอกาสนับจำนวนเหตุผิด |
| `audit_service` | เขียน audit records | สำคัญต่อ accountability ของเจ้าหน้าที่ |
| `event_publisher` | publish `ReportVerifiedEvent` และ `ReportStatusChangedEvent` | ทำให้ระบบเชื่อมกับ downstream แบบ loosely coupled |
| Reverse geocoding service | แปลง lat/lon เป็น address text | ช่วยให้ event ที่ส่งต่ออ่านง่ายขึ้นสำหรับระบบอื่นและมนุษย์ |
| S3 website/frontend | แสดง dashboard และ admin console | ทำให้เดโมเห็นภาพ end-to-end ได้เร็ว |
| S3 media bucket | เก็บหลักฐานรูปภาพ | รองรับ report ที่มี media evidence |

### 3. ข้อมูลไหลอย่างไรแบบ end-to-end

#### 3.1 Ingestion flow

ลำดับจริงในระบบเป็นแบบนี้:

1. Client ส่ง `POST /v1/reports`
2. `ingest_handler` validate payload เบื้องต้น
3. Handler สร้าง `report_id` แล้วส่ง message เข้า SQS
4. Client ได้ `202 Accepted` กลับทันที
5. `ingestion_worker` ดึง message จาก SQS มาประมวลผล
6. Worker query ประวัติ reporter เดิมเพื่อคำนวณ reporter history score
7. Worker เรียก Gemini เพื่อวิเคราะห์ content และ/หรือ image ถ้ามี media
8. Worker คำนวณ trust score แบบผสม AI + rule-based
9. Worker ตรวจ duplicate
10. Worker ตัดสิน initial status เป็น `SPAM`, `DUPLICATE`, หรือ `PENDING_REVIEW`
11. Worker บันทึก report ลง DynamoDB
12. Worker อัปเดต stats และ publish status-changed event สำหรับกรณีที่ถูก auto-process

ประเด็นสำคัญคือ service นี้ **ไม่ auto-verify** รายงานปกติให้เป็น `VERIFIED` ตั้งแต่แรก แต่จะหยุดที่ `PENDING_REVIEW` เพื่อให้คนตัดสินใจ

#### 3.2 Verification flow

เมื่อเจ้าหน้าที่เปิดหน้า review:

1. หน้า `admin-verify` เรียก `GET /v1/reports` เพื่อดึงรายการ
2. เจ้าหน้าที่เปิดรายละเอียด report ดูข้อความ, media, AI analysis, trust score, duplicate candidates, suggested category
3. เจ้าหน้าที่ตัดสินใจ `VERIFIED`, `SPAM`, `REJECTED`, หรือ `DUPLICATE`
4. `api_handler` ตรวจว่าการเปลี่ยนสถานะถูกต้องตาม state transition หรือไม่
5. ระบบเขียน audit log
6. ระบบอัปเดต stats
7. ระบบ publish `ReportStatusChangedEvent`
8. ถ้าเจ้าหน้าที่กด `VERIFIED` ระบบจะ publish `ReportVerifiedEvent` พร้อม `suggested_incident_data`

จุดสำคัญคือ `VERIFIED` เป็น gate ที่คุม downstream impact ทั้งหมด นี่คือหัวใจของ service นี้

#### 3.3 ข้อมูลอะไรถูกส่งต่อเมื่อ verify

ตอน verify แล้ว publish `ReportVerifiedEvent` ระบบไม่ได้ส่งแค่ข้อความดิบ แต่ enrich ข้อมูลเพิ่มด้วย เช่น:

1. `type` จาก suggested category
2. `description` จากข้อความรายงาน
3. `severity_level` ที่คำนวณจากเนื้อหา
4. `location` ถ้ามีพิกัด
5. `reporter_count` ที่คำนวณจาก duplicate/related reports
6. `media_evidence`
7. `address_text` จาก reverse geocoding ถ้าหาได้

แปลว่า service นี้ไม่ได้เป็นแค่ "ฟอร์มรับเรื่อง" แต่ทำหน้าที่ convert ข้อมูลดิบให้เป็น payload ที่ downstream ใช้งานได้ง่ายขึ้น

### 4. ระบบคำนวณ trust score อย่างไร และทำไมตอบคำถามอาจารย์ได้ดี

`ingestion_worker.py` ระบุองค์ประกอบของ trust score ไว้ชัดเจน รวม 100 คะแนน:

1. คุณภาพเนื้อหา 0-30 คะแนน จาก Gemini
2. ความน่าเชื่อถือของ source platform 0-20 คะแนน
3. ประวัติผู้แจ้ง 0-20 คะแนน
4. หลักฐานสื่อ 0-20 คะแนน
5. ข้อมูลพิกัด 0-10 คะแนน

ตัวอย่าง deterministic rule ที่ยกอธิบายบนเวทีได้เลย:

1. `IOT_SENSOR` ได้ base source score สูงกว่าช่องทาง social media
2. ผู้แจ้งที่เคยมีประวัติ verified หลายครั้งจะได้ bonus
3. ผู้แจ้งที่มีประวัติ spam จะโดน penalty
4. ถ้ามี media evidence จะได้คะแนนเพิ่ม และถ้า vision analyze ได้ก็ใช้ image score จริง
5. ถ้ามีพิกัด lat/lon ชัดเจน จะได้คะแนน geography เพิ่ม

threshold สำคัญจาก config ปัจจุบันคือ:

1. `trust_score < 30` มีสิทธิ์ถูกตัดเป็น `SPAM`
2. `trust_score >= 80` จะถูกจัดเป็น high priority ทันที

นอกจากนี้แม้ trust score ยังไม่ถึง 80 แต่ถ้าข้อความมี keyword อันตราย เช่นลักษณะ SOS, น้ำท่วม, ไฟไหม้, แผ่นดินไหว หรือคำ severity สำคัญ ระบบก็ยังสามารถ flag เป็น priority สูงได้

นี่คือเหตุผลที่เวลาถูกถามว่า "AI ของคุณไม่ได้แค่สรุปข้อความใช่ไหม" เราสามารถตอบได้เต็มปากว่าไม่ใช่ เพราะ final decision ของระบบเกิดจาก **AI + deterministic scoring + reporter history + media + geo + human review**

### 5. เหตุผลที่ต้องมี human-in-the-loop

นี่คือจุดที่ควรพูดให้ชัด เพราะเป็นเหตุผลเชิงสถาปัตยกรรม ไม่ใช่ข้อจำกัดเฉย ๆ

เราเลือก human-in-the-loop เพราะ false positive ในระบบภัยพิบัติมีต้นทุนสูงมาก เช่น:

1. ส่งทีมกู้ภัยไปผิดจุด
2. สร้าง incident ซ้ำ
3. ปิดถนนหรือแจ้งเตือนประชาชนผิดพื้นที่
4. ส่งผู้ป่วยไปโรงพยาบาลผิดแห่ง
5. ทำให้ dashboard ส่วนกลางตื่นตระหนกจากข้อมูลปลอม

ดังนั้น service นี้จึง intentionally หยุดที่ `PENDING_REVIEW` สำหรับ report ปกติ ไม่ทำ auto-create incident ตั้งแต่ข้อความแรก เพราะโค้ดวางให้เจ้าหน้าที่เป็น decision gate จริง

### 6. จุดเด่นเชิงสถาปัตยกรรมที่ควรย้ำ

#### 6.1 Event-driven และ loosely coupled

`event_publisher.py` publish แยก 2 ประเภท:

1. `ReportVerifiedEvent` สำหรับ downstream ที่ต้องการข้อมูลเหตุที่ verified แล้ว
2. `ReportStatusChangedEvent` สำหรับ dashboard, notification, หรือระบบเฝ้าดูสถานะ

ข้อดีคือ service นี้ไม่ต้องรู้ internals ของ downstream ทุกตัว และ downstream ก็ไม่ต้องมาผูกกับ database ของเราโดยตรง

#### 6.2 Graceful degradation

ถ้า Gemini key หมด, model ใช้ไม่ได้, หรือ API fail ระบบไม่ได้ล่มทั้งก้อน แต่ fallback ไปใช้ค่า default และบังคับให้พึ่ง manual review มากขึ้น

นี่เป็น design ที่เหมาะกับระบบฉุกเฉิน เพราะ availability สำคัญกว่าการรอให้ AI สมบูรณ์แบบทุกครั้ง

#### 6.3 Traceability และ auditability

ระบบมี:

1. audit log ต่อ report
2. `X-Trace-Id`
3. endpoint `GET /v1/reports/trace/{trace_id}` สำหรับช่วยตาม log ใน CloudWatch
4. endpoint `GET /v1/reports/events` เพื่อดู event ล่าสุดจาก CloudWatch Logs

เพราะฉะนั้นเวลาโดนถามว่า "ถ้า verify ผิดจะตรวจย้อนหลังได้ไหม" คำตอบคือได้ และมีทั้ง audit trail และ trace lookup รองรับ

### 7. ขอบเขตของระบบนี้เมื่อเทียบกับ cluster

ตรงนี้ต้องตอบอย่างซื่อสัตย์ที่สุด เพราะกรรมการมักถาม scenario ที่กว้างกว่าขอบเขต service เดียว

#### 7.1 สิ่งที่ repo นี้ทำได้โดยตรงจากโค้ดปัจจุบัน

1. รับ report ดิบจากหลายช่องทาง
2. วิเคราะห์ข้อความ/รูปเพื่อช่วยประเมิน
3. ให้คะแนนความน่าเชื่อถือ
4. ตรวจ duplicate
5. ให้เจ้าหน้าที่ verify/reject/delete
6. สร้าง payload สำหรับ incident ใหม่หรือ merge กับ incident เดิม
7. publish event ที่ verified แล้ว
8. รับ callback กลับจาก incident side ผ่าน `POST /v1/report-incident`
9. สรุป stats, audit, และ recent events

#### 7.2 สิ่งที่ repo นี้ไม่ได้ implement โดยตรง

1. การ dispatch ทีมกู้ภัย
2. การเลือกโรงพยาบาลหรือบริหารทรัพยากรโรงพยาบาล
3. การค้นหาศูนย์พักพิงว่างหรือจอง capacity
4. การจัดการ donation inventory และ matching
5. การทำ missing person matching/search
6. การทำเคลมความเสียหายทรัพย์สินแบบเต็ม workflow
7. การคำนวณเส้นทางปลอดภัย

เหตุผลไม่ใช่เพราะระบบ "ทำไม่ได้เลย" แต่เพราะเราแบ่ง ownership ตาม microservice boundary

#### 7.3 แล้วระบบนี้เชื่อมกับ cluster อย่างไร

จากโค้ดจริง integration ที่ implement ชัดที่สุดคือ:

1. publish `ReportVerifiedEvent` ไปยัง downstream incident side
2. publish `ReportStatusChangedEvent`
3. รับ callback กลับที่ `POST /v1/report-incident`

ส่วนจาก proposal ของทีมอื่นใน `docs/friends_service/` สามารถใช้พูดเชิงสถาปัตยกรรมได้ว่า verified reports จาก service นี้เหมาะจะถูกนำไปใช้ต่อโดย:

1. Incident Tracking สำหรับสร้าง/merge incident กลาง
2. Rescue/Dispatch side สำหรับจัดทีมช่วยเหลือ
3. Hospital Resource Monitoring สำหรับเคสผู้ป่วย
4. Shelter Service สำหรับเคสศูนย์พักพิง
5. Donation Tracking สำหรับของบริจาค
6. Trace Missing สำหรับเคสคนหาย
7. Property Damage Report สำหรับความเสียหายทรัพย์สิน
8. SafeRoute สำหรับประเมินเส้นทางปลอดภัย

แต่ต้องพูดกำกับทุกครั้งว่า:

> "repo นี้เป็น upstream verified-intake service ของ cluster ไม่ได้ contain logic ภายในของ service ปลายทางเหล่านั้น"

### 8. หลักฐานว่าพฤติกรรมเหล่านี้ไม่ได้มีแค่ในเอกสาร

สิ่งที่ทำให้ตอบอย่างมั่นใจได้คือ behavior หลายอย่างมี test รองรับจริง เช่น:

1. `tests/e2e/test_ingest_flow.py` ยืนยันเส้นทาง ingest แบบ end-to-end
2. `tests/e2e/test_verify_flow.py` ยืนยัน verify flow
3. `tests/integration/test_sqs_flow.py` ยืนยัน SQS -> worker -> DynamoDB
4. `tests/integration/test_eventbridge.py` ยืนยันการ publish event
5. `tests/integration/test_dynamodb_ops.py` ยืนยัน audit query และ atomic stats increment
6. `tests/unit/test_api_handler.py` ยืนยัน upload URL, verify flow, enriched verified payload
7. `tests/unit/test_ingestion_worker.py` ยืนยัน trust/status/priority logic

เวลาถูกถามว่า "นี่คิดเองหรือทำงานจริง" สามารถตอบได้ว่ามีทั้งโค้ด, infrastructure, UI, และ automated tests สอดคล้องกัน

---

## Section III: Live Simulation Demo (45 นาที)

ส่วนนี้เป็นหัวข้อที่กรรมการมักใช้วัดว่าเราเข้าใจขอบเขต service ตัวเองจริงหรือไม่ เพราะจะมีทั้งเคสที่ระบบเราทำได้ตรง ๆ และเคสที่ต้องตอบแบบ "รับได้-verify ได้-ส่งต่อได้ แต่ไม่ใช่ owner ของ workflow ปลายทาง"

### 1. Script เดโมที่แนะนำ

ลำดับที่แนะนำสำหรับ 45 นาทีคือ:

1. เริ่มด้วย `health` และ stats สั้น ๆ เพื่อยืนยันระบบพร้อม
2. ยิง report เข้ามา 1 เคสจาก `dashboard` หรือ client demo
3. โชว์ว่า API ตอบ `202 Accepted` ทันที
4. สลับไปหน้า `admin-verify` เพื่อรอ item เข้า queue review
5. เปิดรายละเอียด report ให้เห็น trust score, AI analysis, source, media, suggested incident data
6. กด `VERIFIED` หรือ `REJECTED` ตาม scenario
7. โชว์ audit trail หลัง action
8. โชว์ recent events ว่ามี `ReportVerifiedEvent` หรือ `ReportStatusChangedEvent`
9. ถ้ามี scenario ต่อเนื่อง ให้ยิง report ใหม่แล้ว verify พร้อม `link_to_incident_id` เพื่อ merge เข้ากับ incident เดิม

ถ้าจะให้ดูสวยและลื่น ควรแบ่งการเดโมเป็น 3 ประเภทเคส:

1. เคสที่ระบบนี้รองรับได้ชัดและโชว์ strength ได้เต็มที่
2. เคสที่ระบบนี้รับและ verify ได้ แต่ต้อง handoff ไป service อื่น
3. เคสที่ระบบนี้ไม่ใช่ owner โดยตรง แต่ยังทำหน้าที่เป็น verified intake layer ได้

### 2. หลักการตอบเมื่อเจอ scenario ที่เกิน scope

ถ้าอาจารย์โยน scenario ที่ระบบนี้ไม่ใช่ owner ห้ามตอบแค่ว่า "ไม่รองรับ" เพราะจะเสียคะแนน integration thinking ควรตอบแบบ 4 ชั้น:

1. **รับข้อมูลได้ไหม**: ได้ เพราะ payload รองรับ natural language report
2. **ช่วยคัดกรอง/verify ได้ไหม**: ได้ เพราะมี AI + trust score + human review
3. **ระบบนี้ทำ action ปลายทางเองไหม**: ไม่เสมอไป ขึ้นกับ domain ownership
4. **แล้วส่งต่อใคร**: ส่ง event/incident ไปยัง service owner ที่เหมาะสม

รูปแบบประโยคที่ควรใช้คือ:

> "เคสนี้ service ของเรารับเข้าและ verify ได้แน่นอน เพื่อให้ข้อมูลที่ downstream เชื่อถือได้ แต่ workflow ปลายทาง เช่น dispatch, shelter allocation, hospital assignment หรือ missing-person matching จะเป็นหน้าที่ของ service owner ตัวนั้น ๆ ใน cluster"

### 3. การตอบราย scenario ตามตัวอย่างที่อาจารย์อาจถาม

#### กรณีที่ 1: เซนเซอร์หรือหน่วยงานรัฐแจ้งระดับน้ำสูงผิดปกติ / มีการเตือนภัย

**ระบบนี้รองรับได้ดีมาก** และควรใช้เป็นตัวเปิดเดโมชุดแรก

เหตุผล:

1. payload รองรับ source ที่เป็น `IOT_SENSOR` หรือ `OFFICIAL_APP`
2. source score ของ `IOT_SENSOR` สูงถึง 20 และ `OFFICIAL_APP` สูงถึง 18 ทำให้ trust score เริ่มต้นดี
3. ถ้ามีพิกัด lat/lon จะได้ geo score เพิ่ม และ downstream map/stats จะมีคุณภาพมากขึ้น
4. หลัง verify แล้ว publish เป็น incident/update ได้ทันที

สิ่งที่ควรสาธิต:

1. ส่งข้อความลักษณะ "ระดับน้ำในคลอง...สูงกว่าค่าปกติ" หรือ "เทศบาลประกาศเตือนอพยพ"
2. ใช้ `reporter_source=IOT_SENSOR` หรือ `OFFICIAL_APP`
3. ให้เจ้าหน้าที่ verify แล้วโชว์ event ที่ถูก publish

สิ่งที่ควรพูดเพิ่ม:

> "service ของเราไม่ใช่ service พยากรณ์อากาศหรือ service แจ้งเตือนประชาชนโดยตรง แต่ทำหน้าที่เปลี่ยนสัญญาณภาคสนามให้เป็น verified event ที่ Incident Tracking หรือระบบแจ้งเตือนส่วนกลางนำไปใช้ต่อได้"

#### กรณีที่ 2: ผู้ประสบภัยส่งข้อความขอความช่วยเหลือ เช่น 'ช่วยด้วย น้ำเข้าบ้านแล้ว ติดอยู่ชั้นสอง'

**ระบบนี้รองรับได้โดยตรงในฐานะ citizen report intake**

เหตุผล:

1. payload รองรับข้อความธรรมชาติใน `raw_content`
2. ไม่บังคับ schema ที่แข็งว่าต้องมี incident type มาก่อน
3. logic priority จะยกระดับเคสที่มี keyword รุนแรง เช่น SOS/อันตราย
4. verify flow รองรับการสร้าง incident ใหม่หลังเจ้าหน้าที่ยืนยัน

สิ่งที่ควรสาธิต:

1. ส่งข้อความตามธรรมชาติจริง ๆ โดยไม่ตกแต่งมาก
2. ถ้ามีพิกัดให้แนบ `geo_location` ด้วย เพื่อให้ trust score และ downstream usefulness สูงขึ้น
3. ในหน้า admin ให้ชี้ให้เห็นว่าระบบเสนอ category และ priority แต่คนยังเป็นผู้ตัดสินใจสุดท้าย

สิ่งที่ควรตอบถ้าถามต่อว่า "แล้วทีมกู้ภัยถูกส่งไปเลยไหม":

> "ไม่ใช่ใน service นี้โดยตรงครับ/ค่ะ เราเป็นชั้น verified intake และ incident trigger ก่อน ส่วนการจัดทีมช่วยเหลือหรือ dispatch ควรเป็น service downstream ที่รับ incident ที่ verify แล้วไปดำเนินการต่อ"

#### กรณีที่ 3: หน่วยงานประกาศอพยพ / แจ้งเส้นทางบางเส้นใช้ไม่ได้

**รองรับได้ดีในฐานะ official situational update** แต่ไม่ใช่ระบบประกาศสาธารณะปลายทางโดยตรง

เหตุผล:

1. ข้อความประเภทประกาศจากหน่วยงานสามารถ ingest ได้เหมือน report ทั่วไป
2. `OFFICIAL_APP` ทำให้ source reliability สูง
3. เจ้าหน้าที่ verify แล้วสามารถสร้าง incident ใหม่ หรือ merge เข้ากับ incident เดิมได้
4. downstream ที่เหมาะสมคือ Incident Tracking, Notification, หรือ SafeRoute side

วิธีเดโมที่ดี:

1. เริ่มจากมี incident น้ำท่วมอยู่แล้ว
2. ยิงรายงานใหม่ว่า "ถนนสาย X ใช้งานไม่ได้ ให้เลี่ยงไปทาง Y"
3. ตอน verify ให้ใส่ `link_to_incident_id` เพื่อแสดงว่าเป็น update ต่อ incident เดิม ไม่ใช่เหตุใหม่แยกออกไป

สิ่งที่ควรพูดกำกับ:

> "ตัว service นี้ไม่ได้คำนวณเส้นทางปลอดภัยเอง แต่ทำให้ข้อมูลภาคสนามนี้ถูก verify และเข้าไปอยู่ใน incident context เพื่อให้ service อย่าง SafeRoute หรือ Notification ใช้ต่อได้"

#### กรณีที่ 4: มีผู้ป่วยหรือผู้สูงอายุอาการหนัก ต้องการส่งต่อโรงพยาบาล

**รองรับได้ในฐานะ urgent medical-related report intake** แต่ไม่ใช่ hospital allocation service

เหตุผล:

1. ระบบรับข้อความธรรมชาติที่สื่อความเร่งด่วนได้
2. severity keywords และ category logic ช่วยยก priority ได้
3. ตอน verify ระบบจะสร้าง enriched payload ที่มี `severity_level`, `reporter_count`, `location`, และ `address_text` ซึ่ง downstream medical/incident service เอาไปใช้ต่อได้ง่าย

การตอบที่ถูกต้องบนเวทีคือ:

> "ระบบของเรารับแจ้งเหตุและ verify ความน่าเชื่อถือของเคสผู้ป่วยได้ จากนั้นส่งต่อเป็น verified incident/update ได้ แต่การเลือกโรงพยาบาลที่เหมาะสม, เช็กทรัพยากร, หรือ dispatch เรือ/รถพยาบาล เป็นหน้าที่ของ hospital/disptach side ไม่ใช่ repo นี้โดยตรง"

ถ้าจะเดโมให้เห็นพลังของระบบนี้ ให้โชว์ว่าเมื่อ verify แล้ว payload ที่ส่งต่อไม่ใช่แค่ข้อความดิบ แต่มี severity และจำนวนผู้รายงานประกอบด้วย

#### กรณีที่ 5: ทีมภาคสนามแจ้งว่าสะพานขาด ถนนใช้ไม่ได้ เรือเข้าพื้นที่ไม่ได้

**รองรับได้ดีมากในฐานะ operational field update**

เหตุผล:

1. นี่คือ report สถานการณ์หน้างานโดยตรง ซึ่งตรงกับขอบเขตระบบ
2. ถ้ามาจากเจ้าหน้าที่ภาคสนามหรือ official channel trust score จะดี
3. ควร verify แล้ว merge เข้า incident เดิม เพื่อทำให้ incident context สมบูรณ์ขึ้น
4. downstream อย่าง Dispatch หรือ SafeRoute จะได้ข้อมูลที่ verified แล้ว

จุดขายของเคสนี้คือ:

> "ระบบของเราไม่ได้คำนวณ route เอง แต่ทำให้ข้อมูล route hazard หรือ access constraint ถูก verify ก่อน แล้วระบบ owner ด้าน route/dispatch ค่อยใช้ข้อมูลนี้ต่อ"

เคสนี้ช่วยโชว์ความสำคัญของ verified updates มาก เพราะถ้าข้อมูลถนนใช้ไม่ได้เป็นข้อมูลผิด downstream จะเสียหายหนัก

#### กรณีที่ 6: ประชาชนแจ้งว่าบ้านหรือทรัพย์สินเสียหาย

**รองรับได้แบบ partial support**

คำตอบที่ถูกต้องคือ:

1. รับแจ้งและ verify ได้แน่นอน
2. ใช้เป็น situational awareness ได้ เช่น รู้ว่าพื้นที่ใดได้รับความเสียหายหนัก
3. แต่ workflow ที่เป็นการประเมินมูลค่าความเสียหาย, แนบเอกสารเคลม, หรือติดตามสถานะการช่วยเหลือทรัพย์สิน ไม่ใช่หน้าที่หลักของ service นี้

เหตุผลจาก implementation:

1. category มี `DAMAGE` และระบบรับข้อความลักษณะนี้ได้
2. แต่ data model ปัจจุบันไม่ได้มีฟิลด์เฉพาะทางสำหรับ claims workflow แบบละเอียด
3. event ที่ส่งต่อเหมาะกับ incident/update มากกว่าการทำ damage-case lifecycle เต็มรูปแบบ

ประโยคที่แนะนำคือ:

> "Request Verify Service เป็นด่านรับและยืนยันความจริงของรายงานความเสียหายได้ แต่ถ้าจะทำเรื่องทรัพย์สินแบบ end-to-end ควรส่งต่อให้ Property Damage Report service ที่เป็นเจ้าของ domain นี้"

#### กรณีที่ 7: มีคนอยากบริจาคอาหาร น้ำ หรือของใช้

**รองรับได้เพียงระดับ intake + verification + handoff เท่านั้น**

นี่เป็นตัวอย่างที่ดีของเคส "ระบบเรารับได้ แต่ไม่ควรแกล้งบอกว่าบริหารทั้ง workflow ได้"

สิ่งที่ทำได้จริง:

1. รับข้อความได้
2. ให้เจ้าหน้าที่อ่านและตัดสินใจว่าเป็นข้อมูลที่ควรเก็บต่อหรือไม่
3. อาจ verify เป็นข้อมูลประกอบสถานการณ์หรือส่งต่อให้เจ้าหน้าที่ที่ดู donation

สิ่งที่ยังไม่ใช่หน้าที่ของ repo นี้:

1. จัด inventory สิ่งของบริจาค
2. matching ความต้องการกับ supply
3. ติดตามสถานะการรับ-ส่งของบริจาค
4. บริหารผู้บริจาค/ผู้รับแบบ domain-specific

ดังนั้นคำตอบที่ดีคือ:

> "ระบบเราทำหน้าที่รับและ verify ข้อมูลเพื่อไม่ให้ข้อมูลดี ๆ หลุดหาย แต่ donation lifecycle จริงควรเป็นหน้าที่ของ Donation Tracking service เพราะต้องมีข้อมูลและ business rules เฉพาะทางมากกว่า report verification"

#### กรณีที่ 8: ญาติแจ้งตามหาคนหายหรือผู้สูญหาย

**รองรับได้ในระดับไม่ให้ข้อมูลสูญหาย แต่ไม่ใช่ owner ของการ matching/search**

สิ่งที่ระบบนี้ช่วยได้:

1. รับข้อความจากญาติหรือผู้พบเห็นเข้ามาได้
2. เก็บเป็น report ที่ trace ได้
3. ให้เจ้าหน้าที่ verify ว่าเคสนี้ควรถูก escalate หรือ handoff ต่อ

สิ่งที่ระบบนี้ไม่ได้ทำ:

1. matching คนหายกับรายชื่อผู้ประสบภัยนิรนาม
2. ติดตามสถานะการค้นหา
3. เชื่อม hospital/shelter record แบบ domain-specific

ดังนั้นบนเวทีควรตอบตรง ๆ ว่า:

> "service ของเรารับแจ้งคนหายได้ในฐานะ intake layer แต่การค้นหาและจับคู่ข้อมูลบุคคลไม่ใช่ logic ใน repo นี้ ควรส่งต่อให้ Trace Missing service ที่เป็น owner ของ missing-person workflow"

การตอบแบบนี้ไม่ได้เสียคะแนน ตรงกันข้าม ถ้าตอบชัดจะสะท้อนว่าเข้าใจ service boundary จริง

#### กรณีที่ 9: มีการเปิดศูนย์พักพิงใหม่ หรือมีประกาศว่าศูนย์พักพิงพร้อมรับคน

**รองรับได้แบบ partial support**

สิ่งที่ทำได้ดี:

1. รับประกาศจากหน่วยงานเป็น official report
2. verify เพื่อทำให้ข้อมูลนี้เชื่อถือได้ก่อน
3. merge เข้ากับ incident ที่เกี่ยวข้องหรือส่งต่อเป็น verified event

สิ่งที่ไม่ได้ทำโดยตรง:

1. เก็บ master data ของ shelter
2. บริหาร capacity แบบ real-time
3. ค้นหา shelter ที่เหมาะที่สุด
4. จองที่พักพิงให้ผู้ประสบภัย

ดังนั้นคำตอบที่ควรใช้คือ:

> "service ของเราช่วย verify ข่าวสารเรื่อง shelter ได้ แต่ shelter capacity/availability และการจัดสรรผู้ประสบภัยควรเป็นหน้าที่ของ Shelter Service ที่เป็นเจ้าของข้อมูลศูนย์พักพิง"

เคสนี้เดโมได้ดีมากถ้าทำเป็น follow-up report ของ incident เดิมแล้วใช้ `link_to_incident_id`

#### กรณีที่ 10: สถานการณ์เริ่มคลี่คลาย น้ำลดแล้ว คนเริ่มกลับบ้านได้

**รองรับได้ดีในฐานะ incident update / recovery signal**

เหตุผล:

1. report ใหม่สามารถใช้เป็น follow-up update ต่อ incident เดิมได้
2. เจ้าหน้าที่สามารถ verify แล้วใส่ `link_to_incident_id` เพื่อ merge
3. downstream incident side จึงมองเห็นว่าบริบทของเหตุเปลี่ยน ไม่ใช่เกิดเหตุใหม่

แต่สิ่งที่ต้องพูดให้ถูกคือ:

> "service นี้ช่วยรับและ verify สัญญาณว่าพื้นที่เริ่มกลับสู่สภาพปกติได้ แต่การปิด incident อย่างเป็นทางการ, การสรุปภารกิจ, หรือการจัดการ recovery workflow ระยะถัดไป จะอยู่ที่ incident/operations side มากกว่า"

เคสนี้เหมาะมากสำหรับปิดเดโม เพราะทำให้เห็นว่า service ไม่ได้มีประโยชน์เฉพาะตอนเกิดเหตุ แต่ยังใช้เก็บ verified updates ตลอด lifecycle ของเหตุการณ์

### 4. Scenario ไหนควรใช้โชว์จุดแข็งที่สุด

ถ้าเลือกเองได้ ควรเรียงลำดับความสวยของเดโมประมาณนี้:

1. **เคสแจ้งเหตุฉุกเฉินจากประชาชน**: เห็นชัดเรื่อง natural-language intake + human verification
2. **เคสจาก sensor/official source**: โชว์ source trust และ event-driven integration
3. **เคส update เหตุการณ์เดิม**: โชว์ `link_to_incident_id` และ incident merge thinking
4. **เคสมีรูปภาพ**: โชว์ multimodal AI และ media evidence
5. **เคสที่ไม่ใช่ owner domain โดยตรง** เช่น donation/missing/shelter: ใช้โชว์ maturity เรื่อง service boundary

### 5. คำถามยากที่น่าจะโดนถาม และคำตอบที่ควรตอบ

#### 5.1 "ทำไมไม่ให้ AI verify ไปเลย"

คำตอบ:

> "เพราะต้นทุนของ false positive ในระบบภัยพิบัติสูงมาก เราจึงใช้ AI เพื่อช่วยจัดลำดับและเสนอข้อมูล แต่ให้มนุษย์เป็น decision gate ตอนเปลี่ยนเป็น VERIFIED ซึ่งโค้ดปัจจุบันก็ออกแบบไว้แบบนั้นจริง"

#### 5.2 "ถ้า Gemini ล่ม ระบบหยุดไหม"

คำตอบ:

> "ไม่หยุดทั้งระบบ เพราะ `gemini_service` มี fallback result และ service ยังรับ report, เข้าคิว, และให้เจ้าหน้าที่ review ด้วยมือได้ เพียงแต่คุณภาพการช่วยวิเคราะห์จะลดลง"

#### 5.3 "ถ้ามีคนส่งข้อความซ้ำกันเยอะ ๆ จะทำอย่างไร"

คำตอบ:

> "ระบบมี duplicate detection หลายชั้น ทั้ง external ID, ใกล้กันภายในรัศมีประมาณ 200 เมตรและ 15 นาที, และ content similarity จึงลดโอกาสนับเหตุซ้ำหรือสร้าง incident ซ้ำได้"

#### 5.4 "ถ้าข้อความมีแต่คำพูดธรรมชาติ ไม่มีพิกัด จะใช้ได้ไหม"

คำตอบ:

> "ยังใช้ได้ เพราะ ingest schema ออกแบบมาให้รับ natural-language report เป็นหลัก แต่ถ้าไม่มีพิกัด trust score และ geospatial usefulness จะต่ำลง จึงเหมาะให้เจ้าหน้าที่เติมข้อมูลหรือใช้เป็น report ที่ต้อง review มากขึ้น"

#### 5.5 "ทำไมไม่ต่อกับ hospital/shelter/donation/missing service โดยตรงใน repo นี้เลย"

คำตอบ:

> "เพราะ service นี้ออกแบบมาให้เป็น verified intake layer การเอา domain logic ของทุกบริการมายัดไว้ที่เดียวจะทำให้ boundary พังและ coupling สูงเกินไป ทางที่ถูกคือ verify ให้ดีแล้ว publish event/incident ต่อให้ service owner แต่ละตัวไปจัดการ workflow เฉพาะของตนเอง"

### 6. ข้อจำกัดที่ควรพูดเองอย่างตรงไปตรงมา

การพูดข้อจำกัดเองก่อนจะดูน่าเชื่อถือกว่ารอให้ถูกจับผิด

1. direct integration ที่เห็นชัดในโค้ดตอนนี้เน้น incident/event side เป็นหลัก ไม่ได้มี client call ไปทุก service ใน cluster
2. security ของ admin/read endpoints ยังเป็น demo-friendly มากกว่า production-grade
3. ถ้า data input ไม่ใส่พิกัดหรือ media downstream usefulness จะลดลง
4. service นี้ไม่ใช่ source of truth ของ hospital, shelter, donation, missing person, หรือ property claim data
5. การตัดสินใจสุดท้ายยังพึ่งเจ้าหน้าที่ จึงไม่ได้เป็น fully automated incident creation system

### 7. ประโยคสรุปที่ควรใช้ปิดการนำเสนอ

> "จุดแข็งของ Request Verify Service ไม่ใช่การพยายามทำทุกอย่างเอง แต่คือการเป็น gatekeeper ของข้อมูลเหตุภาคสนาม ทำให้ข้อมูลที่สกปรก, ซ้ำ, และไม่น่าเชื่อถือ ถูกแปลงเป็น verified event ที่ service อื่นใน cluster กล้านำไปใช้ต่อได้อย่างปลอดภัย"

ประโยคนี้สอดคล้องกับ implementation จริงที่สุด และช่วยให้ตอบคำถามข้าม service ได้อย่างมั่นคง

---

## ภาคผนวก: payload ที่เหมาะกับการเดโม

### ตัวอย่าง ingest payload สำหรับเคสข้อความธรรมชาติ

```json
{
  "reporter_source": "LINE",
  "reporter_id": "demo-user-001",
  "raw_content": "ช่วยด้วย น้ำเข้าบ้านแล้ว ติดอยู่ชั้นสอง มีผู้สูงอายุ 1 คน",
  "geo_location": {
    "lat": 13.7563,
    "lon": 100.5018
  },
  "timestamp": "2026-05-14T10:30:00Z"
}
```

### ตัวอย่าง verify payload สำหรับสร้าง incident ใหม่

```json
{
  "validation_status": "VERIFIED",
  "reviewer_id": "officer-demo",
  "reviewer_notes": "ตรวจสอบแล้วตรงกับรายงานภาคสนาม"
}
```

### ตัวอย่าง verify payload สำหรับ merge เข้ากับ incident เดิม

```json
{
  "validation_status": "VERIFIED",
  "reviewer_id": "officer-demo",
  "reviewer_notes": "เป็นอัปเดตเพิ่มเติมของเหตุเดิม",
  "link_to_incident_id": "inc-demo-001"
}
```

### หมายเหตุสำคัญสำหรับวันเดโม

1. ถ้าจะยิงข้อความคล้ายกันหลายรอบ ให้ปรับ timestamp/พิกัด/ถ้อยคำเพื่อไม่ให้โดน dedup โดยไม่ตั้งใจ
2. ถ้าอยากโชว์ media analysis ให้ทดสอบ `upload-url` ล่วงหน้า
3. ถ้าอยากโชว์ lifecycle ของเหตุการณ์ ให้เตรียม incident เดิมไว้แล้วใช้ `link_to_incident_id`
4. ถ้าอยากตอบได้สวยเวลาเจอเคสนอก scope ให้ยึดหลัก `รับได้ -> verify ได้ -> handoff ได้ -> แต่ไม่ claim ว่าเป็น owner ของ workflow ปลายทาง`