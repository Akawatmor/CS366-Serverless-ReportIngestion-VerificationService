# Service Overview

# **ภาพรวมของบริการ (Service Overview)**

# **Report Ingestion & Verification Service**

1. # **Service Owner**

* # Akawat Moradsatian (6609681231)


2. # **Service Purpose**

* # ทำหน้าที่เป็น **"Central Gateway (ประตูหน้าบ้าน)"** สำหรับรับข้อมูลเหตุภัยพิบัติ (Raw Disaster Reports) จากแหล่งข้อมูลภายนอกทุกช่องทาง (เช่น Social Media Scrapers, Mobile Apps, Third-party APIs) ผ่าน API มาตรฐาน บริการนี้มีหน้าที่ **Sanitize (ทำความสะอาดข้อมูล)**, **Deduplicate (ลดความซ้ำซ้อน)**, และ **Evaluate (ประเมินความน่าเชื่อถือ)** เพื่อเปลี่ยนข้อมูลดิบ (Noise) ให้เป็นข้อมูลกรองแล้ว (Verified Intelligence) ก่อนส่งต่อให้ Incident Service สร้างเป็นเหตุการณ์จริง


3. # **Pain Point ที่แก้ไข**

* # **Information Overload:** ในภาวะวิกฤต มีรายงานเข้ามานับพันรายการต่อนาที (High Throughput) ทำให้มนุษย์ไม่สามารถอ่านได้ทัน

* # **Noise & Redundancy:** รายงานกว่า 80% มักเป็นเรื่องเดิมที่โพสต์ซ้ำๆ (Duplicate) หรือเป็นข่าวปลอม/สแปม (Spam/Fake News)

* # **Unstructured Data:** ข้อมูลจากแต่ละแหล่งมีรูปแบบไม่เหมือนกัน ยากต่อการนำไปใช้งานต่อทันที


4. # **Target User**

* # **Trust & Safety Officer:** เจ้าหน้าที่ผู้ดูแลความถูกต้องของข้อมูล (เป็นผู้กด Verify ขั้นตอนสุดท้าย)

* # **External Systems (Bots/Scrapers):** ระบบอัตโนมัติที่ส่งข้อมูลเข้ามายัง API ของ Service นี้


5. # **Service Boundary**

* ## **In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)**

  * **Data Ingestion API:** ให้บริการ RESTful API สำหรับรับข้อมูลดิบ (Raw JSON Payload) จาก External Sources  
  * **Automated Triage:** ใช้ AI/Logic ในการให้คะแนนความน่าเชื่อถือ (Trust Scoring) และประเมินความรุนแรง (Severity Assessment) เบื้องต้น  
  * **Deduplication Logic:** ตรวจสอบข้อมูลซ้ำซ้อนโดยอิงจาก เวลา (Time Window), สถานที่ (Geospatial Clustering), และเนื้อหา (Content Similarity)  
  * **Verification Workflow:** จัดเตรียม Interface และ State Machine สำหรับให้เจ้าหน้าที่กด "Approve/Reject" หรือ "Merge" ข้อมูล  
  * **Event Publishing:** ส่งสัญญาณ (Event) แบบ Asynchronous เมื่อรายงานได้รับการยืนยันแล้ว เพื่อให้ Service อื่นนำไปใช้ต่อ  
    

* ## **Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)**

  * **Active Scraping:** ไม่รับผิดชอบการเขียน Bot ไปดึงข้อมูลจาก Website (ถือเป็น External Client ที่ต้องยิง API เข้ามาเอง)  
  * **Incident Lifecycle:** ไม่รับผิดชอบการติดตามสถานะการกู้ภัย (เช่น รถถึงไหนแล้ว, ปิดเคสหรือยัง) \-\> หน้าที่ Incident Service  
  * **Resource Dispatching:** ไม่รับผิดชอบการสั่งการรถกู้ภัย \-\> หน้าที่ Dispatch Service

6. # **Autonomy / Decision Logic**

* ## **บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ**

  * ## **การคัดกรอง Spam อัตโนมัติ (Auto-Rejection):** สามารถเปลี่ยนสถานะรายงานเป็น `SPAM` หรือ `REJECTED` ได้ทันที หากค่าความน่าเชื่อถือ (Trust Score) ต่ำกว่าเกณฑ์ขั้นต่ำ เพื่อลดขยะในระบบ

  * ## **การจับกลุ่มรายงานซ้ำซ้อน (Auto-Clustering):** สามารถตัดสินใจได้เองว่ารายงานใหม่ที่เข้ามาเป็นเรื่องเดียวกับรายงานที่มีอยู่แล้วหรือไม่ โดยการ Map เข้ากลุ่ม (Cluster) เดียวกันโดยอัตโนมัติ

  * ## **การจัดลำดับความเร่งด่วน (Queue Prioritization):** สามารถตัดสินใจเลื่อนลำดับรายงานที่มี Keyword วิกฤต (เช่น "ติดอยู่", "หายใจไม่ออก") ขึ้นมาเป็นอันดับแรกในรายการรอตรวจสอบ (Review Queue)

* ## **การตัดสินใจอิงจาก**

  * ## **Trust Score Threshold:** เกณฑ์คะแนนความน่าเชื่อถือที่กำหนดไว้ (เช่น Trust Score \< 30% → Auto Reject, \> 80% → High Priority)

  * ## **Spatio-Temporal Logic:** กฎทางพื้นที่และเวลา (เช่น หากพิกัดห่างกันไม่เกิน 200 เมตร และเวลาห่างกันไม่เกิน 15 นาที ให้ถือว่าเป็นเหตุการณ์เดียวกัน)

  * ## **Severity Keyword Matching:** การเทียบคำในเนื้อหากับฐานข้อมูลคำสำคัญเพื่อประเมินระดับความรุนแรง

    

* ## **บริการสามารถตัดสินใจได้เองภายใต้ business rules ที่กำหนดโดย**

  * ## **ไม่ต้องรอ**การอนุมัติจากมนุษย์ในขั้นตอนการ **คัดกรอง (Filtering), จัดกลุ่ม (Grouping), และจัดลำดับ (Sorting)** เพื่อลดภาระงาน (Workload) ของเจ้าหน้าที่

  * ## **แต่ต้องรอ** การอนุมัติจากมนุษย์ (Human-in-the-loop) ในขั้นตอนสุดท้ายคือการ **"Verify"** เพื่อยืนยันความถูกต้องก่อนส่งข้อมูลออกไปสร้าง Incident จริง

      
      
      
    

7. # **Owned Data**

