# Service Overview

**ภาพรวมของบริการ (Service Overview)**  
EmergencyResourceRequest Service

1. **Service Owner**

นายชนกันต์ ทองรอง รหัสนักศึกษา 6609611816 ภาคปกติ

2. **Service Purpose**

EmergencyResourceRequest Service เป็นบริการที่รับผิดชอบการรับเรื่อง รวบรวม และจัดการคำร้องขอทรัพยากรความช่วยเหลือ เช่น อาหาร น้ำ ยา จากผู้ประสบภัยและหน่วยงานส่วนหน้า โดยทำหน้าที่แปลงข้อมูลคำร้องขอให้อยู่ในรูปแบบที่มีโครงสร้าง (Structured Data) เพื่อส่งต่อให้ทีมกู้ภัยนำไปใช้วางแผนการกระจายสิ่งของได้อย่างมีประสิทธิภาพ

3. **Pain Point ที่แก้ไข**

ในสถานการณ์ภัยพิบัติ ข้อมูลการขอความช่วยเหลือมักกระจัดกระจาย ไม่ระบุพิกัดที่ชัดเจน และมีการแจ้งซ้ำซ้อนเนื่องจากอินเทอร์เน็ตไม่เสถียร ทำให้หน่วยกู้ภัยไม่ทราบว่าพื้นที่ใดมีความต้องการเร่งด่วน บริการนี้จึงเข้ามาช่วยจัดระเบียบข้อมูล แยกแยะระดับความสำคัญ และป้องกันการบันทึกข้อมูลซ้ำซ้อน เพื่อให้ความช่วยเหลือไปถึงผู้ที่ต้องการจริงๆ ได้อย่างรวดเร็ว

**3️. Target Users**

1. Citizen (ประชาชนผู้ประสบภัย): ผ่านทางแอปพลิเคชันหรือเว็บ Frontend  
2. Rescue Team: เจ้าหน้าที่ลงพื้นที่หรือทีมกู้ภัยที่ต้องการดูรายการคำขอและกดรับงาน  
   

**4️. Service Boundary**

* In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ):  
  * รับและจัดเก็บข้อมูลคำร้องขอความช่วยเหลือและทรัพยากร (Resource Requests)  
  * จัดการสถานะการดำเนินการของคำร้องขอ  
  * ตรวจสอบและคัดกรองข้อมูลคำร้องขอซ้ำซ้อน (Duplicate Detection / Idempotency)  
  * จัดเก็บพิกัด (Location) และระดับความเร่งด่วน (Priority) ของแต่ละคำขอ  
* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ):  
  * การจัดการคลังสินค้าหรือสต๊อกสิ่งของบริจาค (Inventory Management)  
  * การจัดการข้อมูลทีมกู้ภัยหรือการนำทางรถบรรทุก (Fleet Routing)  
  * การจัดการข้อมูลภาพรวมของเหตุการณ์ภัยพิบัติ (Incident Master Data)

**5️. Autonomy / Decision Logic**  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การตรวจจับข้อมูลซ้ำซ้อน (Idempotency): หากมีคำร้องขอที่มีข้อมูลผู้แจ้งและพิกัดเดิมส่งเข้ามาในเวลาใกล้เคียงกัน บริการจะปฏิเสธหรือรวมเป็นคำขอเดียวโดยอัตโนมัติ  
* การอัปเดตสถานะ: เมื่อมีการระบุตัวทีมกู้ภัย (`delivery_team_id`) เข้ามาในระบบ บริการสามารถปรับสถานะจาก `NEW` เป็น `IN_PROGRESS` ได้ทันที

การตัดสินใจอิงจาก:

* ความถูกต้องของพิกัด (Location validation)  
* ความสมบูรณ์ของรายการสิ่งของที่ขอ (Items payload)

บริการสามารถตัดสินใจได้เองภายใต้ business rules ที่กำหนด โดยไม่ต้องรอ/ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ

**6️. Owned Data**

* **Resource Request Master Data (ข้อมูลคำร้องขอ):** ข้อมูลรายละเอียดคำขอ เช่น `items`, `requester` (ผู้แจ้ง), `location`, `priority` เป็นข้อมูลแกนหลักที่เกิดจาก Action ภายในบริการนี้ จึงต้องเป็นเจ้าของเพื่อให้แก้ไขและดึงข้อมูลได้อย่างรวดเร็ว  
* **Request Operational State (สถานะการดำเนินการ):** ข้อมูล `status` (`NEW`, `IN_PROGRESS`, `CLOSED`) และ `time_requested` เป็น state ที่เชื่อมโยงกับ Lifecycle ของคำร้องขอ บริการนี้จึงต้องรับผิดชอบเพื่อป้องกันไม่ให้ Service อื่นมาแก้ไขสถานะโดยพลการ  
* **Idempotency Keys / Request Logs (ข้อมูลป้องกันการซ้ำซ้อน):** ข้อมูลสำหรับตรวจสอบประวัติการส่ง Request ซ้ำซ้อน ต้องอยู่ภายใต้บริการนี้เพื่อรับประกันความถูกต้องของการสร้างข้อมูลใหม่

