# Service Overview

**ภาพรวมของบริการ (Service Overview)**  
RecommendRescueTeam Service

**0\.  Github repo**  
[https://github.com/kamonphankanthayod/recommend-rescue-team-service](https://github.com/kamonphankanthayod/recommend-rescue-team-service)

1. **Service Owner**

นายกมลพันธ์ กันธายอด รหัสนักศึกษา 6609520116 ภาคปกติ

2. **Service Purpose**

RecommendRescueTeam Service เป็นบริการแบบ Microservice ที่ทำหน้าที่เป็น Decision-Support Engine สำหรับแนะนำทีมกู้ภัยที่เหมาะสมที่สุดต่อคำร้องขอความช่วยเหลือ (Rescue Request) ภายใต้บริบทของเหตุการณ์ภัยพิบัติ (Incident)

บริการนี้มีหน้าที่: วิเคราะห์ข้อมูลคำร้องขอความช่วยเหลือ, ประเมินความเหมาะสมของทีมกู้ภัยตามเกณฑ์ที่กำหนด, จัดลำดับทีมตามคะแนนความเหมาะสม, สร้างคำแนะนำที่สามารถอธิบายเหตุผลได้ (Explainable Recommendation), คำนวณค่าความเชื่อมั่น (Confidence Score), รองรับการประเมินใหม่เมื่อสถานการณ์เปลี่ยนแปลง

บริการนี้ ไม่ได้ทำหน้าที่ dispatch ทีมกู้ภัย แต่ทำหน้าที่เป็นกลไกสนับสนุนการตัดสินใจให้กับ Dispatcher และ Manage Dispatch Service

3. **Pain Point ที่แก้ไข**

ในสถานการณ์ภัยพิบัติจริง Dispatcher ต้องตัดสินใจอย่างรวดเร็วภายใต้ข้อจำกัดด้านเวลา ความรุนแรงของเหตุการณ์ และทรัพยากรที่จำกัด การตัดสินใจโดยอาศัยการประเมินด้วยมนุษย์เพียงอย่างเดียวอาจก่อให้เกิดปัญหา เช่น เลือกทีมที่ไม่มีความเชี่ยวชาญตรงกับประเภทเหตุการณ์, ส่งทีมที่อยู่ไกลเกินไป ทำให้เกิดความล่าช้า, ใช้ทรัพยากรไม่เหมาะสมกับระดับความรุนแรง, การตัดสินใจไม่สม่ำเสมอในเหตุการณ์ลักษณะคล้ายกัน, ไม่สามารถปรับตัวทันเมื่อสถานการณ์เปลี่ยนแบบ real-time 

บริการนี้จึงช่วยทำให้กระบวนการประเมินเป็นระบบ, ลด Human Error, เพิ่มความโปร่งใส (Explainability), รองรับการปรับประเมินใหม่เมื่อข้อมูลเปลี่ยนแปลง

**4\. Target Users**

* Dispatcher  
* Manage Dispatch Service  
* บริการนี้ไม่ได้ออกแบบให้ผู้ประสบภัยเรียกใช้โดยตรง แต่เป็น backend decision-support service สำหรับ Dispatcher และระบบอื่นใน Disaster Response Ecosystem

**5\. Service Boundary**

* In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)  
  * วิเคราะห์ Rescue Request ร่วมกับบริบทของ Incident  
  * คัดกรองทีมกู้ภัยที่ผ่านเงื่อนไขขั้นต่ำ (Candidate Filtering)  
  * คำนวณคะแนนความเหมาะสม (Scoring Mechanism)  
  * จัดลำดับทีม (Ranking)  
  * สร้าง Recommendation Record  
  * คำนวณ Confidence Score  
  * จัดการ Lifecycle ของ Recommendation (GENERATED / ACCEPTED / EXPIRED / SUPERSEDED)  
  * เก็บ Score Breakdown และ Explanation เพื่อรองรับ Audit  
  * รองรับ Re-evaluation แบบ Asynchronous  
  * จัดเก็บ Model/Rule Version Metadata

* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
  * การจัดการข้อมูล Incident Master Data  
  * การสร้างหรือจัดการ Rescue Request  
  * การจัดลำดับความสำคัญของคำร้อง (เป็นหน้าที่ Rescue Prioritization Service)  
  * การ dispatch ทีมกู้ภัย  
  * การจัดการความพร้อมใช้งานของทีมโดยตรง  
  * การวางแผนเส้นทางหรือการจัดการโลจิสติกส์

**6\. Autonomy / Decision Logic**

บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การกำหนดเกณฑ์การคัดกรองทีมกู้ภัย  
* การคำนวณคะแนนความเหมาะสมของแต่ละทีม  
* การจัดลำดับทีม  
* การคำนวณ Confidence Score ของผลลัพธ์  
* การกำหนดสถานะของ Recommendation  
* การตัดสินใจ Re-evaluate เมื่อบริบทเปลี่ยน

แนวคิดการคำนวณคะแนน:

Suitability Score อาจคำนวณจาก

* ความตรงกันของความเชี่ยวชาญกับประเภทเหตุการณ์  
* ระยะทางจากจุดเกิดเหตุ  
* ความพร้อมใช้งานของทีม  
* ระดับความรุนแรงของเหตุการณ์  
* เวลาตอบสนองโดยประมาณ

คะแนนรวมจะถูกเก็บพร้อมรายละเอียดการคำนวณ (Score Breakdown) เช่น:

* specialization\_score  
* distance\_score  
* availability\_score  
* severity\_weight

### Explainability

ทุก Recommendation จะเก็บ Explanation Metadata เพื่อให้ Dispatcher เข้าใจเหตุผลของการจัดอันดับ

### Re-evaluation

ระบบรองรับการประเมินใหม่เมื่อ:

* ความพร้อมใช้งานของทีมเปลี่ยน  
* ระดับความรุนแรงของเหตุการณ์เปลี่ยน  
* รายละเอียดคำร้องเปลี่ยน

มีการกำหนด Cooldown Window และ Limit ต่อจำนวนครั้งการประเมินใหม่ เพื่อป้องกัน Re-evaluation Storm  
บริการสามารถตัดสินใจสร้างและจัดลำดับคำแนะนำได้เองภายใต้ business rules ที่กำหนด โดยไม่ต้องรอการอนุมัติจากมนุษย์ในขั้นตอนการประเมินปกติ ทั้งนี้ Dispatcher ยังคงเป็นผู้ตัดสินใจขั้นสุดท้ายในการเลือกทีมเพื่อ dispatch

**7\. Owned Data**

* Recommendation Records  
  ข้อมูลผลลัพธ์การแนะนำทีมกู้ภัย ที่ถูกสร้างขึ้นจากกระบวนการประเมินในแต่ละครั้ง โดยข้อมูลดังกล่าวสะท้อนผลการตัดสินใจ ณ เวลาหนึ่ง และใช้สำหรับแสดงผลแก่ Dispatcher, การติดตามสถานะของคำแนะนำ, การตรวจสอบย้อนหลัง, การรองรับ Re-evaluation

* Ranked Team Snapshot  
  ทุกครั้งที่มีการสร้างคำแนะนำ ระบบจะเก็บ Snapshot ของผลการจัดลำดับทีม เพื่อป้องกันการคำนวณซ้ำและรองรับ Explainability ข้อมูลชุดนี้ประกอบด้วยรายชื่อทีมที่ผ่านการคัดกรอง, ลำดับ (Rank), คะแนนรวม, รายละเอียดคะแนนย่อย (Score Breakdown), คำอธิบายเหตุผลของการให้คะแนน (Explanation Metadata)  
  ข้อมูลนี้ถือเป็น Decision Snapshot และจะไม่ถูกแก้ไขย้อนหลัง แม้ภายหลังข้อมูลภายนอกจะเปลี่ยนแปลง

* Projection Read Models (Local Decision Data)  
  เพื่อรองรับการทำงานแบบ Event-Driven และลด Coupling ระหว่างบริการ ระบบจะเก็บสำเนาข้อมูลที่จำเป็นต่อการประเมินในรูปแบบ Local Projection เช่น ข้อมูลสรุปของ Rescue Request, ข้อมูลสถานะ Incident ที่เกี่ยวข้อง, ข้อมูลความพร้อมใช้งานและความเชี่ยวชาญของทีม ข้อมูล Projection เหล่านี้ไม่ถือเป็น Master Data ถูกอัปเดตผ่าน Event จากบริการต้นทาง ใช้เพื่อการประมวลผลภายในเท่านั้น

* Model/Rule Version Metadata  
  ข้อมูลเวอร์ชันของ rule set หรือ scoring logic (model version) มีความสำคัญต่อการตรวจสอบความถูกต้องย้อนหลัง และรองรับการปรับปรุงกฎในอนาคตโดยไม่กระทบข้อมูลเก่า รองรับการวิเคราะห์เชิงสถิติภายหลัง

**8\. Linked Data (Reference Only)**

* ก่อนการแนะนำ ระบบจะต้องอ้างอิงข้อมูลจากบริการอื่นเพื่อใช้เป็น input ในกระบวนการประเมินและให้คะแนนคำนวณคำแนะนำ  
  * incidentId และ สถานะของ Incident จาก Central Incident Schema  
  * ข้อมูลจาก RescueRequest Service  
  * ข้อมูลการเปลี่ยนแปลงระดับความรุนแรงจาก IncidentTracking Service  
  * ข้อมูลความพร้อมใช้งานของทีมจาก Team/Resource Service  