* **`report_id (PK):`** รหัสอ้างอิงของรายงานดิบ  
* **`source_metadata:`** ที่มาของข้อมูล (Platform, User ID, Original Link)  
* **`content_payload:`** ข้อความ, ลิงก์รูปภาพ, พิกัด GPS  
* **`analysis_result:`** ค่า Trust Score, Sentiment Score, Suggested Category  
* **`verification_status:`** สถานะปัจจุบัน `(RECEIVED, PENDING_REVIEW, VERIFIED, SPAM, DUPLICATE)`


8. # **Linked Data (Reference Only)**

* **`incident_id:`** (Foreign Key \- Reference Only) เก็บเพียง ID เพื่อเชื่อมโยงว่า Report นี้ถูกนำไปสร้างเป็น Incident หมายเลขอะไรใน Incident Service (เราอ่านได้ แต่ห้ามไปแก้ข้อมูลใน Incident Service)


9. # Non-Functional Requirements

* **High Scalability (สำคัญที่สุด):** ต้องรองรับ **Write-Heavy Workload** (การเขียนข้อมูลจำนวนมาก) ในช่วงเกิดภัยพิบัติได้ (เช่น รองรับ 10,000 requests/sec ผ่าน Serverless Queue)  
* **Data Integrity:** ข้อมูลที่รับเข้ามา (Ingest) ต้องไม่สูญหายแม้แต่นิดเดียว (Zero Data Loss) แม้ระบบตรวจสอบจะล่ม แต่ข้อมูลดิบต้องถูกเก็บลง Database เสมอ  
* **Asynchronous Processing:** การประมวลผลหนักๆ (AI, Deduplication) ต้องทำแบบ Background Process เพื่อไม่ให้ API ขาเข้าเกิดความล่าช้า (Latency)

# 

# Sync Contract

# **Synchronous Function Contract**

# **Base URL:** ingestverify-365-dev.akawatmor.com/v1/…

# 

# **API Contract \#1: Submit Raw Report (Ingest)**

## **ข้อมูลทั่วไป**

* Name: Ingest Raw Report  
* Method: POST  
* Path: /reports  
* Type: Synchronous (Request/Response แบบ Fire and Forget)


## **คำอธิบาย**

* ### เป็นช่องทางหลักสำหรับนำเข้าข้อมูลจากภายนอกเน้นรับข้อมูลให้ไวที่สุดแล้วตอบกลับทันที เพื่อนำเข้าคิว SQS ให้เร็วที่สุด


### **Request**

**Path/Query Params**

* None

  **Headers**

* Content-Type: application/json  
* X-Api-Key: \<Client-Key\> (เพื่อระบุว่าเป็นข้อมูลจาก Partner เจ้าไหน เช่น TwitterScraper, OfficialApp)

  **Body: (JSON Payload)**

  `{`

    `"reporter_source": "TWITTER", // ENUM: [TWITTER, FACEBOOK, LINE, OFFICIAL_APP, IOT_SENSOR]`

    `"reporter_id": "@user123",    // User ID หรือ Phone Number ของผู้แจ้ง`

    `"raw_content": "Fire reported near Central World! #BKKFire", // ข้อความดิบ`

    `"media_urls": [ // Array Urls สำหรับหลายรูป`

      `"https://img.host/fire123.jpg",`

      `"https://video.host/clip.mp4"`

    `],`

    `"geo_location": {`

      `"lat": 13.746123,`

      `"lon": 100.539123`

    `},`

    `"timestamp": "2026-02-18T14:30:00Z"` 

  `// เวลาที่เกิดเหตุ (สำคัญมากสำหรับการเรียงลำดับ)`

  `}`


### **Validation**

* reporter\_source ต้องอยู่ใน ENUM ที่กำหนด  
* raw\_content หรือ media\_urls ต้องมีอย่างน้อย 1 อย่าง  
* ขนาด Payload รวมต้องไม่เกิน Limit ของ API Gateway/SQS (เช่น ไม่เกิน 256KB)


### **Response**

**Success:** (202 Accepted) พร้อม report\_id และ status  
`{`  
  `"status": "QUEUED",`  
  `"report_id": "r-550e8400-e29b",  // UUID ที่สร้างทันที`  
  `"message": "Report accepted and queued for processing.",`  
  `"estimated_wait_time": "2s"`  
`}`

**Error:** 

- **400 Bad Request:** ข้อมูลไม่ครบ (เช่น ขาด raw\_content หรือ reporter\_source)  
- **401 Unauthorized:** API Key ไม่ถูกต้อง  
- **429 Too Many Requests:** กรณียิงรัวเกิน Rate Limit ที่กำหนด  
- **500 Internal Server Error:** Database หรือ Queue ล่ม

### **Dependency / Reliability**

* ไม่มี External Dependency (ไม่เรียก Service อื่น)  
* Reliability สูงมาก เพราะใช้ API Gateway Integration ยิงตรงเข้าแค่เขียนลง Queue/DB แล้วจบงาน ไม่ต้องผ่าน Lambda เพื่อลด Latency

# **API Contract \#2:** 

### **ข้อมูลทั่วไป**

* **Name:** List Pending Reports  
* **Method:** GET  
* **Path:** /reports  
* **Type:** Synchronous (Request/Response)

### **คำอธิบาย**

- ### เจ้าหน้าที่ต้องดึงรายการรายงานที่รอการตรวจสอบ ถึงจะกด Verify ได้

### **Request**

**Path/Query Param**

* status=PENDING\_REVIEW

* min\_trust\_score=50

* limit=20 (Optional, Default: 5, Max: 100\)

  **Headers**

* Authorization: Bearer \<JWT\_Token\> (ยืนยันตัวตนเจ้าหน้าที่)

  **Body**

* None

  **Validation**

* status ต้องเป็นค่าที่อนุญาต (เช่น PENDING\_REVIEW, VERIFIED)  
* limit ต้องเป็นตัวเลขบวกไม่เกิน 100

### **Response**

**Success:** 

`{`  
  `"data": [`  
    `{`  
      `"report_id": "r-550e8400-e29b",`  
      `"content": "Fire near Central...",`  
      `"trust_score": 85,             // คะแนนจาก AI`  
      `"suggested_category": "FIRE",  // AI แนะนำประเภทมาให้`  
      `"time_ago": "5 mins"`  
    `},`  
    `// ... รายการอื่นๆ`  
  `],`  
  `"total_count": 15`  
`}`

**Error:** 

* 400 Bad Request: Query Params ผิดรูปแบบ  
* 401 Unauthorized: Token หมดอายุหรือไม่ถูกต้อง  
* 403 Forbidden: ไม่มีสิทธิ์เข้าถึง (Role ไม่ถึง)

### **Dependency / Reliability**

* อ่านข้อมูลจาก DynamoDB (สร้าง Global Secondary Index \- GSI ที่มี status เป็น Partition Key เพื่อให้ Query ได้เร็วและไม่เปลือง RCUs)  
    
    
    
    
    
    
    
    
    
    
    
    
    
    
  


