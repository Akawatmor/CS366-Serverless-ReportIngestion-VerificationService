# Service Overview

ภาพรวมของบริการ (Service Overview)  
Donation Tracking Service

Github Repository : [https://github.com/Toninwza/donation-tracking-service](https://github.com/Toninwza/donation-tracking-service)

1. Service Owner

นายกีรติกร บุญเจริญ รหัสนักศึกษา 6609611774

2. Service Purpose

Donation Tracking Service เป็นบริการที่รับผิดชอบการจัดการและบันทึกวงจรชีวิต (Lifecycle) ของชุดสิ่งของบริจาค ตั้งแต่การลงทะเบียนรับเข้าจนถึงการส่งมอบในพื้นที่ภัยพิบัติ โดยทำหน้าที่เป็นแหล่งข้อมูลอ้างอิงสถานะที่ผ่านการตรวจสอบแล้ว เพื่อสร้างความเชื่อมั่นให้กับสาธารณชนและผู้เกี่ยวข้องในระบบตอบสนองภัยพิบัติ 

3. Pain Point ที่แก้ไข

ในสถานการณ์ภัยพิบัติ ผู้บริจาค มักขาดความมั่นใจและความชัดเจนว่าสิ่งของที่ตนเองบริจาคไปนั้นถูกนำไปใช้จริงหรือไม่ หรือติดค้างอยู่ที่ส่วนไหน บริการนี้จึงเข้ามาแก้ปัญหาการขาดความโปร่งใส โดยการรวมศูนย์ข้อมูลสถานะสิ่งของและเปิดให้ตรวจสอบได้แบบ Real-time เพื่อลดความกังวลและป้องกันการทุจริตหรือการจัดการที่ผิดพลาด

3️. Target Users

Donators (Public/Organization): สำหรับติดตามสถานะสิ่งของที่บริจาค 

4️. Service Boundary

* In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)  
  * การบันทึกและจัดการข้อมูลชุดสิ่งของบริจาค (Donation Batch Master Data)  
  * การควบคุมสถานะและ Milestones ของการบริจาค (Status State Machine)  
  * การออกรหัสติดตาม (Tracking ID) สำหรับแต่ละการบริจาค  
  * การตรวจสอบสิทธิ์ของผู้ใช้งานที่จะเข้ามาอัปเดตสถานะสิ่งของ

* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
  * การจับคู่ผู้บริจาคกับผู้รับโดยตรง (P2P Matching)  
  * การบริหารจัดการคลังสินค้าเชิงลึก (Warehouse Management System)  
      
      
    

5️. Autonomy / Decision Logic  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การยืนยันหรือปฏิเสธการลงทะเบียนรับบริจาคใหม่  
* การเปลี่ยนผ่านสถานะ (State Transition) เช่น จะไม่อนุญาตให้ข้ามจาก registered ไป arrived\_at\_zone โดยไม่ผ่าน dispatched  
* การตรวจสอบความถูกต้องของบทบาทผู้ใช้ (Role-based access) ในการอัปเดตแต่ละขั้นตอน

การตัดสินใจอิงจาก:

* Incident Status: ตรวจสอบจาก Central Schema ว่าเหตุการณ์ยังไม่ปิดตัวลง  
* Current Milestone: ลำดับสถานะปัจจุบันของวัตถุนั้นๆ  
* Role Permission: บทบาทของหน่วยงานที่ร้องขออัปเดตสถานะ

บริการสามารถตัดสินใจได้เองภายใต้ business rules ที่กำหนด โดยไม่ต้องรอ/ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ

6️. Owned Data

* Donation Batch Records: ข้อมูลหลักของสิ่งของบริจาค เช่น item\_category, quantity และ tracking\_id เพราะเป็นข้อมูลเฉพาะของ Domain การบริจาค  
* Milestone History: ประวัติการเปลี่ยนสถานะและ Timestamp เพื่อใช้ในการตรวจสอบย้อนหลัง

7️. Linked Data (Reference Only)

* incident\_id: อ้างอิงจาก Central Incident Schema เพื่อเชื่อมโยงว่าของสิ่งนี้ใช้สำหรับเหตุการณ์ใด 

8\. Non-Functional Requirements

Reliability & Failure Handling (การจัดการเมื่อระบบอื่นล่ม):