* การเชื่อมโยงข้อมูลจะทำผ่าน Event Subscription เพื่อสร้าง Local Projection แทนการเรียกแบบ synchronous runtime dependency


**9\. Non-Functional Requirements**

Scalability 

* Stateless Compute  
* รองรับ Horizontal Scaling  
* รองรับ Serverless Architecture  
* รองรับ Burst Traffic ในช่วง Disaster Spike

Reliability & Fault Tolerance

* รองรับ At-Least-Once Event Delivery  
* ต้อง Idempotent ต่อ recommendation\_id และ request\_id  
* มี TTL สำหรับ Recommendation เพื่อลดความเสี่ยงจากข้อมูลล้าสมัย  
* หาก Projection ล่าช้า ระบบจะลด Confidence Score

Performance

* การสร้าง Recommendation ต้องไม่ Block Dispatcher  
* Re-evaluation ทำงานแบบ Asynchronous  
* Latency ในการตอบคำสั่ง Recommendation ต้องอยู่ในระดับที่เหมาะสมต่อการตัดสินใจภาคสนาม

Security

* Role-based Authorization (เฉพาะ Dispatcher / Manage Dispatch Service)  
* Audit Log สำหรับตรวจสอบย้อนหลัง  
* Correlation ID สำหรับ Distributed Tracing  
* รองรับ Event Versioning และ Schema Versioning

Consistency Model

* ใช้แนวคิด Eventual Consistency  
* การตัดสินใจอิงจาก Local Projection ที่อัปเดตจาก Event  
* ไม่ทำ Distributed Transaction ระหว่างบริการ

# Sync Contract

**Synchronous Function Contract**  
**Base URL:** *http://TBD.com*

# **API Contract \#1: Generate Recommendation**

### **ข้อมูลทั่วไป**

* **Name:** Generate recommendation for rescue request  
* **Method:** POST  
* **Path:** /v1/recommendations  
* **Type:** Synchronous

### **คำอธิบาย**

Endpoint นี้ใช้สำหรับให้ Dispatcher ส่งคำขอเพื่อให้ระบบเริ่มวิเคราะห์และสร้างคำแนะนำทีมกู้ภัยที่เหมาะสมสำหรับ rescue request หนึ่งรายการ

**Request**

**Headers**

* Authorization: Bearer \<dispatcher\_token\>  
* Content-Type: application/json  
* Idempotency-Key: \<UUID\> (Required)  
  **Body:**   
  {  
    "request\_id": "REQ-8812-9904",  
    "force\_reevaluate": false  
  }

### **Validation Rules**

* ### request\_id ต้องเป็นค่าที่ถูกต้อง มีอยู่ในข้อมูลของ RescueRequest Service

* ### หากมี ACTIVE recommendation และ force\_reevaluate \= false → return 409

* ### Idempotency-Key ต้องกำหนดมาใน Header Request

  * หากไม่มี return **400 Bad Request**  
  * หากไม่ใช่ UUID (ผิด format) return **400 Bad Request**

### **Response**

**Success: 201 Created**  
{  
  "recommendation\_id": "82270dcf-41c2-49ce-b200-1d1b83603c68",  
  "request\_id": "REQ-8812-9901",  
  "incident\_id": "a5f61e23-2bb8-4bda-90eb-a352537b81ee",  
  "recommendation\_status": "GENERATED",  
  "created\_at": "2025-06-01T10:27:027Z"  
}  
\*\*กรณีที่ 201 Created คือ Key ไม่ซ้ำ and body ไม่ซ้ำ จะสร้างใหม่

**Success: 200 Success**  
{  
  "recommendation\_id": "82270dcf-41c2-49ce-b200-1d1b83603c68",  
  "request\_id": "REQ-8812-9901",  
  "incident\_id": "a5f61e23-2bb8-4bda-90eb-a352537b81ee",  
  "recommendation\_status": "GENERATED",  
  "created\_at": "2025-06-01T10:27:027Z"  
}  
\*\*กรณีที่ 200 Success คือ Key ซ้ำ and body ซ้ำ จะไม่สร้างใหม่และ return อันเดิม  
\*\*กรณีที่ 200 Success คือ Key ไม่ซ้ำ and body ซ้ำ จะไม่สร้างใหม่และ return อันเดิม

