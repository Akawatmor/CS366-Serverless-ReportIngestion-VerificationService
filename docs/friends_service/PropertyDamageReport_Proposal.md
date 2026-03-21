# Service Overview

**ภาพรวมของบริการ (Service Overview)**

PropertyDamageReport Service

*Github repository https://github.com/natchanonsarasang/PropertyDamageReportService*

1. **Service Owner**

นาย ณัฐชนน สาระสังข์ รหัสนักศึกษา 6609611907 ภาคปกติ

2. **Service Purpose**

PropertyDamageReport Service เป็นบริการที่รับผิดชอบการรับและจัดเก็บรายงานความเสียหายต่อทรัพย์สินจากประชาชนในระหว่างหรือหลังเหตุการณ์ภัยพิบัติ โดยทำหน้าที่เป็นจุดศูนย์กลางในการรวบรวมข้อมูลความเสียหาย เพื่อให้หน่วยงานรัฐสามารถตรวจสอบ จัดลำดับความสำคัญ และดำเนินการช่วยเหลือได้อย่างเป็นระบบ

3. **Pain Point ที่แก้ไข**

ในสถานการณ์ภัยพิบัติ ประชาชนมักไม่รู้ว่าจะรายงานความเสียหายที่ใด ข้อมูลกระจัดกระจาย และไม่สามารถติดตามสถานะการดำเนินการของหน่วยงานได้ ส่งผลให้การช่วยเหลือล่าช้า บริการนี้จึงถูกออกแบบมาเพื่อให้มีระบบรายงานความเสียหายที่เป็นมาตรฐาน ตรวจสอบได้ และติดตามผลได้

**3️. Target Users**  
ประชาชนผู้ได้รับผลกระทบจากภัยพิบัติ (Citizen)  
ระบบของหน่วยงานรัฐที่มีหน้าที่รับผิดชอบเรื่องที่เกี่ยวข้อง

**4️. Service Boundary**

* In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)  
  * รับและจัดเก็บรายงานความเสียหายจากประชาชน  
  * จัดการสถานะของรายงาน (workflow ของ report)  
  * ตรวจจับรายงานซ้ำ (duplicate detection)  
  * ส่งต่อรายงานไปยังหน่วยงานที่เกี่ยวข้อง  
  * ให้ประชาชนสามารถติดตามสถานะรายงานของตนได้

* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
  * การตรวจสอบข้อเท็จจริงของความเสียหายภาคสนาม  
  * การประเมินมูลค่าความเสียหาย  
  * การวางแผนหรือดำเนินการซ่อมแซม  
  * การจัดสรรงบประมาณหรือการอนุมัติช่วยเหลือ  
  * การติดตามขั้นตอนการดำเนินงานภายในของหน่วยงานหลังจากรับเรื่องแล้ว

**5️. Autonomy / Decision Logic**  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การรับหรือปฏิเสธรายงานที่ข้อมูลไม่ครบถ้วน  
* การตรวจจับรายงานซ้ำภายในช่วงเวลาที่กำหนด  
* การกำหนดสถานะเริ่มต้นของรายงาน (เช่น new)  
* การเปลี่ยนสถานะเมื่อมีการส่งต่อไปยังหน่วยงานที่เกี่ยวข้อง (เช่น forwarded)

การตัดสินใจอิงจาก:

* incident\_id ของเหตุการณ์  
* location ของรายงาน  
* contact\_phone ของผู้แจ้ง  
* timestamp ของการส่งรายงาน  
* business rules สำหรับ validation และ duplicate detection

บริการสามารถตัดสินใจได้เองภายใต้ business rules ที่กำหนด โดยไม่ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ โดยบทบาทของบริการคือการรับเรื่อง ตรวจสอบเบื้องต้น และส่งต่อข้อมูลเท่านั้น ไม่เกี่ยวข้องกับการตัดสินใจหรือการดำเนินงานของหน่วยงานหลังจากรับเรื่องแล้ว

**6️. Owned Data**

* Damage Report Master Data  
  ใช้เก็บข้อมูลหลักของรายงานความเสียหายที่ประชาชนส่งเข้ามา เช่น ประเภทความเสียหาย รายละเอียด สถานที่เกิดเหตุ ข้อมูลติดต่อ และหลักฐานประกอบ รวมถึงสถานะภาพรวมของรายงาน ข้อมูลชุดนี้เป็นแกนหลักของ domain และถูกสร้างจากการใช้งานของบริการโดยตรง บริการนี้เป็นผู้กำหนด lifecycle ของรายงานตั้งแต่สร้างจนสิ้นสุดกระบวนการ จึงต้องควบคุมข้อมูลชุดนี้เองทั้งหมด  
    
