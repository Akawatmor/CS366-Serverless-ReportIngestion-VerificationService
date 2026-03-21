# Q&A Preparation — คำถามที่อาจถูกถาม (15 ข้อ)

> เรียงจากคำถามที่มีโอกาสถูกถามสูงสุด → ต่ำสุด

---

## Q1: ทำไมถึงเลือกใช้ Google Gemini แทน Amazon Comprehend?

**คำตอบ**:  
> "AWS Learner Lab ไม่รองรับ Amazon Comprehend ครับ ตรวจสอบจาก allow list แล้วไม่มี Comprehend จึงเลือกใช้ Google Gemini API แทน ซึ่งเป็น External Service ไม่ถูกจำกัดโดย Learner Lab ข้อดีคือ Gemini สามารถทำได้ทั้ง text classification, trust scoring, และให้เหตุผลประกอบ (reasoning) ในการเรียก API ครั้งเดียว ซึ่ง Comprehend ต้องเรียกหลาย API แยกกันครับ"

---

## Q2: ถ้า Gemini API ล่มหรือ Rate Limit จะเกิดอะไรขึ้น?

**คำตอบ**:  
> "ระบบมี 3 ชั้นป้องกันครับ:"
> 1. **Multi-key rotation** — มี 2 API keys ถ้า key แรกโดน rate limit ก็สลับไป key ที่สอง
> 2. **Model fallback** — ถ้า model แรก (gemini-2.5-flash-lite) ใช้ไม่ได้ก็ fallback ไป gemini-2.0-flash แล้วก็ gemini-3.1-flash-lite
> 3. **Fallback result** — ถ้าทุก key + ทุก model ล่มหมด ระบบจะ return ค่า default (trust_score=50, category=OTHER, ai_analysis_failed=true) แทนที่จะ crash ข้อมูลจะไม่หาย แค่ยังไม่ได้วิเคราะห์
>
> "นอกจากนี้ SQS ยังมี visibility timeout + DLQ — ถ้า process ล้มเหลว message จะกลับเข้าคิว retry ได้ 3 ครั้ง ถ้ายังไม่ได้ก็เข้า Dead Letter Queue ไม่มี data loss ครับ"

---

## Q3: Optimistic Locking ทำงานยังไง? ทำไมไม่ใช้ DynamoDB Transaction?

**คำตอบ**:  
> "ใช้ ConditionExpression ของ DynamoDB ครับ — เวลา update สถานะ ระบบจะส่ง condition ว่า 'validation_status ต้องเท่ากับค่าที่อ่านมา' ถ้ามีคนอื่นเปลี่ยนไปก่อนแล้ว DynamoDB จะ throw ConditionalCheckFailedException ระบบก็ return 409 Conflict"
>
> "ที่ไม่ใช้ Transaction เพราะ operations ต่อเนื่อง 3 ขั้นตอน (update_item → put_item audit → put_events) ถ้าขั้นแรกล้มเหลวก็ไม่ทำขั้นต่อไป เป็น sequential ไม่จำเป็นต้อง atomic ทั้ง 3 แถม Transaction มี cost สูงกว่า 2 เท่าสำหรับ WCU ครับ"

---

## Q4: Deduplication ใช้วิธีอะไร? แม่นยำแค่ไหน?

**คำตอบ**:  
> "ใช้ 3 เงื่อนไขร่วมกันครับ:"
> 1. **Idempotency** — ตรวจ source_external_id ผ่าน GSI ถ้า external ID ซ้ำ = skip ทันที
> 2. **Geospatial** — ใช้ Haversine formula คำนวณระยะจาก GPS ถ้าอยู่ในรัศมี 200 เมตร = อาจซ้ำ
> 3. **Time window** — เหตุการณ์ต้องเกิดภายใน 15 นาทีเดียวกัน
>
> "ต้องผ่านทั้ง geo + time ถึงจะถือว่า duplicate ครับ ไม่ได้ดูแค่ตำแหน่งอย่างเดียว ค่า 200m กับ 15 นาทีปรับได้ผ่าน environment variable DEDUP_RADIUS_METERS และ DEDUP_TIME_WINDOW_MINUTES"