**Error: 409 IDEMPOTENCY\_CONFLICT**  
{  
  "error": {  
    "code": "IDEMPOTENCY\_KEY\_REUSE\_WITH\_DIFFERENT\_PAYLOAD",  
    "message": "Same Idempotency-Key used with different request body",  
    "trace\_id": "aaUrTgkGIAMEZiw="  
  }  
}  
\*\*กรณีที่ 409 Conflict คือ Key ซ้ำ and body ไม่ซ้ำ จะไม่สร้างใหม่และ return 409

**Header Error: 400 Bad Request**  
{  
  "error": {  
    "code": "VALIDATION\_HEADER\_ERROR",  
    "message": "Idempotency-Key is required",  
    "trace\_id": "aaUrTgkGIAMEZiw=",  
    "details": \[  
      {  
        "field": "request\_id",  
        "issue": "missing"  
      }  
    \]  
  }  
}

**Header Error: 400 Bad Request**  
{  
  "error": {  
    "code": "VALIDATION\_HEADER\_ERROR",  
    "message": "Invalid idempotency\_key format \- Idempotency-Key must be a valid UUID",  
    "trace\_id": "aaUrTgkGIAMEZiw=",  
    "details": \[  
      {  
        "field": "request\_id",  
        "issue": "invalid\_format"  
      }  
    \]  
  }  
}

**Error: 400 Bad Request**  
{  
  "error": {  
    "code": "VALIDATION\_ERROR",  
    "message": "request\_id is required",  
    "trace\_id": "aaUrTgkGIAMEZiw=",  
    "details": \[  
      {  
        "field": "request\_id",  
        "issue": "missing"  
      }  
    \]  
  }  
}

**Error: 404 Not Found**  
{  
  "error": {  
    "code": "REFERENCE\_NOT\_FOUND",  
    "message": "request\_id not found",  
    "trace\_id": "aaUrTgkGIAMEZiw="  
  }  
}

**Error: 500 Internal Server Error**  
{  
  "error": {  
    "code": "INTERNAL\_SERVER\_ERROR",  
    "message": "Fail to create recommendation",  
    "trace\_id": "aaUrTgkGIAMEZiw="  
  }  
}

### **Dependency / Reliability**

* ไม่เรียก service อื่นแบบ synchronous  
* ใช้ Local Projection  
* Idempotent (ผ่าน Idempotency-Key)  
  * If Key ซ้ำ \+ body เหมือนเดิม return response เดิม return **200 Success**  
  * If Key ไม่ซ้ำ \+ body เหมือนเดิม return response เดิม return **200 Success** (จริงๆ ไม่ควร)  
  * If Key ซ้ำ \+ body ต่าง return **409 IDEMPOTENCY\_CONFLICT**  
  * If Key ไม่ซ้ำ \+ body ต่าง สร้างใหม่  return **201 Created**  
* บริการต้องสามารถสร้าง Recommendation ได้ภายในระยะเวลาไม่เกิน 2 วินาที ภายใต้ภาระงานปกติ (Normal Operating Load)  
* Stateless compute  
* trace\_id:  
  * Unique identifier for each API request  
  * Derived from API Gateway requestContext.requestId  
  * Used for tracing logs across distributed services

# **API Contract \#2: Get Recommendation Detail**

### **ข้อมูลทั่วไป**

* **Name:** Get Recommendation Detail  
* **Method:** GET  
* **Path:** /v1/recommendations/{request\_id}  
* **Type:** Synchronous

### **คำอธิบาย**

ใช้ดึงรายละเอียด Recommendation ด้วย request\_id

ซึ่งตอนนี้ 1 request มี 1 recommendation เท่านั้น

### **Request**

**Path Param**

* request\_id (String, required)

  **Headers**

* Accept: application/json  
* Authorization: Bearer \<token\>

### **Validation Rules**

* ### request\_id ต้องเป็นค่าที่ถูกต้อง มีอยู่ในข้อมูลของ RescueRequest Service

### **Response**

**Response Headers**

* ETag: "\<version\>"  
  **Success: 200 Success**  
  {  
    "recommendation\_id": "82270dcf-41c2-49ce-b200-1d1b83603c68",  
    "request\_id": "REQ-8812-9904",  
    "recommendation\_status": "GENERATED",  
    "confidence\_score": 4.0,  
    "ranked\_teams": \[  
      {  
        "team\_id": "TEAM-01",  
        "rank": 1,  
        "total\_score": 87.5,  
        "score\_breakdown": {  
          "specialization\_score": 30.0,  
          "distance\_score": 25.0,  
          "availability\_score": 20.0,  
          "severity\_weight": 12.5  
        },  
        "explanation": "Team specialization matches flood response"  
      }  
    \],  
    "model\_version": "v1.2.0",  
    "evaluated\_at": "2025-06-01T10:27:027Z"  
  }

  **Error: 404 NOT\_FOUND**

  {

    "error": {

      "code": "REFERENCE\_NOT\_FOUND",

      "message": "recommendation not found for request\_id",

      "trace\_id": "aaUrTgkGIAMEZiw="

    }

  }

