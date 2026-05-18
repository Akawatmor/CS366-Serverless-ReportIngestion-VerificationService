# บทพูดนำเสนอระบบ 5-7 นาที

> โทนที่แนะนำ: อธิบายแบบ demo-driven ให้กรรมการเห็นว่า service นี้ไม่ได้แค่รับข้อมูล แต่มี write path, review path, event path, และ traceability ครบ
>
> หน้าจอที่ควรเปิดไว้ล่วงหน้า: `dashboard` 1 tab และ `admin-verify` 1 tab
>
> ถ้ามี `incident_id` ตัวอย่างและ environment ตั้ง `INCIDENT_SERVICE_BASE_URL` แล้ว ให้ใช้ flow link incident เดิมในช่วง verify; ถ้ายังไม่มี ให้พูดตามบรรทัด fallback ที่ผมใส่ไว้ให้

---

## 0:00-0:40 เปิดเรื่อง

"สวัสดีครับ โปรเจกต์นี้คือ Report Ingestion and Verification Service ซึ่งเป็น upstream intake service ของระบบจัดการภัยพิบัติ หน้าที่ของมันไม่ใช่การบริหาร incident ทั้ง lifecycle แต่เป็นการรับ report จากหลายแหล่ง คัดกรอง ประเมินความน่าเชื่อถือ ส่งให้เจ้าหน้าที่ตรวจสอบ และ handoff ต่อไปยัง incident side อย่างเป็นระบบ"

"ปัญหาที่ service นี้แก้คือ เวลามีเหตุจริง report จะเข้ามาเร็วมาก มีทั้งข้อมูลซ้ำ ข้อมูลไม่ครบ และข้อมูลที่เชื่อถือได้ไม่เท่ากัน ถ้าโยนให้คนดูทั้งหมดตั้งแต่ต้น ระบบจะตันเร็วมาก เราเลยออกแบบให้ write path เป็น asynchronous และให้ AI ช่วยคัดกรองก่อนเข้าสู่ human review"

---

## 0:40-1:20 โชว์ health และ architecture แบบสั้น

[เปิดหน้า `dashboard` และกด health]

"ตอนนี้ผมเริ่มจาก health endpoint ก่อน เพราะมันช่วยยืนยันว่าระบบพร้อมทั้งในมุม API, queue, database, AI dependency และ event bus"

"จุดที่สำคัญคือ health ของระบบนี้ไม่ได้เช็กแค่ Lambda ตอบได้ แต่เช็ก DynamoDB, SQS, Gemini และ EventBridge แบบแยก component ดังนั้นถ้า Gemini มีปัญหา ระบบยังทำงานต่อได้ในโหมด degraded และผลคือเราจะพึ่ง manual review มากขึ้น ไม่ใช่ระบบล่มทั้งก้อน"

"Gemini เองก็มี fallback model chain หลายตัว ทำให้ service นี้เหมาะกับงานฉุกเฉินที่ availability สำคัญกว่าการรอ AI ตัวเดียวให้สมบูรณ์แบบทุกครั้ง"

---

## 1:20-2:20 โชว์ ingest path

[อยู่หน้า `dashboard` ยิง `POST /v1/reports`]

"ต่อไปผมจะส่ง report ใหม่เข้าระบบผ่าน `POST /v1/reports` จุดสำคัญคือ endpoint นี้ตอบกลับเป็น `202 Accepted` ไม่ใช่ `200` เพราะเราแยกงานหนักออกไปหลังบ้านผ่าน SQS ตั้งแต่ต้น"

"นี่แปลว่า client ส่งข้อมูลมาแล้วไม่ต้องรอ AI, ไม่ต้องรอ dedup, และไม่ต้องรอ incident creation ระบบจะรับงานเข้าคิวก่อน แล้ว worker ค่อยไปประมวลผลต่อ ทำให้ write path รับโหลดสูงได้ดีกว่า synchronous แบบยิงทีเดียวจบ"

"payload ที่ระบบรับได้มีทั้ง citizen report ทั่วไปที่ใช้ `raw_content`, report ที่แนบ `media_urls`, และกรณี sensor หรือหน่วยงานรัฐที่ส่ง `sensor_data` แบบ structured เช่น `metric_name`, `metric_value`, `threshold`, `observed_at`"

"หลังยิง request แล้ว เราจะได้ `report_id` กลับมาทันที พร้อม `traceId` สำหรับตามรอย request นี้ข้ามหลาย Lambda ในภายหลัง"

ถ้าจะเดโม upload media ด้วย ให้พูดเพิ่มว่า:

"ถ้าต้องใช้รูปหรือวิดีโอ ระบบมี `POST /v1/reports/upload-url` เพื่อขอ presigned URL ก่อน แล้วค่อยเอา `media_url` ที่ได้กลับมาแนบใน report จริง ทำให้เราไม่ต้องส่งไฟล์หนักผ่าน ingest API ตรง ๆ"

---

## 2:20-3:30 โชว์ admin review และ AI-assisted triage

[สลับไปหน้า `admin-verify` รีเฟรชรายการ]

"ตอนนี้ผมสลับมาที่หน้า admin review จะเห็นว่ารายงานที่เข้ามาไม่ได้ถูกส่งต่อไปสร้าง incident ทันที แต่จะมาอยู่ในสถานะ `PENDING_REVIEW` ก่อน เพื่อให้เจ้าหน้าที่มีสิทธิ์ตัดสินใจขั้นสุดท้าย"