* EventPublishLog data  
  ใช้สำหรับบันทึกข้อมูลการ publish event ที่ระบบส่งออกไปยัง message broker (SNS Topic) เพื่อรองรับการทำงานแบบ asynchronous communication ทุกครั้งที่ระบบ publish event เพื่อใช้สำหรับ ตรวจสอบการทำงานของระบบ (debugging) การติดตาม event ที่ถูกส่งออกไป หรือใช้ เมื่อเกิดความผิดพลาดในระบบ asynchronous messaging  
    
* AgencyResponses data  
  ใช้เก็บข้อมูลการตอบกลับจากหน่วยงานที่ได้รับรายงานความเสียหายผ่านระบบ messaging เนื่องจากหนึ่งรายงานอาจถูกพิจารณาโดยหลายหน่วยงาน ทำให้อาจมีการตอบกลับหลายรายการสำหรับ report เดียวกัน ตารางนี้จึงถูกออกแบบเพื่อเก็บ response ของแต่ละหน่วยงานแยกจากกัน ข้อมูลที่บันทึกประกอบด้วยชื่อหน่วยงาน สถานะการตอบรับ รวมถึงเหตุผลในการปฏิเสธในกรณีที่หน่วยงานไม่รับเรื่องรายงานนั้นๆ  
    
    
  


**7️. Linked Data (Reference Only)**  
**บริการนี้มีการอ้างอิงข้อมูลจากบริการอื่นในระบบภัยพิบัติ แต่ไม่เก็บสำเนาข้อมูลเหล่านั้นอย่างถาวร ได้แก่**	

* Incident Service  
  ใช้ incidentId เพื่อยืนยันว่ารายงานเชื่อมโยงกับเหตุการณ์ภัยพิบัติที่มีอยู่จริง  
  บริการนี้ตรวจสอบเพียงการมีอยู่ของเหตุการณ์ก่อนรับรายงาน แต่ไม่จัดเก็บข้อมูลเหตุการณ์เอง  
* Agency / Organization Service (ถ้ามี)  
  ใช้ข้อมูลหน่วยงานเพื่อระบุปลายทางการส่งต่อรายงาน  
  บริการนี้บันทึกเพียงชื่อหรือรหัสหน่วยงานที่ส่งต่อ แต่ไม่จัดเก็บรายละเอียดของหน่วยงาน

**8\. Non-Functional Requirements**

* ระบบต้องไม่ crash เมื่อได้รับ request ที่ข้อมูลไม่ถูกต้อง และต้องตอบกลับด้วย error message ที่ชัดเจน  
* ระบบต้องรองรับการส่งข้อมูลซ้ำแบบ **at-least-once delivery** ได้ โดยต้องมีการตรวจจับ duplicate report จาก incidentId, location และ contactPhone ภายในช่วงเวลาที่กำหนด  
* API ต้องรองรับ **idempotency** เพื่อป้องกันการสร้างรายงานซ้ำจากการกดส่งหลายครั้งหรืออินเทอร์เน็ตไม่เสถียร  
* ข้อมูลรายงานและข้อมูลติดต่อประชาชนต้องถูกจัดเก็บอย่างปลอดภัย และปฏิบัติตามหลัก **data privacy protection**  
* หากบริการภายนอกที่ใช้ส่งต่อรายงานไม่ตอบสนอง ระบบต้องยังสามารถรับรายงานไว้ก่อนได้ (graceful degradation) และ retry การส่งต่อภายหลัง


# Sync Contract

**Synchronous Function Contract**  
**Base URL:** https://zj5oc3gb5l.execute-api.us-east-1.amazonaws.com/v1

# **API Contract \#1: Create Damage Report**

### **ข้อมูลทั่วไป**

* **Name:** Create damage report  
* **Method:** POST  
* **Path:** /damage-reports  
* **Type:** Synchronous

### **คำอธิบาย**

### ใช้สำหรับให้ประชาชนส่งรายงานความเสียหายเข้าสู่ระบบ เมื่อบันทึกสำเร็จ ระบบจะสร้างข้อมูลใน Damage Report Master Data และหลังจากนั้นจะมีการ publish event แบบ asynchronous เพื่อส่งต่อหน่วยงานต่างๆที่เกี่ยวข้อง