**Error: 500 Internal Error**  
{  
  "error": {  
    "code": "INTERNAL\_SERVER\_ERROR",  
    "message": "Fail to get recommendation detail",  
    "trace\_id": "aaUrTgkGIAMEZiw="  
  }  
}

### **Dependency / Reliability**

* ไม่เรียก service อื่น  
* Idempotent: Yes (read-only operation)

# **API Contract \#3: Delete Recommendation**

### **ข้อมูลทั่วไป**

* **Name:** Delete Recommendation  
* **Method:** DELETE  
* **Path:** /v1/recommendations/{recommendation\_id}  
* **Type:** Synchronous

### **คำอธิบาย**

ใช้ ลบ Recommendation ด้วย recommendation\_id

### **Request**

**Path Param**

* recommendation\_id (UUID, required)

  **Headers**

* Accept: application/json  
* Authorization: Bearer \<token\>

### **Validation Rules**

* ### recommendation\_id ต้องเป็นค่า UUID ที่ถูกต้อง มีอยู่ในข้อมูลของ IncidentTracking Service

### **Response**

**Success: 200 Success**

{  
  "recommendation\_id": "82270dcf-41c2-49ce-b200-1d1b83603c68",  
  "request\_id": "REQ-8812-9904",  
  "recommendation\_status": "GENERATED",  
  "confidence\_score": 4.0,  
  "ranked\_teams": \[  
    {  
      "team\_id": "TEAM-01",  
      "rank": 1,  
      "total\_score": 87.5,  
      "score\_breakdown": {  
        "specialization\_score": 30.0,  
        "distance\_score": 25.0,  
        "availability\_score": 20.0,  
        "severity\_weight": 12.5  
      },  
      "explanation": "Team specialization matches flood response"  
    }  
  \],  
  "model\_version": "v1.2.0",  
  "evaluated\_at": "2025-06-01T10:27:027Z"  
}

**Error: 404 NOT\_FOUND**  
{  
  "error": {  
    "code": "REFERENCE\_NOT\_FOUND",  
    "message": "recommendation not found for request\_id",  
    "trace\_id": "aaUrTgkGIAMEZiw="  
  }  
}

**Error: 500 Internal Error**  
{  
  "error": {  
    "code": "INTERNAL\_SERVER\_ERROR",  
    "message": "Fail to get recommendation detail",  
    "trace\_id": "aaUrTgkGIAMEZiw="  
  }  
}

### **Dependency / Reliability**

* ไม่เรียก service อื่น  
* Idempotent: Yes (read-only operation)


# **API Contract \#4: Accept Recommendation**

### **ข้อมูลทั่วไป**

* **Name:** Accept recommendation for rescue request  
* **Method:** PATCH  
* **Path:** /v1/recommendations/{recommendation\_id}/accept  
* **Type:** Synchronous

### **คำอธิบาย**

Endpoint นี้ใช้สำหรับให้ Dispatcher ยืนยันเลือกทีมจาก Recommendation

**Recommendation Lifecycle**

States:

* GENERATED (ACTIVE)  
* ACCEPTED (INACTIVE)  
* SUPERSEDED (INACTIVE)  
* EXPIRED (INACTIVE)

Rules:

* Only one ACTIVE recommendation per request  
* When force\_reevaluate \= true, the currently ACTIVE recommendation (if any) will be marked as SUPERSEDED before generating a new recommendation within the same transaction boundary.  
* ACCEPTED เป็น terminal state

**Request**

**Path Param**

* recommendation\_id (UUID, required)

  **Headers**

* If-Match: "\<etag\>" (Required)  
  **Body:**   
  {  
    "selected\_team\_id": "TEAM-01",  
    "accepted\_by": "dispatcher-01"  
  }

### **Validation Rules**

* ### selected\_team\_id ต้องอยู่ใน ranked list

* ### recommendation\_status ต้องเป็น GENERATED

  * ถ้า status \= SUPERSEDED → 409 INVALID\_STATE  
  * ถ้า status \= EXPIRED → 409 INVALID\_STATE

### **Response**

**Response Headers**