---

## Q5: ทำไมใช้ SQS แทนการ process ตรงใน Lambda เดียวกัน?

**คำตอบ**:  
> "เพื่อ decouple ครับ — API ที่รับข้อมูลต้องตอบเร็ว (< 500ms) แต่การเรียก Gemini AI อาจใช้เวลา 2-5 วินาที ถ้า process ตรงเดียวกัน client ต้องรอนาน"
>
> "SQS ช่วยให้:"
> 1. API ตอบ 202 ทันที — ไม่ต้องรอ AI
> 2. Worker scale ได้อิสระจาก API
> 3. ถ้า Worker ล่ม message ยังอยู่ใน queue retry ได้
> 4. มี DLQ สำหรับ message ที่ fail 3 รอบ — zero data loss
>
> "ตรงตาม Non-Functional Requirement เรื่อง Asynchronous Processing ใน Proposal ครับ"

---

## Q6: State Transition มีอะไรบ้าง? ทำไม VERIFIED ถึงเปลี่ยนไม่ได้?

**คำตอบ**:  
> "State Machine มี 7 สถานะครับ:"
> - RECEIVED → PENDING_REVIEW, SPAM, REJECTED, DUPLICATE
> - PENDING_REVIEW → VERIFIED, SPAM, REJECTED, DUPLICATE
> - VERIFIED → Terminal (เปลี่ยนสถานะอื่นไม่ได้ ยกเว้น soft-delete → DELETED)
> - SPAM, REJECTED, DUPLICATE → Terminal (เช่นกัน ยกเว้น soft-delete → DELETED)
> - ทุกสถานะ (ที่ไม่ใช่ DELETED) → DELETED ผ่าน DELETE endpoint
>
> "VERIFIED เปลี่ยนไม่ได้เพราะมีผลอย่างร้ายแรง — ระบบ publish event ไปสร้าง Incident แล้ว ถ้ายอมให้เปลี่ยนกลับ อาจเกิด Incident ที่ไม่ถูกต้องค้างอยู่ในระบบของ service อื่น ออกแบบตาม principle 'verified is final' ครับ"

---

## Q7: EventBridge Event ที่ publish ออกไป ฝั่ง Consumer ใช้ยังไง?

**คำตอบ**:  
> "ตอนนี้ใช้ mock ครับ คือ event ถูก publish จริงบน EventBridge Custom Bus ชื่อ disaster-event-bus แต่ยังไม่มี Rule ที่จะ route ไป consumer จริง"
>
> "เมื่อเพื่อนที่ทำ Incident Service พร้อม แค่สร้าง EventBridge Rule ที่ match DetailType=ReportVerifiedEvent แล้ว target ไปที่ Lambda ของเพื่อนก็ integrate ได้ทันที ไม่ต้องแก้ code ฝั่งเราเลย นี่คือข้อดีของ Event-Driven Architecture ครับ"

---

## Q8: ทำไมใช้ DynamoDB 3 ตาราง? ทำไมไม่รวมเป็นตารางเดียว?

**คำตอบ**:  
> "แยก 3 ตารางเพราะ access pattern ต่างกันครับ:"
> 1. **Reports** — read/write heavy, ใช้ GSI query by status, main data
> 2. **AuditLogs** — write-heavy, append-only, ใช้ GSI query by report_id + timestamp
> 3. **StatsCounter** — ใช้ Atomic Increment (ADD), BatchGetItem อ่านเร็วมาก
>
> "ถ้ารวมเป็น Single Table Design ก็ทำได้ แต่จะซับซ้อนเกินไปสำหรับ use case นี้ และ StatsCounter ที่ใช้ ADD operation ควรแยกเพื่อไม่ให้กระทบ reports table ครับ DynamoDB ไม่คิดค่า table เพิ่ม คิดแค่ RCU/WCU ครับ"