**7️. Linked Data (Reference Only)**

* `incident_id`: อ้างอิงเหตุการณ์ภัยพิบัติจาก Incident Service เพื่อระบุว่าคำขอนี้เกิดในภัยพิบัติรอบไหน  
* `delivery_team_id`: อ้างอิงทีมกู้ภัยจาก Rescue Team Service (ระบบจะไม่เก็บชื่อหรือเบอร์โทรทีมกู้ภัยไว้ที่นี่ แต่จะเก็บแค่ ID)  
* item\_id: อ้างอิงถึงสินค้าที่มีอยู่ใน stock (จะอยู่ใน field jsonb items) โดยจะอิงไปถึง service ที่เกี่ยวข้องกับจัดการ stock

**8\. Non-Functional Requirements**

* **Idempotency:** API สำหรับสร้างคำขอ (`POST`) ต้องรองรับ Idempotency Key ป้องกันการสร้างข้อมูลซ้ำเมื่อผู้ประสบภัยกดส่งซ้ำเพราะเน็ตหลุด  
* **Availability:** เนื่องจากเป็นระบบที่ใช้งานในภาวะฉุกเฉิน API ฝั่งรับเรื่อง (Create Request) ต้องสามารถทำงานได้ (High Availability) แม้ Service อื่นที่เกี่ยวข้องจะล่ม  
* **Data Integrity & Concurrency:** หากมีทีมกู้ภัย 2 ทีมพยายามกดรับเคสเดียวกันพร้อมกัน (อัปเดตสถานะเป็น `IN_PROGRESS`) ระบบต้องมีกลไก Optimistic Locking ป้องกันไม่ให้รับเคสซ้ำซ้อน  
* **Security:** API Endpoint สำหรับดึงข้อมูลไปแสดงผลหรืออัปเดตสถานะ (ที่ใช้โดยทีมกู้ภัย) ต้องมีการยืนยันตัวตน (Authentication) เพื่อป้องกันข้อมูลส่วนบุคคลของผู้ประสบภัยรั่วไหล

# Sync Contract

**Synchronous Function Contract**  
**Base URL:** *http://TBD.com*

# **API Contract \#1: Create Resource Request**

### **ข้อมูลทั่วไป**

* **Name:** Create a new resource request  
* **Method:** POST  
* **Path:** `/v1/request`  
* **Type:** Synchronous

### **คำอธิบาย**

ใช้สำหรับสร้างคำร้องขอทรัพยากรและความช่วยเหลือใหม่จากผู้ประสบภัยหรือเจ้าหน้าที่ส่วนหน้า

### **Request**

**Query Params**

* 

  **Headers**

* Content-Type: application/json

* Idempotency-Key: \<uuid\>

  **Body:** 

  {

     "items": \[

      {

        "id": "1",

        "amount": 1

      }

    \],

    "extra\_items": \[

      {

        "name": "ยาหม่อง", “amount”: 3,

      }

    \],

    "from": {

      "name": "Somchai Maipong",

      "location": {

        "address": "32/1 Phichit",

        "description": "Behind 7-11",

        "latitude": 16.4425,

        "longitude": 100.3488

      },

      "contact": {

        "phone": "012345678"

      }

    },

  }

### **Response**

**Success: 201**  
{ "id": "req-1234-uuid", "status": "NEW", "requested\_at": "2026-01-30T14:25:00Z" }

**Error: 400**  
{   
  "code": "VALIDATION\_ERROR",  
 "message": "from.location.latitude and longitude are required"   
} 

### **Dependency / Reliability**

* ไม่เรียก service อื่นแบบ Synchronous  
* ต้องทำ Idempotency check จาก Header  
* Timeout: 10s

# **API Contract \#2: List Requests**

**ข้อมูลทั่วไป**

* **Name:** List requests by incident and status  
* **Method:** GET  
* **Path:** `/v1/requests`  
* **Type:** Synchronous

### **คำอธิบาย**

