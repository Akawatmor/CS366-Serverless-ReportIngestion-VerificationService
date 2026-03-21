# Service Overview

**ภาพรวมของบริการ (Service Overview)**  
RescueRequest Service 

**0\. Repository**  
GitHub: [https://github.com/Phattharaphum/rescue-request-service](https://github.com/Phattharaphum/rescue-request-service)

**1\. Service Owner**  
นายภัทรภูมิ กิ่งชัย รหัสนักศึกษา 6609612160 ภาคปกติ

**2\. Service Purpose**  
**RescueRequest Service** เป็นบริการที่รับผิดชอบการจัดการคำร้อง สถานะของคำร้องขอความช่วยเหลือจากประชาชน (Citizens) ตั้งแต่การรับเรื่อง การจัดเก็บรายละเอียดที่สำคัญ (เช่น พิกัด, จำนวนคน, ความต้องการพิเศษ) รวมถึงการแจ้งข้อมูลรายละเอียดเพิ่มเติม ไปจนถึงการติดตามสถานะการช่วยเหลือ โดยทำหน้าที่เป็นจุดรับข้อมูล (Intake) กลาง เพื่อให้มั่นใจว่าคำร้องทุกรายการถูกบันทึกและสามารถตรวจสอบสถานะได้ตลอดเวลา

**3\. Pain Point ที่แก้ไข**  
ในสถานการณ์ภัยพิบัติ ผู้ประสบภัยมักประสบปัญหาในการแจ้งขอความช่วยเหลือเนื่องจากขาดช่องทางที่ระบุรายละเอียดสำคัญ (เช่น พิกัดที่แม่นยำ หรือผู้ป่วยติดเตียง) ได้อย่างครบถ้วนในครั้งเดียว และมักเกิดความกังวลเมื่อไม่ทราบสถานะว่ามีใครรับเรื่องแล้วหรือไม่ นอกจากนี้ ปัญหาเครือข่ายที่ไม่เสถียรทำให้เกิดการส่งข้อมูลซ้ำซ้อน (Duplicate requests) จนเจ้าหน้าที่สับสน บริการนี้จึงถูกออกแบบมาเพื่อรวบรวมข้อมูลให้เป็นระบบ ลดความซ้ำซ้อน และให้ผู้ประสบภัยติดตามความคืบหน้าได้ (Trackable status)

**4\. Target Users**

1. **Citizens (ผู้ประสบภัย):** ส่งคำร้อง \+ แจ้งรายละเอียดเพิ่มเติม \+ ตรวจสอบสถานะ  
2. **Dispatchers / Triage Staff:** คัดกรอง/จัดลำดับความสำคัญ/ปรับสถานะ  
3. **Rescue Teams:** ใช้ข้อมูลหน้างานผ่านระบบที่เชื่อมต่อ (เช่น Dispatch/Operations)

**5\. Service Boundary**

* In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)  
  * **Request Ingestion & Validation:**  
    รับคำร้อง ตรวจสอบรูปแบบและความครบถ้วนของข้อมูลสำคัญ (Location, Contact, Needs)  
  * **State Machine Management:** จัดการสถานะของคำร้องตาม Flow   
    SUBMITTED → TRIAGED → ASSIGNED → IN\_PROGRESS → RESOLVED หรือ CANCELLED  
  * **Duplicate Handling (Idempotency):**  
    ตรวจสอบและจัดการคำร้องที่ซ้ำกันจากผู้ใช้คนเดิมในเวลาใกล้เคียงกัน  
  * **Status Tracking:** ให้บริการข้อมูลสถานะปัจจุบันแก่ผู้ร้องขอ  
  * **Audit Trail / Logs:** เก็บประวัติการเปลี่ยนแปลงสถานะทั้งหมด เพื่อใช้ตรวจสอบย้อนหลัง  
* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
  * **Resource Dispatching:** การสั่งการหรือจัดสรรยานพาหนะ/ทีมกู้ภัย (เป็นหน้าที่ของ Dispatch Service)  
  * **Incident Management:** การจัดการข้อมูลภาพรวมของภัยพิบัติ (เป็นหน้าที่ของ Incident Service)  
  * **Medical Diagnosis:** การประเมินอาการทางการแพทย์เชิงลึก  
  * **Social Media Scraping/Crawling:** ดึงข้อมูลขอความช่วยเหลือจากโพสต์ในโซเชียลมีเดีย (เช่น Facebook, X) โดยตรง 

**6\. Autonomy / Decision Logic**  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การยอมรับ (Accept) หรือปฏิเสธ (Drop) คำร้องที่ซ้ำซ้อน (De-duplication logic)  
* การตรวจสอบความถูกต้องของรูปแบบข้อมูล (Data Validation) ก่อนบันทึก  
* การอนุญาตให้เปลี่ยนสถานะ (State Transition) ว่าเป็นไปตาม Flow ที่กำหนดหรือไม่

หลักการตัดสินใจ (Decision inputs):  
6.1 Idempotency (Strong)

* ใช้ X-Idempotency-Key (UUID) จาก client  
* ถ้า key เดิมถูกใช้แล้ว → ต้องคืน ผลลัพธ์เดิมเสมอ ( TTL 24 ชม.)  
* คืนผลเดิม (รวม status code) พร้อม Idempotency-Replayed: true

6.2 Duplicate Heuristic (Weak, เมื่อไม่มี key)

* ตรวจจับคำร้องซ้ำโดยใช้ uniqueness key:

  incidentId(UUID) \+ normalizedPhonePrimary \+ requestType \+ geoHash(7) \+ timeBucket(5 minutes)

* ถ้าซ้ำ → ตอบ 409 Conflict พร้อม existingRequestId เพื่อให้ user track รายการเดิม

6.3 Current Status & Completeness

* ถ้า RESOLVED หรือ CANCELLED แล้ว: เป็น terminal state อาจไม่อนุญาตแก้ไข  
* ต้องมีข้อมูลจำเป็นครบ: Location, Phone number, peopleCount ≥ 1

บริการสามารถตัดสินใจจัดการข้อมูลซ้ำได้เอง (System decision) โดยไม่ต้องรออนุมัติจากมนุษย์

**7\. Owned Data**

* **Rescue Request Records (Core Domain):** ข้อมูลหลักของคำร้อง ได้แก่ requestId, description, peopleCount, specialNeeds, Location, contact ซึ่งเป็นข้อมูล Core Domain ที่บริการนี้สร้างและดูแลความถูกต้อง  
* **Request Lifecycle State:** ข้อมูลสถานะปัจจุบัน (status) และเวลาที่รับเรื่อง (submittedAt) ซึ่งสะท้อนความเป็นไปของคำร้องนั้นๆ  
* **Audit Trail:** ประวัติการเปลี่ยนสถานะครบทุกครั้ง

**8\. Linked Data (Reference Only)**

* **incidentId:** อ้างอิงจาก Incident Service เพื่อระบุว่าคำร้องนี้อยู่ภายใต้เหตุการณ์ภัยพิบัติใด (ใช้เพื่อจัดกลุ่มคำร้อง แต่ไม่ได้เก็บรายละเอียดเหตุการณ์ไว้ที่นี่)

**9\. Non-Functional Requirements**

* **Idempotency:** ระบบต้องรองรับการส่งคำร้องซ้ำ (Retry) จากฝั่ง Client กรณีเครือข่ายไม่ดี โดยต้องไม่สร้าง Record ใหม่ แต่ให้คืนค่า requestId เดิมและสถานะล่าสุดกลับไป  
* **High Availability:** API สำหรับรับคำร้อง (Create Request) ต้องมีความพร้อมใช้งานสูง รองรับ Load ได้มากในช่วงวิกฤต  
* **Data Consistency:** สถานะ (status) ต้องมีความถูกต้อง เพื่อให้ผู้ประสบภัยและเจ้าหน้าที่เห็นข้อมูลตรงกัน  
* **Response Time:** การตรวจสอบสถานะ (Get Details) ต้องรวดเร็วเพื่อลดความกังวลของผู้ใช้งาน

**10\. State Machine Specification**  
**Status Enum (Global):**

SUBMITTED, TRIAGED, ASSIGNED, IN\_PROGRESS, RESOLVED, CANCELLED

Terminal States:

RESOLVED, CANCELLED

Allowed Transitions

| From | To | Allowed Roles | Notes |
| ----- | ----- | ----- | ----- |
| SUBMITTED | TRIAGED | TRIAGE, DISPATCHER | คัดกรอง \+ กำหนด priority |
| TRIAGED | ASSIGNED | DISPATCHER | ต้องมี responderUnitId |
| ASSIGNED | IN\_PROGRESS | RESCUE\_TEAM, DISPATCHER | เริ่มปฏิบัติ |
| IN\_PROGRESS | RESOLVED | RESCUE\_TEAM, DISPATCHER | จบภารกิจ |
| SUBMITTED | CANCELLED | DISPATCHER, ADMIN | ต้องมี reason |
| TRIAGED | CANCELLED | DISPATCHER, ADMIN | ต้องมี reason |
| ASSIGNED | CANCELLED | DISPATCHER, ADMIN | ต้องมี reason |
| IN\_PROGRESS | CANCELLED | DISPATCHER, ADMIN | ต้องมี reason |
| RESOLVED / CANCELLED | any | ✗ | ห้ามเปลี่ยน |

# Sync Contract

**Synchronous Function Contract**

# **\#1 Create Rescue Request**

ชื่อ: CreateRescueRequest  
HTTP Method: **POST**  
Path: **/v1/rescue-requests**  
สรุป:  
รับคำร้องขอความช่วยเหลือจากประชาชน/ช่องทางต่าง ๆ สร้างคำร้องใหม่ พร้อมออก “tracking code 6 หลัก” สำหรับติดตามและแจ้งข้อมูลเพิ่ม  
**Request**  
Path parameters

* ไม่มี

Query parameters

* ไม่มี

Headers

* Content-Type: application/json (Required)  
* Accept: application/json  
* X-Idempotency-Key: \<uuid\> — ทำให้การ retry ไม่สร้างคำร้องซ้ำ  
* X-Client-Id: \<string\> (Optional) — เช่น citizen-app  
* X-Forwarded-For (Optional) — ใช้จาก API Gateway/Load balancer  
* User-Agent (Optional)

Body ตัวอย่าง:  
{  
  "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
  "requestType": "flood\_rescue",  
  "description": "ติดอยู่ชั้น 2",  
  "peopleCount": 4,  
  "specialNeeds": \["bedridden"\],  
  "location": {  
    "latitude": 18.7883,  
    "longitude": 98.9853,  
    "locationDetails": { "floor": "2", "landmark": "หน้าโรงเรียน" },  
    "province": "เชียงใหม่",  
    "district": "เมืองเชียงใหม่",  
    "subdistrict": "สุเทพ",  
    "addressLine": "123 ม.2 ถ.ห้วยแก้ว"  
  },  
  "contact": {  
    "contactName": "สมชาย",  
    "contactPhone": "0812345678"  
  },  
  "sourceChannel": "MOBILE\_APP"  
}

Validation rules

* incidentId ต้องเป็น UUID ที่ถูกต้อง  
* peopleCount ต้อง \>= 1  
* location.latitude อยู่ในช่วง \[-90, 90\] และ location.longitude อยู่ในช่วง \[-180, 180\]  
* contact.contactPhone ต้อง normalize ได้ (เช่น แปลงเป็น E.164 ได้) และไม่ว่าง  
* X-Idempotency-Key ต้องเป็น UUID

**Response**  
Success case

* 201 Created (ครั้งแรกที่สร้างสำเร็จ)  
  * Headers:  
    * Location: /v1/rescue-requests/{requestId}  
    * X-Trace-Id: \<uuid\>

  Body ตัวอย่าง:

      {

    "requestId": "REQ-8812-9901",

    "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",

    "status": "SUBMITTED",

    "tracking": {

      "trackingCode": "493027",

      "contactPhoneLast4": "5678"

    },

    "submittedAt": "2026-02-21T10:30:00Z"

  }

  *   
* 200 OK (กรณี replay จาก idempotency key เดิม)  
  * Headers:  
    * Idempotency-Replayed: true  
    * X-Trace-Id: \<uuid\>  
  * Body: เหมือน success เดิม (คืนผลลัพธ์เดิมเสมอ)

Error case (ตัวอย่างที่พบบ่อย)

* 400 Bad Request — รูปแบบ JSON ผิด/parse ไม่ได้  
* 401 Unauthorized — (ถ้าคุณบังคับ auth บาง channel)  
  409 Conflict — ตรวจพบคำร้องซ้ำแบบ heuristic (ไม่มี idempotency key) ตัวอย่าง:

  {  
    "message": "Duplicate request detected",  
    "traceId": "0c7f6d5e-55b1-4f4e-9e58-1d9b0a2c91bb",  
    "details": \[  
      { "existingRequestId": "REQ-8812-9901" }  
    \]  
  }

* 409 Conflict — idempotency key เดิมแต่ payload เปลี่ยน (fingerprint mismatch)  
* 422 Unprocessable Entity — validation ไม่ผ่าน (เช่น peopleCount \< 1\)  
* 429 Too Many Requests — ถูกจำกัดอัตรา (กัน spam)  
* 500 Internal Server Error  
* 503 Service Unavailable — DB/Dependency ไม่พร้อม

**Dependency, Reliability, Failure handling**

* Dependency หลัก: Database (Master \+ Current State \+ Idempotency \+ Tracking Index)  
* เรียก service อื่นไหม: ไม่จำเป็นต้องเรียก Incident Service แบบ synchronous (แค่ validate UUID)  
* ถ้า DB ล่ม: ตอบ 503 พร้อม traceId  
* Timeout: 3–5 วินาทีต่อ request (Lambda \+ DB)  
* Retry:  
  * ฝั่ง client retry ได้ แต่ให้ส่ง X-Idempotency-Key ทุกครั้ง  