### **Request**

**Path/Query Params**

* ไม่มี

  **Headers**

* Content-Type: application/json

  **Body:**

  {

    "incidentId": "INC-2026-01",

    "damageType": "building",

    "ownershipType": "personal",

    "description": "Roof damaged after storm",

    "location": "Rangsit, Pathum Thani",

    "reporterName": "Somchai Jaidee",

    "contactPhone": "0812345678",

    "evidenceUrl": "https://img.com/1.jpg"

  }

  **Validation Rules**

* incidentId ต้องมี  
* damageType ต้องเป็น (building / vehicle / infrastructure / utility / other)  
* ownershipType ต้องเป็น (personal / public)  
* description ต้องมี  
* location ต้องมี  
* reporterName ต้องมี  
* contactPhone ต้องมี  
* evidenceUrl optional แต่ถ้ามีต้องเป็น URL

### **Response**

**Success: 201 Created**

{

  "reportId": "REP-001",

  "overallStatus": "new",

  "createdAt": "2026-02-21T10:00:00Z"

}

**Error: 400 Bad Request**

{

  "error": {

    "code": "VALIDATION\_ERROR",

    "message": "missing required field",

    "traceId": "uuid"

  }

}

### **Dependency / Reliability**

* มี duplicate detection เพื่อให้ทำงานแบบ idempotent   
* ไม่จำเป็นต้องเรียก service อื่นแบบ synchronous  
* ไม่มี synchronous dependency  
* การส่งต่อหน่วยงานทำผ่าน asynchronous event  
* Timeout ≤ 30s

# **API Contract \#2: Get Damage Report by ID**

### **ข้อมูลทั่วไป**

* **Name:** Get damage report detail  
* **Method:** GET  
* **Path:** /damage-reports/{reportId}  
* **Type:** Synchronous

### 

### **คำอธิบาย**

ใช้ดึงรายละเอียดรายงานความเสียหายตาม reportId พร้อมสถานะปัจจุบัน

### **Request**

**Path/Query Param**

* reportId (string, required)

  **Headers**

* Accept: application/json

  **Body**

* ไม่มี

### **Response**

**Success: 200 OK**

{

"reportId": "REP-1773151475212",

"incidentId": "INC-2026-01",

"damageType": "building",

"ownershipType": "personal",

"description": "Roof damaged after storm",

"location": "Rangsit, Pathum Thani",

"reporterName": "Somchai Jaidee",

"contactPhone": "0812345678",

"evidenceUrl": "https://img.com/1.jpg",

"overallStatus": "acknowledged",

"assignedAgency": "PathumThaniLocalAuthority",

"createdAt": "2026-02-21T10:00:00Z",

"updatedAt": "2026-02-21T10:10:00Z"

}

**Error: 400 Bad Request**

{

"error": {

"code": "INVALID\_ID\_FORMAT",

"message": "invalid reportId format",

"traceId": "uuid"

}

}

**Error: 404 Not Found**

{  
"error": {  
"code": "REPORT\_NOT\_FOUND",  
"message": "reportId not found",  
"traceId": "uuid"  
}  
}

### 

### **Dependency / Reliability**

* เป็น read-only operation   
* ไม่มี synchronous dependency กับ service อื่น  
* ใช้ database read เพียงอย่างเดียว  
* Timeout ≤ 30s  
* รองรับ retry ได้โดยไม่มี side effect


# **API Contract \#3: List Damage Reports**

### **ข้อมูลทั่วไป**

* **Name:** List damage reports  
* **Method:** GET  
* **Path:** /damage-reports  
* **Type:** Synchronous

### 

### **คำอธิบาย**

ใช้สำหรับให้ staff ดึงรายการรายงานความเสียหายทั้งหมดในระบบ สามารถ filter ตาม `overallStatus` ได้

### **Request**

**Path/Query Param**

* incidentId (string, required)

* overallStatus (optional → new / forwarded / acknowledged)

  **Headers**

* Accept: application/json

  **Body** 

* ไม่มี


  

### **Response**

**Success: 200 OK**

