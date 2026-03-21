# Service Overview

**ภาพรวมของบริการ (Service Overview)**

**Manage Dispatch Service**

**Github:** [https://github.com/Slasherw/ManageDispatchService](https://github.com/Slasherw/ManageDispatchService)

**1\. Service Owner**  
นายนพกรณ์ สงเคราะห์ รหัสนักศึกษา 6609540023

**2\. Service Purpose**  
Manage Dispatch Service เป็นบริการที่รับผิดชอบการบริหารจัดการคำสั่งการกู้ภัย โดยทำหน้าที่เชื่อมโยงทีมกู้ภัย (Rescue team) ที่เฉพาะเจาะจงเข้ากับคำร้องขอความช่วยเหลือ (Request) รวมถึงติดตามสถานะการร้องขอทั้งหมดที่เกิดขึ้นในเหตุการณ์ภัยพิบัติ เพื่อให้ส่วนกลางสามารถมอนิเตอร์สถานะการทำงานได้อย่างมีประสิทธิภาพ

**3\. Pain Point ที่แก้ไข**  
ในช่วงเหตุการณ์ภัยพิบัติที่มีความโกลาหล ศูนย์สั่งการ (Dispatchers) มักจะสูญเสียการติดตามสถานะของหน่วยกู้ภัยที่ถูกส่งออกไปปฏิบัติหน้าที่ ซึ่งปัญหาดังกล่าวนำไปสู่การส่งทีมกู้ภัยไปทำงานซ้ำซ้อนในพื้นที่เดิม หรือทำให้มีบางพื้นที่ที่ต้องการความช่วยเหลือถูกละเลยไป

**4\. Target Users**

* เจ้าหน้าที่ศูนย์สั่งการ / ผู้สั่งการ (Dispatcher)   
* บริการนี้ทำหน้าที่เป็น Backend Service หลักที่เชื่อมต่อระหว่าง Request Service, Team Service และ Mission Progress Service

**5\. Service Boundary**  
In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ):

* จัดเก็บและจัดการข้อมูลคำสั่งการ (Dispatch Records)  
* จัดการสถานะการตอบรับภารกิจ (Mission Acceptance Status) ตั้งแต่เริ่มต้น (PENDING) ไปจนถึงรับภารกิจ (ACCEPT) หรือยกเลิก (DECLINE)   
* บังคับใช้ตรรกะการตรวจสอบความพร้อมของทีมกู้ภัยก่อนลงพื้นที่

Out-of-scope / Not Responsible For (ไม่รับผิดชอบ):

* การจัดการข้อมูลพื้นฐานของทีมกู้ภัย (Team Master Data)   
* การจัดการรายละเอียดเชิงลึกของคำร้องขอความช่วยเหลือจากประชาชน (Request/Incident Master Data)

**6\. Autonomy / Decision Logic**  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การตรวจสอบและตัดสินใจอนุมัติคำสั่งการ โดยอิงจากสถานะ "AVAILABLE" ของทีมกู้ภัยจาก Team Service   
* การปฏิเสธการสร้างคำสั่งการ (Dispatch) หากอ้างอิงถึงข้อมูลที่ไม่มีอยู่จริง (เช่น ไม่มี Incident ID) เพื่อป้องกันการเกิดข้อมูลกำพร้า (Orphan data) ในระบบ   
* การจัดการสถานะ Flow การทำงาน เช่น การเปลี่ยนสถานะจาก PENDING เป็น ACCEPT หรือ DECLINE

**7\. Owned DataDispatch Records:** 

* ข้อมูลหลักของการสั่งการ เช่น dispatch\_id, เวลาที่ส่งทีมออกไป (dispatched\_at), เวลาที่ทีมไปถึงที่หมาย (arrival\_time), และบันทึกหลังจบภารกิจ(completion\_note)  บริการนี้ต้องเป็นเจ้าของข้อมูลเหล่านี้เพื่อใช้ควบคุมการทำงาน  
* Mission Acceptance State: สถานะปัจจุบันของการสั่งการ  ที่เปลี่ยนแปลงโดยการรับทำภารกิจหรือปฎิเสธภารกิจของ Rescue Team