* Idempotent:  
  * เป็น Idempotent 

---

# **\#2 Get Rescue Request Details**

ชื่อ: GetRescueRequest  
HTTP Method: **GET**  
Path: **/v1/rescue-requests/{requestId}**  
สรุป:  
ดึงรายละเอียดคำร้อง \+ สถานะล่าสุด (จาก Current State) สำหรับเจ้าหน้าที่ หรือประชาชนที่ยืนยันด้วย “เบอร์ \+ tracking code”  
**Request**  
Path parameters

* requestId (string, Required) — รหัสคำร้อง เช่น REQ-8812-9901

Query parameters (Optional)

* includeEvents (boolean, Optional, default=false) — ถ้าต้องการแนบ event history  
* includeCitizenUpdates (boolean, Optional, default=false) — ถ้าต้องการแนบการแจ้งข้อมูลเพิ่ม

Headers (เลือกอย่างใดอย่างหนึ่งสำหรับการเข้าถึง)

* แบบ Staff  
  * Authorization: Bearer \<token\> (Required สำหรับ staff)  
* แบบ Citizen  
  * X-Citizen-Phone: \<string\> (Required) — เบอร์ที่ใช้แจ้ง  
  * X-Tracking-Code: \<string\> (Required) — เลข 6 หลัก  
* ทั่วไป:  
  * Accept: application/json (Optional)

Validation rules

* requestId ต้อง match pattern เช่น ^REQ-\[0-9\]{4}-\[0-9\]{4}$  
* Citizen access: phone \+ trackingCode ต้อง match กับ Tracking Lookup Index/Master  
* ถ้า includeEvents=true จำกัดจำนวน/ช่วงเวลา (กัน payload ใหญ่เกิน)

**Response**  
Success case

* 200 OK  
  * Headers:  
    * X-Trace-Id: \<uuid\>

  Body ตัวอย่าง (แสดงทั้ง master \+ current state):  
      {

    "request": {

      "requestId": "REQ-8812-9901",

      "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",

      "requestType": "flood\_rescue",

      "description": "ติดอยู่ชั้น 2",

      "peopleCount": 4,

      "specialNeeds": \["bedridden"\],

      "location": {

        "latitude": 18.7883,

        "longitude": 98.9853,

        "locationDetails": { "floor": "2", "landmark": "หน้าโรงเรียน" },

        "province": "เชียงใหม่",

        "district": "เมืองเชียงใหม่",

        "subdistrict": "สุเทพ",

        "addressLine": "123 ม.2 ถ.ห้วยแก้ว"

      },

      "contact": {

        "contactName": "สมชาย",

        "contactPhoneMasked": "081\*\*\*678"

      },

      "sourceChannel": "MOBILE\_APP",

      "submittedAt": "2026-02-21T10:30:00Z",

      "lastCitizenUpdateAt": "2026-03-03T08:10:00Z"

    },

    "current": {

      "status": "ASSIGNED",

      "priority\_score": 85,

      "priority\_level": "High",

      "assignedUnitId": "UNIT-BOAT-05",

      "assignedAt": "2026-02-21T11:00:00Z",

      "latestNote": { "message": "กำลังเดินทาง" },

      "stateVersion": 3,

      "lastEventId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",

      "lastUpdatedAt": "2026-02-21T11:00:00Z"

    }

  }

Error case

* 401 Unauthorized — staff token ไม่มี/ไม่ถูกต้อง  
* 403 Forbidden — citizen phone+trackingCode ไม่ผ่าน  
* 404 Not Found — ไม่พบ requestId  
* 429 Too Many Requests  
* 500 / 503 ตามระบบ

**Dependency, Reliability, Failure handling**

* Dependency: DB (Master \+ Current State), (Optional) อ่าน Events/Updates เมื่อ include=true  
* Timeout: 2–3 วินาที  
* Retry: GET retry ได้ (safe)  
* Idempotent: ใช่ (GET)

---

# **\#3 Patch Rescue Request (Add/Update Details)**

ชื่อ: PatchRescueRequestDetails  
HTTP Method: **PATCH**  
Path: **/v1/rescue-requests/{requestId}**  
สรุป:  
ให้ผู้ร้อง/เจ้าหน้าที่อัปเดตรายละเอียดคำร้อง (ไม่ใช่การเปลี่ยนสถานะ) เช่น เพิ่ม landmark, เปลี่ยน peopleCount, เพิ่ม specialNeeds และบันทึก audit (Citizen Request Updates)  
**Request**  
Path parameters

* requestId (string, Required)

Query parameters

* ไม่มี

Headers

* แบบ Staff  
  * Authorization: Bearer \<token\> (Required)  
* แบบ Citizen  
  * X-Citizen-Phone: \<string\> (Required)  
  * X-Tracking-Code: \<string\> (Required)  
* เพิ่มเติม (แนะนำ):  
  * Content-Type: application/json (Required)  
  * X-Idempotency-Key: \<uuid\> (Optional แต่แนะนำสำหรับ PATCH)  
  * If-Match: \<stateVersion\> (Optional) — กันชนกันเขียนทับ (optimistic concurrency)

Body (JSON) ตัวอย่าง:  
{  
  "description": "น้ำเริ่มสูงขึ้น",  
  "peopleCount": 5,  
  "specialNeeds": \["bedridden", "infant"\],  
  "locationDetails": { "floor": "2", "landmark": "หน้าวัด" },  
  "addressLine": "123 ม.2 ถ.ห้วยแก้ว"  
}

Validation rules

* อย่างน้อยต้องมี 1 ฟิลด์ให้แก้ (body ห้ามว่าง)  
* peopleCount ถ้ามีต้อง \>= 1  
* specialNeeds ถ้ามีต้องเป็น array และจำนวนสมาชิกไม่เกินที่กำหนด ( \<= 10\)  
* ห้ามแก้ incidentId และ ห้ามแก้ status ผ่าน endpoint นี้  
* ถ้า Current State เป็น RESOLVED หรือ CANCELLED → ปฏิเสธ (409)

**Response**  
Success case

* 200 OK  
  * Headers:  
    * X-Trace-Id: \<uuid\>

  Body ตัวอย่าง:  
      {

    "requestId": "REQ-8812-9901",

    "updatedFields": \["description", "peopleCount", "specialNeeds", "locationDetails", "addressLine"\],

    "lastCitizenUpdateAt": "2026-03-03T08:10:00Z"

  }

  * ภายในระบบควร:  
    * update Master Data  
    * insert 1 record ใน Citizen Request Updates (audit)  
    * publish async event rescue-request.citizen-updated

Error case

* 401 / 403 — auth ไม่ผ่าน  
* 404 — ไม่พบ requestId  
* 409 Conflict — อยู่ใน terminal state (RESOLVED/CANCELLED) หรือ If-Match ไม่ตรง (ถ้าคุณใช้)  
* 409 Conflict — idempotency key เดิมแต่ payload เปลี่ยน (ถ้าคุณใช้ X-Idempotency-Key)  
* 422 — validation ไม่ผ่าน  
* 429 — rate limit / lockout (กันเดารหัส tracking)  
* 500 / 503

**Dependency, Reliability, Failure handling**

* Dependency: DB (Master \+ CitizenUpdates)  
* ถ้าเขียน audit ไม่สำเร็จ: ถือว่า request ล้มเหลว (transaction/atomicity)  
* Timeout: 3–5 วินาที  
* Retry: แนะนำให้ client retry ได้เมื่อมี X-Idempotency-Key  
* Idempotent:  
  * เป็น idempotent 

---

# **\#4 Citizen Tracking Lookup**

ชื่อ: CitizenTrackingLookup  
HTTP Method: **POST**  
Path: **/v1/citizen/tracking/lookup**  
คำอธิบาย:  
ตรวจสอบ “เบอร์โทร \+ tracking code 6 หลัก” เพื่อค้นหา requestId ของคำร้องที่เจ้าของต้องการติดตาม/แจ้งข้อมูลเพิ่ม  
**Request**  
Path parameters

* ไม่มี

Query parameters

* ไม่มี

Headers

* Content-Type: application/json (Required)  
* Accept: application/json (Optional)  
* User-Agent (Optional)

Body (JSON) ตัวอย่าง:  
{  
  "contactPhone": "0812345678",  
  "trackingCode": "493027"  
}

Validation rules 

* trackingCode ต้องเป็นตัวเลข 6 หลัก (^\[0-9\]{6}$)  
* contactPhone ต้องไม่ว่าง และ normalize เป็น contactPhoneNormalized ได้  
* จำกัดจำนวนครั้งต่อ IP/เบอร์ (กัน brute force) 5 ครั้ง/10 นาที → เกินแล้ว 429

**Response**  
Success case

* 200 OK  
  * Headers:  
    * X-Trace-Id: \<uuid\>  
      Body ตัวอย่าง:

      {  
        "requestId": "REQ-8812-9901",  
        "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
        "status": "ASSIGNED",  
        "matchedBy": "PHONE\_PLUS\_TRACKING\_CODE"  
      }  
  * ความหมาย:  
    * requestId ใช้ไปเรียกดูสถานะ/ส่งข้อมูลเพิ่ม  
    * status (ถ้ามี cache ใน Current State/Index) เพื่อแสดงหน้าติดตามได้เร็ว

Error case

* 400 Bad Request — JSON ผิด/ฟิลด์ไม่ครบ  
* 403 Forbidden — เบอร์+โค้ดไม่ถูกต้อง (ตั้งใจไม่บอกว่า “ไม่พบ” เพื่อกันการเดา)

  {

    "message": "Invalid tracking credentials",

    "traceId": "..."

  }

* 429 Too Many Requests — เดาผิดถี่/เกิน rate limit  
* 503 Service Unavailable — DB ไม่พร้อม

**Dependency, Reliability, Failure handling**

* Dependency: DB ภายใน (อ่าน Tracking Lookup Index เป็นหลัก)  
* เรียก service อื่นไหม: ไม่เรียก  
* ถ้า DB ล่ม: ตอบ 503  
* Timeout: 2–3 วินาที  
* Retry: ทำได้ (ปลอดภัย)  
* Idempotent: ใช่ 

---

# **\#5 Get Citizen Rescue Request Status**

ชื่อ: GetCitizenRescueRequestStatus  
HTTP Method: **GET**  
Path: **/v1/citizen/rescue-requests/{requestId}/status**  
คำอธิบาย:  
ให้ผู้ร้องดูสถานะล่าสุดของคำร้อง โดยต้องยืนยันด้วย “เบอร์ \+ tracking code”  
**Request**  
Path parameters

* requestId (string, Required) — รหัสคำร้อง เช่น REQ-8812-9901

Query parameters

* ไม่มี 

Headers

* Accept: application/json (Optional)  
* X-Citizen-Phone: \<string\> (Required)  
* X-Tracking-Code: \<string\> (Required)

Validation rules 

* requestId ต้องมีรูปแบบถูกต้อง (ตาม pattern ที่กำหนด)  
* X-Tracking-Code ต้องเป็นเลข 6 หลัก  
* phone+code ต้อง match กับ requestId

**Response**  
Success case

* 200 OK  
  * Headers:  X-Trace-Id: \<uuid\>

Body ตัวอย่าง:  
{  
  "requestId": "REQ-8812-9901",  
  "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
  "status": "ASSIGNED",  
  "assignedUnitId": "UNIT-BOAT-05",  
  "latestNote": { "message": "กำลังเดินทาง" },  
  "lastUpdatedAt": "2026-02-21T11:00:00Z",  
  "stateVersion": 3,  
  "lastEventId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111"  
}

* 

Error case

* 403 Forbidden — ยืนยันตัวตนไม่ผ่าน (เบอร์+โค้ดไม่ตรงกับ requestId)  
* 404 Not Found — ถ้า requestId ไม่มีจริง (สำหรับ citizen ตอบ 403 เพื่อกัน enumeration)  
* 429 Too Many Requests  
* 503 Service Unavailable

**Dependency, Reliability, Failure handling**

* Dependency: DB ภายใน (อ่าน Rescue Request Current State เป็นหลัก; ถ้าไม่มี Current State ก็อ่าน latest event จาก Status Events)  
* เรียก service อื่นไหม: ไม่เรียก  
* Timeout: 2–3 วินาที  
* Retry: ได้ (GET)  
* Idempotent: ใช่

---

# **\#6 Create Citizen Rescue Request Update**

ชื่อ: CreateCitizenRescueRequestUpdate  
HTTP Method: **POST**  
Path: **/v1/citizen/rescue-requests/{requestId}/updates**  
คำอธิบาย:  
ให้ผู้ร้องส่งรายละเอียดเพิ่มเติม (เช่น NOTE/LOCATION\_DETAILS/PEOPLE\_COUNT/ฯลฯ) โดยยืนยันด้วย “เบอร์ \+ tracking code” และบันทึกลง Citizen Request Updates  
**Request**  
Path parameters

* requestId (string, Required)

Query parameters

* ไม่มี

Headers

* Content-Type: application/json (Required)  
* Accept: application/json (Optional)  
* X-Citizen-Phone: \<string\> (Required)  
* X-Tracking-Code: \<string\> (Required)  
* X-Idempotency-Key: \<uuid\> 

Body (JSON) ตัวอย่าง:  
{  
  "updateType": "NOTE",  
  "updatePayload": {  
    "note": "น้ำสูงขึ้นถึงเอว"  
  }  
}

ตัวอย่าง (อัปเดต peopleCount):  
{  
  "updateType": "PEOPLE\_COUNT",  
  "updatePayload": {  
    "peopleCount": 5  
  }  
}  
Validation rules