# **API Contract \#3:** 

### **ข้อมูลทั่วไป**

* **Name:** Verify Report (Decision)  
* **Method:** PATCH  
* **Path:** /reports/{report\_id}  
* **Type:** Synchronous

### **คำอธิบาย**

* ### ยืนยันสถานะความถูกต้องของรายงาน หากเป็น VERIFIED ระบบจะส่ง Event ไปสร้าง Incident ต่อแบบเบื้องหลัง

### **Request**

**Path/Query Param**

* report\_id (Path param: ระบุ ID ของ Report ที่ต้องการอัปเดต)

  **Headers**

* Content-Type: application/json  
* Authorization: Bearer \<JWT\_Token\>

  **Body**

  `{`

    `"validation_status": "VERIFIED",        // ENUM: [VERIFIED, SPAM, DUPLICATE, REJECTED]`

    `"reviewer_id": "officer_007",           // ID เจ้าหน้าที่ผู้ทำรายการ`

    `"reviewer_notes": "Confirmed via CCTV feed.",`

    `"link_to_incident_id": "inc-1234-5678"  // OPTIONAL: ใส่เมื่อต้องการ Merge เข้าเหตุการณ์เดิม`

    `// หมายเหตุ: ถ้า link_to_incident_id เป็น null และ status=VERIFIED ระบบจะถือว่าให้ "สร้าง Incident ใหม่"`

  `}`


  **Validation**

* ถ้า validation\_status เป็น VERIFIED ต้องมี reviewer\_id เสมอ  
* ใช้ Conditional Check (Optimistic Locking) ใน DynamoDB ป้องกันไม่ให้อัปเดต Report ที่มีสถานะเปลี่ยนจาก PENDING\_REVIEW ไปแล้ว

### **Response**

**Success: (200 OK)**

`{`  
  `"report_id": "r-550e8400-e29b",`  
  `"validation_status": "VERIFIED",`  
  `"action_taken": "TRIGGER_NEW_INCIDENT", // หรือ "MERGED_EXISTING_INCIDENT"`  
  `"updated_at": "2026-02-18T15:00:00Z"`  
`}`

**Error:** 

* **400 Bad Request: ส่ง State ที่ไม่อนุญาต**  
* **404 Not Found: ไม่พบ report\_id นี้**  
* **409 Conflict: รายงานนี้ถูกจัดการไปแล้วโดยผู้อื่น**


### **Dependency / Reliability**

* อัปเดต DynamoDB Table หลัก และอาจจะมีการบันทึกลง Table Audit Logs ควบคู่กัน (ใช้ DynamoDB Transactions เพื่อความชัวร์)  
* External (Logic): การยิงไปหา Incident Service จะทำแบบ Asynchronous (Background) หลังจากตอบ 200 OK กลับไปหาหน้าบ้านแล้ว (เพื่อไม่ให้เจ้าหน้าที่ต้องรอโหลดนาน)

# **API Contract \#4:** 

### **ข้อมูลทั่วไป**

* **Name:** Get Report Detail (Insight Data)  
* **Method:** GET  
* **Path:** /reports/{report\_id}  
* **Type:** Synchronous

### **คำอธิบาย**

* ### ดึงข้อมูลเชิงลึกของแต่ละ Report เช่น ภาพความละเอียดสูง Metadata และเหตุผลการวิเคราะห์จาก AI

### **Request**

**Path/Query Param**

* report\_id (Path param)

  **Headers**

* Authorization: Bearer \<JWT\_Token\>

  **Body**

* None

  **Validation**

* report\_id ต้องไม่เป็นค่าว่าง

### **Response**

**Success: (200 OK)**

`{`  
  `"report_id": "r-550e8400-e29b",`  
  `"reporter_info": {`  
    `"source": "Twitter",`  
    `"user_handle": "@somchai_123",`  
    `"account_age_years": 5,  // ข้อมูลประกอบการตัดสินใจ`  
    `"followers_count": 1200`  
  `},`  
  `"content": {`  
    `"text": "ไฟไหม้ร้านทอง เยาวราช ตอนนี้เลย!",`  
    `"images": ["https://s3.aws.../img1_hd.jpg"],`  
    `"video": "https://s3.aws.../vid1.mp4"`  
  `},`  
  `"analysis": {`  
    `"trust_score": 88,`  
    `"ai_reasoning": "Detected fire and smoke in image. Multiple users reporting same location.",`  
    `"potential_duplicates": ["r-999", "r-888"] // Link ไปดูอันที่คล้ายกัน`  
  `},`  
  `"status": "PENDING_REVIEW",`  
  `"created_at": "2026-02-18T10:00:00Z"`  
`}`

**Error:** 

* 404 Not Found: ไม่พบข้อมูล


### **Dependency / Reliability**

* ดึงข้อมูลจาก DynamoDB Table หลัก (ใช้ GetItem ซึ่งเร็วและประหยัดที่สุด)

# 

# **API Contract \#5:** 

### **ข้อมูลทั่วไป**

* **Name:**  Get Dashboard Stats (Summary)  
* **Method:** GET  
* **Path:** /reports/stats  
* **Type:** Synchronous

### **คำอธิบาย**

* ### ดึงตัวเลขสรุปภาพรวมสำหรับ Dashboard ให้ผู้บัญชาการประเมินสถานการณ์

### **Request**

**Path/Query Param**

* timeframe=today (Optional: today, last\_24h, last\_7d)  
* region=bkk (Optional: กรองตามพื้นที่)

  **Headers**

* Authorization: Bearer \<JWT\_Token\>

  **Body**

* None

  **Validation**

* timeframe ต้องอยู่ในช่วงที่อนุญาต

### **Response**

**Success: (200 OK)**

`{`  
  `"timestamp": "2026-02-18T12:00:00Z",`  
  `"summary": {`  
    `"total_received_today": 1500,`  
    `"pending_review": 50,`  
    `"verified_incidents": 120,`  
    `"spam_rejected": 1330`  
  `},`  
  `"trending_keywords": ["ไฟไหม้", "เยาวราช", "รถติด"],`  
  `"heatmap_data": [ // เอาไปพล็อตจุดสีแดงบนแผนที่`  
    `{"lat": 13.7, "lon": 100.5, "intensity": 9},`  
    `{"lat": 13.2, "lon": 100.2, "intensity": 2}`  
  `]`  
`}`

**Error:** 

* 500 Internal Server Error: ระบบคำนวณสถิติขัดข้อง


### **Dependency / Reliability**