---

## Q9: ตัวเลข Trust Score คำนวณจากอะไร?

**คำตอบ**:  
> "ส่งให้ Gemini AI วิเคราะห์ครับ prompt จะบอกให้ดูหลายปัจจัย:"
> 1. เนื้อหาเกี่ยวข้องกับภัยพิบัติจริงไหม
> 2. มีรายละเอียดเฉพาะเจาะจง (ตำแหน่ง, เวลา, สภาพ) หรือแค่ข้อความทั่วไป
> 3. ภาษาที่ใช้เป็น spam pattern ไหม (เช่น promotional links)
> 4. แหล่งที่มาน่าเชื่อถือไหม (OFFICIAL_APP vs TWITTER)
>
> "AI จะตอบกลับเป็น JSON: trust_score (0-100), suggested_category (FIRE/FLOOD/etc.), reasoning (คำอธิบาย), keywords (tags) ทั้งหมดนี้จะถูกเก็บลง DynamoDB ให้เจ้าหน้าที่ดูประกอบการตัดสินใจครับ"

---

## Q10: ถ้ามี 10,000 requests/sec เข้ามาพร้อมกัน ระบบรองรับได้ไหม?

**คำตอบ**:  
> "ได้ครับ เพราะทุก component เป็น serverless:"
> - API Gateway รองรับ 10,000 req/s by default (soft limit AWS)
> - Lambda scale ได้ concurrent executions (Learner Lab มี limit ที่ 1,000)
> - SQS Standard Queue ไม่มี limit throughput — รับได้ไม่จำกัด
> - DynamoDB On-Demand รองรับ auto-scaling
>
> "bottleneck จริงๆ อยู่ที่ Gemini API rate limit ครับ แต่เราก็มี multi-key rotation + DLQ เป็น safety net ข้อมูลจะไม่หายแค่ process ช้าลงในช่วง peak"

---

## Q11: API Key Authentication เพียงพอไหม? ทำไมไม่ใช้ JWT/OAuth?

**คำตอบ**:  
> "สำหรับ scope ของ project นี้ API Key เพียงพอครับ เพราะ:"
> 1. AWS Learner Lab ไม่มี Cognito ให้ใช้ (ไม่อยู่ใน allow list)
> 2. API Key ผ่าน Usage Plan ของ API Gateway ให้ rate limiting + throttling ได้
> 3. ในระบบจริงจะใช้ JWT + Cognito + RBAC แต่ตอนนี้ยังไม่ implement (noted ใน proposal)
>
> "Health Check endpoint เปิดเป็น public ไม่ต้องมี key เพื่อให้ monitoring system เข้าถึงได้ตลอด ตาม best practice ครับ"

---

## Q12: IaC ใช้ Terraform — deploy ยังไง?

**คำตอบ**:  
> "มี deploy script 5 ขั้นตอนครับ:"
> 1. Clean — ลบ zip เก่า
> 2. Build Layer — pip install dependencies (target platform linux)
> 3. Build Source — zip source code + dependencies รวมกัน
> 4. Terraform Init — initialize providers
> 5. Terraform Apply — สร้าง/อัปเดต resources ทั้งหมด (~75 resources)
>
> "ทุกอย่าง reproducible ครับ ลบแล้วสร้างใหม่ได้เหมือนเดิมทุกครั้ง Terraform state เก็บ local (Learner Lab ไม่มี S3 backend ที่เหมาะ)"

---

## Q13: Audit Log เก็บอะไรบ้าง? ใช้ทำอะไร?