* updateType ต้องอยู่ในชุดที่อนุญาต: NOTE, LOCATION\_DETAILS, PEOPLE\_COUNT, SPECIAL\_NEEDS, CONTACT\_INFO  
* updatePayload ต้องสอดคล้องกับ updateType (เช่น PEOPLE\_COUNT ต้องมี peopleCount)  
* peopleCount ถ้ามีต้อง \>= 1  
* ถ้าสถานะปัจจุบันเป็น RESOLVED หรือ CANCELLED → ปฏิเสธ (409)  
* จำกัดขนาด payload ( ≤ 4KB) กัน spam/ข้อมูลใหญ่เกิน

**Response**  
Success case

* 201 Created  
  * Headers:  
    * X-Trace-Id: \<uuid\>

Body ตัวอย่าง:

{  
  "updateId": "b21f0c2a-9d11-4fbb-9a4c-2b0a1f0c9d11",  
  "requestId": "REQ-8812-9901",  
  "updateType": "NOTE",  
  "createdAt": "2026-03-03T08:10:00Z"  
}

*   
* 200 OK (ถ้า replay ด้วย idempotency key เดิม)  
  * Headers:  
    * Idempotency-Replayed: true

Error case

* 400 Bad Request — JSON ผิด/ฟิลด์ไม่ครบ  
* 403 Forbidden — phone+code ไม่ผ่าน  
* 409 Conflict — อยู่ terminal state (RESOLVED/CANCELLED)  
* 409 Conflict — idempotency key เดิมแต่ payload เปลี่ยน (fingerprint mismatch)  
* 422 Unprocessable Entity — validation ไม่ผ่าน (peopleCount \< 1 ฯลฯ)  
* 429 Too Many Requests — rate limit/lockout  
* 503 Service Unavailable

**Dependency, Reliability, Failure handling**

* Dependency: DB ภายใน (เขียน Citizen Request Updates; อัปเดต Master.lastCitizenUpdateAt)  
* เรียก service อื่นไหม: ไม่เรียกแบบ synchronous (publish event)  
* ถ้า DB ล่ม: ตอบ 503  
* Timeout: 3–5 วินาที  
* Retry:  
  * retry ได้เช็คจาก X-Idempotency-Key  
* Idempotent:  
  * เป็น idempotent

---

# **\#7 List Citizen Rescue Request Updates**

ชื่อ: ListCitizenRescueRequestUpdates  
HTTP Method: **GET**  
Path: **/v1/citizen/rescue-requests/{requestId}/updates**  
คำอธิบาย:  
ให้ผู้ร้องดึงรายการ “ข้อมูลเพิ่มเติมที่เคยส่ง” ของคำร้องนั้น ๆ โดยยืนยันด้วย “เบอร์ \+ tracking code”  
**Request**  
Path parameters

* requestId (string, Required)

Query parameters

* limit (int, Optional, default=20) — จำนวนรายการต่อหน้า (เช่น 1–50)  
* cursor (string, Optional) — token สำหรับ pagination  
* since (datetime, Optional) — ดึงเฉพาะรายการหลังเวลาที่กำหนด

Headers

* Accept: application/json (Optional)  
* X-Citizen-Phone: \<string\> (Required)  
* X-Tracking-Code: \<string\> (Required)

Validation rules

* limit ต้องอยู่ในช่วงที่กำหนด (เช่น 1–50)  
* since ถ้ามีต้องเป็น datetime format ถูกต้อง  
* phone+code ต้อง match กับ requestId

**Response**  
Success case

* 200 OK  
  * Headers:  
    * X-Trace-Id: \<uuid\>

Body ตัวอย่าง:  
{  
  "requestId": "REQ-8812-9901",  
  "items": \[  
    {  
      "updateId": "b21f0c2a-9d11-4fbb-9a4c-2b0a1f0c9d11",  
      "updateType": "NOTE",  
      "updatePayload": { "note": "น้ำสูงขึ้นถึงเอว" },  
      "createdAt": "2026-03-03T08:10:00Z"  
    }  
  \],  
  "nextCursor": "eyJrZXkiOiAiLi4uIn0="  
}

* 

Error case

* 403 Forbidden — auth ไม่ผ่าน  
* 404 Not Found — requestId ไม่มีจริง   
* 422 Unprocessable Entity — query param ไม่ถูกต้อง (limit เกิน, since format ผิด)  
* 429 Too Many Requests  
* 503 Service Unavailable

**Dependency, Reliability, Failure handling**

* Dependency: DB ภายใน (อ่าน Citizen Request Updates)  
* เรียก service อื่นไหม: ไม่เรียก  
* Timeout: 2–3 วินาที  
* Retry: ได้ (GET)  
* Idempotent: ใช่

---

# **\#8 List Rescue Request Status Events**

ชื่อ: ListRescueRequestStatusEvents  
HTTP Method: **GET**  
Path: **/v1/rescue-requests/{requestId}/events**  
คำอธิบาย:  
ดึงประวัติการเปลี่ยนสถานะ (event log) ของคำร้องตามลำดับ version/เวลา เพื่อใช้ audit และแสดง timeline ให้เจ้าหน้าที่  
**Request**  
Path parameters

* requestId (string, Required) — รหัสคำร้อง เช่น REQ-8812-9901

Query parameters

* limit (int, Optional, default=50) — จำนวน event ต่อหน้า (แนะนำ 1–200)  
* cursor (string, Optional) — token สำหรับ pagination  
* sinceVersion (int, Optional) — ดึงเฉพาะ event ที่ version \> sinceVersion  
* order (enum, Optional, default=asc) — asc หรือ desc ตาม version

Headers

* Authorization: Bearer \<token\> (Required) — สำหรับ staff/dispatcher/admin  
* Accept: application/json (Optional)

Validation rules

* requestId ต้องอยู่ในรูปแบบที่ระบบกำหนด  
* limit ต้องอยู่ในช่วงที่กำหนด (เช่น 1–200)  
* sinceVersion ถ้ามีต้อง \>= 0  
* order ต้องเป็น asc หรือ desc

**Response**  
Success case

* 200 OK  
  * Headers:  
    * X-Trace-Id: \<uuid\>

Body ตัวอย่าง:  
{  
  "requestId": "REQ-8812-9901",  
  "items": \[  
    {  
      "eventId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
      "previousStatus": "TRIAGED",  
      "newStatus": "ASSIGNED",  
      "changedBy": "STAFF-009",  
      "changedByRole": "DISPATCHER",  
      "changeReason": "เปลี่ยนทีมเนื่องจากรถเสีย",  
      "meta": { "eta\_min": 15 },  
      "priority\_score": 85,  
      "responderUnitId": "UNIT-BOAT-05",  
      "version": 3,  
      "occurredAt": "2026-02-21T11:00:00Z"  
    }  
  \],  
  "nextCursor": "eyJrZXkiOiAiLi4uIn0="  
}

* ความหมาย:  
  * items\[\] คือ timeline ของการเปลี่ยนสถานะ  
    * nextCursor ใช้เรียกหน้าถัดไป

Error case

* 401 Unauthorized — token ไม่มี/ไม่ถูกต้อง  
* 403 Forbidden — role ไม่อนุญาต  
* 404 Not Found — ไม่พบ requestId  
* 422 Unprocessable Entity — query param ไม่ถูกต้อง  
* 503 Service Unavailable — DB ไม่พร้อม

**Dependency, Reliability, Failure handling**

* Dependency: DB ภายใน (อ่าน Rescue Request Status Events)  
* เรียก service อื่นไหม: ไม่เรียก  
* ถ้า DB ล่ม: ตอบ 503  
* Timeout: 2–3 วินาที  
* Retry: ได้ (GET)  
* Idempotent: ใช่

---

# **\#9 Append Rescue Request Status Event**

ชื่อ: AppendRescueRequestStatusEvent  
HTTP Method: **POST**  
Path: **/v1/rescue-requests/{requestId}/events**  
คำอธิบาย:  
เพิ่มเหตุการณ์เปลี่ยนสถานะ (append-only) ตามกฎ state machine และอัปเดต Current State ให้ตรงกับ event ล่าสุด หมายเหตุ: endpoint นี้ใช้สำหรับ staff/dispatcher/rescue-team เท่านั้น (ไม่ใช่ citizen)  
**Request**  
Path parameters

* requestId (string, Required)

Query parameters

* ไม่มี

Headers

* Authorization: Bearer \<token\> (Required)  
* Content-Type: application/json (Required)  
* Accept: application/json (Optional)  
* X-Idempotency-Key: \<uuid\> (Optional แต่แนะนำ) — กันส่งซ้ำจาก network/retry  
* If-Match: \<stateVersion\> (Optional แต่แนะนำ) — optimistic concurrency (ต้องเท่ากับ current.stateVersion)

Body (JSON) ตัวอย่าง:  
{  
  "newStatus": "ASSIGNED",  
  "responderUnitId": "UNIT-BOAT-05",  
  "changeReason": "มอบหมายทีมเรือ",  
  "meta": { "eta\_min": 15 },  
  "priority\_score": 85  
}

Validation rules

* newStatus ต้องอยู่ใน enum: SUBMITTED, TRIAGED, ASSIGNED, IN\_PROGRESS, RESOLVED, CANCELLED  
* ต้องผ่านกฎ transition (เช่น TRIAGED \-\> ASSIGNED เท่านั้น)  
* ถ้า newStatus \= ASSIGNED ต้องมี responderUnitId  
* ถ้า newStatus \= CANCELLED ต้องมี changeReason  
* ถ้า Current State อยู่ RESOLVED/CANCELLED ห้ามเปลี่ยน (409)  
* ถ้าใช้ If-Match ต้องตรงกับ current.stateVersion ไม่งั้น 409 (กันเขียนทับ)

**Response**  
Success case

* 201 Created  
  * Headers:  
    * X-Trace-Id: \<uuid\>

Body ตัวอย่าง:  
{  
  "requestId": "REQ-8812-9901",  
  "event": {  
    "eventId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
    "previousStatus": "TRIAGED",  
    "newStatus": "ASSIGNED",  
    "changedBy": "STAFF-009",  
    "changedByRole": "DISPATCHER",  
    "changeReason": "มอบหมายทีมเรือ",  
    "meta": { "eta\_min": 15 },  
    "priority\_score": 85,  
    "responderUnitId": "UNIT-BOAT-05",  
    "version": 3,  
    "occurredAt": "2026-02-21T11:00:00Z"  
  },  
  "current": {  
    "status": "ASSIGNED",  
    "assignedUnitId": "UNIT-BOAT-05",  
    "stateVersion": 3,  
    "lastEventId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
    "lastUpdatedAt": "2026-02-21T11:00:00Z"  
  }  
}

* 

Error case

* 400 Bad Request — JSON ผิด/parse ไม่ได้  
* 401 Unauthorized — token ไม่ถูกต้อง  
* 403 Forbidden — role ไม่ผ่าน (เช่น citizen เรียก)  
* 404 Not Found — requestId ไม่พบ  
* 409 Conflict — transition ไม่ถูกต้อง / terminal state / If-Match ไม่ตรง / idempotency fingerprint mismatch  
* 422 Unprocessable Entity — validation ไม่ผ่าน (เช่น responderUnitId ขาด)  
* 503 Service Unavailable — DB ไม่พร้อม

**Dependency, Reliability, Failure handling**

* Dependency: DB ภายใน 2 ส่วน  
  * เขียน Status Events (append)  
  * อัปเดต Current State (materialized view)  
* เรียก service อื่นไหม: ไม่เรียกแบบ synchronous  
* ถ้า DB ล่ม: ตอบ 503  
* Timeout: 3–5 วินาที  
* Retry:  
  * ได้  
* Idempotent:  
  * เป็น idempotent  
* Failure handling (partial write):  
  * ต้องไม่เกิดเคส “event ถูกเขียนแล้ว แต่ current ไม่อัปเดต”

---

# **\#10 Get Rescue Request Current State**

ชื่อ: GetRescueRequestCurrentState  
HTTP Method: **GET**  
Path: **/v1/rescue-requests/{requestId}/current**  
คำอธิบาย:  
ดึงสถานะล่าสุด (materialized view) ของคำร้องแบบรวดเร็ว โดยคืน stateVersion และ lastEventId สำหรับการทำ optimistic concurrency  
**Request**  
Path parameters

* requestId (string, Required)

Query parameters

* ไม่มี

Headers

* Authorization: Bearer \<token\> (Required) — staff/dispatcher/rescue-team  
* Accept: application/json (Optional)

Validation rules

* requestId ต้องรูปแบบถูกต้อง  
* ผู้เรียกต้องมี role ที่อนุญาต (authorization)

**Response**  
Success case  
200 OK  
{  
  "requestId": "REQ-8812-9901",  
  "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
  "status": "ASSIGNED",  
  "priority\_score": 85,  
  "priority\_level": "High",  
  "assignedUnitId": "UNIT-BOAT-05",  
  "assignedAt": "2026-02-21T11:00:00Z",  
  "latestNote": { "message": "กำลังเดินทาง" },  
  "stateVersion": 3,  
  "lastEventId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
  "lastUpdatedBy": "STAFF-009",  
  "lastUpdatedAt": "2026-02-21T11:00:00Z"  
}

* 

Error case

* 401 Unauthorized  
* 403 Forbidden  
* 404 Not Found  
* 503 Service Unavailable

**Dependency, Reliability, Failure handling**

* Dependency: DB ภายใน (อ่าน Rescue Request Current State)  
* เรียก service อื่นไหม: ไม่เรียก  
* Timeout: 2–3 วินาที  
* Retry: ได้ (GET)  
* Idempotent: ใช่

---

# **\#11 List Rescue Requests by Incident**