* การ Scan DynamoDB เพื่อทำ Aggregate (เช่น นับจำนวนทั้งหมด) จะกิน Resource และแพงมาก แนะนำให้ใช้ DynamoDB Streams ส่งข้อมูลไปอัปเดต Counter ในอีก Table หนึ่ง (หรือใช้ Redis) และให้ API นี้ไปอ่านจาก Counter Table แทนครับ

# **API Contract \#6:** 

### **ข้อมูลทั่วไป**

* **Name:** Soft Delete / Archive  
* **Method:** DELETE  
* **Path:** /reports/{report\_id}  
* **Type:** Synchronous

### **คำอธิบาย**

* ปิดการมองเห็นของ Report (แปะป้ายลบ) สำหรับกรณีข้อมูลทดสอบ ข้อมูลละเมิด PDPA หรือเหตุผลด้านกฎหมาย

### **Request**

**Path/Query Param**

* report\_id (Path param)

  **Headers**

* **Authorization: Bearer \<JWT\_Token\> (ควรจำกัดสิทธิ์เฉพาะ Admin หรือ Supervisor)**  
* **Content-Type: application/json**

  **Body (JSON)**

  {

    "reason": "Contains sensitive personally identifiable information (PII)",

    "deleted\_by": "admin\_001"

  }


  **Validation**

* ตรวจสอบสิทธิ์ (Role-based Access Control) ให้แน่ใจว่าผู้เรียกมีสิทธิ์ทำลาย/ซ่อนข้อมูล  
* reason ควรระบุเหตุผลเพื่อการ Audit

### **Response**

**Success: (200 OK)**

`{`  
  `"report_id": "r-550e8400-e29b",`  
  `"status": "DELETED",`  
  `"message": "Report has been archived and removed from public view."`  
`}`

**Error:** 

* **403 Forbidden: ไม่มีสิทธิ์ลบ**  
* **404 Not Found: ไม่พบ Report**


### **Dependency / Reliability**

* อัปเดต status ใน DynamoDB เป็น DELETED (Soft Delete)  
* บันทึกการกระทำลงใน Table Audit Logs อย่างละเอียด

# Async Contract

**Asynchronous Function Contract**

## **Message Contract \#1: Incident Creation Request**

### **ข้อมูลทั่วไป** 

* **Message Name:** ReportVerifiedEvent  
* **Interaction Style:** Asynchronous (Publish/Subscribe)  
* **Producer:** Report Ingestion & Verification Service  
* **Consumer:** Incident Tracking Service  
* **Channel/Queue:** report.verified  
* **Version:** v1

### **คำอธิบาย**

* ### เหตุการณ์นี้จะถูกส่งออกมาเมื่อเจ้าหน้าที่กด "Verify" และเลือก "Create New Incident" ระบบจะส่งข้อมูลที่กรองแล้ว (Sanitized Data) ไปให้ Incident Service เพื่อสร้าง Master Record

### **Request** 

### **Message Headers**

* x-event-id: evt-1234567890 (Unique ID ของ Event นี้)  
* x-timestamp: 2026-02-18T10:30:00Z  
* x-source: service.report-verify  
* x-action: CREATE\_NEW\_INCIDENT  
* x-detail-type: ReportVerifiedEvent

  **Message Body (JSON)**

  `{`

    `"report_ref_id": "r-550e8400-e29b",`

    `"suggested_incident_data": {`

      `"type": "FIRE",`

      `"description": "Fire reported at Central World, smoke visible from 5km away.",`

      `"severity_level": 3,`

      `"location": {`

        `"lat": 13.746,`

        `"lon": 100.539,`

        `"address_text": "Ratchaprasong Intersection, Bangkok"`

      `},`

      `"reporter_count": 15,`

      `"media_evidence": [`

        `"https://s3.aws.../img1.jpg",`

        `"https://s3.aws.../img2.jpg"`

      `]`

    `},`

    `"verified_by": "officer_007",`

    `"verification_notes": "Confirmed via traffic camera."`

  `}`


  

  **Field Definition:**

| Field | Type | Required | Description | Validation Rules |
| ----- | ----- | ----- | ----- | ----- |
| report\_ref\_id | UUID | YES | ID ของ Report ต้นทาง (เพื่อให้ Incident Service เก็บไว้ Trace กลับมาได้) | Must be valid UUID v4 format |
| suggested\_incident\_data.type | String | YES | ประเภทเหตุการณ์ที่ระบบ/เจ้าหน้าที่แนะนำ | Enum: `FIRE`, `FLOOD`, `EARTHQUAKE`, `ACCIDENT` |
| suggested\_incident\_data.description | String | YES | รายละเอียดเหตุการณ์ที่สรุปมาแล้ว | Max 500 chars, No HTML tags |
| suggested\_incident\_data.severity\_level | Integer | YES | ระดับความรุนแรง (1-5) | 1 (Low) \- 5 (Critical) |
| suggested\_incident\_data.location.lat | Float | YES | พิกัดละติจูด | \-90 to 90 |
| suggested\_incident\_data.location.lon | Float | YES | พิกัดลองจิจูด | \-180 to 180 |
| verified\_by | String | YES | ID ของเจ้าหน้าที่ผู้ยืนยัน | Non-empty string |

**Validation Rules**

(อยู่ในตารางข้างบน)

**Response**

	**Message Headers** 

* id: evt-res-88889999 (Unique ID ของ Event ตอบกลับตัวนี้)  
* time: 2026-02-18T10:30:05Z (เวลาที่สร้าง Incident เสร็จหรือเกิด Error)  
* source: service.incident-tracking (สำคัญ: เปลี่ยนเป็นชื่อ Service ของเพื่อนที่รับผิดชอบ Incident)  
* detail-type: IncidentCreationResultEvent (ชื่อ Event แจ้งผลลัพธ์)  
* x-correlation-id: evt-1234567890 (ต้องส่ง ID ของ Event ต้นทาง หรือ report\_ref\_id กลับมาใน Header ด้วย เพื่อให้ Service ของเราสามารถจับคู่กลับได้ว่าผลลัพธ์นี้เป็นของ Report ใบไหน)

  **Success Message Body (JSON)**


  {

    "incident\_id": "inc-9999-8888",  // ID จริงที่ถูกสร้าง

    "original\_report\_ref\_id": "r-550e8400-e29b", // ส่งคืนมาเพื่อบอกว่า "Report นี้สร้างเสร็จแล้วนะ"

    "status": "CREATED",

    "timestamp": "2026-02-18T10:30:05Z"

  }


  

  **Reject/Error Message Body (JSON)**


  {

    "original\_report\_ref\_id": "r-550e8400-e29b",

    "status": "FAILED",

    "error\_code": "DUPLICATE\_INCIDENT",

    "error\_message": "An incident at this location already exists (inc-5555)."

  }


  


  

  **Field Definition:**