* เนื่องจากบริการนี้ต้องตรวจสอบสถานะจาก Incident Service ทุกครั้งก่อนสร้างรายการ หาก Incident Service ไม่ตอบสนอง (Timeout) ระบบจะทำการ Retry 1 ครั้ง พร้อมกลไก Backoff  
* หาก Retry แล้วยังไม่สำเร็จ ระบบจะตอบกลับ REJECTED พร้อมระบุ reasonCode ว่าไม่สามารถติดต่อระบบตรวจสอบเหตุการณ์ได้ เพื่อป้องกันการสร้างข้อมูลที่ผิดพลาด	

Security:

* API ที่เป็นแบบ Synchronous (เช่น การอัปเดตสถานะโดยเจ้าหน้าที่) ต้องมีการตรวจสอบสิทธิ์ (Authentication) และสิทธิ์ตามบทบาท (Role-based access) อย่างเข้มงวด

 	Idempotency (การป้องกันรายการซ้ำ):

* ระบบต้องใช้รหัสที่ส่งมาจากฝั่งผู้ใช้ (เช่น messageId หรือรหัสอ้างอิง) เพื่อตรวจสอบก่อนบันทึกลง Database เพื่อให้มั่นใจว่าหากผู้ใช้ส่งคำขอเดิมซ้ำ (เช่น เพราะเน็ตช้าแล้วกดรัวๆ) ระบบจะประมวลผลให้เพียงครั้งเดียวเท่านั้น


# Sync Contract

Synchronous Function Contract  
Base URL:

### **API Contract \#1: Create Donation Record**

ข้อมูลทั่วไป

* Name: Create new donation record  
* Method: POST  
* Path: /donations  
* Type: Synchronous

คำอธิบาย ใช้สำหรับลงทะเบียนรับสิ่งของบริจาคเข้าสู่ระบบ โดยจะมีการตรวจสอบสถานะของเหตุการณ์ภัยพิบัติก่อนบันทึกข้อมูล

Request

* Headers  
  * Content-Type: application/json  
  * Authorization: Bearer \<token\> (สำหรับเจ้าหน้าที่รับของ)  
* Body  
  JSON

  {

    "incident\_id": "8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10",

    "item\_category": "FOOD\_AND\_WATER",

    "total\_quantity": 100,

    "unit": "pack"

  }


* Validation Rules  
  1. incident\_id ต้องไม่ว่างและเป็นรูปแบบ UUID  
  2. total\_quantity ต้องเป็นตัวเลขที่มากกว่า 0  
  3. item\_category ต้องเป็นค่าที่กำหนดใน Enum เท่านั้น

Response

* Success: 201 Created  
  JSON

  {

    "donation\_id": "don-99001",

    "batch\_id": "batch-xyz",

    "current\_milestone": "registered",

    "created\_at": "2026-03-03T14:00:00Z"

  }


* Error: 400 Bad Request (กรณี Incident ถูกปิดไปแล้ว หรือข้อมูลไม่ถูกต้อง)  
  JSON

  {

    "error": {

      "code": "INCIDENT\_CLOSED",

      "message": "Cannot create donation for a closed incident",

      "traceId": "uuid-12345"

    }

  }


Dependency / Reliability

* เรียก Service อื่น: เรียก Incident Service (GET /incidents/{id}) เพื่อเช็คสถานะ  
* Reliability: หาก Incident Service ล่ม จะทำการ Retry 1 ครั้ง หากยังล้มเหลวจะตอบกลับ Error  
* Timeout: 5 วินาที


  


  


**API Contract \#2: Update Donation Status**  
ข้อมูลทั่วไป

* Name: Update donation milestone  
* Method: PATCH  
* Path: /donations/{donation\_id}  
* Type: Synchronous

คำอธิบาย ใช้สำหรับอัปเดตสถานะ (Milestone) ของชุดสิ่งของบริจาคเมื่อมีการเคลื่อนย้ายหรือส่งมอบถึงพื้นที่

Request

* Path Param  
  * donation\_id (string, required): รหัสการบริจาค  
* Headers  
  * Content-Type: application/json  
  * Authorization: Bearer \<token\>  
* Body  
  JSON

  {

    "milestone": "arrived\_at\_zone",

    "updated\_by\_role": "field\_unit"

  }


* Validation Rules  
  1. milestone ต้องเป็นหนึ่งในค่า: registered, received\_at\_hub, dispatched\_to\_zone, arrived\_at\_zone, confirmed\_by\_field\_unit  
  2. updated\_by\_role ต้องไม่เป็นค่าว่าง

Response

* Success: 200 OK  
  JSON

  {

    "batch\_id": "batch-xyz",

    "current\_milestone": "arrived\_at\_zone",

    "milestone\_updated\_at": "2026-03-03T15:30:00Z"

  }