ชื่อ: ListRescueRequestsByIncident  
HTTP Method: **GET**  
Path: **/v1/incidents/{incidentId}/rescue-requests**  
คำอธิบาย:  
ดึงรายการคำร้องใน incident เดียวกันเพื่อให้ dispatcher/triage ดูภาพรวม กรองตามสถานะ/ความสำคัญ และเรียงลำดับได้  
**Request**  
Path parameters

* incidentId (uuid, Required) — รหัส incident

Query parameters

* status (enum, Optional) — กรองตามสถานะ: SUBMITTED, TRIAGED, ASSIGNED, IN\_PROGRESS, RESOLVED, CANCELLED  
* priorityLevel (enum, Optional) — Low, Medium, High  
* assignedUnitId (string, Optional) — กรองตามหน่วยที่รับงาน  
* limit (int, Optional, default=50) — จำนวนรายการต่อหน้า (เช่น 1–200)  
* cursor (string, Optional) — pagination token  
* sort (enum, Optional, default=updated\_desc) — updated\_desc, priority\_desc, submitted\_asc

Headers

* Authorization: Bearer \<token\> (Required)  
* Accept: application/json (Optional)

Validation rules 

* incidentId ต้องเป็น UUID ถูกต้อง  
* limit ต้องอยู่ในช่วงที่กำหนด (เช่น 1–200)  
* status/priorityLevel ถ้ามีต้องอยู่ใน enum ที่กำหนด  
* sort ต้องเป็นค่าที่รองรับเท่านั้น

**Response**  
Success case  
200 OK  
{  
  "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
  "items": \[  
    {  
      "requestId": "REQ-8812-9901",  
      "status": "ASSIGNED",  
      "priority\_score": 85,  
      "priority\_level": "High",  
      "assignedUnitId": "UNIT-BOAT-05",  
      "latitude": 18.7883,  
      "longitude": 98.9853,  
      "district": "เมืองเชียงใหม่",  
      "submittedAt": "2026-02-21T10:30:00Z",  
      "lastUpdatedAt": "2026-02-21T11:00:00Z",  
      "stateVersion": 3  
    }  
  \],  
  "nextCursor": "eyJrZXkiOiAiLi4uIn0="  
}

* 

Error case

* 401 Unauthorized  
* 403 Forbidden  
* 404 Not Found — incident ไม่พบ (ถ้าคุณเช็คในระบบนี้) หรือคืน list ว่างก็ได้  
* 422 Unprocessable Entity — query param ผิด  
* 503 Service Unavailable

**Dependency, Reliability, Failure handling**

* Dependency: DB ภายใน (อ่านจาก Current State เป็นหลัก \+ join/merge บางส่วนจาก Master ถ้าต้องแสดง location/summary)  
* เรียก service อื่นไหม: ไม่จำเป็นต้องเรียก Incident Service แบบ synchronous (ถือ incidentId เป็น reference)  
* ถ้า DB ล่ม: ตอบ 503  
* Timeout: 3–5 วินาที (list อาจหนักกว่า)  
* Retry: ได้ (GET)  
* Idempotent: ใช่

---

API Contract สำหรับ Staff / Dispatcher Operations ทั้ง 5 endpoint โดยออกแบบให้ “แต่ละ operation” ทำงานเป็นคำสั่ง (command) ที่บังคับกฎ state machine และ เขียน Status Event \+ อัปเดต Current State ทุกครั้ง มาตรฐาน Error Response (ใช้ร่วมกันทุก endpoint)  
{  
  "message": "Human readable error message",  
  "traceId": "4f3c2c1b-8a2f-4fbb-9a4c-2b0a1f0c9d11",  
  "details": \[  
    { "field": "If-Match", "issue": "stateVersion mismatch" }  
  \]  
}

Common (ใช้ร่วมกันทุก Operation Endpoint) Headers (Required)

* Authorization: Bearer \<token\> — staff/dispatcher/rescue-team  
* Content-Type: application/json  
* Accept: application/json

Headers (Recommended)

* X-Idempotency-Key: \<uuid\> — กันการกดซ้ำ/เน็ตหลุด (ทุก operation)  
* If-Match: \<int\> — เท่ากับ current.stateVersion ล่าสุด เพื่อกันแก้ชนกัน  
* X-Request-Id: \<string\> (Optional) — ถ้าคุณอยากรับ request id จาก gateway

Common Validation rules 

* requestId ต้องถูก format  
* ต้อง ผ่าน authorization ตาม role ที่ endpoint กำหนด  
* ถ้า Current State เป็น RESOLVED หรือ CANCELLED → ห้ามทุก operation (409)  
* ถ้า If-Match ถูกส่งมา ต้องตรงกับ current.stateVersion (ไม่ตรง → 409\)  
* X-Idempotency-Key ถ้ามี ต้องเป็น UUID

Common Success Response shape (แนะนำให้เหมือนกันทุก operation) เขียน event ใหม่ 1 ตัว (เพิ่ม version) คืนทั้ง event และ current เพื่อให้ UI อัปเดตทันที

{  
  "requestId": "REQ-8812-9901",  
  "event": { "... event fields ..." },  
  "current": { "... current state fields ..." }  
}

**Dependencies / Reliability (ทุก operation)**

* Dependency: DB ภายใน  
  * Append Rescue Request Status Events  
  * Update Rescue Request Current State  
* เรียก service อื่น: ไม่เรียก synchronous (dispatching จริง ๆ เป็นงานของ Dispatch Service ตาม boundary)  
* Atomicity: ควรทำให้ “event \+ current” สำเร็จ/ล้มเหลวพร้อมกัน (transaction หรือ conditional write)  
* Timeout: 3–5 วินาที  
* Retry: retry ได้  
* Idempotent: เป็น idempotent

# **\#12 Triage Rescue Request**

ชื่อ: TriageRescueRequest  
HTTP Method: **POST**  
Path: **/v1/rescue-requests/{requestId}:triage**  
สรุป:  
เปลี่ยนสถานะจาก SUBMITTED → TRIAGED พร้อมกำหนดคะแนน/ระดับความสำคัญสำหรับการจัดคิวช่วยเหลือ  
**Request**  
Path parameters

* requestId (string, Required) — รหัสคำร้อง

Query parameters

* ไม่มี

Body (JSON) ตัวอย่าง:  
{  
  "priority\_score": 85,  
  "priority\_level": "High",  
  "note": "ผู้ป่วยติดเตียง ต้องเร่งด่วน"  
}

Validation rules

* Allowed transition ต้องเป็น SUBMITTED → TRIAGED เท่านั้น (ไม่ใช่สถานะอื่น)  
* priority\_score ถ้ามีต้องอยู่ในช่วงที่กำหนด (เช่น 0–100)  
* priority\_level ถ้ามีต้องเป็น Low|Medium|High  
* note ความยาวไม่เกินที่กำหนด (เช่น 500 ตัวอักษร)

**Response**  
Success case  
201 Created  
{  
  "requestId": "REQ-8812-9901",  
  "event": {  
    "eventId": "3f2a1111-2222-3333-4444-555566667777",  
    "previousStatus": "SUBMITTED",  
    "newStatus": "TRIAGED",  
    "changedBy": "STAFF-009",  
    "changedByRole": "TRIAGE",  
    "changeReason": "Triage completed",  
    "meta": { "note": "ผู้ป่วยติดเตียง ต้องเร่งด่วน" },  
    "priority\_score": 85,  
    "version": 2,  
    "occurredAt": "2026-02-21T10:40:00Z"  
  },  
  "current": {  
    "status": "TRIAGED",  
    "priority\_score": 85,  
    "priority\_level": "High",  
    "stateVersion": 2,  
    "lastEventId": "3f2a1111-2222-3333-4444-555566667777",  
    "lastUpdatedAt": "2026-02-21T10:40:00Z"  
  }  
}

* 

Error case

* 401/403 auth/role ไม่ผ่าน  
* 404 ไม่พบ requestId  
* 409 transition ไม่ถูกต้อง / terminal state / If-Match mismatch / idempotency mismatch  
* 422 validation ไม่ผ่าน  
* 503 DB ล่ม

---

# **\#13 Assign Rescue Request**

ชื่อ: AssignRescueRequest  
HTTP Method: **POST**  
Path: **/v1/rescue-requests/{requestId}:assign**  
สรุป:  
เปลี่ยนสถานะจาก TRIAGED → ASSIGNED และกำหนดหน่วยกู้ภัยที่รับผิดชอบ (assignedUnitId)  
**Request**  
Path parameters

* requestId (string, Required)

Body (JSON) ตัวอย่าง:  
{  
  "assignedUnitId": "UNIT-BOAT-05",  
  "note": "ทีมเรือใกล้ที่สุด",  
  "meta": { "eta\_min": 15 }  
}

Validation rules

* Allowed transition ต้องเป็น TRIAGED → ASSIGNED  
* assignedUnitId ต้องไม่ว่าง (Required)  
* meta.eta\_min ถ้ามีต้องเป็นจำนวนเต็ม \>= 0

**Response**  
Success case  
201 Created  
{  
  "requestId": "REQ-8812-9901",  
  "event": {  
    "eventId": "aaaa1111-2222-3333-4444-555566667777",  
    "previousStatus": "TRIAGED",  
    "newStatus": "ASSIGNED",  
    "changedBy": "STAFF-009",  
    "changedByRole": "DISPATCHER",  
    "changeReason": "Assigned unit",  
    "meta": { "eta\_min": 15, "note": "ทีมเรือใกล้ที่สุด" },  
    "responderUnitId": "UNIT-BOAT-05",  
    "version": 3,  
    "occurredAt": "2026-02-21T11:00:00Z"  
  },  
  "current": {  
    "status": "ASSIGNED",  
    "assignedUnitId": "UNIT-BOAT-05",  
    "assignedAt": "2026-02-21T11:00:00Z",  
    "stateVersion": 3,  
    "lastEventId": "aaaa1111-2222-3333-4444-555566667777",  
    "lastUpdatedAt": "2026-02-21T11:00:00Z"  
  }  
}

* 

Error case

* เหมือน common \+ เพิ่ม:  
* 422 ถ้า assignedUnitId ว่าง

---

# **\#14 Start Rescue Request**

ชื่อ: StartRescueRequest  
HTTP Method: **POST**  
Path: **/v1/rescue-requests/{requestId}:start**  
สรุป:  
เปลี่ยนสถานะจาก ASSIGNED → IN\_PROGRESS เมื่อทีมเริ่มปฏิบัติการจริง  
**Request**  
Path parameters

* requestId (string, Required)

Body (JSON) ตัวอย่าง:  
{  
  "note": "ถึงพื้นที่แล้ว เริ่มช่วยเหลือ",  
  "meta": { "arrived": true }  
}

Validation rules

* Allowed transition ต้องเป็น ASSIGNED → IN\_PROGRESS  
* ผู้เรียกต้องมี role RESCUE\_TEAM หรือ DISPATCHER  
* meta ถ้ามีต้องเป็น JSON ถูกต้อง

**Response**  
Success case  
201 Created (คืน event+current แบบเดียวกัน)  
{  
  "requestId": "REQ-8812-9901",  
  "event": {  
    "eventId": "bbbb1111-2222-3333-4444-555566667777",  
    "previousStatus": "ASSIGNED",  
    "newStatus": "IN\_PROGRESS",  
    "changedBy": "TEAM-007",  
    "changedByRole": "RESCUE\_TEAM",  
    "changeReason": "Operation started",  
    "meta": { "note": "ถึงพื้นที่แล้ว เริ่มช่วยเหลือ", "arrived": true },  
    "responderUnitId": "UNIT-BOAT-05",  
    "version": 4,  
    "occurredAt": "2026-02-21T11:12:00Z"  
  },  
  "current": {  
    "status": "IN\_PROGRESS",  
    "assignedUnitId": "UNIT-BOAT-05",  
    "stateVersion": 4,  
    "lastEventId": "bbbb1111-2222-3333-4444-555566667777",  
    "latestNote": { "message": "ถึงพื้นที่แล้ว เริ่มช่วยเหลือ" },  
    "lastUpdatedAt": "2026-02-21T11:12:00Z"  
  }  
}

* 

Error case

* เหมือน common

---

# **\#15 Resolve Rescue Request**

ชื่อ: ResolveRescueRequest  
HTTP Method: **POST**  
Path: **/v1/rescue-requests/{requestId}:resolve**  
สรุป:  
เปลี่ยนสถานะจาก IN\_PROGRESS → RESOLVED เมื่อช่วยเหลือเสร็จสิ้น (terminal state)  
**Request**  
Path parameters

* requestId (string, Required)

Body (JSON) ตัวอย่าง:  
{  
  "note": "อพยพสำเร็จ ส่งถึงศูนย์พักพิง",  
  "meta": { "peopleRescued": 4 }  
}

Validation rules

* Allowed transition ต้องเป็น IN\_PROGRESS → RESOLVED  
* ผู้เรียกต้องมี role RESCUE\_TEAM หรือ DISPATCHER  
* meta.peopleRescued ถ้ามีต้องเป็น int \>= 0  
* หลัง RESOLVED แล้วห้ามเปลี่ยนสถานะอีก (enforce ที่ระบบ)

**Response**  
Success case  
201 Created  
{  
  "requestId": "REQ-8812-9901",  
  "event": {  
    "eventId": "cccc1111-2222-3333-4444-555566667777",  
    "previousStatus": "IN\_PROGRESS",  
    "newStatus": "RESOLVED",  
    "changedBy": "TEAM-007",  
    "changedByRole": "RESCUE\_TEAM",  
    "changeReason": "Resolved",  
    "meta": { "note": "อพยพสำเร็จ ส่งถึงศูนย์พักพิง", "peopleRescued": 4 },  
    "responderUnitId": "UNIT-BOAT-05",  
    "version": 5,  
    "occurredAt": "2026-02-21T11:45:00Z"  
  },  
  "current": {  
    "status": "RESOLVED",  
    "assignedUnitId": "UNIT-BOAT-05",  
    "stateVersion": 5,  
    "lastEventId": "cccc1111-2222-3333-4444-555566667777",  
    "lastUpdatedAt": "2026-02-21T11:45:00Z"  
  }  
}