| Field | Type | Required | Description | Validation |
| ----- | ----- | ----- | ----- | ----- |
| incident\_id | UUID | Yes (Success only) | ID ของ Incident ที่ถูกสร้างสำเร็จ | Valid UUID |
| original\_report\_ref\_id | UUID | Yes | ID ของ Report ต้นทางที่ส่งไป | Must match original request |
| status | String | Yes | ผลลัพธ์การทำงาน | Enum: `CREATED`, `FAILED` |
| error\_code | String | No | รหัสข้อผิดพลาด (ถ้ามี) |  |

	**Validation Rules**

(อยู่ในตารางข้างบน)

## **Message Contract \#2: Incident Creation Request**

### **ข้อมูลทั่วไป** 

* **Message Name:** ReportStatusChangedEvent  
* **Interaction Style:** Asynchronous (Publish/Subscribe)  
* **Producer:** Report Ingestion & Verification Service  
* **Consumer:** Dashboard Service, Notification Service, Property Damage Service  
* **Channel/Queue:** report.status\_updates  
* **Version:** v1

### **คำอธิบาย**

* ### เหตุการณ์นี้ถูกส่งออกไป (Broadcast) ทุกครั้งที่สถานะของ Report มีการเปลี่ยนแปลง (เช่น PENDING \-\> SPAM, หรือ PENDING \-\> VERIFIED) เพื่อให้ Service อื่นๆ นำไปอัปเดตหน้าจอ Dashboard แบบ Real-time หรือนำไปคำนวณสถิติต่อ

### **Request** 

### **Message Headers**

* id: evt-0987654321  
* time: 2026-02-18T11:15:00Z  
* source: service.report-verify  
* detail-type: ReportStatusChangedEvent

  **Message Body (JSON)**

  `{`

    `"report_id": "r-123",`

    `"old_status": "PENDING_REVIEW",`

    `"new_status": "SPAM",`

    `"reason": "Auto-rejected by AI (Trust Score < 10%)",`

    `"changed_by": "system_ai",`

    `"timestamp": "2026-02-18T11:15:00Z"`

  `}`

  **Field Definition:**

| Field | Type | Required | Description | Validation Rules |
| ----- | ----- | ----- | ----- | ----- |
| report\_id | UUID | YES | ID ของ Report ที่ถูกเปลี่ยนสถานะ | Must be valid UUID |
| old\_status | String | YES | สถานะเดิมก่อนเปลี่ยน | Enum: RECEIVED, PENDING\_REVIEW, VERIFIED, SPAM, DUPLICATE |
| new\_status | String | YES | สถานะใหม่ที่ถูกเปลี่ยน | Enum: RECEIVED, PENDING\_REVIEW, VERIFIED, SPAM, DUPLICATE |
| reason | String | NO | เหตุผลที่เปลี่ยนสถานะ (สำคัญเวลาโดน Reject) | Max 255 chars |
| changed\_by | String | YES | ผู้เปลี่ยนสถานะ (คน หรือ AI) | ID ของเจ้าหน้าที่ หรือ 'system\_ai' |
| timestamp | String | YES | เวลาที่เกิดการเปลี่ยนสถานะ | ISO8601 Format |

**Validation Rules**

(อยู่ในตารางข้างบน)

**Response**

* None (This is a Broadcast Event. No response or callback is expected from consumers.)

# Service Data

# **Service Data**

# **1\) Reports Data (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| **`report_id`** (PK) | UUID | Yes | รหัสอ้างอิงของรายงาน (สร้างโดยระบบเมื่อรับข้อมูล) | r-550e8400-e29b |
| source\_platform | String (Enum) | Yes | แหล่งที่มาของข้อมูล | `TWITTER`, `LINE_OFFICIAL`, `MOBILE_APP` |
| source\_external\_id | String | No | ID อ้างอิงจากต้นทาง (เช่น Tweet ID) เพื่อกันการดึงซ้ำ | 1758930222345 |
| reporter\_id | String | Yes | User ID หรือเบอร์โทรของผู้แจ้ง (ใช้ระบุตัวตน/แบน) | @somchai\_za |
| raw\_content | Text | Yes | ข้อความดิบที่ได้รับแจ้งมา | "ไฟไหม้ร้านทอง เยาวราช ช่วยด้วย\!" |
| media\_urls | List/Array | No | ลิงก์รูปภาพหรือวิดีโอหลักฐาน | \["https://s3.../img1.jpg"\] |
| geo\_location | JSON / Object | Yes | พิกัดละติจูด/ลองจิจูด (สำคัญมากสำหรับการ Map) | { "lat": 13.74, "lon": 100.50 } |
| ingested\_at | DateTime | Yes | เวลาที่ข้อมูลถูกบันทึกลงระบบ (System Time) | 2026-02-18T10:00:00Z |
| trust\_score | Integer (0-100) | Yes | คะแนนความน่าเชื่อถือที่ AI ประเมิน (ค่าตั้งต้น \= 0\) | 85 |
| ai\_analysis\_tags | List/Array | No | ป้ายกำกับที่ AI ตรวจจับได้ (ใช้ช่วย Search/Filter) | \["FIRE", "URGENT", "SMOKE"\] |
| validation\_status | String (Enum) | Yes | สถานะปัจจุบันของรายงาน | `RECEIVED`, `PENDING_REVIEW`, `VERIFIED`, `SPAM`, `REJECTED`, `DUPLICATE` |
| verified\_by | String | No | ID ของเจ้าหน้าที่/ระบบ ที่ทำการเปลี่ยนสถานะล่าสุด | `officer_007` (หรือ `SYSTEM_AI`) |
| verification\_notes | Text | No | หมายเหตุจากการตรวจสอบ (ทำไมถึงผ่าน/ไม่ผ่าน) | "ยืนยันจากกล้อง CCTV แล้ว" |
| linked\_incident\_id | UUID | No | (Reference) ID ของ Incident จริงที่รายงานนี้ถูกส่งไปรวม | inc-9988-7766 |

# **2\) Report Audit Logs (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| **`log_id`** (PK) | UUID | Yes | รหัสประจำรายการ Log | log-1122-3344 |
| report\_ref\_id | UUID | Yes | (FK) อ้างอิงไปยัง Report ตัวไหน | r-550e8400-e29b |
| actor\_id | String | Yes | ID ของผู้กระทำ (User หรือ System Name) | officer\_007 |
| action\_type | String | Yes | ประเภทการกระทำ | `STATUS_CHANGE`, `DATA_EDIT` |
| previous\_value | JSON/String |  | ค่าเดิมก่อนแก้ไข (เพื่อดูความเปลี่ยนแปลง) | { "status": "PENDING" } |
| new\_value | JSON/String | Yes | ค่าใหม่หลังแก้ไข | { "status": "VERIFIED" } |
| timestamp | DateTime | Yes | เวลาที่เกิดการกระทำ | 2026-02-18T10:05:00Z |