ใช้ดึงข้อมูลรายการคำร้องขอ เพื่อให้ระบบส่วนกลาง (Dispatcher) หรือทีมกู้ภัย ใช้ดูว่ามีเคสไหนบ้างที่ยังไม่มีคนไปช่วยเหลือ หรือเพื่อจัดพิกัดการส่งของ

### **Request**

**Query Params**

* `incident_id` (uuid, required)  
* `status` (string, optional)  
* `priority` (string, optional)

  **Headers**

* Content-Type: application/json  
* Authorization: Bearer \<token\>

  **Body**


  **Validation**

* capacityAvailable ≥ 0  
* status ∈ {OPEN, FULL, CLOSED}  
* incidentId required

### **Response**

**Success: 200**

\[  
{  
   “id”: “uuid”,  
   "items": \[  
    {  
      "id": "1",  
      "amount": 1  
    }  
  \],  
  "extra\_items": \[  
    {  
      "name": "ยาหม่อง", “amount”: 3,  
    }  
  \],  
  "from": {  
    "name": "Somchai Maipong",  
    "location": {  
      "address": "32/1 Phichit",  
      "description": "Behind 7-11",  
      "latitude": 16.4425,  
      "longitude": 100.3488  
    },  
    "contact": {  
      "phone": "012345678"  
    }  
  },  
}  
\]

**Error: 404**

{  
    "code": "VALIDATION\_ERROR",  
    "message": "incident\_id required",  
}

### **Dependency / Reliability**

* ไม่เรียก service อื่น  
* Idempotent (Safe method)  
* Timeout: 30s




# Async Contract

Asynchronous Function Contract

## Message Contract \#1: Request Resource

### ข้อมูลทั่วไป 

* Message Name: ResourceRequestCreated  
* Interaction Style: Request–Async Response (via Message Broker)  
* Producer: EmergencyResourceRequest Service  
* Consumer: Dispatch Service, Inventory Service  
* Channel/Queue: emergency.resource.events.v1  
* Version: v1

### คำอธิบาย

### เมื่อมีผู้ประสบภัยส่งคำร้องขอทรัพยากรเข้ามาใหม่และระบบทำการบันทึกลง Database สำเร็จ บริการนี้จะทำการส่ง Event ออกไปทันที เพื่อแจ้งให้ระบบอื่นรับทราบและนำข้อมูลไปดำเนินการต่อในส่วนของตนเอง (เช่น เช็กสต๊อก หรือ จัดทีมกู้ภัย) โดยไม่ต้องรอให้ Service อื่นทำงานเสร็จ เพื่อรักษา High Availability ของระบบรับแจ้งเหตุ

### Request 

### Message Headers

* messageType: ResourceRequestCreated  
* eventId: UUID (รหัสอ้างอิงของข้อความนี้ ป้องกันส่งซ้ำ)  
* sentAt: ISO-8601 datetime  
* traceId: string/uuid (optional \- สำหรับใช้ track log ข้าม service)

  Message Body

  {

    "request\_id": "req-1234-uuid",

    "incident\_id": "8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10",

    "request\_for": "CITIZEN",

    "priority": "CRITICAL",

    "item": \[

      { "id": "1", "amount": 1 }

    \],

    "extra\_item": \[

      { "name": "ยาหม่อง", "amount": 3 }

    \],

    "location": {

      "latitude": 16.4425,

      "longitude": 100.3488

    },

    "requested\_at": "2026-01-30T14:25:00Z"

  }


  Field Definition:

| Field | Type | Required | Description |
| :---- | :---- | :---- | :---- |
| request\_id | string | Y | รหัสคำร้องขอที่สร้างสำเร็จ (PK จากบริการของเรา) |
| incident\_id | UUID | Y | รหัสอ้างอิงเหตุการณ์ภัยพิบัติ |
| request\_for | string | Y | ประเภทของคำร้องขอว่าสำหรับใคร |
| priority | string | Y | ความเร่งด่วน: CRITICAL / NORMAL / LOW |
| items | array\<json\> | N | รายการสิ่งของที่มีในระบบและจำนวนที่ต้องการ |
| extra\_items | array\<json\> | N | รายการสิ่งของนอกระบบ (พิมพ์ชื่อเอง) และจำนวนที่ต้องการ |
| location | json | Y | ตำแหน่งและพิกัดจุดเกิดเหตุ (Latitude, Longitude) |
| requested\_at | datetime | Y | วัน-เวลาที่ส่งคำร้องขอ |

Validation Rules