* 

Error case

* เหมือน common

---

# **\#16 Cancel Rescue Request**

ชื่อ: CancelRescueRequest  
HTTP Method: **POST**  
Path: **/v1/rescue-requests/{requestId}:cancel**  
สรุป:  
เปลี่ยนสถานะเป็น CANCELLED จากสถานะที่อนุญาต (SUBMITTED/TRIAGED/ASSIGNED/IN\_PROGRESS) โดยต้องระบุเหตุผล (terminal state)  
**Request**  
Path parameters

* requestId (string, Required)

Body (JSON) ตัวอย่าง:  
{  
  "reason": "ไม่สามารถติดต่อผู้ร้องได้",  
  "reasonCode": "UNREACHABLE",  
  "note": "โทรไม่ติด 3 ครั้ง",  
  "meta": { "attempts": 3 }  
}  
Validation rules

* Allowed transition: SUBMITTED|TRIAGED|ASSIGNED|IN\_PROGRESS → CANCELLED  
* ต้องมี reason (Required, ไม่ว่าง)  
* reasonCode ถ้ามีต้องอยู่ใน enum ที่กำหนด เช่น DUPLICATE, USER\_REQUEST, UNREACHABLE, UNSAFE, OTHER  
* role ต้องเป็น DISPATCHER หรือ ADMIN (ตาม spec)

**Response**  
Success case  
201 Created  
{  
  "requestId": "REQ-8812-9901",  
  "event": {  
    "eventId": "dddd1111-2222-3333-4444-555566667777",  
    "previousStatus": "ASSIGNED",  
    "newStatus": "CANCELLED",  
    "changedBy": "STAFF-010",  
    "changedByRole": "DISPATCHER",  
    "changeReason": "ไม่สามารถติดต่อผู้ร้องได้",  
    "meta": { "reasonCode": "UNREACHABLE", "note": "โทรไม่ติด 3 ครั้ง", "attempts": 3 },  
    "responderUnitId": "UNIT-BOAT-05",  
    "version": 6,  
    "occurredAt": "2026-02-21T11:20:00Z"  
  },  
  "current": {  
    "status": "CANCELLED",  
    "assignedUnitId": "UNIT-BOAT-05",  
    "stateVersion": 6,  
    "lastEventId": "dddd1111-2222-3333-4444-555566667777",  
    "lastUpdatedAt": "2026-02-21T11:20:00Z"  
  }  
}

* 

Error case

* เหมือน common \+ เพิ่ม:  
* 422 ถ้า reason ว่าง  
* 403 ถ้า role ไม่ใช่ DISPATCHER/ADMIN

---

# **\#17 Get Idempotency Key Record**

ชื่อ: GetIdempotencyKeyRecord  
HTTP Method: **GET**  
Path: **/v1/idempotency-keys/{idempotencyKeyHash}**  
สรุป:  
ใช้สำหรับ staff/support/debug เพื่อตรวจสอบสถานะของ idempotency record ว่า request ถูก replay หรือค้างอยู่ (IN\_PROGRESS) หรือเคยล้มเหลว และดูผลลัพธ์ที่ถูกบันทึกไว้สำหรับ replay  
**Request**  
Path parameters

* idempotencyKeyHash (string, Required)  
  * ความหมาย: ค่า hash ของ X-Idempotency-Key (เช่น sha256:\<hex/base64\>) ที่ใช้เป็น primary key ในตาราง Idempotency Keys  
  * ตัวอย่าง: sha256:9f2c...a1b0

Query parameters

* includeResponse (boolean, Optional, default=false)  
  * ความหมาย: ถ้า true จะคืน responseHeaders และ responseBody เพื่อ debug (ควรจำกัดสิทธิ์/ปิดใน prod หรือ mask ข้อมูล)  
* includeRequestFingerprint (boolean, Optional, default=false)  
  * ความหมาย: ถ้า true จะคืน requestFingerprint เพื่อช่วยตรวจสอบ mismatch

Headers

* Authorization: Bearer \<token\> (Required) — เฉพาะ staff/admin/support  
* Accept: application/json (Optional)

Validation rules 

* idempotencyKeyHash ต้องขึ้นต้นด้วย sha256: และตามด้วยอักขระที่ระบบรองรับ (เช่น hex/base64)  
* ผู้เรียกต้องมี role ที่อนุญาต (เช่น ADMIN หรือ SUPPORT)  
* ถ้า includeResponse=true ต้องมีสิทธิ์ระดับสูง (เช่น SUPPORT\_SENSITIVE)

**Response**  
Success case

* 200 OK  
  * Headers:  
    * X-Trace-Id: \<uuid\>

Body ตัวอย่าง (default: ไม่คืน responseBody/headers):  
{  
  "idempotencyKeyHash": "sha256:9f2c...a1b0",  
  "operationName": "CreateRescueRequest",  
  "status": "COMPLETED",  
  "resultResourceId": "REQ-8812-9901",  
  "lockedAt": "2026-03-03T08:01:12Z",  
  "lockExpiresAt": "2026-03-03T08:02:12Z",  
  "createdAt": "2026-03-03T08:01:12Z",  
  "updatedAt": "2026-03-03T08:01:15Z",  
  "expiresAt": "2026-03-04T08:01:12Z",  
  "clientId": "citizen:U-10029",  
  "requestIp": "203.0.113.10",  
  "userAgent": "RescueApp/1.2.0 (iOS)"  
}

* 

กรณี includeResponse=true:  
{  
  "idempotencyKeyHash": "sha256:9f2c...a1b0",  
  "operationName": "CreateRescueRequest",  
  "status": "COMPLETED",  
  "resultResourceId": "REQ-8812-9901",  
  "responseStatusCode": 201,  
  "responseHeaders": {  
    "Location": "/requests/REQ-8812-9901"  
  },  
  "responseBody": {  
    "requestId": "REQ-8812-9901",  
    "status": "SUBMITTED"  
  },  
  "createdAt": "2026-03-03T08:01:12Z",  
  "updatedAt": "2026-03-03T08:01:15Z",  
  "expiresAt": "2026-03-04T08:01:12Z"  
}

* 

Error case

* 401 Unauthorized — ไม่มี/invalid token  
* 403 Forbidden — role ไม่พอ

404 Not Found — ไม่พบ idempotencyKeyHash (อาจถูก TTL purge แล้ว)  
{  
  "message": "Idempotency record not found",  
  "traceId": "..."  
}

* 422 Unprocessable Entity — รูปแบบ idempotencyKeyHash ไม่ถูกต้อง  
* 503 Service Unavailable — DB ไม่พร้อม

**Dependency, Reliability และ Failure handling**

* Dependency: DB ภายใน (ตาราง Idempotency Keys)  
* เรียก service อื่นหรือไม่: ไม่เรียก  
* ถ้า dependency ล่ม: ตอบ 503 Service Unavailable พร้อม traceId  
* Timeout: 2–3 วินาที  
* Retry: ได้ (GET เป็น safe) แต่ถ้าได้ 503 ควร backoff  
* Idempotent: ใช่ (GET)

# Async Contract

**Asynchronous Function Contract**  
Common Envelope (ใช้ร่วมกันทุก event)  
โครงสร้าง JSON มาตรฐานทุก message จะอยู่ในรูปแบบ:  
{   
  "header": { ... },   
  "body": { ... }   
}

ข้อมูลทั่วไป

* Interaction Style: Event-driven / Publish–Subscribe  
* Role: Producer \= RescueRequest Service  
* Channel/Topic: rescue-request-events.v1  
* Versioning: schemaVersion: "1.0" ใน header และชื่อ event แบบ v1 โดยนัย 

Request Header (ตัวอย่าง JSON)  
{  
  "messageId": "f3d2b2d6-3a9b-4cdb-8c8a-8d0d0a57d0a1",  
  "eventType": "rescue-request.created",  
  "schemaVersion": "1.0",  
  "producer": "rescue-request-service",  
  "occurredAt": "2026-03-03T08:01:12Z",  
  "traceId": "4f3c2c1b-8a2f-4fbb-9a4c-2b0a1f0c9d11",  
  "correlationId": "REQ-8812-9901",  
  "partitionKey": "REQ-8812-9901",  
  "contentType": "application/json"  
}

Field Definition (Header)

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| messageId | uuid | Y | ไอดีของ message ไม่ซ้ำ |
| eventType | string | Y | ชื่อ event เช่น rescue-request.created |
| schemaVersion | string | Y | เวอร์ชัน schema ของ payload |
| producer | string | Y | ชื่อ service ผู้ส่ง |
| occurredAt | datetime | Y | เวลาเกิดเหตุการณ์ในโดเมน |
| traceId | string | Y | ใช้ trace ข้ามระบบ |
| correlationId | string | Y | ใช้โยงเหตุการณ์ชุดเดียวกัน (แนะนำ \= requestId) |
| partitionKey | string | Y | ใช้กำหนดลำดับ/partition (แนะนำ \= requestId) |
| contentType | string | Y | application/json |

---

**Publish Response (ผลลัพธ์ที่ Producer ได้จากการ publish)**  
เพื่อยืนยันว่าขึ้น bus แล้วหรือไม่ (รับกลับมาจากช่องทาง publish เช่น SDK/API ของ Event Bus)  
Success (PublishAck)  
ตัวอย่าง JSON:  
{  
  "header": {  
    "traceId": "4f3c2c1b-8a2f-4fbb-9a4c-2b0a1f0c9d11",  
    "correlationId": "REQ-8812-9901"  
  },  
  "body": {  
    "publishStatus": "ACCEPTED",  
    "busMessageId": "bus-7a9d0a57d0a1",  
    "channel": "rescue-request-events.v1",  
    "publishedAt": "2026-03-03T08:01:12Z"  
  }  
}

Field Definition (PublishAck Body):

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| publishStatus | enum | Y | ACCEPTED |
| busMessageId | string | Y | ไอดีที่ bus คืนให้ |
| channel | string | Y | topic/channel ที่ publish |
| publishedAt | datetime | Y | เวลา bus รับเข้าแล้ว |

Reject/Error (PublishReject)  
ตัวอย่าง JSON:  
{  
  "header": {  
    "traceId": "4f3c2c1b-8a2f-4fbb-9a4c-2b0a1f0c9d11",  
    "correlationId": "REQ-8812-9901"  
  },  
  "body": {  
    "publishStatus": "REJECTED",  
    "errorCode": "BUS\_UNAVAILABLE",  
    "errorMessage": "Event bus publish failed",  
    "retryable": true,  
    "failedAt": "2026-03-03T08:01:13Z"  
  }  
}

Field Definition (PublishReject Body):

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| publishStatus | enum | Y | REJECTED |
| errorCode | string | Y | เช่น SCHEMA\_VALIDATION\_FAILED, BUS\_UNAVAILABLE |
| errorMessage | string | Y | ข้อความสาเหตุ |
| retryable | boolean | Y | ควร retry ได้ไหม |
| failedAt | datetime | Y | เวลาที่ล้มเหลว |

Validation rules (สำหรับ publish response)

* publishStatus=ACCEPTED ต้องมี busMessageId  
* publishStatus=REJECTED ต้องมี errorCode, retryable  
* publishedAt / failedAt ต้องเป็น ISO-8601 UTC

---

# **\#1 rescue-request.created**

ข้อมูลทั่วไป

* Message Name: rescue-request.created  
* Channel: rescue-request-events.v1  
* Producer: RescueRequest Service  
* Purpose: แจ้งว่า “มีการสร้างคำร้องใหม่” เพื่อให้ระบบอื่น (เช่น Dispatch/Analytics/Notification) รับรู้และเริ่มกระบวนการต่อ  
* Linking: ใช้ correlationId=requestId และ field requestId ใน body

Request (Full JSON ตัวอย่าง)  
{  
  "header": {  
    "messageId": "f3d2b2d6-3a9b-4cdb-8c8a-8d0d0a57d0a1",  
    "eventType": "rescue-request.created",  
    "schemaVersion": "1.0",  
    "producer": "rescue-request-service",  
    "occurredAt": "2026-03-03T08:01:12Z",  
    "traceId": "4f3c2c1b-8a2f-4fbb-9a4c-2b0a1f0c9d11",  
    "correlationId": "REQ-8812-9901",  
    "partitionKey": "REQ-8812-9901",  
    "contentType": "application/json"  
  },  
  "body": {  
    "requestId": "REQ-8812-9901",  
    "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
    "requestType": "flood\_rescue",  
    "description": "ติดอยู่ชั้น 2",  
    "peopleCount": 4,  
    "specialNeeds": \["bedridden"\],  
    "location": {  
      "latitude": 18.7883,  
      "longitude": 98.9853,  
      "province": "เชียงใหม่",  
      "district": "เมืองเชียงใหม่",  
      "subdistrict": "สุเทพ",  
      "addressLine": "123 ม.2 ถ.ห้วยแก้ว"  
    },  
    "contact": {  
      "contactName": "สมชาย",  
      "contactPhoneHash": "sha256:91ab..."  
    },  
    "sourceChannel": "MOBILE\_APP",  
    "submittedAt": "2026-03-03T08:01:12Z",  
    "initialStatus": "SUBMITTED",  
    "initialStateVersion": 1  
  }  
}  
Field Definition (Body)

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| requestId | string | Y | รหัสคำร้อง |
| incidentId | uuid | Y | อ้างอิง incident |
| requestType | string | Y | ประเภทคำร้อง |
| description | string | N | รายละเอียดเพิ่มเติม |
| peopleCount | int | Y | จำนวนคน (\>=1) |
| specialNeeds | array\[string\] | N | ความต้องการพิเศษ |
| location.latitude | decimal | Y | ละติจูด |
| location.longitude | decimal | Y | ลองจิจูด |
| location.province | string | N | จังหวัด |
| location.district | string | N | อำเภอ/เขต |
| location.subdistrict | string | N | ตำบล/แขวง |
| location.addressLine | string | N | ที่อยู่ข้อความ |
| contact.contactName | string | N | ชื่อผู้ติดต่อ (เลือกส่งได้) |
| contact.contactPhoneHash | string | Y | hash เบอร์ (หลีกเลี่ยง PII) |
| sourceChannel | enum | N | MOBILE\_APP / WEB / CALLCENTER / LINE |
| submittedAt | datetime | Y | เวลาส่งคำร้อง |
| initialStatus | enum | Y | SUBMITTED |
| initialStateVersion | int | Y | เวอร์ชันเริ่มต้น |