**8\. Linked Data (Reference Only)**

* request\_id อ้างอิงจาก Request Service   
* team\_id อ้างอิงจาก Team Service   
* mission\_status อาจมีการดึงหรือเชื่อมโยงจาก Mission Progress Service

**9\. Non-Functional Requirements**

* ระบบต้องมีกลไกป้องกันข้อมูลตกหล่น (Idempotency) และไม่สร้าง Dispatch record ซ้ำซ้อน หาก Request ID ไม่มีอยู่จริงในระบบ ระบบต้องตอบกลับด้วย HTTP 404 Not Found ทันที   
* ต้องมีการจัดการข้อผิดพลาด (Failure handling) ที่ดี หากไม่สามารถดึงข้อมูลสถานะทีมจาก Team Service ได้

# Sync Contract

**Synchronous Function Contract**  
**Base URL:** [http://TBD.com](http://TBD.com)

API Contract 1: Create Dispatch Order (สร้างคำสั่งการและรอการตอบรับ)

ข้อมูลทั่วไป

* Name: Create Dispatch Order for assign Rescuer to request  
* Method: POST  
* Path: /dispatches  
* Type: Syncronous

คำอธิบาย  
สร้างบันทึกคำสั่งการใหม่ เพื่อส่งงานไปให้ทีมกู้ภัย (ระบบจะตั้งสถานะเริ่มต้นเป็น PENDING)

**Request** 

**Query Params** 

* ไม่มี

**Headers** 

* Accept: application/json   
* Content-Type: application/json

**Body:** 

{ "requestId": "REQ-10293", "teamId": "TEAM-005", "priorityLevel": 1 }

Response  
	Created: 201  
	{  
 	 "dispatch\_id": "DSP-88472",  
  	"request\_id": "REQ-10293",  
 	 "team\_id": "TEAM-005",  
  	"status": "PENDING",  
  	"dispatched\_at": "2026-03-03T14:30:00Z"  
}

Error: 400  
{  
  "error": {  
    "code": "VALIDATION\_ERROR",  
    "message": "requestId and teamId required",  
    "traceId": "uuid"  
  }  
}

Error: 404  
{  
  "error": {  
    "code": "NOT\_FOUND",  
    "message": "teamId or requestId not found",  
    "traceId": "uuid"  
  }  
}

**Dependency / Reliability**

* เรียก Team Service เพื่อตรวจสอบสถานะทีมกู้ภัย (AVAILABLE)  
* เรียก Request Service เพื่อตรวจสอบความถูกต้องของ request\_id  
* ไม่ Idempotent (Not Idempotent)  
* Timeout: 30s

### **API Contract \#2: Get Dispatches by Team**

**ข้อมูลทั่วไป** 

* Name: Get dispatches by team   
* Method: GET Path: /v1/dispatches   
* Type: Synchronous

**คำอธิบาย** 

ใช้ดึงข้อมูลคำสั่งการที่ถูกมอบหมายให้กับทีมกู้ภัยแต่ละทีม เพื่อให้บริการอื่น (เช่น แอปพลิเคชันของกู้ภัย) ใช้แสดงผลว่ามีภารกิจไหนที่กำลังรอการตอบรับ (PENDING) หรือรับงานไปแล้ว (ACCEPT)

**Request** **Query Params**

*  teamId (string, required)   
* status (string, optional)

**Headers** 

* Accept: application/json

**Body:** ไม่มี

**Response** 

**Success: 200**

{  
  "teamId": "TEAM-005",  
  "items": \[  
    {  
      "dispatchId": "DSP-88472",  
      "requestId": "REQ-10293",  
      "status": "PENDING",  
      "priorityLevel": 1,  
      "dispatchedAt": "2026-03-03T14:30:00Z"  
    }  
  \]  
}

**Error: 400**

JSON  
{  
  "error": {  
    "code": "VALIDATION\_ERROR",  
    "message": "teamId required",  
    "traceId": "uuid"  
  }  
}

**Dependency / Reliability** 

* ไม่เรียก service อื่น   
* Idempotent   
* Timeout: 30s


### **API Contract \#3: Update Mission Acceptance Status**

**ข้อมูลทั่วไป** 

* Name: Update mission acceptance status  
* Method: PATCH   
* Path: /v1/dispatches/{dispatchId}/  
* status Type: Synchronous

**คำอธิบาย**

ใช้สำหรับให้ทีมกู้ภัยอัปเดตสถานะการตอบรับภารกิจ โดยเปลี่ยนจาก PENDING เป็น ACCEPT (รับงาน) หรือ DECLINE (ปฏิเสธงานพร้อมระบุเหตุผล)

**Request** 

**Query Params** ไม่มี

**Headers** 

* Accept: application/json   
* Content-Type: application/json

**Body:** 

{ "status": "ACCEPT", "note": "" }

**Response**

**Success: 200**

{

  "dispatchId": "DSP-88472",

  "status": "ACCEPT",

  "updatedAt": "2026-03-03T14:35:00Z"

}

**Error: 400**

{

  "error": {

    "code": "VALIDATION\_ERROR",

    "message": "invalid status value (must be ACCEPT or DECLINE)",

    "traceId": "uuid"

  }

}

**Error: 409**

{

  "error": {

    "code": "CONFLICT\_ERROR",

    "message": "dispatch order already accepted or declined",

    "traceId": "uuid"

  }

}

**Dependency / Reliability** 

* ไม่เรียก service อื่น   
* Idempotent   
* Timeout: 30s

# Async Contract

**Asynchronous Function Contract**

### **Message Contract \#1: Request Team Dispatch**

**ข้อมูลทั่วไป** 

* **Message Name:** `DispatchTeamRequested`   
* **Interaction Style:** Request–Async Response (via Message Broker)   
* **Producer:** Request Service (หรือ Incident Service)   
* **Consumer:** Manage Dispatch Service   
* **Channel/Queue:** `dispatch.commands.v1`   
* **Version:** v1

**คำอธิบาย** 

ส่งคำขอให้จ่ายงาน (dispatch) ทีมกู้ภัยไปยังคำร้องขอความช่วยเหลือแบบ asynchronous โดยผู้ส่ง (Producer) จะได้รับแจ้งผลลัพธ์การสร้างคำสั่งการกลับไปภายหลังผ่าน result event ที่เชื่อมโยงด้วย correlationId

**Request** 

**Message Headers (required unless stated)**

* `messageType`: DispatchTeamRequested  
* `messageId`: UUID (ใช้เป็น idempotency key ของคำขอ)  
* `replyTo`: `request.dispatch.results.v1`  
* `sentAt`: ISO-8601 datetime  
* `traceId`: string/uuid (optional)

**Message Body**

{  
  "requestId": "REQ-10293",  
  "teamId": "TEAM-005",  
  "priorityLevel": 1,  
  "requestedBy": "RequestService"  
}

**Field Definition:** 

| Field | Type | Require | Description |
| ----- | ----- | ----- | ----- |
| `requestId` | string |  Y | รหัสคำร้องขอความช่วยเหลือจาก  Request Service |
| `teamId` | string |  Y | รหัสทีมกู้ภัยเป้าหมายที่ต้องการส่งไป |
| `priorityLevel` | integer |  Y | ระดับความสำคัญของงาน (เช่น 1=สูงมาก, 2=ปานกลาง, 3=ต่ำ) |
| `requestedBy` |  string |  Y | ชื่อ service ผู้ส่งคำขอ |

**Validation Rules**

* `requestId` และ `teamId` ต้องไม่เป็นค่าว่าง  
* `priorityLevel` ต้องเป็นจำนวนเต็มและมากกว่า 0  
* `messageId` ต้องไม่ซ้ำกับ message ที่เคยประมวลผลแล้ว (idempotency check ป้องกันการส่งทีมซ้ำซ้อน)

---

**Response** **Message Headers (required unless stated)**

* `messageType`: DispatchOrderCreated (กรณีสำเร็จ) หรือ DispatchTeamRejected (กรณีล้มเหลว)  
* `messageId`: UUID ของข้อความนี้  
* `correlationId`: request.messageId (เชื่อมโยงกับคำขอต้นทาง)  
* `sentAt`: ISO-8601 datetime  
* `traceId`: string/uuid (optional)

**Success Message Body**

{  
  "requestId": "REQ-10293",  
  "teamId": "TEAM-005",  
  "dispatchId": "DSP-88472",  
  "status": "PENDING",  
  "dispatchedAt": "2026-03-03T14:30:00Z"  
}

**Reject/Error Message Body**

{  
  "requestId": "REQ-10293",  
  "teamId": "TEAM-005",  
  "status": "REJECTED",  
  "reasonCode": "TEAM\_NOT\_AVAILABLE",  
  "reasonMessage": "The requested rescue team is currently not available or engaged in another mission."  
}

**Field Definition:** |

| Field | Type | Require | Description |
| ----- | ----- | ----- | ----- |
| `requestId` | string |  Y | รหัสคำร้องขอความช่วยเหลือจากระบบต้นทาง |
| `teamId` | string |  Y | รหัสทีมกู้ภัยเป้าหมาย |
| `dispatchId` | string |  N | รหัสคำสั่งการที่ถูกสร้างขึ้นโดย Manage Dispatch Service (มีเฉพาะกรณีสำเร็จ) |
| `status` | enum |  Y | สถานะผลลัพธ์ของคำขอ (PENDING / REJECTED) |
| `dispatchedAt` | datetime |  N | เวลาที่ทำการสร้างคำสั่งการสำเร็จ |
| `reasonCode` | string | N | รหัสเหตุผลที่เป็น machine-readable ใช้สำหรับระบบอื่นตัดสินใจต่อ (มีเฉพาะกรณี REJECTED) |
| `reasonMessage` | string | N | ข้อความอธิบายแบบ human-readable เพื่อใช้แสดงผลใน log หรือช่วย debug (มีเฉพาะกรณี REJECTED) |

**Validation Rules**

* `correlationId` ต้องตรงกับ `messageId` ของ request ที่เคยได้รับ  
* ถ้า `status = PENDING` ต้องมี `dispatchId` และ `dispatchedAt`  
* ถ้า `status = REJECTED` ต้องมี `reasonCode` และ `reasonMessage`  
* `reasonCode` ต้องเป็นค่าที่กำหนดไว้ล่วงหน้า (เช่น `TEAM_NOT_AVAILABLE`, `REQUEST_NOT_FOUND`) ไม่ใช่ free text

# Service Data

### **Service Data**

### **1\) Dispatch Records (Owned by this service)**

ข้อมูลหลักของการสั่งการ ควบคุมว่าส่งทีมไหน ไปทำภารกิจใด และจบงานตอนไหน

| Field Name | Type | Required | Description | Example |
| :---- | :---- | :---- | :---- | :---- |
| dispatchId | string | Y (Primary Key) | รหัสคำสั่งการ | DSP-88472 |
| requestId | string | Y (Foreign Key) | อ้างอิงคำร้องขอความช่วยเหลือจาก Request Service | REQ-10293 |
| teamId | string | Y (Foreign Key) | อ้างอิงทีมกู้ภัยจาก Team Service | TEAM-005 |
| priorityLevel | integer | Y | ระดับความสำคัญของงาน (1=สูงมาก) | 1 |
| dispatchedAt | datetime | Y | เวลาที่สร้างคำสั่งการ/มอบหมายงาน | 2026-03-03T14:30:00Z |
| arrivalTime | datetime | N | เวลาที่ทีมกู้ภัยเดินทางไปถึงจุดเกิดเหตุ | 2026-03-03T15:00:00Z |
| completionNote | text | N | บันทึกรายงานจากทีมกู้ภัยหลังจบภารกิจ | ช่วยเหลือผู้บาดเจ็บ 2 รายสำเร็จ |
| idempotencyKey | uuid | Y | ป้องกันการสร้างคำสั่งการซ้ำซ้อน | f47ac10b-... |
| createdAt | datetime | Y | เวลาที่สร้างข้อมูลนี้ในระบบ | 2026-03-03T14:30:00Z |

### **2\) Mission Acceptance Status (Owned by this service)**

ข้อมูลสถานะปัจจุบันของการสั่งการ ที่อัปเดตโดยการตอบรับหรือปฏิเสธของ Team กู้ภัยหน้างาน

| Field Name | Type | Required | Description | Example |
| :---- | :---- | :---- | :---- | :---- |
| dispatchId | string | Y (Foreign Key) | อ้างอิงรหัสคำสั่งการ (Dispatch Record) | DSP-88472 |
| status | enum | Y | PENDING / ACCEPT / DECLINE | ACCEPT |
| statusNote | string | N | เหตุผลหรือหมายเหตุประกอบการเปลี่ยนสถานะ | ทีมพร้อมเดินทางภายใน 5 นาที |
| updatedBy | string | N | รหัสผู้ใช้งานหรือระบบที่เปลี่ยนสถานะ (เช่น รหัสหัวหน้าทีม) | USER-992 |
| lastUpdatedAt | datetime | Y | เวลาที่มีการอัปเดตสถานะล่าสุด | 2026-03-03T14:35:00Z |

# Service Architecture

**Service Architecture**  
**![][image1]**

#### **Components**

* **User/Client**: ผู้เรียกใช้งานระบบ ได้แก่ เจ้าหน้าที่ศูนย์สั่งการ (Dispatcher) ที่ใช้งานผ่าน Web Dashboard และทีมกู้ภัย (Rescue Team) ที่ใช้งานผ่าน Mobile Application  
* **API Gateway**: จุดรับคำขอแบบ Synchronous สำหรับการเรียกดูข้อมูลรายการสั่งการ (GET) และการอัปเดตสถานะการรับภารกิจ (PATCH)  
* **Lambda REST API Handler**: ทำหน้าที่ประมวลผล Logic ในการดึงข้อมูลจากฐานข้อมูล หรือตรวจสอบเงื่อนไขก่อนเปลี่ยนสถานะภารกิจจาก PENDING เป็น ACCEPT หรือ DECLINE  
* **DynamoDB**: ฐานข้อมูล NoSQL ที่จัดเก็บข้อมูลที่ Manage Dispatch Service เป็นเจ้าของ ได้แก่ Dispatch Records และ Mission Acceptance State  
* **Amazon SQS (dispatch.commands.v1)**: คิวรับคำขอสั่งการ (Dispatch Request) แบบ Asynchronous ที่ส่งมาจาก Request Service  
* **Lambda Async Worker**: ทำการ Poll ข้อความคำขอสั่งการจาก SQS เพื่อตรวจสอบความพร้อมของทีมกู้ภัย และบันทึกข้อมูลการสั่งการลงใน DynamoDB  
* **Amazon SNS**: ช่องทางประกาศผลลัพธ์การสร้างคำสั่งการ (Dispatch Result) เพื่อแจ้งกลับไปยัง Service ต้นทางที่ร้องขอ  
* **Subscriber (request.dispatch.results.v1)**: บริการที่รอรับผลลัพธ์ เช่น Request Service เพื่ออัปเดตสถานะในส่วนของตนเองต่อไป

#### 

#### **Explanation**

สถาปัตยกรรมของ Manage Dispatch Service ประกอบด้วยสองรูปแบบการทำงานหลัก:

1. **การสื่อสารแบบ Synchronous**: ผู้ใช้งาน (Dispatcher หรือ Rescue Team) จะเรียกใช้งาน API ผ่าน **Amazon API Gateway** เพื่อสอบถามสถานะภารกิจหรืออัปเดตการตอบรับงาน ซึ่งคำขอจะถูกส่งต่อไปยัง **AWS Lambda** เพื่อตรวจสอบความถูกต้องและอ่าน/เขียนข้อมูลลงใน **Amazon DynamoDB** โดยตรง รูปแบบนี้ช่วยให้ทีมกู้ภัยสามารถยืนยันการรับงานได้ทันที  
2. **การสื่อสารแบบ Asynchronous**: เมื่อมีการร้องขอให้ส่งทีมกู้ภัยจากระบบอื่น ระบบจะส่งข้อความมายัง **Amazon SQS** ซึ่งทำหน้าที่เป็น Buffer รับงานไว้ไม่ให้ข้อมูลสูญหายแม้ในช่วงที่มีโหลดสูง จากนั้น **Lambda Async Worker** จะดึงงานไปประมวลผลเพื่อสร้างเรคคอร์ดการสั่งการ และประกาศผลลัพธ์กลับผ่าน **Amazon SNS** เพื่อให้ระบบต้นทางรับทราบสถานะการจองทีมกู้ภัยโดยไม่ต้องรอการประมวลผลจนเสร็จสิ้น ช่วยเพิ่มความทนทานและความน่าเชื่อถือให้กับระบบในภาวะภัยพิบัติที่มีการร้องขอเข้ามาจำนวนมาก

# Service Interaction

**Service Interaction**  
![][image2]

#### **Upstream Services (บริการต้นทางที่เรียกใช้งาน Manage Dispatch Service)**

* **Dispatcher Dashboard Service**  
  * เรียกใช้งาน `GET /v1/dispatches` แบบ **synchronous** เพื่อดึงข้อมูลรายการคำสั่งการและสถานะการปฏิบัติงานของทีมกู้ภัยทั้งหมด สำหรับนำไปแสดงผลบนหน้าจอควบคุมและสนับสนุนการตัดสินใจของผู้สั่งการ  
* **Request Service**  
  * ส่งคำขอสั่งการทีมกู้ภัยในรูปแบบ event `DispatchTeamRequested` ผ่าน command queue (`dispatch.commands.v1`) แบบ **asynchronous** เพื่อมอบหมายงานกู้ภัยไปยังพื้นที่เกิดเหตุโดยไม่รอผลลัพธ์ทันที  
* **Rescue Team Application**  
  * เรียกใช้งาน `PATCH /v1/dispatches/{dispatchId}/status` แบบ **synchronous** เพื่อให้ทีมกู้ภัยในพื้นที่สามารถอัปเดตสถานะการตอบรับภารกิจ (ACCEPT/DECLINE) กลับมายังระบบส่วนกลางได้ทันที

#### **Downstream Services (บริการปลายทางที่ Manage Dispatch Service เรียกหรือส่งข้อมูลไป)**

* **Team Service**  
  * ถูกเรียกใช้งานแบบ **synchronous** ผ่าน `GET /v1/teams/{teamId}/status` เพื่อยืนยันว่าทีมกู้ภัยมีตัวตนจริงและมีสถานะ "AVAILABLE" ก่อนที่ระบบจะดำเนินการสร้างเรคคอร์ดคำสั่งการ  
* **Request Service**  
  * ถูกเรียกใช้งานแบบ **synchronous** ผ่าน `GET /v1/requests/{requestId}` เพื่อยืนยันความถูกต้องและสถานะของคำร้องขอความช่วยเหลือก่อนทำการบันทึกข้อมูลการสั่งการ เพื่อป้องกันการเกิดข้อมูลที่ไม่มีแหล่งอ้างอิง (Orphan data)  
* **Notification / Result Channel (`request.dispatch.results.v1`)**  
  * รับ event `DispatchOrderCreated` หรือ `DispatchTeamRejected` ที่ส่งออกจาก Manage Dispatch Service เพื่อแจ้งผลลัพธ์ของการประมวลผลคำสั่งการกลับไปยัง Request Service หรือระบบที่เกี่ยวข้อง

# Dependency Mapping

### **Dependency Mapping – Manage Dispatch Service**

#### **1\. Team Service**

* **Type:** Service  
* **Interaction Style:** Synchronous (REST)  
* **Purpose:** ตรวจสอบสถานะความพร้อมของทีมกู้ภัย (เช่น ต้องเป็น AVAILABLE) ก่อนดำเนินการมอบหมายภารกิจ  
* **Criticality:** Critical  
* **Failure Handling:** หาก Team Service ไม่ตอบสนอง จะปฏิเสธคำขอการ Dispatch ชั่วคราว และส่งผลลัพธ์เป็น REJECTED พร้อม `reasonCode = TEAM_SERVICE_UNAVAILABLE`

#### **2\. Request Service**

* **Type:** Service  
* **Interaction Style:** Synchronous (REST)  
* **Purpose:** ตรวจสอบความถูกต้องและสถานะของรหัสคำร้องขอความช่วยเหลือ (`requestId`) ก่อนทำการบันทึกข้อมูลการสั่งการ  
* **Criticality:** Critical  
* **Failure Handling:** หากบริการไม่ตอบสนอง จะปฏิเสธการสร้างคำสั่งการทันทีเพื่อป้องกันการเกิดข้อมูลที่ไม่มีแหล่งอ้างอิง (Orphan Data) ในระบบ

#### **3\. Amazon SQS (dispatch.commands.v1)**

* **Type:** Queue  
* **Interaction Style:** Asynchronous (Command Queue)  
* **Purpose:** รับคำสั่งมอบหมายภารกิจกู้ภัยแบบเป็นลำดับจาก Request Service หรือบริการอื่นที่เกี่ยวข้อง  
* **Criticality:** Critical  
* **Failure Handling:** \* ใช้ Retry Policy ของ AWS Lambda ในการพยายามประมวลผลใหม่  
  * หากการประมวลผลล้มเหลวซ้ำจนครบจำนวนครั้งที่กำหนด จะส่งข้อความไปยัง Dead Letter Queue (DLQ) เพื่อการตรวจสอบภายหลัง

#### **4\. Amazon SNS (request.dispatch.results.v1)**

* **Type:** Topic  
* **Interaction Style:** Asynchronous (Event Notification)  
* **Purpose:** กระจายผลลัพธ์การสร้างคำสั่งการ (Dispatch Order Created/Rejected) ให้กับบริการต้นทางหรือระบบแจ้งเตือนอื่นๆ  
* **Criticality:** Non-critical  
* **Failure Handling:** หากการประกาศเหตุการณ์ (Publish) ไม่สำเร็จ ระบบจะบันทึก Log และทำการ Retry ตาม Policy ของ AWS โดยไม่ส่งผลกระทบต่อข้อมูลการสั่งการที่บันทึกสำเร็จแล้วในฐานข้อมูล

#### **5\. Amazon DynamoDB**

* **Type:** Database  
* **Interaction Style:** Internal Data Access  
* **Purpose:** จัดเก็บข้อมูลหลักของบริการ ได้แก่ Dispatch Records และสถานะการตอบรับภารกิจ (Mission Acceptance State)  
* **Criticality:** Critical  
* **Failure Handling:** หากการเขียนข้อมูล (Write) ล้มเหลว ระบบจะทำการยับยั้งกระบวนการทั้งหมด และจะไม่ส่ง Event แจ้งผลลัพธ์ออกไปทาง SNS เพื่อรักษาความถูกต้องของข้อมูล (Data Consistency)

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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>