* ETag: "\<version\>"

  **Success: 200 OK**

  {

    "recommendation\_id": "82270dcf-41c2-49ce-b200-1d1b83603c68",

    "recommendation\_status": "ACCEPTED",

    "accepted\_at": "2025-06-01T10:27:02Z"

  }


  **Error: 400 Bad Request**

  {

    "error": {

      "code": "INVALID\_SELECTED\_TEAM",

      "message": "selected\_team\_id not found in ranked list",

      "trace\_id": "12bfb35d-00c5-41fa-8e08-8e1e5c9c1685"

    }

  }

  **Error: 404 NOT\_FOUND**

  {

    "error": {

      "code": "NOT\_FOUND",

      "message": "recommendation not found",

      "trace\_id": "12bfb35d-00c5-41fa-8e08-8e1e5c9c1685"

    }

  }


  **Error: 409 Conflict**

  {

    "error": {

      "code": "ACCEPT\_CONFLICT",

      "message": "Recommendation already accepted with different team",

      "trace\_id": "12bfb35d-00c5-41fa-8e08-8e1e5c9c1685"

    }

  }


  **Error: 412 Precondition Failed**

  {

    "error": {

      "code": "VERSION\_MISMATCH",

      "message": "Recommendation has been modified by another process",

      "trace\_id": "12bfb35d-00c5-41fa-8e08-8e1e5c9c1685"

    }

  }


### **Dependency / Reliability**

* Idempotent: Yes   
  * หาก recommendation ถูก ACCEPTED แล้ว การเรียกซ้ำจะคืนค่าเดิมโดยไม่เกิด side effect (ACTIVE \= GENERATED ||| INACTIVE \= ACCEPTED | SUPERSEDED | EXPIRED)  
  * ถ้า ACCEPTED แล้ว \+ selected\_team\_id ต่าง → return 409 ACCEPT\_CONFLICT  
* Dependency: Publish Event  
  * RecommendationAcceptedEvent  
  * RecommendationGeneratedEvent

# Async Contract

**Asynchronous Function Contract**

## **Message Contract \#1: Dispatch Team Assignment**

### **ข้อมูลทั่วไป** 

* **Message Name:** TeamDispatchRequested   
* **Interaction Style:** Request–Async Response (via Message Broker)  
* **Producer:** RecommendRescueTeam Service  
* **Consumer:** Dispatch Management Service  
* **Channel/Queue:** dispatch.team.commands.v1  
* **Version:** v1

### **คำอธิบาย**

Message นี้ถูกส่งออกเมื่อ Dispatcher ทำการ Accept Recommendation สำเร็จแล้ว เพื่อร้องขอให้ Dispatch Management Service ดำเนินการจัดส่งทีมกู้ภัยไปยังจุดเกิดเหตุแบบ asynchronous

ผู้ส่งจะได้รับผลลัพธ์ภายหลังผ่าน result event โดยอ้างอิงด้วย `correlation_id`

### **Request**

### **Message Headers (required unless stated)**

* message\_type: TeamDispatchRequested  
* message\_id: UUID (ใช้เป็น idempotency key ของคำขอ)  
* reply\_to: dispatch.team.results.v1  
* sent\_at: ISO-8601 datetime   
* trace\_id: uuid (optional)

  **Message Body**

  {

    "recommendation\_id": "82270dcf-41c2-49ce-b200-1d1b83603c68",

    "request\_id": "0fb43812-524a-4084-9df4-28ec426f0b85",

    "incident\_id": "a5f61e23-2bb8-4bda-90eb-a352537b81ee",

    "selected\_team\_id": "TEAM-01",

    "priority": "HIGH",

    "accepted\_by": "dispatcher-01"

  }


  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| recommendation\_id | UUID | Y | อ้างอิง Recommendation ที่ถูก ACCEPT |
| request\_id | UUID | Y | รหัส rescue request |
| incident\_id | UUID | Y | อ้างอิงเหตุการณ์จาก Central Incident Schema |
| selected\_team\_id | string | Y | ทีมที่ Dispatcher เลือก |
| priority | enum | Y | LOW / NORMAL / HIGH |
| accepted\_by | string | Y | ผู้ทำการยืนยันคำแนะนำ |

**Validation Rules**

1. recommendation\_id ต้องเป็น UUID ที่ถูกต้อง  
2. selected\_team\_id ต้องไม่เป็นค่าว่าง  
3. priority ต้องเป็นหนึ่งในค่าที่กำหนด  
4. message\_id ต้องไม่ซ้ำกับ message ที่เคยประมวลผลแล้ว (idempotency check)

Consumer ต้องรองรับการรับ message ซ้ำ (at-least-once delivery assumption)

**Response**

	**Message Headers (required unless stated)**