Validation rules (Request)

* peopleCount \>= 1  
* location.latitude ∈ \[-90,90\] และ location.longitude ∈ \[-180,180\]  
* incidentId ต้องเป็น UUID ถูกต้อง  
* contactPhoneHash ต้องไม่ว่าง

---

# **\#2 rescue-request.status-changed**

ข้อมูลทั่วไป

* Message Name: rescue-request.status-changed  
* Purpose: แจ้งทุกครั้งที่สถานะเปลี่ยน (SUBMITTED→…→RESOLVED/CANCELLED) ให้ระบบอื่นทำงานต่อ/แสดงผล  
* Linking: requestId, version (กัน out-of-order)

Request (Full JSON ตัวอย่าง)  
{  
  "header": {  
    "messageId": "7e0f8c6a-3f6b-4b87-9a0c-111122223333",  
    "eventType": "rescue-request.status-changed",  
    "schemaVersion": "1.0",  
    "producer": "rescue-request-service",  
    "occurredAt": "2026-03-03T08:05:00Z",  
    "traceId": "4f3c2c1b-8a2f-4fbb-9a4c-2b0a1f0c9d11",  
    "correlationId": "REQ-8812-9901",  
    "partitionKey": "REQ-8812-9901",  
    "contentType": "application/json"  
  },  
  "body": {  
    "eventId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c999",  
    "requestId": "REQ-8812-9901",  
    "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
    "previousStatus": "TRIAGED",  
    "newStatus": "ASSIGNED",  
    "responderUnitId": "UNIT-BOAT-05",  
    "priority\_score": 85,  
    "changedBy": "STAFF-009",  
    "changedByRole": "DISPATCHER",  
    "changeReason": "Assigned unit",  
    "meta": { "eta\_min": 15 },  
    "version": 3,  
    "occurredAt": "2026-03-03T08:05:00Z"  
  }  
}

Field Definition (Body)

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| eventId | uuid | Y | ไอดี event |
| requestId | string | Y | รหัสคำร้อง |
| incidentId | uuid | Y | รหัส incident |
| previousStatus | enum | N | สถานะเดิม |
| newStatus | enum | Y | สถานะใหม่ |
| responderUnitId | string | N | หน่วยที่เกี่ยวข้อง (จำเป็นเมื่อ ASSIGNED) |
| priority\_score | int | N | คะแนนความสำคัญ ณ ตอนนั้น |
| changedBy | string | Y | ผู้กระทำ |
| changedByRole | string | N | role ผู้กระทำ |
| changeReason | string | N | เหตุผล/หมายเหตุ |
| meta | object | N | ข้อมูลเสริม |
| version | int | Y | ลำดับ event ต่อคำร้อง (เพิ่มทีละ 1\) |
| occurredAt | datetime | Y | เวลาเกิด event |

Validation rules

* version ต้องมากกว่า event เดิมเสมอ (monotonic per requestId)  
* ถ้า newStatus=ASSIGNED ต้องมี responderUnitId  
* ถ้า newStatus=CANCELLED ต้องมี changeReason  
* newStatus ต้องอยู่ใน enum ที่กำหนด

---

# **\#3 rescue-request.citizen-updated**

ข้อมูลทั่วไป

* Message Name: rescue-request.citizen-updated  
* Purpose: แจ้งว่าผู้ร้องส่งข้อมูลเพิ่มเติม (เพื่อให้ staff UI/analytics/notification ทำงานต่อ)  
* Linking: requestId, updateId

Request (Full JSON ตัวอย่าง)  
{  
  "header": {  
    "messageId": "d0b1c2d3-e4f5-6789-a0b1-c2d3e4f56789",  
    "eventType": "rescue-request.citizen-updated",  
    "schemaVersion": "1.0",  
    "producer": "rescue-request-service",  
    "occurredAt": "2026-03-03T08:10:00Z",  
    "traceId": "4f3c2c1b-8a2f-4fbb-9a4c-2b0a1f0c9d11",  
    "correlationId": "REQ-8812-9901",  
    "partitionKey": "REQ-8812-9901",  
    "contentType": "application/json"  
  },  
  "body": {  
    "updateId": "b21f0c2a-9d11-4fbb-9a4c-2b0a1f0c9d11",  
    "requestId": "REQ-8812-9901",  
    "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
    "updateType": "NOTE",  
    "updatePayload": { "note": "น้ำสูงขึ้นถึงเอว" },  
    "citizenAuthMethod": "PHONE\_PLUS\_TRACKING\_CODE",  
    "citizenPhoneHash": "sha256:91ab...",  
    "trackingCodeHash": "sha256:3c1f...",  
    "createdAt": "2026-03-03T08:10:00Z"  
  }  
}

Field Definition (Body)

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| updateId | uuid | Y | ไอดีการอัปเดต |
| requestId | string | Y | รหัสคำร้อง |
| incidentId | uuid | Y | รหัส incident |
| updateType | enum | Y | NOTE/LOCATION\_DETAILS/PEOPLE\_COUNT/SPECIAL\_NEEDS/CONTACT\_INFO |
| updatePayload | object | Y | payload ตามประเภท |
| citizenAuthMethod | enum | Y | PHONE\_PLUS\_TRACKING\_CODE |
| citizenPhoneHash | string | Y | hash เบอร์ |
| trackingCodeHash | string | Y | hash โค้ดติดตาม |
| createdAt | datetime | Y | เวลาแจ้งข้อมูลเพิ่ม |

Validation rules

* updatePayload ต้องสอดคล้องกับ updateType (เช่น PEOPLE\_COUNT ต้องมี peopleCount)  
* จำกัดขนาด updatePayload (เช่น ≤ 4KB)  
* createdAt ต้องเป็น ISO-8601 UTC

---

# **\#4 rescue-request.cancelled**

ข้อมูลทั่วไป

* Message Name: rescue-request.cancelled  
* Purpose: แจ้ง terminal event เมื่อคำร้องถูกยกเลิก (เพื่อให้ระบบอื่นปิดงาน/หยุดติดตาม)  
* Linking: requestId, version  
* หมายเหตุ: โดยทั่วไป “ควร publish ทั้ง status-changed และ cancelled” เพื่อให้ subscriber เลือก subscribe แบบละเอียด/แบบ terminal-only ได้

Request (Full JSON ตัวอย่าง)  
{  
  "header": {  
    "messageId": "11112222-3333-4444-5555-666677778888",  
    "eventType": "rescue-request.cancelled",  
    "schemaVersion": "1.0",  
    "producer": "rescue-request-service",  
    "occurredAt": "2026-03-03T08:20:00Z",  
    "traceId": "4f3c2c1b-8a2f-4fbb-9a4c-2b0a1f0c9d11",  
    "correlationId": "REQ-8812-9901",  
    "partitionKey": "REQ-8812-9901",  
    "contentType": "application/json"  
  },  
  "body": {  
    "eventId": "dddd1111-2222-3333-4444-555566667777",  
    "requestId": "REQ-8812-9901",  
    "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
    "previousStatus": "ASSIGNED",  
    "newStatus": "CANCELLED",  
    "reason": "ไม่สามารถติดต่อผู้ร้องได้",  
    "reasonCode": "UNREACHABLE",  
    "changedBy": "STAFF-010",  
    "changedByRole": "DISPATCHER",  
    "responderUnitId": "UNIT-BOAT-05",  
    "version": 6,  
    "occurredAt": "2026-03-03T08:20:00Z"  
  }  
}

Field Definition (Body)

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| eventId | uuid | Y | ไอดี event |
| requestId | string | Y | รหัสคำร้อง |
| incidentId | uuid | Y | รหัส incident |
| previousStatus | enum | Y | สถานะก่อนยกเลิก |
| newStatus | enum | Y | ต้องเป็น CANCELLED |
| reason | string | Y | เหตุผลการยกเลิก |
| reasonCode | string | N | รหัสเหตุผล เช่น UNREACHABLE/DUPLICATE/OTHER |
| changedBy | string | Y | ผู้ยกเลิก |
| changedByRole | string | N | role |
| responderUnitId | string | N | หน่วยที่เกี่ยวข้อง (ถ้ามี) |
| version | int | Y | เวอร์ชันลำดับเหตุการณ์ |
| occurredAt | datetime | Y | เวลาเกิดเหตุ |

Validation rules

* newStatus ต้องเป็น CANCELLED  
* reason ต้องไม่ว่าง  
* version ต้องเป็นลำดับล่าสุดของ requestId

---

# **\#5 rescue-request.resolved**

ข้อมูลทั่วไป

* Message Name: rescue-request.resolved  
* Purpose: แจ้ง terminal event เมื่อช่วยเหลือเสร็จสิ้น (ปิดเคส)  
* Linking: requestId, version  
* หมายเหตุ: โดยทั่วไป publish ทั้ง status-changed และ resolved

Request (Full JSON ตัวอย่าง)  
JSON  
{  
  "header": {  
    "messageId": "99990000-aaaa-bbbb-cccc-ddddeeeeffff",  
    "eventType": "rescue-request.resolved",  
    "schemaVersion": "1.0",  
    "producer": "rescue-request-service",  
    "occurredAt": "2026-03-03T08:45:00Z",  
    "traceId": "4f3c2c1b-8a2f-4fbb-9a4c-2b0a1f0c9d11",  
    "correlationId": "REQ-8812-9901",  
    "partitionKey": "REQ-8812-9901",  
    "contentType": "application/json"  
  },  
  "body": {  
    "eventId": "cccc1111-2222-3333-4444-555566667777",  
    "requestId": "REQ-8812-9901",  
    "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",  
    "previousStatus": "IN\_PROGRESS",  
    "newStatus": "RESOLVED",  
    "changedBy": "TEAM-007",  
    "changedByRole": "RESCUE\_TEAM",  
    "responderUnitId": "UNIT-BOAT-05",  
    "resolutionNote": "อพยพสำเร็จ ส่งถึงศูนย์พักพิง",  
    "meta": { "peopleRescued": 4 },  
    "version": 7,  
    "occurredAt": "2026-03-03T08:45:00Z"  
  }  
}

Field Definition (Body)

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| eventId | uuid | Y | ไอดี event |
| requestId | string | Y | รหัสคำร้อง |
| incidentId | uuid | Y | รหัส incident |
| previousStatus | enum | Y | สถานะก่อนหน้า |
| newStatus | enum | Y | ต้องเป็น RESOLVED |
| changedBy | string | Y | ผู้ปิดเคส |
| changedByRole | string | N | role |
| responderUnitId | string | N | หน่วยที่เกี่ยวข้อง |
| resolutionNote | string | N | หมายเหตุปิดเคส |
| meta | object | N | ข้อมูลเสริม เช่น peopleRescued |
| version | int | Y | เวอร์ชันลำดับเหตุการณ์ |
| occurredAt | datetime | Y | เวลาเกิดเหตุ |

Validation rules

* newStatus ต้องเป็น RESOLVED  
* ถ้ามี meta.peopleRescued ต้องเป็น int \>= 0  
* version ต้องเป็นลำดับล่าสุดของ requestId

# Service Data

**Service Data**

### **1\) Rescue Request Master Data**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| requestId | string | Y | (PK) รหัสคำร้อง | REQ-8812-9901 |
| incidentId | uuid | Y | (Ref) รหัสเหตุการณ์ | 8b9b6d5b... |
| requestType | string | Y | ประเภทคำร้อง | flood\_rescue |
| description | text | N | รายละเอียดเพิ่มเติม | ติดอยู่ชั้น 2 |
| peopleCount | integer | Y | จำนวนคน  (\>=1) | 4 |
| specialNeeds | array | N | ความต้องการพิเศษ | \["bedridden"\] |
| latitude | decimal | Y | พิกัดละติจูด | 18.7883 |
| longitude | decimal | Y | พิกัดลองจิจูด | 98.9853 |
| locationDetails | json | N | ข้อมูลตำแหน่งเพิ่ม | {"floor":"2","landmark":"หน้าโรงเรียน"} |
| province | string | N | จังหวัด | เชียงใหม่ |
| district | string | N | อำเภอ/เขต | เมืองเชียงใหม่ |
| subdistrict | string | N | ตำบล/แขวง | สุเทพ |
| addressLine | string | N | ที่อยู่แบบข้อความ (ถ้ามี) | 123 ม.2 ถ.ห้วยแก้ว |
| contactName | string | Y | ชื่อผู้ติดต่อ | สมชาย |
| contactPhone | string | Y | เบอร์โทรศัพท์ | 0812345678 |
| contactPhoneNormalized | string | Y | เบอร์โทร normalize ใช้จับคู่กับ trackingCode | \+66812345678 |
| contactPhoneHash | string | Y | hash ของเบอร์ (เพื่อทำ index/ค้นหาโดยไม่ใช้เบอร์ดิบ) | sha256:91ab... |
| trackingCodeHash | string | Y | hash ของเลขสุ่ม 6 หลัก (ไม่เก็บเลขจริง) ใช้คู่กับ phoneHash เพื่อ lookup/ยืนยัน | sha256:3c1f... |
| sourceChannel | enum | N | ช่องทางที่มาของคำร้อง: MOBILE\_APP, WEB, CALLCENTER, LINE | MOBILE\_APP |
| submittedAt | datetime | Y | เวลาส่งคำร้อง | 2026-02-21T10:30Z |
| lastCitizenUpdateAt | datetime | N | เวลา “ผู้ร้อง” อัปเดตข้อมูลล่าสุด | 2026-03-03T08:10:00Z |