* Error: 404 Not Found (ไม่พบรหัสการบริจาค)  
  JSON

  {

    "error": {

      "code": "NOT\_FOUND",

      "message": "Donation ID not found",

      "traceId": "uuid-67890"

    }

  }


Dependency / Reliability

* เรียก Service อื่น: ไม่เรียก  
* Idempotent: เป็น Idempotent Update (การส่งสถานะเดิมซ้ำจะไม่ทำให้ข้อมูลผิดเพี้ยน)  
* Timeout: 10 วินาที


  


### 

# Async Contract

## **Asynchronous Function Contract**

**Message Contract \#1: Donation Status Updated**

### ข้อมูลทั่วไป

* Message Name: DonationStatusUpdated  
* Interaction Style: Event-driven (Publish-Subscribe)  
* Producer: Donation Tracking Service  
* Consumer: Notification Service, Dashboard Service, Logistics Optimizer  
* Channel/Queue: donation.status.events.v1  
* Version: v1

  ### คำอธิบาย

ใช้สำหรับประกาศเหตุการณ์ (Broadcast) เมื่อชุดสิ่งของบริจาคมีการเปลี่ยนสถานะ Milestone (เช่น จาก dispatched\_to\_zone เป็น arrived\_at\_zone) เพื่อให้ระบบอื่นสามารถนำข้อมูลไปประมวลผลต่อได้ทันทีโดยไม่ต้องรอการเรียกแบบ Synchronous

### 

### **Request (Event Structure)**

**Message Headers**

* messageType: DonationStatusUpdated  
* messageId: UUID (ใช้เป็น Idempotency Key สำหรับผู้รับเพื่อป้องกันการประมวลผลซ้ำ)  
* sentAt: ISO-8601 datetime  
* traceId: string/uuid (สำหรับติดตาม Workflow ข้ามระบบ)

**Message Body**

JSON

{

  "donation\_id": "550e8400-e29b-41d4-a716-446655440000",

  "incident\_id": "8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10",

  "batch\_id": "abc123-def456-ghi789",

  "item\_category": "FOOD\_AND\_WATER",

  "item\_description": "น้ำดื่มสะอาดขนาด 1.5 ลิตร",

  "total\_quantity": 100.0,

  "unit": "pack",

  "current\_milestone": "arrived\_at\_zone",

  "milestone\_updated\_at": "2026-03-03T15:30:00Z",

  "last\_updated\_by\_role": "field\_unit",

  "created\_at": "2026-03-03T10:00:00Z"

}

**Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| Field | Type | Required | Description |
| donation\_id | uuid | Y | รหัสการบริจาคที่เป็น Primary Key |
| incident\_id | uuid | Y | อ้างอิงเหตุการณ์จาก Central Incident Schema |
| batch\_id | uuid | Y | รหัสชุดสิ่งของบริจาค |
| item\_category | enum | Y | หมวดหมู่สิ่งของ (เช่น FOOD\_AND\_WATER, MEDICINE) |
| item\_description | string | Y | รายละเอียดสิ่งของบริจาค |
| total\_quantity | float | Y | จำนวนสิ่งของทั้งหมด (ต้อง \> 0\) |
| unit | string | Y | หน่วยนับของสิ่งของ |
| current\_milestone | enum | Y | สถานะล่าสุดตาม Flow 5 ขั้นตอน |
| milestone\_updated\_at | datetime | Y | วันเวลาที่มีการอัปเดตสถานะล่าสุด |
| last\_updated\_by\_role | string | Y | บทบาทของผู้ที่ทำการอัปเดตข้อมูล |
| created\_at | datetime | Y | วันเวลาที่เริ่มสร้างรายการบริจาค |

**Validation Rules**