ข้อมูลเพิ่มเติม

1. ทำไมต้องมี source\_external\_id?  
   เพื่อทำ Idempotency ครับ สมมติ Bot รวนแล้วส่ง Tweet เดิมมา 10 รอบ เราจะเช็ค Field นี้ก่อน ถ้ามีแล้วเราจะไม่ออก report\_id ใหม่ แต่จะอัปเดต timestamp แทน หรือ ignore ไปเลย

2. ทำไม linked\_incident\_id ถึงใช้เป็นแค่อ้างอิง (Reference)?  
   เพราะ ID นี้เป็นของ Incident Service เราแค่เก็บไว้แปะป้ายว่า "รายงานนี้ส่งไปที่แฟ้มคดีไหนแล้ว" เราไม่มีสิทธิ์ไปแก้ข้อมูลใน Incident นั้นครับ

# Service Architecture

**Service Architecture**  
**![][image1]**  
Ingestion Flow (Async):\[External Sources (Bots/Apps)\] \--\> (HTTPS POST) \--\> \[Amazon API Gateway\]\[Amazon API Gateway\] \---(Enqueue Raw Data)---\> \[Amazon SQS (report-ingestion-queue)\]\[Amazon SQS\] \---(Trigger Batch)---\> \[AWS Lambda (Ingestion Worker)\]\[AWS Lambda (Ingestion Worker)\] \<---(Analyze Text)---\> \[Amazon Comprehend (AI)\]\[AWS Lambda (Ingestion Worker)\] \---(Write/Deduplicate)---\> \[Amazon DynamoDB (Reports Table)\]

Verification Flow (Sync):\[Trust Officer (Dashboard)\] \<--(HTTPS GET/PATCH)--\> \[Amazon API Gateway\]\[Amazon API Gateway\] \---(Route Request)---\> \[AWS Lambda (API Handler)\]\[AWS Lambda (API Handler)\] \<---(Read/Update Status)---\> \[Amazon DynamoDB (Reports Table)\]

Broadcast Flow (Event-Driven):\[AWS Lambda (API Handler)\] \---(Publish Verified Event)---\> \[Amazon EventBridge (Disaster Event Bus)\]\[Amazon EventBridge\] \---(Rule Matching)---\> \[Target: Incident Tracking Service\]

**Components**  
**User / Client:**

* **External Sources:** Social Media Scrapers, Mobile Apps ที่ส่งข้อมูลเข้ามา  
* **Trust Officer:** เจ้าหน้าที่ผู้ใช้งานผ่านหน้า Web Dashboard เพื่อตรวจสอบข้อมูล  
  **Amazon API Gateway:**  
* ทำหน้าที่เป็นประตูหลัก (Entry Point) รับคำขอทั้งแบบ Synchronous (จากเจ้าหน้าที่) และ Asynchronous Ingestion (จาก Bot)  
  **Amazon SQS (report-ingestion-queue):**  
* คิวสำหรับพักข้อมูล (Buffer) จาก External Sources เพื่อรองรับ Traffic มหาศาล (Spike Traffic) ป้องกันระบบล่ม และช่วยลด Rate Limit  
  **AWS Lambda (Ingestion Worker):**  
* ฟังก์ชันเบื้องหลังที่ตื่นขึ้นมาเมื่อมีข้อมูลใน SQS ทำหน้าที่เรียก AI มาประมวลผล (Scoring), ตรวจสอบข้อมูลซ้ำ (Deduplicate), และบันทึกลงฐานข้อมูล  
  **Amazon Comprehend:**  
* บริการ AI สำหรับวิเคราะห์ข้อความ (NLP) เพื่อหา Keywords, Sentiment, และประเมินค่าความน่าเชื่อถือ (Trust Score)  
  **Amazon DynamoDB (Reports Table):**  
* ฐานข้อมูล NoSQL หลักของ Service เก็บข้อมูล Reports ทั้งหมด, สถานะการตรวจสอบ, และ Audit Logs รองรับการอ่าน/เขียนความเร็วสูง  
  **AWS Lambda (API Handler):**  
* ฟังก์ชันสำหรับให้บริการหน้า Dashboard (Get List, View Detail) และประมวลผลคำสั่งยืนยัน (Verify) จากเจ้าหน้าที่  
  **Amazon EventBridge (Custom Event Bus):**  
* ช่องทางสื่อสารหลักไปยัง Service อื่นๆ (Event Bus) เมื่อมีการยืนยันข้อมูล (Verified) ระบบจะ "ตะโกน" บอก EventBridge เพื่อให้ Service ปลายทาง (เช่น Incident Service) มารับข้อมูลไปทำงานต่อ

**Explanation**  
สถาปัตยกรรมของ Report Ingestion & Verification Service ถูกออกแบบโดยเน้นความทนทาน (Resilience) และการแยกส่วนการทำงาน (Decoupling) โดยแบ่งออกเป็น 3 ส่วนหลัก ดังนี้:

1\. ส่วนการรับข้อมูลและประมวลผลเบื้องต้น (Asynchronous Ingestion):  
เนื่องจากการแจ้งเหตุภัยพิบัติมักมีปริมาณมหาศาลและมาพร้อมกันในเวลาสั้นๆ (Traffic Spikes) ระบบจึงใช้ Amazon SQS เข้ามาคั่นกลางระหว่าง API Gateway และส่วนประมวลผล เมื่อ External Sources ส่งข้อมูลเข้ามา API Gateway จะส่งข้อมูลลง SQS และตอบกลับทันที (202 Accepted) เพื่อลดระยะเวลารอคอย จากนั้น AWS Lambda (Ingestion Worker) จะดึงข้อมูลจาก SQS ไปประมวลผลทีละ Batch โดยมีการเรียกใช้ Amazon Comprehend เพื่อวิเคราะห์ความน่าเชื่อถือ (Trust Score) และตรวจสอบความซ้ำซ้อนกับข้อมูลใน Amazon DynamoDB ก่อนบันทึก กระบวนการนี้ช่วยให้ระบบรองรับ Load ได้ไม่จำกัดโดยไม่กระทบต่อฐานข้อมูลหลัก

2\. ส่วนการตรวจสอบและบริหารจัดการ (Synchronous Management):  
สำหรับเจ้าหน้าที่ (Trust Officer) ที่ต้องคัดกรองข้อมูล ระบบใช้รูปแบบ REST API ผ่าน API Gateway เชื่อมต่อกับ AWS Lambda (API Handler) โดยตรง เพื่อดึงรายการที่ AI คัดกรองแล้ว (Pending Review) มาแสดงผล และรองรับคำสั่งตรวจสอบยืนยัน (Verify) หรือปฎิเสธ (Reject) โดยมีการอ่านและอัปเดตสถานะลงใน DynamoDB แบบ Real-time เพื่อให้เจ้าหน้าที่เห็นสถานะล่าสุดทันที