* request\_id และ incident\_id ต้องไม่เป็นค่าว่าง  
* อย่างน้อยต้องมีข้อมูลใน items หรือ extra\_items (array ยาวกว่า 0\)  
* Consumer (ผู้รับ) ต้องใช้ eventId ใน Header เพื่อทำ Idempotency Check ป้องกันการประมวลผลคำขอซ้ำซ้อน

Response

	Message Headers 

* Content-Type: application/json

* Idempotency-Key: \<uuid\>

  Success Message Body

  {

    "request\_id": "req-1234-uuid",

    "incident\_id": "8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10",

    "status": "ACCEPTED",

    "processed\_by": "DispatchService",

    "message": "Resource request accepted and routed to rescue team"

  }


  


  

  Reject/Error Message Body

  {

    "request\_id": "req-1234-uuid",

    "incident\_id": "8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10",

    "status": "REJECTED",

    "reasonCode": "OUT\_OF\_STOCK",

    "message": "Inventory service reports no requested items available in this zone"

  }


Field Definition:

| Field | Type | Required | Description |
| :---: | :---: | :---: | :---: |
| request\_id | string | Y | รหัสคำร้องขอต้นทาง (เพื่อให้เราเอาไปอัปเดต Database ของเราถูกเคส) |
| incident\_id | UUID | Y | รหัสอ้างอิงเหตุการณ์ภัยพิบัติ |
| status | enum | Y | ผลลัพธ์จากการประมวลผล: ACCEPTED / REJECTED |
| processed\_by | string | N | ชื่อ Service ที่เป็นคนตอบกลับมา (เช่น DispatchService) |
| reasonCode | string | N | รหัสข้อผิดพลาด (Machine-readable) จะมีค่าเมื่อสถานะเป็น REJECTED |
| message | string | Y | ข้อความอธิบายผลลัพธ์ (Human-readable) สำหรับเก็บลง Log หรือแสดงผล |

Validation Rules

* หาก status เป็น ACCEPTED ควรระบุ processed\_by เพื่อให้ทราบว่าใครรับผิดชอบต่อ  
* หาก status เป็น REJECTED บังคับว่าต้องมี reasonCode (เช่น OUT\_OF\_STOCK, OUT\_OF\_SERVICE\_AREA) เพื่อให้ระบบของเรารู้ว่าจะต้องจัดการคำขอนี้อย่างไรต่อไป

# Service Data

# **Service Data**

1) # **Resource Request Master Data (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| :---- | :---- | :---- | :---- | :---- |
| id | UUID (PK) | Y | รหัสอ้างอิงของคำร้องขอ (Primary Key) | req-1234-uuid |
| incident\_id | UUID | Y | รหัสอ้างอิงเหตุการณ์ภัยพิบัติ (เชื่อมกับ Incident Service) | 8b9e4b0d-3b7e... |
| request\_for | String | Y | ประเภทของการร้องขอสำหรับใคร | CITIZEN |
| priority | String (Enum) | Y | ระดับความเร่งด่วน (CRITICAL, NORMAL, LOW) | CRITICAL |
| requester | JSONB | Y | ข้อมูลผู้แจ้ง (ชื่อ, เบอร์ติดต่อฉุกเฉิน) | {"name": "Somchai", "phone": "012345678"} |
| location | JSONB | Y | พิกัดจุดเกิดเหตุ และคำอธิบายที่อยู่ | {"latitude": 16.4425, "longitude": 100.3488} |
| status | String (Enum) | Y | สถานะปัจจุบัน (NEW, IN\_PROGRESS, CLOSED) | NEW |
| delivery\_team\_id | UUID | N | รหัสทีมกู้ภัยที่รับหน้าที่จัดการ (จะอัปเดตภายหลัง) | team-789-uuid |
| requested\_at | Timestamp | Y | วัน-เวลาที่มีการสร้างคำร้องขอนี้ขึ้นมา | 2026-01-30T14:25:00Z |

\*items และ extra\_items อนุญาตให้เป็น Null ได้ แต่ในการ Validation ของ API บังคับว่าต้องมีข้อมูลอย่างน้อยใน 1 ฟิลด์)

# **2\) Request Line Item (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| :---- | :---- | :---- | :---- | :---- |
| id | UUID (PK) | Y | รหัสอ้างอิงของรายการย่อย (Primary Key) | item-8899-uuid |
| request\_id | UUID (FK) | Y | รหัสคำร้องขอหลัก | req-1234-uuid |
| item\_type | String | Y | ประเภทสิ่งของ (STANDARD \= มีในระบบ, EXTRA \= นอกระบบ) | EXTRA |
| item\_ref\_id | String | N | รหัสสิ่งของอ้างอิง (กรณีเป็น STANDARD) | 1 (ปล่อยว่างถ้าเป็น EXTRA) |
| item\_name | String | N | ชื่อสิ่งของ (กรณีเป็น EXTRA ที่ผู้ใช้พิมพ์เอง) | "ยาหม่อง" |
| amount\_requested | Integer | Y | จำนวนที่ร้องขอ | 3 |