### **2\) Rescue Request Status Events**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| eventId | uuid | Y | (PK) ไอดีเหตุการณ์ | 8b9b6d5b... |
| requestId | string | Y | (FK) อ้างอิงคำร้อง | REQ-8812-9901 |
| previousStatus | enum | N | สถานะก่อนหน้า | SUBMITTED |
| newStatus | enum | Y | สถานะใหม่ (รวม ASSIGNED) | ASSIGNED |
| changedBy | string | Y | ผู้กระทำ (System/Staff) | STAFF-009 |
| changedByRole | string | N | Role ผู้กระทำ | DISPATCHER |
| changeReason | text | N | เหตุผล/หมายเหตุ | เปลี่ยนทีมเนื่องจากรถเสีย |
| meta | json | N | ข้อมูลเสริม (ETA, Distance) | {"eta\_min": 15} |
| priority\_score | int | N | คะแนนความสำคัญ ณ ตอนนั้น | 85 |
| responderUnitId | string | N | (สำคัญ) หน่วยที่เกี่ยวข้องใน Event นี้ | UNIT-BOAT-05 |
| version | int | Y | เวอร์ชันลำดับเหตุการณ์ | 3 |
| occurredAt | datetime | Y | เวลาเกิดเหตุการณ์ | 2026-02-21T11:00Z |

### **3\) Rescue Request Current State** 

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| requestId | string | Y | (PK/FK) รหัสคำร้อง | REQ-8812-9901 |
| incidentId | uuid | Y | รหัสเหตุการณ์ | 8b9b6d5b... |
| lastEventId | uuid | Y | event ล่าสุดที่ถูก apply เข้ามาใน Current State | 8b9b6d5b... |
| stateVersion | int | Y | เวอร์ชันล่าสุดที่ apply (ต้องเท่ากับ event.version ล่าสุด) | 3 |
| status | enum | Y | สถานะล่าสุด | ASSIGNED |
| priority\_score | int | N | คะแนนล่าสุด | 85 |
| priority\_level | enum | N | ระดับความสำคัญ | High |
| assignedUnitId | string | N | หน่วยที่รับผิดชอบปัจจุบัน | UNIT-BOAT-05 |
| assignedAt | datetime | N | เวลาที่เริ่ม Assign ล่าสุด | 2026-02-21T11:00Z |
| latestNote | json | N | หมายเหตุล่าสุด | {"message":"กำลังเดินทาง"} |
| lastUpdatedBy | string | N | แก้ไขล่าสุดโดย | STAFF-009 |
| lastUpdatedAt | datetime | Y | เวลาอัปเดตล่าสุด | 2026-02-21T11:00Z |

### **4\) Idempotency Keys** 

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| idempotencyKeyHash | string | Y | (PK) ค่า hash ของ X-Idempotency-Key (แนะนำ SHA-256 \+ base64/hex) เพื่อไม่เก็บ raw key | sha256:9f2c...a1b0 |
| operationName | string | Y | ชื่อ operation ที่ idempotent เช่น CreateRescueRequest | CreateRescueRequest |
| requestFingerprint | string | N | hash ของ request body หลัง normalize เพื่อใช้ตรวจว่า key เดิมแต่ payload เปลี่ยน (ถ้าเปลี่ยนให้ 409\) | sha256:ab12...ff90 |
| status | enum | Y | สถานะของ idempotency record: IN\_PROGRESS, COMPLETED, FAILED | COMPLETED |
| lockOwner | string | N | ตัวระบุคน/ตัวประมวลผลที่ถือ “ล็อก” ตอน IN\_PROGRESS (เช่น awsRequestId) | awsReq:6d9c... |
| lockedAt | datetime | N | เวลาเริ่มถือ lock | 2026-03-03T08:01:12Z |
| lockExpiresAt | datetime | N | เวลาหมดอายุ lock | 2026-03-03T08:02:12Z |
| responseStatusCode | int | N | HTTP status code ของผลลัพธ์ครั้งแรก | 201 |
| responseHeaders | json | N | headers ที่จำเป็นต้อง replay (เช่น Location, ETag, custom) | {"Location":"/requests/REQ-8812-9901"} |
| responseBody | json/text | N | response body ที่จะ replay กลับไป (แนะนำเก็บ “เฉพาะ payload ที่คืนให้ client”) | {"requestId":"REQ-8812-9901","status":"SUBMITTED"} |
| resultResourceId | string | N | id ของ resource ที่ถูกสร้าง/อ้างอิง เช่น requestId เพื่อ query ภายใน | REQ-8812-9901 |
| errorCode | string | N | ถ้าล้มเหลว เก็บ code สำหรับ replay แบบคงที่ | VALIDATION\_ERROR |
| errorMessage | string | N | ข้อความ error  | peopleCount must be \>= 1 |
| createdAt | datetime | Y | เวลา insert record | 2026-03-03T08:01:12Z |
| updatedAt | datetime | Y | เวลา update ล่าสุด | 2026-03-03T08:01:15Z |
| expiresAt | datetime | Y | TTL 24 ชม. เพื่อ purge record อัตโนมัติ | 2026-03-04T08:01:12Z |
| clientId | string | N | ตัวระบุ client/app/user  | citizen:U-10029 |
| requestIp | string | N | IP ต้นทาง | 203.0.113.10 |
| userAgent | string | N | UA (debug) | RescueApp/1.2.0 (iOS) |

**5\) Citizen Request Updates**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| updateId | uuid | Y | (PK) ไอดีการแจ้งข้อมูลเพิ่ม | `b21f...` |
| requestId | string | Y | (FK) อ้างอิงคำร้อง | `REQ-8812-9901` |
| updateType | enum | Y | ประเภทการอัปเดต เช่น `NOTE`, `LOCATION_DETAILS`, `PEOPLE_COUNT`, `SPECIAL_NEEDS`, `CONTACT_INFO` | `NOTE` |
| updatePayload | json | Y | เนื้อหาที่อัปเดต (เฉพาะ field ที่เปลี่ยน) | `{"note":"น้ำสูงขึ้นถึงเอว"}` |
| citizenAuthMethod | enum | Y | วิธีพิสูจน์: `PHONE_PLUS_TRACKING_CODE` | `PHONE_PLUS_TRACKING_CODE` |
| citizenPhoneHash | string | Y | hash เบอร์ที่ใช้ยืนยันตอนอัปเดต (เก็บเพื่อ audit) | `sha256:91ab...` |
| trackingCodeHash | string | Y | hash ของเลขติดตามที่ใช้ (audit) | `sha256:3c1f...` |
| clientIp | string | N | IP ผู้ส่ง | `203.0.113.10` |
| userAgent | string | N | UA | `RescueApp/1.2.0 (iOS)` |
| createdAt | datetime | Y | เวลาแจ้งข้อมูลเพิ่ม | `2026-03-03T08:10:00Z` |

**6\) Tracking Lookup Index**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| phoneHash | string | Y | (PK) hash เบอร์ normalize | `sha256:91ab...` |
| trackingCodeHash | string | Y | (SK/Unique) hash เลขติดตาม 6 หลัก | `sha256:3c1f...` |
| requestId | string | Y | requestId ที่ต้องการชี้ไป | `REQ-8812-9901` |
| incidentId | uuid | Y | incident สำหรับจัดกลุ่ม/ตรวจสอบ | `8b9b6d5b...` |
| createdAt | datetime | Y | เวลาเริ่มใช้ tracking | `2026-03-03T08:01:12Z` |
| expiresAt | datetime | N | TTL ของ index (เช่น ลบหลังปิดงาน 30 วัน) | `2026-04-02T08:01:12Z` |

# Service Architecture

**Service Architecture**

**Components**

**Citizen Client (Mobile/Web)**  
ช่องทางที่ประชาชนใช้ติดต่อระบบเพื่อแจ้งเหตุ ขอความช่วยเหลือ ติดตามความคืบหน้า และส่งข้อมูลเพิ่มเติมระหว่างที่คำร้องยังดำเนินอยู่  
หน้าที่หลัก:  
\- สร้างคำร้องขอความช่วยเหลือ  
\- ติดตามสถานะคำร้อง  
\- ส่งข้อมูลอัปเดตเพิ่มเติมจากหน้างานหรือผู้แจ้งเหตุ

**Staff Client (Triage / Dispatcher / Admin Console)**  
ช่องทางสำหรับเจ้าหน้าที่ใช้บริหารจัดการคำร้องและควบคุมการทำงานภายใน  
หน้าที่หลัก:  
\- ดูรายละเอียดคำร้อง  
\- ตรวจสอบสถานะปัจจุบันและประวัติการเปลี่ยนแปลง  
\- บันทึกข้อมูลเพิ่มเติมจากฝั่งเจ้าหน้าที่  
\- สนับสนุนการคัดกรอง การประสานงาน และการติดตามการช่วยเหลือ

**Command / Workflow Layer**  
กลไกสำหรับควบคุมการเปลี่ยนสถานะของคำร้องตาม business workflow หรือ state machine ของระบบ  
หน้าที่หลัก:  
\- บังคับให้การเปลี่ยนสถานะเป็นไปตามลำดับที่กำหนด  
\- แยกคำสั่งเชิง workflow ออกจากการแก้ไขข้อมูลทั่วไป  
\- ทำให้ lifecycle ของ rescue request มีความชัดเจนและตรวจสอบได้

**Amazon API Gateway**  
จุดรับคำขอแบบ synchronous ของระบบจาก client ทุกประเภท  
หน้าที่หลัก:  
\- เป็น entry point กลางของบริการ  
\- ทำ routing ไปยัง service logic ภายใน  
\- รองรับ security control, throttling และการป้องกันทราฟฟิกผิดปกติ

**Lambda: RescueRequest Service Handler**  
แกนกลางของ RescueRequest Service ทำหน้าที่ประมวลผล business logic ทั้งหมดของระบบ  
หน้าที่หลัก:  
\- รับและประมวลผลคำขอจาก client  
\- ตรวจสอบความถูกต้องของข้อมูลและกฎทางธุรกิจ  
\- จัดการ lifecycle ของ rescue request  
\- ควบคุม state transition  
\- บันทึกข้อมูลหลักและประวัติการเปลี่ยนแปลง  
\- publish domain events ไปยังระบบ downstream

**Amazon DynamoDB**  
ฐานข้อมูลหลักที่ RescueRequest Service เป็นเจ้าของและดูแลเอง  
องค์ประกอบหลัก:  
1\. RescueRequestTable  
เก็บข้อมูลหลักของคำร้อง รวมถึง current state หรือข้อมูลล่าสุดที่ระบบใช้ตอบ query  
2\. IdempotencyTable  
เก็บข้อมูลสำหรับป้องกันการประมวลผลซ้ำจากคำขอเดิม  
หน้าที่หลัก:  
\- เก็บข้อมูลธุรกรรมหลักของคำร้อง  
\- เก็บสถานะล่าสุดของแต่ละคำร้อง  
\- รองรับการติดตาม request ที่ถูกส่งซ้ำ  
\- สนับสนุนการออกแบบที่ต้องการทั้งความเร็วและความทนทานในการรับโหลด

**Event Bus (Amazon SNS)**  
ช่องทางกลางสำหรับกระจายเหตุการณ์สำคัญที่เกิดขึ้นใน RescueRequest Service ไปยังบริการอื่นแบบ asynchronous  
หน้าที่หลัก:  
\- ประกาศ domain events ของระบบ  
\- ลดการผูกกันโดยตรงระหว่าง RescueRequest Service กับ downstream services  
\- รองรับการขยาย consumer ในอนาคตได้ง่าย