{

  "items": \[

    {

      "reportId": "REP-1773151475212",

      "incidentId": "INC-2026-01",

      "description": "Roof damaged after storm",

      "contactPhone": "0812345678",

      "location": "Rangsit, Pathum Thani",

      "overallStatus": "forwarded",

      "assignedAgency": none,

      "createdAt": "2026-02-21T10:00:00Z"

    },

    {

      "reportId": "REP-1773152000000",

      "incidentId": "INC-2026-01",

      "description": "Flooded road",

      "contactPhone": "0891234567",

      "location": "Khlong Luang",

      "overallStatus": "acknowledged",

      "assignedAgency": "DisasterManagementService",

      "createdAt": "2026-02-21T11:00:00Z"

    }

  \]

}

### **Dependency / Reliability**

* เป็น read-only operation (idempotent โดยธรรมชาติ)  
* ไม่เรียก service ภายนอก  
* query จาก DynamoDB  
* Timeout ≤ 30s

# **API Contract \#4: Agency Response**

### **ข้อมูลทั่วไป**

* **Name:** Agency respond to damage report  
* **Method:** POST  
* **Path:** /agency-responses  
* **Type:** Synchronous

### 

### **คำอธิบาย**

ใช้สำหรับให้หน่วยงานตอบรับหรือปฏิเสธรายงานความเสียหาย ถ้าหน่วยงานตอบ accepted ระบบจะ  
Update overallStatus เป็น acknowledge และ publish event เพื่อแจ้งให้หน่วยงานอื่นรู้ว่ารายงานนี้มีคนรับเรื่องแล้ว

### **Request**

**Path/Query Param**

* ไม่มี

  **Headers**

* Accept: application/json

  **Body** 

  {

  "reportId": "REP-1773151475212",

  "agencyName": "PathumThaniLocalAuthority",

  "status": "accepted"

  }

  validation Rules

* `reportId` ต้องมีอยู่ใน DamageReports table  
* `agencyName` ต้องไม่ว่าง  
* status ต้องเป็นaccepted หรือ rejected  
* rejectReasonCode เป็น optional แต่ควรมีเมื่อ status \= rejected


### **Response**

**Success: 200 OK Agency Service accept**

{

"message": "Agency response recorded",

"responseId": "RESP-1773152000000",

"reportId": "REP-1773151475212",

"status": "accepted"

}

**Success: 200 OK Agency Service reject**

{

  "message": "Agency response recorded",

  "responseId": "RESP-1773153000000",

  "reportId": "REP-1773151475212",

  "status": "rejected"

}

**ตัวอย่าง request ที่ปฏิเสธ**

{

  "reportId": "REP-1773151475212",

  "agencyName": "DisasterManagementService",

  "status": "rejected",

  "rejectReasonCode": "OUT\_OF\_JURISDICTION"

}

**Error: 400 Bad Request**

{

"error": {

"code": "VALIDATION\_ERROR",

"message": "missing required field",

"traceId": "uuid"

}

}

**Error: 400 Invalid Status**

{

  "error": {

    "code": "INVALID\_STATUS",

    "message": "status must be accepted or rejected",

    "traceId": "uuid"

  }

}

**Dependency / Reliability**

1. เป็น synchronous API  
2. ไม่มี synchronous dependency กับ service อื่น  
3. ใช้ DynamoDB write

# Async Contract

**Asynchronous Function Contract**

## **Message Contract \#1: DamageReportForwarded**

### **ข้อมูลทั่วไป** 

* **Message Name:** DamageReportForwarded  
* **Interaction Style:** Event-driven / Publish–Subscribe   
* **Message Broker:** Amazon SNS Topic → Amazon SQS  
* **Producer:** PropertyDamageReport Service  
* **Consumer:** Agency Services (เช่น LocalAuthorityService, DisasterManagementService)  
* **Channel/Topic:** damage-report.forwarded.v1  
* **Version:** v1

### **คำอธิบาย**

### Event นี้จะถูก publish หลังจากระบบบันทึก Report ที่ถูกสร้างจากประชาชน เขียนลงฐานข้อมูลเรียบร้อยแล้ว โดย PropertyDamageReport Service จะส่ง event ไปยัง SNS Topic เพื่อกระจายข้อมูลรายงานความเสียหายไปยังหน่วยงานที่เกี่ยวข้องผ่าน SQS Queue แบบ asynchronous event-driven communication หลังจาก publish event สำเร็จ ระบบจะอัปเดตสถานะของรายงานในฐานข้อมูล เพื่อระบุว่ารายงานได้ถูกส่งต่อไปยังหน่วยงานแล้ว

### **Request (Event Publish)**

Event message จะถูก publish ไปยัง SNS Topic ในรูปแบบ JSON ดังนี้