* message\_type: TeamDispatchResult   
* message\_id: UUID ของข้อความนี้  
* correlation\_id: request.message\_id  
* sent\_at: ISO-8601 datetime   
* trace\_id: uuid (optional)

  **Success Message Body**

  {

    "recommendation\_id": "82270dcf-41c2-49ce-b200-1d1b83603c68",

    "dispatch\_id": "DSP-1045",

    "team\_id": "TEAM-01",

    "estimated\_arrival\_time": "2025-06-01T11:05:00Z",

    "status": "DISPATCH\_CONFIRMED"

  }

  **Reject/Error Message Body**

  {

    "recommendation\_id": "82270dcf-41c2-49ce-b200-1d1b83603c68",

    "team\_id": "TEAM-01",

    "status": "DISPATCH\_REJECTED",

    "reason\_code": "TEAM\_UNAVAILABLE",

    "reason\_message": "Selected team is no longer available"

  }

  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| recommendation\_id | UUID | Y | อ้างอิง recommendation เดิม |
| dispatch\_id | string | Y (ถ้า success) | รหัสการ dispatch ที่สร้างโดย Dispatch Service |
| team\_id | string | Y | ทีมที่ถูกดำเนินการ |
| estimated\_arrival\_time | datetime | Y (ถ้า success) | เวลาถึงโดยประมาณ |
| status | enum | Y  | DISPATCH\_CONFIRMED / DISPATCH\_REJECTED |
| reason\_code | string | Y (ถ้า rejected) | machine-readable error |
| reason\_message | string | Y (ถ้า rejected) | human-readable explanation |

	**Validation Rules**

1. correlation\_id ต้องตรงกับ message\_id ของ request  
2. ถ้า status \= DISPATCH\_CONFIRMED ต้องมี dispatch\_id และ estimated\_arrival\_time  
3. ถ้า status \= DISPATCH\_REJECTED ต้องมี reason\_code และ reason\_message  
4. reasonCode ต้องเป็นค่าที่กำหนดล่วงหน้า เช่น:  
* TEAM\_UNAVAILABLE  
* TEAM\_ALREADY\_DISPATCHED  
* INCIDENT\_CANCELLED

	**Reliability & Delivery Guarantees**

* Delivery Model: At-least-once  
* Consumer ต้องรองรับ duplicate message  
* Producer ใช้ Outbox Pattern เพื่อป้องกัน lost message  
* Ordering guarantee ภายใน scope ของ recommendation\_id

	**Architectural Rationale**

* Recommendation Service ไม่ต้องรอ Dispatch Service แบบ synchronous  
* ลด coupling ระหว่าง domain  
* รองรับ scaling แยกอิสระ  
* รองรับ retry โดยไม่เกิด side effect (idempotent by message\_id)

# Service Data

# **Service Data**

# **1\) Recommendation Master Data  (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| recommendation\_id | uuid | Y (PK) | รหัส recommendation | b94cb0eb-b627-41b9-a009-ed777ab3db38 |
| request\_id | string | Y (reference only) | อ้างอิง rescue request | REQ-8812-9901 |
| incident\_id | uuid | Y (reference only) | อ้างอิง incident | e7fbc96c-24a6-49e5-95c7-1581f656de4b |
| recommendation\_status | enum | Y | GENERATED / ACCEPTED / SUPERSEDED / EXPIRED / DISPATCH\_CONFIRMED / DISPATCH\_FAILED | GENERATED |
| confidence\_score | Integer (1-5) | Y | ค่าความมั่นใจ | 4 |
| model\_version | string | Y | เวอร์ชันโมเดล | v1.2.0 |
| is\_force\_reevaluate | boolean | Y | สร้างจาก force reevaluate หรือไม่ | false |
| version | integer | Y | optimistic locking | 3 |
| accepted\_team\_id | string | N | ทีมที่ถูกเลือก | TEAM-01 |
| accepted\_by | string | N | dispatcher ผู้ยืนยัน | dispatcher-01 |
| accepted\_at | datetime | N | เวลาที่ยืนยัน | 2025-06-01T10:27:02Z |
| expires\_at | datetime | Y | เวลาหมดอายุ | 2025-06-01T10:27:02Z |
| created\_at | datetime | Y | เวลาสร้าง | 2025-06-01T10:27:02Z |
| updated\_at | datetime | Y | เวลาปรับปรุงล่าสุด | 2025-06-01T10:27:02Z |