"เบื้องหลัง worker จะทำ 3 อย่างหลัก ๆ คือ หนึ่ง วิเคราะห์ด้วย Gemini เพื่อสร้าง content score และ reasoning สอง ประกอบคะแนนรวมกับ source score, history score และ media score ให้เป็น trust score และสาม ตรวจ duplicate จากเวลา พิกัด และข้อมูลเดิมในระบบ"

"สิ่งที่เจ้าหน้าที่ได้เห็นจึงไม่ใช่แค่ข้อความดิบ แต่เป็น report ที่มี trust score, suggested category, AI reasoning, duplicate candidates และข้อมูลประกอบอื่นพร้อมใช้ในการตัดสินใจ ซึ่งลดงาน manual triage ได้มาก"

"ถ้าเป็น `IOT_SENSOR` เราจะเห็น `sensor_data` อยู่ใน detail ด้วย จุดนี้สำคัญเพราะระบบไม่ได้บังคับให้ sensor ต้องเขียน narrative เหมือน human reporter แต่รองรับ structured alert โดยตรง"

---

## 3:30-4:40 โชว์ verify path และ incident handoff

[เลือก report หนึ่งรายการแล้วกด verify]

"ตอนนี้ผมจะ verify report นี้ ขั้นตอนนี้เป็น human-in-the-loop gate ของระบบ คือ AI ช่วยคัดกรองได้ แต่การยืนยันว่า report นี้พร้อม handoff หรือไม่ ยังต้องผ่านเจ้าหน้าที่ก่อน"

ถ้ามี incident เดิมเตรียมไว้ ให้พูดว่า:

"ในช่อง `link_to_incident_id` ผมสามารถใส่ incident เดิมได้ ถ้า environment นี้ตั้งค่า Incident Service ไว้ ระบบ backend จะ validate incident reference นี้ก่อน แล้วจึงส่ง merge intent ออกไปพร้อม event"

ถ้ายังไม่มี incident เดิม ให้พูดว่า:

"ถ้าไม่ใส่ `link_to_incident_id` ระบบจะถือว่าเป็น verified report ที่พร้อม trigger incident ใหม่ downstream"

"จุดสำคัญคือ service นี้ไม่ได้ claim ว่าเป็น owner ของ incident lifecycle แต่ทำหน้าที่ publish verified data ที่พร้อมใช้งานต่อ ดังนั้น action หลัง verify จะออกมาเป็นทั้งกรณี trigger new incident หรือ merge existing incident ตามบริบทที่เจ้าหน้าที่เลือก"

---

## 4:40-5:40 โชว์ events, audit, และ traceability

[กลับหน้า `dashboard` เปิด events หรือ audit]

"หลัง verify แล้ว ระบบจะ publish event ออกไปผ่าน EventBridge โดยมีอย่างน้อย 2 ชนิดคือ `ReportVerifiedEvent` และ `ReportStatusChangedEvent` เพื่อให้ downstream service มารับต่อแบบ decoupled"

"นอกจาก event path แล้ว ระบบยังเก็บ audit log ของการเปลี่ยนสถานะไว้ด้วย ทำให้เราตอบได้ว่า report นี้ถูกใครแก้ ถูก verify เมื่อไร และถ้ามี callback จาก incident side ระบบก็จะบันทึกการ link กลับเข้ามาอีกชั้นหนึ่ง"

[เปิด trace panel ถ้ามีเวลา]

"ส่วน `traceId` ที่ได้จากตอน ingest สามารถใช้ตามรอยข้ามหลาย Lambda ได้ผ่าน trace lookup endpoint ทำให้เวลา debug production issue เราไม่ต้องเดาว่า request หายตรงไหน แต่สามารถไล่จาก write path ไปจนถึง event path ได้จริง"

---

## 5:40-6:20 ปิดการนำเสนอ

"สรุปสั้น ๆ คือ service นี้รับ report ได้จากหลาย source, scale write path ได้ด้วย queue, ช่วยคัดกรองด้วย AI, เปิดโอกาสให้ human verify ก่อน handoff, และมี event plus audit plus trace ครบสำหรับใช้งานในระบบที่ต้องการความน่าเชื่อถือ"

"ดังนั้นคุณค่าหลักของโปรเจกต์นี้ไม่ใช่แค่รับข้อความเข้า API แต่คือการเปลี่ยน raw disaster reports ให้กลายเป็น verified, traceable, integration-ready data สำหรับระบบจัดการภัยพิบัติส่วนอื่นของ cluster"

"ถ้ามองในเชิง architecture จุดแข็งคือ decoupling, graceful degradation และการออกแบบให้คนกับระบบอัตโนมัติทำงานร่วมกันได้อย่างชัดเจน ขอบคุณครับ"

---

## หมายเหตุสั้นก่อนอัดคลิป

1. ถ้าจะโชว์ media flow ให้เตรียมรูปไว้ล่วงหน้าและยิง upload-url ก่อนเริ่มอัด
2. ถ้าจะโชว์ merge incident เดิม ให้เตรียม `incident_id` ที่ lookup ได้จริงก่อน
3. ถ้าเวลาจำกัด ให้ตัดส่วน trace panel ออกก่อนส่วนอื่น
4. ถ้า review list ยังไม่ขึ้นทันทีหลัง ingest ให้เว้นจังหวะสั้น ๆ แล้วรีเฟรชหน้า admin-verify