1. incident\_id ต้องเป็น UUID ที่ถูกต้องและแยกจากข้อมูลภายในของ Service อย่างชัดเจน  
2. total\_quantity ต้องเป็นตัวเลขและมีค่ามากกว่า 0 เสมอ  
3. current\_milestone ต้องเป็นหนึ่งในค่าที่กำหนดใน State Machine เท่านั้น  
4. messageId ต้องไม่ซ้ำกับข้อความที่เคยประมวลผลสำเร็จแล้ว (Idempotency Check

**Response**

	Message Headers 

messageType: DonationStatusProcessingResult

messageId: UUID ของข้อความตอบกลับนี้

correlationId: ต้องตรงกับ messageId ของ Request ต้นทาง เพื่อใช้จับคู่ว่าการตอบกลับนี้มาจากคำขอไหน

sentAt: ISO-8601 datetime 

**Success Message Body**  
{  
  "donation\_id": "550e8400-e29b-41d4-a716-446655440000",  
  "incident\_id": "8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10",  
  "status": "PROCESSED",  
  "processed\_at": "2026-03-03T15:35:00Z",  
  "remarks": "Notification sent to donator and dashboard updated."  
}

**Reject/Error Message Body**

{  
  "donation\_id": "550e8400-e29b-41d4-a716-446655440000",  
  "incident\_id": "8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10",  
  "status": "REJECTED",  
  "reasonCode": "INVALID\_MILESTONE\_SEQUENCE",  
  "reasonMessage": "Cannot transition from 'registered' directly to 'arrived\_at\_zone' without 'dispatched' status."  
}

**Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| Field | Type | Required | Description |
| donation\_id | uuid | Y | รหัสการบริจาคที่ใช้อ้างอิง |
| incident\_id | uuid | Y | รหัสเหตุการณ์จาก Central Schema |
| status | enum | Y | ผลลัพธ์การประมวลผล (PROCESSED / REJECTED) |
| reasonCode | string | Y (ถ้า REJECT) | รหัสเหตุผลที่ปฏิเสธ เพื่อให้ระบบอื่นตัดสินใจต่อได้ |
| reasonMessage | string | Y (ถ้า REJECT) | ข้อความอธิบายเหตุผลสำหรับมนุษย์อ่าน  |

	**Validation Rule**

	1.correlationId ต้องตรงกับ messageId ของคำขอที่ส่งไปตอนแรกเสมอเพื่อป้องกันการสับสนของข้อมูล

	2.หากสถานะเป็น REJECTED ต้องระบุ reasonCode ที่เป็นมาตรฐาน (Enum) ห้ามใช้ข้อความลอยๆ เพื่อให้ระบบทำการ Retry หรือแจ้งเตือนได้ถูกต้อง 

# Service Data

# **Service Data**

# **1\) Donation Master Data (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| **Field Name** | **Type** | **Required** | **Description** | **Example** |
| **donation\_id** | uuid | Y (PK) | รหัสการบริจาคที่เป็น Primary Key ของระบบ | 550e8400-e29b... |
| **batch\_id** | uuid | Y | รหัสชุดสิ่งของบริจาค (Batch Reference) | abc123-def456 |
| **incident\_id** | uuid | Y (Ref) | **(Reference Only)** รหัสเหตุการณ์จาก Central Schema | 8b9e4b0d-3b7e... |
| **item\_category** | enum | Y | หมวดหมู่สิ่งของ (เช่น FOOD, MEDICINE) | FOOD\_AND\_WATER |
| **item\_description** | string | Y | รายละเอียดของที่บริจาค | ข้าวสาร 5กก. 10ถุง |
| **total\_quantity** | float | Y | จำนวนสิ่งของทั้งหมด (ต้อง \> 0\) | 10.0 |
| **unit** | string | Y | หน่วยนับของสิ่งของ | pack |
| **created\_at** | datetime | Y | วันเวลาที่เริ่มลงทะเบียนข้อมูล | 2026-03-03T10:00Z |

# **2\) Donation Operational State (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| **Field Name** | **Type** | **Required** | **Description** | **Example** |
| **donation\_id** | uuid | Y (FK) | อ้างอิงไปยัง Donation Master Data | 550e8400-e29b... |
| **current\_milestone** | enum | Y | สถานะปัจจุบัน (ตาม Flow 5 ขั้นตอน) | arrived\_at\_zone |
| **milestone\_updated\_at** | datetime | Y | วันเวลาที่สถานะถูกเปลี่ยนแปลงล่าสุด | 2026-03-03T15:30Z |
| **last\_updated\_by\_role** | string | Y | บทบาทของผู้ที่ทำการอัปเดตสถานะล่าสุด | field\_unit |

# Service Architecture

**Service Architecture**  
**![][image1]**

**Components**

* 

**Explanation**

# Service Interaction

**Service Interaction**

# Dependency Mapping

**Dependency Mapping – ชื่อ service**

1. **ชื่อ service/system**  
   **Type:** Service/Queue/Topic/Database  
   **Interaction Style:** Synchronous/Asynchronous  
   **Purpose:**   
   **Criticality:** Critical/Non-Critical  
   **Failure Handling:**  
   

[image1]: <data:image/png;base64,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>