3\. ส่วนการส่งต่อข้อมูล (Event-Driven Broadcast):  
เมื่อเจ้าหน้าที่ทำการยืนยันข้อมูล (Status \= VERIFIED) ระบบจะไม่เรียก API ของ Service อื่นโดยตรง (เพื่อป้องกันการผูกติดกันเกินไป) แต่ AWS Lambda จะทำการ Publish Event ชื่อ ReportVerified ไปยัง Amazon EventBridge ซึ่งทำหน้าที่เป็น Router กลาง เพื่อกระจายข่าวดังกล่าวไปยัง Service ที่เกี่ยวข้อง (เช่น Incident Tracking Service) ให้นำข้อมูลไปสร้าง Incident ต่อไป รูปแบบนี้ช่วยให้ระบบมีความเป็นอิสระ (Autonomy) และง่ายต่อการขยาย Service ใหม่ๆ ในอนาคต

# Service Interaction

**Service Interaction**

ภาพ Diagram (คำอธิบายสำหรับการวาด)  
Center Node: Report Ingestion & Verification Service (Service ของคุณ)

Left Side (Upstream \- ผู้เรียกใช้งานเรา):

DisasterMonitoring Service (IoT/Sensors) → ชี้มาที่ Service คุณ (เส้นทึบ: HTTP POST)

Operation Update Service (Dashboard) → ชี้มาที่ Service คุณ (เส้นทึบ: HTTP GET)

External Sources (Mock Bots/Apps) → ชี้มาที่ Service คุณ (เส้นทึบ: HTTP POST)

Right Side (Downstream \- เราส่งข้อมูลไปหา):

Service คุณ → ชี้ไปที่ IncidentTracking Service (เส้นประ: Async Event ReportVerified) (เส้นหลัก)

Service คุณ → ชี้ไปที่ RescueRequest Service (เส้นประ: Async Event ReportVerified เฉพาะเคสขอความช่วยเหลือ)

Service คุณ → ชี้ไปที่ PropertyDamageReport Service (เส้นประ: Async Event ReportVerified เฉพาะเคสทรัพย์สินเสียหาย)

**Upstream Services (บริการต้นทางที่เรียกใช้งาน Report Ingestion & Verification Service)**  
1\. DisasterMonitoring Service (IoT & Sensors)

Interaction Type: Synchronous (HTTP POST)

Action: เรียกใช้งาน API POST /reports

Description: เมื่อ Sensor ตรวจจับความผิดปกติได้ (เช่น ระดับน้ำสูงเกินพิกัด) Service นี้จะส่งข้อมูลดิบเข้ามาเป็น "Report" หนึ่งรายการ เพื่อให้ Service ของคุณทำการประเมินร่วมกับข้อมูลจาก Social Media ว่าเป็นเหตุการณ์จริงหรือไม่ (Data Correlation)

2\. Operation Update Service (Command Center Dashboard)

Interaction Type: Synchronous (HTTP GET)

Action: เรียกใช้งาน API GET /reports/stats หรือ GET /reports?status=PENDING

Description: ดึงข้อมูลสถิติยอดรวมรายงาน (Total Reports), พื้นที่ที่มีการแจ้งเหตุหนาแน่น (Heatmap Data), และรายการที่รอการตรวจสอบ เพื่อนำไปแสดงผลบน Dashboard ให้ผู้บัญชาการเห็นภาพรวมสถานการณ์ข่าวสาร (Situational Awareness)

**Downstream Services (บริการปลายทางที่ Report Ingestion & Verification Service เรียกหรือส่งข้อมูลไป)**  
1\. IncidentTracking Service (Consumer หลัก)

Interaction Type: Asynchronous (Event-Driven ผ่าน EventBridge/PubSub)

Event Name: ReportVerified (Topic: report.verified)

Description: นี่คือหัวใจสำคัญของการเชื่อมต่อ เมื่อรายงานได้รับการยืนยัน (Status \= VERIFIED) Service ของคุณจะประกาศ Event ออกไป IncidentTracking Service จะรับข้อมูลนี้ (Subscribe) เพื่อนำไป "สร้าง Incident ใหม่" (Create New Incident) หรือ "อัปเดตข้อมูล Incident เดิม" (Merge Info) โดยอัตโนมัติ ทำให้ข้อมูลไหลลื่นโดยไม่ต้องรอ API ตอบกลับ

2\. RescueRequest Service (Consumer รอง \- เฉพาะเหตุ SOS)

Interaction Type: Asynchronous (Event-Driven)

Event Name: ReportVerified (Filter: type=SOS or severity=CRITICAL)

Description: หากรายงานที่ผ่านการ Verify แล้วมีเนื้อหาขอความช่วยเหลือเร่งด่วน (เช่น "ติดอยู่บนหลังคา", "คนแก่ป่วยหนัก") Service นี้จะดักจับ Event ดังกล่าวเพื่อนำไปสร้างเป็น "ใบงานกู้ภัย" (Rescue Ticket) ทันที เพื่อลดขั้นตอนการคีย์ข้อมูลซ้ำซ้อน

3\. PropertyDamageReport Service (Consumer รอง \- เฉพาะเหตุความเสียหาย)

Interaction Type: Asynchronous (Event-Driven)

Event Name: ReportVerified (Filter: type=DAMAGE)

Description: หากรายงานเป็นเรื่องสิ่งปลูกสร้างเสียหาย (เช่น "ถนนขาด", "สะพานพัง", "บ้านถล่ม") แต่ไม่มีผู้บาดเจ็บ ข้อมูลจะถูกส่งต่อไปยัง Service นี้เพื่อบันทึกเป็นรายการความเสียหายรอการซ่อมแซมหรือประเมินมูลค่า

4\. Incident Service (Reference Check \- Optional but Good)

Interaction Type: Synchronous (HTTP GET)

Action: เรียกใช้งาน API GET /incidents?active=true

Description: ในขั้นตอนที่เจ้าหน้าที่กำลังจะกด Verify และต้องการ Link ข้อมูลเข้ากับ Incident เดิม หน้า Dashboard ของคุณอาจจะเรียก API นี้เพื่อดึงรายชื่อ Incident ที่เปิดอยู่มาให้เจ้าหน้าที่เลือก (Dropdown List) เพื่อความถูกต้องของข้อมูล (Data Consistency)