# **2\) Ranked Team Snapshot (Immutable)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| ranked\_team\_id | uuid | Y (PK) | รหัสประจำรายการจัดอันดับทีม | 3fa85f64-5717-4562-b3fc-2c963f66afa6 |
| recommendation\_id | uuid | Y (FK) | อ้างอิงไปยัง recommendation หลักที่ระบบสร้างขึ้น | b94cb0eb-b627-41b9-a009-ed777ab3db38 |
| team\_id | string | Y | รหัสทีมกู้ภัยที่ถูกจัดอันดับ | team\_bangkok\_01 |
| team\_rank | integer | Y | ลำดับอันดับของทีม (1 \= ดีที่สุด) | 1 |
| total\_score | decimal(5,2) | Y | คะแนนรวมทั้งหมดหลังคำนวณ weighted score | 92.75 |
| specialization\_score | decimal(5,2) | Y | คะแนนด้านความเชี่ยวชาญของทีม | 30.00 |
| distance\_score | decimal(5,2) | Y | คะแนนด้านระยะทางจากจุดเกิดเหตุ | 25.50 |
| availability\_score | decimal(5,2) | Y | คะแนนด้านความพร้อมใช้งานของทีม | 20.00 |
| severity\_weight | decimal(5,2) | Y | ค่าน้ำหนักที่ใช้ตามระดับความรุนแรงของเหตุการณ์ | 1.20 |
| explanation | string | N | คำอธิบายเหตุผลที่ทีมนี้ได้อันดับดังกล่าว | Highest trauma specialization and closest distance. |
| created\_at | datetime | Y | วันที่และเวลาที่สร้าง snapshot นี้ | 2026-03-03T09:15:30Z |

# **3\) Dispatch Operational State (Async Feedback)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| recommendation\_id | uuid | Y (PK/FK) | อ้างอิง recommendation ที่เกี่ยวข้อง | b94cb0eb-b627-41b9-a009-ed777ab3db38 |
| dispatch\_id | string | N | รหัสการ dispatch จากระบบภายนอก | dispatch\_20260303\_01 |
| dispatch\_status | enum | Y (PENDING / CONFIRMED / REJECTED) | สถานะการตอบรับของทีม (`PENDING`, `CONFIRMED`, `REJECTED`) | CONFIRMED |
| estimated\_arrival\_time | datetime | Y | เวลาที่ทีมคาดว่าจะถึงจุดเกิดเหตุ | 2026-03-03T09:20:10Z |
| rejection\_reason\_code | string | Y | รหัสเหตุผลที่ปฏิเสธ (กรณี REJECTED) | NO\_AVAILABLE\_UNIT |
| rejection\_reason\_message | string | Y | ข้อความอธิบายเหตุผลการปฏิเสธ | All units currently assigned to other incidents. |
| last\_updated\_at | datetime | Y | เวลาที่มีการอัปเดตสถานะล่าสุด | 2026-03-03T09:20:10Z |

หมายเหตุ: rejection\_reason\_code และ rejection\_reason\_message ควร nullable ถ้า status ≠ REJECTED

# 

# **4\) Idempotency Record**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| idempotency\_key | uuid | Y (PK) | คีย์ที่ client ส่งมาเพื่อควบคุม idempotency | 8e2f8f84-7b2a-4bcb-a4b6-123456789abc |
| request\_hash | string | Y | ค่า hash ของ request payload เพื่อป้องกัน key reuse ผิด payload | a94a8fe5ccb19ba61c4c0873d391e987982fbbd3 |
| response\_payload | json | Y | response ที่เคยส่งกลับ client | {"recommendation\_id":"b94c...","status":"CREATED"} |
| response\_status\_code | integer | Y | HTTP status code ที่เคยตอบกลับ | 201 |
| created\_at | datetime | Y | เวลาที่บันทึก idempotency record | 2026-03-03T09:10:00Z |

# **5\) Outbox Event Table**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| event\_id | uuid | Y (PK/FK) | รหัส event | 5c3c3f0e-2d4e-4a8b-b9d2-987654321abc |
| aggregate\_id | uuid | Y (recommendation\_id) | อ้างอิง recommendation\_id ที่เป็น aggregate root | b94cb0eb-b627-41b9-a009-ed777ab3db38 |
| aggregate\_type | string | Y | ประเภท aggregate | recommendation |
| event\_type | string | Y | ประเภทของ event ที่เกิดขึ้น | recommendation\_created |
| payload | string | Y | ข้อมูล event ในรูปแบบ JSON string | {"recommendation\_id":"b94c...","top\_team\_id":"team\_bangkok\_01"} |
| is\_published | boolean | Y | ระบุว่า event ถูก publish แล้วหรือยัง | false |
| created\_at | datetime | Y | เวลาที่สร้าง event | 2026-03-03T09:15:40Z |
| published\_at | datetime | N | เวลาที่ publish สำเร็จ | 2026-03-03T09:15:40Z |

**Enum Definition**  
recommendation\_status

* GENERATED  
* ACCEPTED  
* SUPERSEDED  
* EXPIRED  
* DISPATCH\_CONFIRMED  
* DISPATCH\_FAILED

dispatch\_status

* PENDING  
* CONFIRMED  
* REJECTED