**Message Body**  
{  
"eventType": "DamageReportForwarded",  
"eventId": "a3d9c3e2-42e1-4e6e-b0d1-7f0cfa55b2d1",  
"occurredAt": "2026-02-21T10:00:00Z",  
"data": {  
"reportId": "REP-001",  
"incidentId": "INC-2026-01",  
"damageType": "building",  
"ownershipType": "personal",  
"description": "Roof damaged after storm",  
"location": "Rangsit, Pathum Thani",  
"reporterName": "Somchai Jaidee",  
"contactPhone": "0812345678",  
"evidenceUrl": "https://img.com/1.jpg",  
"createdAt": "2026-02-21T10:00:00Z"  
}  
}  
**Field Definition (Body)**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| eventType | string | Y | ชนิดของ event |
| eventId | UUID | Y | รหัส event |
| occurredAt | datetime | Y | เวลาที่ event ถูกสร้าง |
| data | object | Y | ข้อมูลของ damage report |

**Event Payload (data)**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| reportId | string | Y | รหัสรายงานความเสียหาย |
| incidentId | string | Y | รหัสเหตุการณ์ที่เกี่ยวข้อง |
| damageType | enum | Y | ประเภทความเสียหาย |
| ownershipType | enum | Y | ประเภทความเป็นเจ้าของทรัพย์สิน (personal / public) |
| location | string | Y | ตำแหน่งที่เกิดความเสียหาย |
| description | string | Y | รายละเอียดความเสียหาย |
| reporterName | string | Y | ชื่อผู้ยื่นคำร้อง |
| contactPhone | string | Y | เบอร์ติดต่อผู้แจ้ง |
| evidenceUrl | string | N | ลิงก์รูปหลักฐาน |
| createdAt | datetime | Y | เวลาที่สร้างรายงาน |

**Validation Rules**

	1\. reportId ต้องมีอยู่จริงใน Master Data และไม่ว่าง

2\. incidentId ต้องไม่ว่าง

3\. location ต้องไม่ว่าง

4\. eventId ต้องไม่ซ้ำ (idempotency check)

**Response**

Event นี้เป็น asynchronous communication จึงไม่มี synchronous response กลับมายัง producer หลังจาก publish event ไปยัง SNS Topic สำเร็จ ระบบจะถือว่าการส่งต่อรายงานเสร็จสิ้น และไม่รอผลลัพธ์จาก consumer services การตอบกลับจากหน่วยงานจะเกิดขึ้นผ่าน API POST /v1/agency-responses ซึ่งจะถูกจัดเก็บใน AgencyResponses table

## 

## 

## 

## 

## 

## 

## 

## 

## 

## 

## 

## 

## 

## 

## **Message Contract \#2: DamageReportAcknowledged**

### **ข้อมูลทั่วไป** 

* **Message Name:** DamageReportAcknowledged  
* **Interaction Style:** Event-driven / Publish–Subscribe  
* **Message Broker:** Amazon SNS Topic → Amazon SQS  
* **Producer:** PropertyDamageReport Service  
* **Consumer:** Agency Services (เช่น LocalAuthorityService, DisasterManagementService)  
* **Channel/Topic:** damage-report.acknowledged.v1  
* **Version:** v1

### **คำอธิบาย**

### Event นี้จะถูก publish เมื่อมีหน่วยงานใดหน่วยงานหนึ่ง ตอบรับรายงานความเสียหาย (accept) ผ่าน synchronous API POST /v1/agency-responsesหลังจากระบบบันทึกข้อมูลการตอบรับลงใน AgencyResponses table และอัปเดตสถานะของรายงานใน DamageReports table ระบบจะ publish event นี้ไปยัง SNS Topic เพื่อแจ้งให้ consumer services ทุกตัวทราบว่า รายงานนี้มีหน่วยงานรับเรื่องแล้ว และไม่จำเป็นต้องพิจารณาเพิ่มเติม

### **Request Event**  

Event message ถูกส่งในรูปแบบ JSON payload ดังนี้

**Message Body**

{

  "eventType": "DamageReportAcknowledged",

  "eventId": "c1c9fdd1-0f21-4f03-9f3a-9c0c82c7d211",

  "occurredAt": "2026-02-21T10:10:00Z",

  "data": {

    "reportId": "REP-001",

    "incidentId": "INC-2026-01",

    "assignedAgency": "DisasterManagementService",

    "acknowledgedAt": "2026-02-21T10:10:00Z"

  }

}