**Explanation**  
สถาปัตยกรรมของ RescueRequest Service ถูกออกแบบให้เป็น ศูนย์กลางจัดการ rescue request โดยแยกบทบาทของระบบออกเป็นส่วนรับคำขอ, ส่วนประมวลผล, ส่วนจัดเก็บข้อมูล และส่วนกระจายเหตุการณ์ไปยังบริการอื่นอย่างชัดเจน  
ในฝั่งผู้ใช้งาน ระบบรองรับทั้งประชาชนและเจ้าหน้าที่ผ่าน client คนละบริบท แต่เชื่อมเข้าสู่บริการกลางเดียวกันผ่าน API Gateway ทำให้การควบคุมด้านความปลอดภัย การกำหนดนโยบายการเข้าถึง และการจัดการทราฟฟิกทำได้จากจุดเดียว  
แกนหลักของระบบคือ Lambda-based RescueRequest Service Handler ซึ่งเป็นจุดรวมของ business logic ทั้งหมด ไม่ว่าจะเป็นการรับคำร้อง การดูแลสถานะ การจัดการ workflow และการตรวจสอบความถูกต้องของข้อมูลที่เกี่ยวข้องกับ incident โดยเมื่อจำเป็น ระบบจะอ้างอิง IncidentTracking Service เพื่อยืนยันข้อมูล incident จากแหล่งข้อมูลต้นทางที่เชื่อถือได้  
ในด้านการจัดเก็บข้อมูล ระบบใช้ DynamoDB เป็น owned data store เพื่อให้ RescueRequest Service ควบคุมโครงสร้างข้อมูลและ lifecycle ของข้อมูลได้เอง โดยแยกข้อมูลคำร้องหลักออกจากข้อมูล idempotency อย่างชัดเจน ช่วยให้ระบบรองรับทั้งการทำงานแบบธุรกรรมหลักและการป้องกันคำสั่งซ้ำจากการ retry ได้อย่างเหมาะสม  
อีกส่วนสำคัญคือการแยก การประมวลผลแบบ synchronous ออกจาก การสื่อสารแบบ asynchronous เมื่อเกิดเหตุการณ์สำคัญในคำร้อง ระบบจะ publish event ไปยัง Amazon SNS เพื่อให้ downstream services รับไปทำงานต่อได้โดยไม่ทำให้เส้นทางหลักของระบบช้าลง แนวทางนี้ช่วยลด coupling ระหว่างบริการ และทำให้สามารถเพิ่มความสามารถใหม่ในอนาคตได้ง่าย  
บริการปลายทางที่เชื่อมต่ออยู่ในระบบปัจจุบัน เช่น RecommendRescueTeam Service และ Rescue Prioritization Service มีบทบาทเฉพาะทางในการช่วยวิเคราะห์และตัดสินใจต่อจากข้อมูลคำร้อง โดยไม่ต้องฝัง logic เหล่านั้นไว้ใน RescueRequest Service เอง ส่งผลให้บริการหลักยังคงเรียบง่าย ดูแลได้ง่าย และโฟกัสกับหน้าที่หลักคือการเป็นระบบรับและจัดการคำร้อง  
โดยสรุป สถาปัตยกรรมนี้ทำให้ RescueRequest Service มีบทบาทเป็น transactional core ของระบบ รับผิดชอบ lifecycle ของคำร้องโดยตรง ขณะที่ความสามารถเชิงวิเคราะห์และการตัดสินใจขั้นต่อไปถูกกระจายออกไปยังบริการเฉพาะทางผ่าน event-driven architecture ซึ่งเหมาะกับระบบที่ต้องรองรับโหลดสูง ขยายต่อได้ง่าย และต้องทำงานได้ต่อเนื่องในสถานการณ์วิกฤต

# Service Interaction

**Service Interaction**

**Upstream Services (บริการต้นทางที่เรียกใช้งาน RescueRequest Service)**  
1\) Citizen Mobile/Web App (Citizens)  
ใช้สำหรับประชาชนในการสร้างคำร้อง ติดตามสถานะ และส่ง/ดูข้อมูลอัปเดตของคำร้อง  
**Public Endpoints (Citizens)**  
**POST /v1/rescue-requests**  
ใช้สร้างคำร้องขอความช่วยเหลือใหม่

**POST /v1/citizen/tracking/lookup**  
ใช้ค้นหาคำร้องหรือข้อมูลติดตามจากข้อมูลอ้างอิงที่ประชาชนมี

**GET /v1/citizen/rescue-requests/{requestId}/status**  
ใช้ตรวจสอบสถานะล่าสุดของคำร้อง

**POST /v1/citizen/rescue-requests/{requestId}/updates**  
ใช้ส่งข้อมูลอัปเดตเพิ่มเติมจากประชาชน เช่น อาการเปลี่ยน สถานที่เปลี่ยน หรือข้อมูลติดต่อเพิ่มเติม

**GET /v1/citizen/rescue-requests/{requestId}/updates**  
ใช้ดูประวัติข้อมูลอัปเดตของคำร้อง

2\) Staff Console (Triage / Dispatcher / Admin)  
ใช้สำหรับเจ้าหน้าที่ในการดูรายละเอียดคำร้อง แก้ไขข้อมูล ติดตาม event และตรวจสอบข้อมูลประกอบการปฏิบัติงาน  
**Staff Endpoints**  
**GET /v1/rescue-requests/{requestId}**  
ใช้ดูรายละเอียดของคำร้อง

**PATCH /v1/rescue-requests/{requestId}**  
ใช้แก้ไขข้อมูลคำร้อง

**GET /v1/rescue-requests/{requestId}/events**  
ใช้ดูประวัติ event หรือ timeline ของคำร้อง

**POST /v1/rescue-requests/{requestId}/events**  
ใช้บันทึก event ใหม่เข้าสู่คำร้อง

**GET /v1/rescue-requests/{requestId}/current**  
ใช้ดู current state หรือ snapshot ปัจจุบันของคำร้อง

**GET /v1/incidents/{incidentId}/rescue-requests**  
ใช้ค้นหารายการ rescue request ที่ผูกกับ incident เดียวกัน

**GET /v1/idempotency-keys/{idempotencyKeyHash}**  
ใช้ตรวจสอบสถานะของคำขอที่ทำแบบ idempotent เพื่อป้องกันการสร้างข้อมูลซ้ำ

3\) Workflow / Staff Action / Orchestrator  
ใช้สำหรับสั่งเปลี่ยน state ของคำร้องตาม business workflow หรือ state machine  
**Command Endpoints (State Machine)**  
**POST /v1/rescue-requests/{requestId}/triage**  
ใช้เปลี่ยนสถานะเข้าสู่ขั้นตอนคัดกรอง (triage)

**POST /v1/rescue-requests/{requestId}/assign**  
ใช้มอบหมายทีม/หน่วยให้คำร้อง

**POST /v1/rescue-requests/{requestId}/start**  
ใช้เปลี่ยนสถานะเมื่อเริ่มปฏิบัติงาน

**POST /v1/rescue-requests/{requestId}/resolve**  
ใช้ปิดงานเมื่อคำร้องได้รับการช่วยเหลือหรือเสร็จสิ้น

**POST /v1/rescue-requests/{requestId}/cancel**  
ใช้ยกเลิกคำร้อง

**Downstream Services (บริการปลายทางที่ RescueRequest Service เรียกหรือส่งข้อมูลไป)**  
A) Downstream แบบ Synchronous  
**IncidentTracking Service (Krittamet)**  
RescueRequest Service เรียกใช้งาน IncidentTracking Service เพื่อใช้ตรวจสอบและอ้างอิงว่า incidentId ถูกต้อง มีอยู่จริง และสามารถใช้เชื่อมโยงคำร้องเข้ากับ incident ที่เกี่ยวข้องได้  
ตัวอย่างการเรียก:  
GET /v1/incidents/{incidentId}  
ผลลัพธ์ที่คาดหวัง:  
\- 200 OK เมื่อพบ incident  
\- 404 Not Found เมื่อไม่พบ incident  
\- 503 Service Unavailable เมื่อบริการปลายทางไม่พร้อมใช้งาน  
บทบาทหลัก:  
\- validate ความถูกต้องของ incidentId  
\- enrich ข้อมูลอ้างอิง incident ให้กับคำร้อง  
\- เป็นแหล่งอ้างอิงหลักของ incident registry / incident tracking

B) Downstream แบบ Asynchronous (ส่งข้อมูลผ่าน Pub/Sub)   
**Event Bus (SNS)**  
RescueRequest Service จะ publish domain events ออกไปยัง Event Bus ผ่าน topic รูปแบบ:  
**rescue-request-events-v1-{stage}**  
โดย {stage} หมายถึง environment หรือ deployment stage เช่น  
rescue-request-events-v1-dev  
rescue-request-events-v1-uat  
rescue-request-events-v1-prod  
เหตุการณ์ที่ publish ครอบคลุมการเปลี่ยนแปลงสำคัญของ rescue request เช่น  
request created  
request updated  
state transitioned  
citizen update added  
assignment changed  
request resolved  
request cancelled

**RecommendRescueTeam Service (Kamonphan)**  
รับ event จาก Event Bus ผ่านคิว:  
SQS: recommend-rescue-team.inbox.v1  
บทบาทหลัก:  
\- ประมวลผลข้อมูลคำร้องและข้อมูล incident ที่เกี่ยวข้อง  
\- แนะนำทีมกู้ภัยหรือหน่วยปฏิบัติการที่เหมาะสม  
\- สนับสนุนการตัดสินใจในขั้นตอน assign หรือ dispatch

**Rescue Prioritization Service (Nattasak)**  
รับ event จาก Event Bus ผ่านคิว:  
SQS: rescue-prioritization.inbox.v1  
บทบาทหลัก:  
\- ประเมินลำดับความเร่งด่วนของคำร้อง  
\- คำนวณ priority score จากข้อมูลเหตุการณ์ อาการ สถานที่ หรือข้อมูลประกอบอื่น  
\- สนับสนุน triage และการจัดลำดับคิวการช่วยเหลือ

**สรุปภาพรวมการไหลของข้อมูล**  
1\. ประชาชนเรียกใช้งาน Public Endpoints เพื่อสร้างคำร้อง ติดตามสถานะ และส่งข้อมูลอัปเดต  
2\. เจ้าหน้าที่เรียกใช้งาน Staff Endpoints เพื่อดู แก้ไข และติดตามรายละเอียดของคำร้อง  
3\. การเปลี่ยน state หลักของคำร้องทำผ่าน Command Endpoints เพื่อให้ workflow ชัดเจนและควบคุมได้ตาม state machine  
4\. RescueRequest Service เรียก IncidentTracking Service แบบ synchronous เพื่อตรวจสอบความถูกต้องของ incidentId  
5\. เมื่อเกิดการเปลี่ยนแปลงสำคัญในระบบ RescueRequest Service จะ publish events ไปยัง rescue-request-events-v1-{stage}  
6\. บริการปลายทาง เช่น RecommendRescueTeam Service และ Rescue Prioritization Service จะ consume events ผ่าน SQS ของตนเองเพื่อนำไปประมวลผลต่อ

# Dependency Mapping

## **Dependency Mapping – RescueRequest Service**

### **1\) Incident Service**

* **Type:** Service  
* **Interaction Style:** Synchronous (REST)  
* **Purpose:** ตรวจสอบความถูกต้อง/การมีอยู่ของ `incidentId` ก่อนบันทึกคำร้อง (ใช้เป็น registry/reference)  
* **Criticality:** Critical  
* **Failure Handling:**  
  * หาก Incident Service ไม่ตอบสนอง/timeout → ตอบ `503 INCIDENT_REGISTRY_UNAVAILABLE` ให้ client retry

### **2\) Amazon DynamoDB**

* **Type:** Database  
* **Interaction Style:** Internal Data Access (read/write)  
* **Purpose:** จัดเก็บข้อมูลที่ RescueRequest Service เป็นเจ้าของ  
  * RescueRequests (Master)  
  * RescueRequestState (Snapshot/Current Status)  
  * RescueRequestEvents (Audit Trail)  
  * IdempotencyKeys (TTL 24h)  
  * DuplicateIndex (TTL short)  
* **Criticality:** Critical  
* **Failure Handling:**  
  * ใช้ **DynamoDB Transaction** เพื่อให้ master/state/audit เขียนสอดคล้องกัน  
  * หาก write/transaction ล้มเหลว → ไม่สร้างคำร้อง/ไม่เปลี่ยนสถานะ และไม่ publish event

### **3\) Amazon DynamoDB – IdempotencyKeys**

* **Type:** Database (DynamoDB Table)  
* **Interaction Style:** Internal Data Access (read/write)  
* **Purpose:** รองรับ **Strong Idempotency** ด้วย `X-Idempotency-Key` ให้ replay ผลลัพธ์เดิมได้ (TTL 24 ชั่วโมง)  
* **Criticality:** Critical  
* **Failure Handling:**  
  * หากอ่าน/เขียน idempotency mapping ล้มเหลว → ปฏิเสธการสร้างคำร้อง (ตอบ 5xx) เพื่อกันการสร้างซ้ำ  
  * ใช้ conditional write/atomic put เพื่อลด race condition

### **4\) Amazon DynamoDB – DuplicateIndex**

* **Type:** Database (DynamoDB Table)  
* **Interaction Style:** Internal Data Access (read/write)  
* **Purpose:** รองรับ **Weak Duplicate Heuristic** เมื่อไม่มี idempotency key เพื่อตรวจจับคำร้องซ้ำในช่วงเวลาสั้น   
* **Criticality:** Non-Critical   
* **Failure Handling:**  
  * หากตาราง dedupe ใช้งานไม่ได้/อ่านไม่สำเร็จ → ระบบยัง “รับคำร้องได้” แต่เสี่ยงเกิด duplicate มากขึ้น   
  * หากเขียน dedupe key ไม่สำเร็จ → ไม่ block การสร้างคำร้อง

### **5\) Amazon SNS (rescue.request.created.v1)**

* **Type:** Topic / Event Bus  
* **Interaction Style:** Asynchronous (Event Pub/Sub)  
* **Purpose:** กระจายเหตุการณ์ “สร้างคำร้องสำเร็จ” ให้บริการปลายทางเริ่มทำงาน (Dispatch/Notification/Analytics)  
* **Criticality:** Non-Critical (ต่อการตอบ REST) / Critical (ต่อ workflow ปลายทาง)  
* **Failure Handling:**  
  * หาก publish ไม่สำเร็จ → บันทึก log/metric และ retry 

### **6\) Amazon SNS (rescue.request.status-changed.v1)**

* **Type:** Topic / Event Bus  
* **Interaction Style:** Asynchronous (Event Pub/Sub)  
* **Purpose:** แจ้งการเปลี่ยนสถานะ (TRIAGED/ASSIGNED/IN\_PROGRESS/RESOLVED/CANCELLED) ให้ Notification และ Dashboard อัปเดต near real-time  
* **Criticality:** Non-Critical (ต่อการเปลี่ยนสถานะในฐานข้อมูล)  
* **Failure Handling:**  
  * หาก publish ไม่สำเร็จ → retry/log และให้ state ใน DB เป็น source of truth (client ยัง query GET ได้)