# Service Architecture

![][image1]

### **Service Architecture**

**Components**

* **Client:** ผู้เรียกใช้งานระบบ (เช่น ประชาชนผู้ประสบภัย หรือเจ้าหน้าที่ส่วนหน้า) ที่ส่งคำขอและรอรับผลลัพธ์  
* **Backend:** บริการหลัก (Core Service) ทำหน้าที่รับคำขอแบบ Synchronous จาก Client รวมถึงสามารถดึงข้อความ/เหตุการณ์จากคิวมาประมวลผลได้  
* **AWS RDS:** ฐานข้อมูลเชิงสัมพันธ์ (Relational Database) สำหรับจัดเก็บข้อมูลที่ EmergencyResourceRequest Service เป็นเจ้าของ (เช่น ข้อมูลคำร้องขอ, สถานะคำขอ และประวัติการอัปเดต)  
* **Amazon SQS:** จุดรับคำขอแบบ Asynchronous (เช่น คำร้องขอทรัพยากร) ที่ถูกส่งเข้ามาจาก Client เพื่อลดภาระการรอคอยของระบบ  
* **Message Queue (`emergency.resource.events.v1`):** คิวสำหรับพักและจัดการ Event "Request Resource" ก่อนที่จะกระจายงานไปให้ส่วนอื่นๆ ประมวลผล  
* **Async Worker (AWS Lambda):** ฟังก์ชันที่ทำงานอยู่เบื้องหลัง ทำหน้าที่ดึงข้อความจากคิวมาประมวลผล อ่าน/เขียนข้อมูลลงในฐานข้อมูล และแจ้งผลลัพธ์กลับไปยัง Client โดยตรง

**Explanation** สถาปัตยกรรมของ EmergencyResourceRequest Service ถูกออกแบบให้รองรับทั้งการทำงานแบบประสานเวลา (Synchronous) และไม่ประสานเวลา (Asynchronous) โดยใช้ฐานข้อมูลส่วนกลางคือ **AWS RDS** ในการจัดเก็บข้อมูลสถานะคำร้องขอ

การทำงานแบ่งออกเป็น 2 เส้นทางหลัก ดังนี้:

1. **Synchronous Flow (สำหรับงานที่ต้องการผลลัพธ์ทันที):** Client สามารถสื่อสารโดยตรงกับ **Backend** (ผ่านรูปแบบ Request/Response) เพื่อดูข้อมูลหรือตรวจสอบสถานะคำขอ โดย Backend จะทำการอ่านและเขียนข้อมูล (Read/Write) กับ AWS RDS แล้วตอบกลับไปยัง Client ทันที รูปแบบนี้เหมาะสำหรับการดึงข้อมูล (Query) เพื่อแสดงผลบนหน้าจอ  
2. **Asynchronous Flow (สำหรับงานสร้างคำร้องขอ หรือประมวลผลที่ใช้เวลา):** เมื่อ Client ต้องการส่งคำร้องขอทรัพยากร (Request Resource) คำขอนั้นจะถูกส่งไปเข้าคิวที่ **Amazon SQS** และจัดเก็บในคิว **`emergency.resource.events.v1`** ซึ่งช่วยให้ Client ไม่ต้องรอระบบประมวลผลจนเสร็จ จากนั้น **Async Worker (AWS Lambda)** จะทำการดึงข้อมูลจากคิวไปประมวลผล ทำการบันทึกหรืออัปเดตข้อมูลลงใน **AWS RDS** เมื่อทุกอย่างเสร็จสมบูรณ์ Async Worker จะส่งผลลัพธ์การดำเนินการ (Request Result) กลับไปแจ้งให้ Client ทราบ (เช่น ผ่าน Push Notification หรือ Webhook) นอกจากนี้ ตัว Backend เองก็สามารถรับ Event จากคิวนี้ไปใช้ประโยชน์ในการอัปเดตสถานะของระบบย่อยอื่นๆ ได้เช่นเดียวกัน รูปแบบนี้ช่วยลดคอขวดของระบบและทำให้รองรับคำขอจำนวนมากพร้อมกันในสถานการณ์ภัยพิบัติได้อย่างมีประสิทธิภาพ

# Service Interaction

# Dependency Mapping

[image1]: <data:image/png;base64,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>