**เหตุผลที่ออกแบบแบบนี้ (Technical Rationale)**  
การใช้ Asynchronous Event (ReportVerified) ส่งออกไปให้หลายๆ Service (IncidentTracking, RescueRequest, PropertyDamage) พร้อมกัน เรียกว่ารูปแบบ "Fan-out Pattern" ครับ

ข้อดี: คุณ (ReportVerify) ไม่ต้องรู้ Logic ของเพื่อนครับ หน้าที่จบแค่บอกว่า "ข่าวนี้จริงนะ"

ใครอยากได้ข้อมูล (Incident, Rescue, Damage) ก็มารับไปจัดการต่อเอง

ถ้าระบบกู้ภัย (RescueRequest) ล่ม ระบบของคุณก็ยังทำงานต่อได้ ไม่พังตามกัน (Fault Isolation)

# Dependency Mapping

**Dependency Mapping – Report Ingestion & Verification Service**

#### **1\. Incident Tracking Service**

* **Type: Microservice (External)**  
* **Interaction Style: Synchronous (REST API via HTTP GET)**  
* **Purpose: เรียกดูรายการเหตุการณ์ที่กำลังดำเนินอยู่ (Active Incidents) เพื่อให้เจ้าหน้าที่ (Trust Officer) สามารถเลือกเชื่อมโยงรายงาน (Link Report) เข้ากับเหตุการณ์ที่มีอยู่แล้วได้ถูกต้อง แทนที่จะสร้างเหตุการณ์ใหม่ซ้ำซ้อน**  
* **Criticality: Medium (Service ยังทำงานต่อได้ แต่ฟีเจอร์การ Link จะใช้งานไม่ได้)**  
* **Failure Handling:**  
  * **Graceful Degradation: หาก Incident Tracking Service ไม่ตอบสนอง ระบบจะปิดการใช้งานปุ่ม "Link to Existing Incident" ชั่วคราว (Disable UI Option)**  
  * **Fallback: บังคับให้เจ้าหน้าที่เลือก "Create New Incident" หรือบันทึกสถานะเป็น VERIFIED ไว้ก่อน แล้วค่อยมาทำการ Merge ข้อมูลในภายหลังเมื่อระบบกลับมาปกติ**

  #### **2\. Amazon SQS (report.ingestion.queue.v1)**

* **Type: Queue (AWS Service)**  
* **Interaction Style: Asynchronous (Buffer & Load Leveling)**  
* **Purpose: เป็นจุดพักข้อมูล (Buffer) สำหรับรับ Raw Reports จำนวนมหาศาลจาก External Sources (Bots, Apps) เพื่อป้องกันไม่ให้ Database หรือระบบประมวลผลล่มในช่วงที่มี Traffic Spike (เช่น ช่วงเกิดภัยพิบัติรุนแรง)**  
* **Criticality: Critical (ถ้า SQS ล่ม ข้อมูลขาเข้าจะสูญหาย)**  
* **Failure Handling:**  
  * **ใช้ Retry Policy ของ AWS Lambda ในการพยายามดึงข้อมูลไปประมวลผลซ้ำหากเกิด Error ชั่วคราว**  
  * **หากประมวลผลล้มเหลวครบตามจำนวนที่กำหนด (Max Retries Exceeded) ข้อมูลจะถูกย้ายไปยัง Dead Letter Queue (DLQ) โดยอัตโนมัติ เพื่อให้ทีม Developer เข้ามาตรวจสอบและ Re-drive ข้อมูลกลับเข้าระบบในภายหลัง (Zero Data Loss)**

  #### **3\. Amazon EventBridge (disaster.event.bus.v1)**

* **Type: Event Bus (AWS Service)**  
* **Interaction Style: Asynchronous (Event Publishing / Fan-out)**  
* **Purpose: เป็นช่องทางหลักในการกระจายข่าวเมื่อรายงานได้รับการยืนยัน (Event: `ReportVerified`) ไปยัง Service ปลายทางหลายตัวพร้อมกัน (เช่น Incident Service, Rescue Service, Dashboard) โดยไม่ต้องเชื่อมต่อกันโดยตรง**  
* **Criticality: High (ถ้าส่ง Event ไม่ได้ Service อื่นจะไม่รู้ว่ามีเหตุเกิด)**  
* **Failure Handling:**  
  * **หาก Publish Event ไม่สำเร็จ ระบบจะบันทึก Error Log พร้อม Payload ลงใน Database (Local Outbox Pattern)**  
  * **มีระบบ Scheduled Retry Task ที่จะคอยกวาด Event ที่ส่งไม่ผ่านใน Database เพื่อทำการส่งใหม่อีกครั้งจนกว่าจะสำเร็จ**

  #### **4\. Amazon DynamoDB (Reports Table)**

* **Type: Database (NoSQL)**  
* **Interaction Style: Internal Data Access (Read/Write)**  
* **Purpose: เป็นแหล่งข้อมูลหลัก (Single Source of Truth) ของ Service จัดเก็บข้อมูล Raw Reports ทั้งหมด, ผลการวิเคราะห์จาก AI, สถานะการตรวจสอบ (Validation Status), และประวัติการแก้ไข (Audit Logs)**  
* **Criticality: Critical (ระบบจะหยุดทำงานทันทีหาก Database ล่ม)**  
* **Failure Handling:**  
  * **Write Failure: หากบันทึกข้อมูลไม่สำเร็จ API จะตอบกลับ Error 500 (กรณี Sync) หรือโยน Exception เพื่อให้ SQS Retry (กรณี Async)**  
  * **Throttling: หากมีการเขียนเกิน Read/Write Capacity Unit ระบบจะใช้ Exponential Backoff ในการรอและลองเขียนใหม่**

  #### **5\. Amazon Comprehend (or Internal AI Logic)**

* **Type: AI Service (AWS Managed)**  
* **Interaction Style: Synchronous (Request/Response)**  
* **Purpose: วิเคราะห์ข้อความในรายงานเพื่อคำนวณค่าความน่าเชื่อถือ (Trust Score), ตรวจจับอารมณ์ (Sentiment), และหา Keywords สำคัญ (Entity Recognition)**  
* **Criticality: Medium (ระบบยังทำงานได้แม้ไม่มี AI)**  
* **Failure Handling:**  
  * **Fallback to Neutral: หาก AI Service ไม่ตอบสนองหรือ Error ระบบจะตั้งค่า Trust Score เป็นค่ากลาง (Default \= 50 หรือ Unknown)**  
  * **Flag for Review: รายงานนั้นจะถูกติดป้ายกำกับว่า "AI Analysis Failed" และส่งเข้าคิว Manual Review เพื่อให้มนุษย์เป็นผู้ตรวจสอบเอง 100% แทนที่จะปฎิเสธรายงานนั้นทิ้ง**