**Field Definition (Body)**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| eventType | string | Y | ชนิดของ event |
| eventId | UUID | Y | รหัส event |
| occurredAt | datetime | Y | เวลาที่ event ถูกสร้าง |
| data | object | Y | ข้อมูลของ damage report |

	  
**Event Payload (data)**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| reportId | string | Y | รหัสรายงานความเสียหาย |
| incidentId | string | Y | รหัสเหตุการณ์ภัยพิบัติ |
| assignedAgency | string | Y | หน่วยงานที่ตอบรับคำขอ |
| acknowledgedAt | datetime | Y | เวลาที่หน่วยงานตอบรับ |

**Validation Rules (Response)**  
1 `reportId` ต้องมีอยู่จริงใน DamageReports table  
2 `assignedAgency` ต้องไม่ว่าง  
3 `eventId` ต้องไม่ซ้ำ (idempotency check)

**Response**

	Event นี้เป็นการสื่อสารแบบ asynchronous event-driven communication จึงไม่มี synchronous response จาก consumer services Consumer services ที่ subscribe queue จะได้รับ eventเพื่อให้ service ทราบว่า report นี้มี agency รับแล้วและสามารถ ยกเลิกการพิจารณาหรือ ignore message ที่เกี่ยวข้องกับ report นี้ได้

# Service Data

# **Service Data**

# **1\) Damage Report Master Data (Owned by this service)**

# 

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| reportId | string | Y (PK) | รหัสรายงานความเสียหาย | REP-001 |
| incidentId | string | Y | รหัสเหตุการณ์ภัยพิบัติที่เกี่ยวข้อง | INC-2026-01 |
| damageType | enum | Y | ประเภทความเสียหาย (building / vehicle / infrastructure / utility / other) | building |
| ownershipType | enum | Y | ประเภททรัพย์สิน (personal / public) | personal |
| description | string | Y | รายละเอียดความเสียหาย | Roof damaged after storm |
| location | string | Y | พื้นที่ที่เกิดเหตุ | Rangsit, Pathum Thani |
| reporterName | string | Y | ชื่อผู้ยื่นคำร้อง | Somchai Jaidee |
| contactPhone | string | Y | เบอร์ติดต่อผู้แจ้ง | 0812345678 |
| evidenceUrl | string | N | ลิงก์รูปหลักฐาน | https://img.com/1.jpg |
| overallStatus | enum | Y | new / forwarded / acknowledged | forwarded |
| assignedAgency | string | N | หน่วยงานที่รับเรื่อง | DisasterManagementService |
| createdAt | datetime | Y | เวลาที่สร้างรายงาน | 2026-02-21T10:00:00Z |
| updatedAt | datetime | Y | เวลาที่แก้ไขล่าสุด | 2026-02-21T10:02:00Z |

# **2\) EventPublishLog Table (Owned by this service)**

ใช้บันทึกว่า **ระบบ publish event ไป SNS แล้ว** เพื่อใช้สำหรับ debugging หรือ event tracing

# 

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| eventId | string | Y (PK) | UUID ของ event | uuid-1234-abcd |
| reportId | string | Y | report ที่เกี่ยวข้อง | REP-001 |
| eventType | string | Y | ชื่อ event | DamageReportForwarded |
| topicName | string | Y | SNS topic | damage-report.forwarded.v1 |
| messageId | string | Y | message id จาก SNS | a9f23c88-9b21-4eab |
| publishedAt | datetime | Y | เวลาที่ publish | 2026-02-21T10:03:00Z |
| createdAt | datetime | Y | เวลาที่บันทึก log | 2026-02-21T10:03:00Z |

# 

# **3\) AgencyResponses Table**

เก็บ **การตอบกลับจาก agency** เพราะหลาย agency อาจตอบกลับมา

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| responseId | string | Y (PK) | รหัส response | RESP-001 |
| reportId | string | Y | report ที่เกี่ยวข้อง | REP-001 |
| agencyName | string | Y | ชื่อหน่วยงาน | DisasterManagementService |
| status | enum | Y | accepted / rejected | accepted |
| rejectReasonCode | string | N | เหตุผล reject | Out of scope |
| respondedAt | datetime | Y | เวลาที่หน่วยงานตอบ | 2026-02-21T10:05:00Z |
| createdAt | datetime | Y | เวลาบันทึก record | 2026-02-21T10:05:00Z |