**คำตอบ**:  
> "เก็บทุกการเปลี่ยนแปลงสถานะครับ มี 4 action types:"
> - **STATUS_CHANGE** — เจ้าหน้าที่เปลี่ยนสถานะ (verify/reject)
> - **AI_ANALYSIS** — ผล AI วิเคราะห์
> - **SOFT_DELETE** — ใครลบ เมื่อไหร่ ด้วยเหตุผลอะไร
> - **DATA_EDIT** — แก้ไขข้อมูล (reserved for future)
>
> "แต่ละ log มี: log_id, report_ref_id, actor_id, previous_value, new_value, timestamp ใช้ตรวจสอบย้อนหลังได้ว่าใครทำอะไรเมื่อไหร่ เหมาะกับ compliance/PDPA ครับ"

---

## Q14: Test 107 ตัว ครอบคลุมอะไรบ้าง?

**คำตอบ**:  
> "แบ่ง 3 ระดับครับ:"
> - **Unit (69 ตัว)**: test validators ทุก case (33), API handler routing + verify + list (10), Gemini service rotation/fallback (13), Dedup haversine + time window (9)  
> - **Integration (13 ตัว)**: ใช้ moto mock AWS — DynamoDB CRUD + GSI + optimistic locking (6), SQS flow + auto-reject spam (3), EventBridge publish + health (4)
> - **E2E (25 ตัว)**: ยิง request จริงไปที่ API บน AWS — CORS (4), ingest contract (4), list/detail/verify/stats/health contracts (13), full verify flow (4)
>
> "ทั้ง 107 ตัวผ่าน 100% ไม่มี skip ไม่มี fail ครับ"

---

## Q15: Design นี้ใช้งานจริงในสถานการณ์ภัยพิบัติได้จริงไหม?

**คำตอบ**:  
> "ในแง่ Architecture — ใช้ได้ครับ pattern ทั้งหมดเป็น production-grade:"
> - Fire-and-forget + queue-based processing รับ burst ได้
> - AI-assisted triage ลดภาระเจ้าหน้าที่ได้จริง
> - Audit trail ครบตาม compliance
> - Event-driven ต่อ service อื่นง่าย ไม่ tight-coupling
>
> "สิ่งที่ต้องเพิ่มสำหรับ production จริง:"
> - JWT + RBAC (ไม่ใช่แค่ API Key)
> - Multi-region deployment (DR)
> - Image/Video analysis (ตอนนี้วิเคราะห์แค่ text)
> - Rate limit ระดับ per-user ไม่ใช่แค่ per-API-key
> - Monitoring + alerting ผ่าน CloudWatch Alarms
> - S3 backend สำหรับ Terraform state (not local)
>
> "แต่สำหรับ MVP และ demo ในขอบเขตวิชาเรียน ระบบนี้ทำงานได้ครบตาม requirement ครับ"

---

## Bonus: คำถามจากเพื่อนที่อาจทำ Incident Service

### BQ1: EventBridge event มี schema ยังไง? จะ integrate ต้องทำอะไร?

> "Event ใช้ format ตาม Message Contract #1 — Source=`service.report-verify`, DetailType=`ReportVerifiedEvent` ฝั่งเพื่อนแค่สร้าง EventBridge Rule ที่ match DetailType แล้ว target ไป Lambda ของเพื่อน Detail ข้างในเป็น JSON มี report_ref_id, suggested_incident_data (type, description, severity_level, location, media_evidence), verified_by, verification_notes ครับ"

### BQ2: ถ้าอยากเปลี่ยน threshold สำหรับ auto-reject SPAM ทำยังไง?

> "เปลี่ยน environment variable TRUST_AUTO_REJECT ครับ ตอนนี้ default เป็น 30 ถ้าอยากให้เข้มขึ้นก็เพิ่มเป็น 40-50 ถ้าอยากให้ผ่อนปรนก็ลดเหลือ 20 deploy ใหม่ด้วย terraform apply ก็เสร็จเลยครับ ไม่ต้องแก้ code"
