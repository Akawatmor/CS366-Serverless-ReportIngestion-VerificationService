# Service Overview

# **ภาพรวมของบริการ (Service Overview)**

MonitorDisaster Service (Flood)

1. **Service Owner**

นายธนัช เกิดทิพย์ รหัสนักศึกษา 6609611980 ภาคปกติ

2. **Service Purpose**

MonitorDisaster Service เป็นบริการที่รับผิดชอบการรวบรวม (Ingest) ข้อมูลปริมาณน้ำฝนและระดับน้ำจาก API ภายนอกแบบ Real-time โดยทำหน้าที่ประมวลผลเพื่อปรับสถานะภัยพิบัติ (NORMAL ⇄ WATCH ⇄ WARNING ⇄ CRITICAL) แบบอัตโนมัติ   
	บริการนี้ทำหน้าที่เป็นแหล่งความจริงเดียว (Single Source of Truth) ด้านสถานการณ์น้ำ เพื่อสนับสนุนการตัดสินใจของผู้สั่งการ (Dispatcher) และให้ข้อมูลที่แม่นยำแก่ประชาชนเพื่อเตรียมรับมือหรืออพยพได้อย่างทันท่วงที

3. **Pain Point ที่แก้ไข**  
* **ปัญหาทั่วไป:**   
  	ข้อมูลระดับน้ำและสภาพอากาศกระจัดกระจายอยู่ตามหลายแห่ง ไม่มีศูนย์รวมข้อมูล  
* **ปัญหาที่เกี่ยวข้องกับ Service:**   
  	Dispatcher ขาดข้อมูลแบบ Real-time ที่ถูกประมวลผลความเสี่ยงมาให้แล้ว ทำให้ต้องเสียเวลาเปิดดูหลายหน้าจอเพื่อวิเคราะห์สถานการณ์เอง  
* **ผลกระทบหากไม่มี Service นี้:**   
  	การประเมินสถานการณ์จะล่าช้าและเกิด Human Error ได้ง่าย ส่งผลให้การออกประกาศเตือนภัยหรือการสั่งอพยพประชาชนทำได้ช้า ซึ่งอาจก่อให้เกิดความสูญเสียต่อชีวิตและทรัพย์สิน

**3️. Target Users**

* **Dispatcher (เจ้าหน้าที่):**   
  	ใช้สำหรับเฝ้าระวังและสั่งการปรับเปลี่ยนสถานะฉุกเฉิน (Manual Override)  
* **Citizen (ประชาชนในพื้นที่):**   
  	ใช้สำหรับดูข้อมูลระดับน้ำและสถานะแจ้งเตือนในพื้นที่ของตนเอง  
* **Frontend:**   
  	ระบบหน้าบ้านที่เรียก API (GET) ไปแสดงผลเป็น Dashboard  
* **Notification Service:**   
  	ระบบแจ้งเตือนที่รอรับ Async Event เพื่อนำไปส่ง SMS หรือ Push Notification

**4️. Service Boundary**

* **In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ):**  
  * รับและจัดเก็บข้อมูลตัวเลขระดับน้ำและปริมาณฝน (Ingestion Data)  
  * ประมวลผลและจัดการสถานะภัยพิบัติ (Disaster Status State)  
  * ตรวจสอบความสดใหม่ของข้อมูล (Data Freshness / Outdated Flag)  
  * กระจายข่าว (Publish Event) เมื่อมีการเปลี่ยนแปลงระดับความรุนแรงของภัยพิบัติ  
* **Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)**  
  * การส่งข้อความแจ้งเตือน SMS/Email ไปยังผู้ใช้ปลายทาง (เป็นหน้าที่ของ Notification Service)  
  * การจัดการข้อมูลพิกัดแผนที่แบบละเอียด หรือข้อมูลประชากรในพื้นที่ (เป็นหน้าที่ของ Location/Citizen Service)  
  * การจัดการเส้นทางอพยพ หรือจัดการศูนย์พักพิง

**5️. Autonomy / Decision Logic**  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การเลื่อนระดับหรือลดระดับสถานะภัยพิบัติ (Status Transition) ตามตัวเลขที่รับมา  
* การกำหนดสถานะข้อมูลล้าสมัย (is\_outdated) หากไม่ได้รับข้อมูลอัปเดตเกินเวลาที่กำหนด  
* การระงับการอัปเดตอัตโนมัติชั่วคราว หากถูกแทรกแซงโดยเจ้าหน้าที่ผู้สั่งการ (Manual Override)

การตัดสินใจอิงจาก:

* water\_level\_cm (ระดับน้ำ) และ rainfall\_mm (ปริมาณน้ำฝน)  
* last\_updated (เวลาที่อัปเดตข้อมูลล่าสุด) เทียบกับเวลาปัจจุบัน  
* is\_manual\_override (คำสั่งจาก Dispatcher ที่มี Priority สูงสุด)

บริการสามารถตัดสินใจได้เองภายใต้ business rules (เช่น ถ้าน้ำ \> 150 cm ให้ปรับเป็น CRITICAL) โดยไม่ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ

**6️. Owned Data**

* **API Data** (water\_level\_cm, rainfall\_mm):  
  	ข้อมูลตัวเลขระดับน้ำและฝน ควรอยู่ภายใต้บริการนี้เพราะเป็นข้อมูลแกนหลักที่รับเข้ามา และเป็นปัจจัยตั้งต้นในการประมวลผล  
* **Disaster Status State** (disaster\_status, status\_description):   
  	ข้อมูลสถานะการเตือนภัยเป็นผลลัพธ์จาก Decision Logic ของบริการนี้ (เช่น การปรับเป็น WARNING) จึงต้องอยู่ภายใต้บริการนี้เพื่อให้สามารถควบคุมความถูกต้องของการอัปเดตได้  
* **Operational Metadata** (last\_updated, is\_outdated, is\_manual\_override):   
  	ข้อมูลควบคุมการทำงาน เป็นสิ่งจำเป็นต่อการตรวจสอบย้อนหลัง และการทำ Concurrency Control

**7️. Linked Data (Reference Only)**  
ก่อนบันทึกข้อมูลและแสดงผล ระบบจะใช้ข้อมูลอ้างอิงเพื่อระบุตัวตนของพื้นที่ผ่าน Location Service

* **area\_id** (รหัสพื้นที่จากระบบกลาง)  
* **area\_name** (ชื่อพื้นที่เพื่อความสะดวกในการแสดงผล) 

บริการนี้ไม่เก็บสำเนาข้อมูลเขตการปกครอง หรือพิกัด GIS อย่างถาวรและจะไม่มีการแก้ไขชื่อพื้นที่ในบริการนี้

**8\. Non-Functional Requirements**

* **Idempotency**:   
  	API รับข้อมูลขาเข้า (POST /ingest) ต้องตรวจสอบ timestamp เพื่อป้องกันการเขียนข้อมูลซ้ำ หรือการอัปเดตทับด้วยข้อมูลที่เก่ากว่า (Out-of-order messages)  
* **Event Delivery**:   
  	การกระจาย Event แจ้งเตือนสถานะเปลี่ยน ใช้รูปแบบ Message Delivery แบบ At-least-once (ผ่าน Message Broker)  
* **Fault Tolerance (Fallback):**   
  	หาก API ต้นทาง (เช่น กรมอุตุฯ) ล่มหรือไม่ส่งข้อมูลมาเกิน 15 นาที ระบบต้องไม่ crash แต่จะปรับค่า is\_outdated \= true และยังคงให้บริการดึงข้อมูล (GET) ค่าล่าสุดที่บันทึกไว้ได้ตามปกติ  
* **Concurrency Control:**   
  	การอัปเดตข้อมูลพร้อมกันต้องใช้กลไกป้องกัน Race Condition โดยเฉพาะการชนกันระหว่างระบบคำนวณอัตโนมัติ และการสั่ง Manual Override ของ Dispatcher  
* **Performance:**   
  	API แบบ Synchronous สำหรับดึงข้อมูล (GET /areas/{area\_id}) ต้องรองรับปริมาณ Request ที่สูงมาก (Read-heavy) ในช่วงเกิดเหตุภัยพิบัติ  
* **Security:**   
  	API สำหรับปรับสถานะด้วยตนเอง (PATCH /status) ต้องมีการ Authentication และ Authorization เพื่อยืนยันสิทธิ์ของ Dispatcher ก่อนดำเนินการ

# Sync Contract

**Synchronous Function Contract**  
**Base URL:** *http://TBD.com*

# **API Contract \#1: Ingest External Data**

### **ข้อมูลทั่วไป**

* **Name:** Ingest External Data   
* **Method:** POST   
* **Path:** /api/monitor-disaster/ingest   
* **Type:** Synchronous

### **คำอธิบาย**

###  ใช้รับข้อมูลระดับน้ำและฝนจาก API ภายนอก เพื่อนำมาประมวลผลสถานะภัยพิบัติอัตโนมัติ

### **Request**

**Headers**

* Content-Type: application/json

  **Body:** 

  {

    "area\_id": "TH-BKK-001",

    "source\_api": "RID-API",

    "water\_level\_cm": 45.0,

    "rainfall\_mm": 10.0,

    "timestamp": "2026-02-21T10:00:00Z"

  }

  **Validation:**

* area\_id, source\_api, timestamp : Required  
* water\_level\_cm, rainfall\_mm : Number (≥ 0\)

### **Response**

**Success: 200**

{

  "message": "Data ingested successfully",

  "updated\_status": "WARNING"

}

**Error: 400 Bad Request**  
{

  "error": {

    "code": "VALIDATION\_ERROR",

    "message": "Required fields are missing or invalid format",

    "traceId": "uuid"

  }

}

### **Dependency / Reliability**

* ไม่เรียก service อื่น, Idempotent (เช็ค timestamp เพื่อป้องกันข้อมูลเก่าเขียนทับ), Timeout: 30s

# **API Contract \#2: Get Area Status**

### **ข้อมูลทั่วไป**

* **Name:** Get Area Status   
* **Method:** GET   
* **Path:** /api/monitor-disaster/areas/{area\_id}   
* **Type:** Synchronous

### **คำอธิบาย**

### ใช้ดึงข้อมูลสถานการณ์น้ำปัจจุบันและสถานะภัยพิบัติล่าสุด เพื่อให้บริการหน้าบ้าน (Frontend) นำไปแสดงผลบน Dashboard ของ Dispatcher หรือแอปพลิเคชันของ Citizen

### **Request**

**Path/Query Param**

* area\_id (string, required)

  **Headers**

* Accept: application/json

  **Body:** ไม่มี

### **Response**

**Success: 200 OK**

{

  "area\_id": "TH-BKK-001",

  "disaster\_status": "WARNING",

  "water\_level\_cm": 120.5,

  "is\_outdated": false,

  "last\_updated": "2026-02-21T10:00:00Z"

}

**Error: 404 Not Found**

{

  "error": { "code": "NOT\_FOUND", "message": "Area ID not found" }

}

### **Dependency / Reliability**

* ไม่เรียก service อื่น   
* Idempotent (เป็นการอ่านข้อมูล / Read-only)   
* Timeout: 30s

# **API Contract \#3:  Override Disaster Status**

### **ข้อมูลทั่วไป**

* **Name:** Override Disaster Status   
* **Method:** PATCH   
* **Path:** /api/monitor-disaster/areas/{area\_id}/status   
* **Type:** Synchronous

### **คำอธิบาย**

### สำหรับ Dispatcher ปรับสถานะด้วยตนเอง (Manual Override) มี Priority สูงกว่าระบบอัตโนมัติ

### **Request**

**Path/Query Param**

* area\_id (string, required)

  **Headers**

* Content-Type: application/json   
* Authorization: Bearer \<token\>

  **Body:** 

  {

    "disaster\_status": "CRITICAL",

    "status\_description": "พนังกั้นน้ำพัง ต้องอพยพทันที",

    "overridden\_by": "dispatcher\_01"

  }

  **Validation**

* disaster\_status : Must be in \[NORMAL, WATCH, WARNING, CRITICAL\]  
* status\_description, overridden\_by : Required

### **Response**

**Success: 200 OK**	

{

  "message": "Status overridden successfully"

}

**Error: 403 Forbidden**

{ 

"error": 

{ 

"code": "UNAUTHORIZED\_ROLE",

 "message": "Insufficient permissions" 

} 

}

### **Dependency / Reliability**

* ไม่เรียก service อื่น  
* เป็น idempotent update  
* มี Concurrency Control (ตั้งค่า is\_manual\_override \= true เพื่อกัน Ingestion API มาเขียนทับ)  
* Timeout: 30s

# Async Contract

**Asynchronous Function Contract**

## **Message Contract \#1: Publish Disaster Status Changed**

### **ข้อมูลทั่วไป** 

* **Message Name:** DisasterStatusChanged  
* **Interaction Style:** Publish-Subscribe / Event Broadcast (Fire-and-forget)  
* **Producer:** MonitorDisaster Service  
* **Consumer:** Notification Service, Web Portal Service (และ Service อื่นๆ ที่เกี่ยวข้อง)  
* **Channel/Topic:** MonitoringDisaster-Topic (Amazon SNS)  
* **Version:** v1

### **คำอธิบาย**

### กระจายข่าว (Publish event) แบบ asynchronous เมื่อระบบตรวจพบว่าสถานะภัยพิบัติ (NORMAL ⇄ WATCH ⇄ WARNING ⇄ CRITICAL) ของพื้นที่ใดพื้นที่หนึ่งมีการเปลี่ยนแปลง เพื่อให้ระบบอื่น ๆ (เช่น Notification Service) นำไปแจ้งเตือนประชาชนต่อทันที โดย Service ของเราไม่ต้องรอการตอบกลับ 

### **Request** 

### **Message Headers (Metadata บน SNS/SQS)**

* **messageType:** DisasterIncidentReported  
* **eventId:** ใช้ incident\_id (UUID) เพื่อระบุตัวตนของ Event และป้องกันการประมวลผลซ้ำ  
* **publishedAt:** ISO-8601 datetime

  **Message Body**

  {

    "incident\_id": "b1b86d1b-7a19-4b41-893d-XXXXXXXXXXXX",

    "incident\_type": "flood",

    "exact\_location": "TH-BKK-001",

    "impact\_level": 3,

    "status": "Reported",

    "reported\_by": "SYSTEM\_AUTO",

    "created\_at": "2026-03-08T15:05:00.000Z",

    "details": {

      "water\_level\_cm": 120.5,

      "rainfall\_mm": 80.0,

      "previous\_status": "NORMAL"

    }

  }




  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| incident\_id | UUID | Y | รหัสอ้างอิงเหตุการณ์ที่สร้างขึ้นใหม่ (ใช้เป็น Event ID ได้) |
| incident\_type | String | Y | ประเภทของภัยพิบัติ (ค่าเริ่มต้นคือ "flood") |
| exact\_location | String | Y | รหัสพื้นที่ที่เกิดเหตุ (อ้างอิงจาก area\_id) |
| impact\_level | Number | Y | ระดับความรุนแรง (1 \= NORMAL, 2 \= WATCH, 3 \= WARNING, 4 \= CRITICAL) |
| status | String | Y | สถานะของการรายงาน (เช่น "Reported") |
| reported\_by | String | Y | ระบุสาเหตุการเกิด Event เช่น "SYSTEM\_AUTO" (ระบบอัตโนมัติ) หรือระบุรหัส Dispatcher (กรณีทำ Manual Override) |
| created\_at | Timestamp | Y | วันที่และเวลาที่สร้าง Event (ISO-8601) |
| details | Object | Y | ข้อมูลเซ็นเซอร์และสถานะแวดล้อมที่เกี่ยวข้องกับเหตุการณ์ |
| details.water\_level\_cm | Float | Y | ระดับน้ำล่าสุด ณ เวลาที่เกิดเหตุการณ์ |
| details.rainfall\_mm | Float | Y | ปริมาณน้ำฝนล่าสุด ณ เวลาที่เกิดเหตุการณ์ |
| details.previous\_status | String | Y | สถานะความรุนแรงก่อนหน้าที่จะเกิด Event นี้ |

**Validation Rules**

* incident\_id ต้องไม่เป็นค่าว่างและต้องเป็นรูปแบบ UUID  
* exact\_location ต้องไม่เป็นค่าว่าง  
* impact\_level ต้องเป็นตัวเลขจำนวนเต็มตั้งแต่ 1 ถึง 4  
* details.water\_level\_cm และ details.rainfall\_mm ต้อง \>= 0

**Response**   
	เนื่องจากเป็น Broadcast Interaction Style บริการ MonitoringDisaster (Producer) จะไม่มีการรอรับ Message Response หรือ Payload กลับจาก Consumer ในทุกกรณี (Fire-and-forget)

**Expected Behavior:**

* **Consumer Services:** เมื่อตู้รับจดหมาย (SQS) ของ Consumer ได้รับ Event จะทำการดึง exact\_location และ impact\_level เพื่อไปทริกเกอร์ Business Logic ของตนเอง (เช่น หาก impact\_level \= 4 ให้ระบบ Notification ส่ง SMS อพยพด่วน)  
* **Idempotency:** ฝั่ง Consumer ต้องใช้ incident\_id ในการตรวจสอบเทียบกับฐานข้อมูลของตนเอง เพื่อป้องกันการประมวลผลซ้ำ (กรณี Message Broker มีการทำงานแบบ At-least-once delivery)

# Service Data

# **Service Data**

**1\) Area Disaster Operational State (Owned by this service)** ข้อมูลตารางหลักที่เก็บสถานะล่าสุดของแต่ละพื้นที่ เพื่อใช้ในการตัดสินใจและแสดงผลแบบเรียลไทม์

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| area\_id | string | Y (Primary Key) | รหัสพื้นที่ (อ้างอิง Location Service) | TH-BKK-001 |
| area\_name | string | Y | ชื่อพื้นที่เพื่อความสะดวกในการแสดงผล | Bangkok \- Don Mueang |
| water\_level\_cm | float | Y | ระดับน้ำล่าสุด ณ ปัจจุบัน | 120.50 |
| rainfall\_mm | float | Y | ปริมาณน้ำฝนสะสมล่าสุด | 185.20 |
| disaster\_status | enum | Y | NORMAL / WATCH / WARNING / CRITICAL | WARNING |
| status\_description | string | N | รายละเอียด (ระบบใส่ให้ หรือ Dispatcher พิมพ์) | น้ำล้นตลิ่งเข้าพื้นที่ต่ำ |
| is\_outdated | boolean | Y | true ถ้าระบบไม่ได้รับ API อัปเดตเกิน 15 นาที | false |
| source\_api | string | Y | รหัส API ต้นทางที่ส่งข้อมูลมาให้ | TMD-Weather-API |
| is\_manual\_override | boolean | Y | true ถ้าระบุโดย Dispatcher (กัน API เขียนทับ) | false |
| last\_updated | datetime | Y | เวลาที่ข้อมูลแถวนี้มีการแก้ไขล่าสุด | 2026-02-21T10:00:00Z |

**2\) Disaster Status Audit Log (Owned by this service)**  
ข้อมูลประวัติการเปลี่ยนแปลงสถานะ (History) เพื่อใช้ตรวจสอบย้อนหลังว่าใครเป็นคนเปลี่ยนสถานะ และใช้เป็นฐานข้อมูลสำหรับยิง Async Event แจ้งเตือน

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| logId | uuid | Y (Primary Key) | รหัสบันทึกประวัติ (ใช้เป็น eventId ตอน Publish) | 550e8400-e29b-... |
| area\_id | string | Y *(Foreign Key)* | อ้างอิงรหัสพื้นที่ที่เกิดการเปลี่ยนแปลง | TH-BKK-001 |
| previous\_status | enum | Y | สถานะก่อนหน้า | WATCH |
| new\_status | enum | Y | สถานะใหม่ที่ถูกเปลี่ยน | WARNING |
| water\_level\_cm | float | Y | ระดับน้ำ ณ เวลาที่บันทึกประวัตินี้ | 120.50 |
| rainfall\_mm | float | Y | ปริมาณน้ำฝน ณ เวลาที่บันทึกประวัตินี้ | 185.20 |
| triggered\_by | string | Y | รหัสผู้สั่งเปลี่ยน (Dispatcher) หรือ "SYSTEM\_AUTO" | SYSTEM\_AUTO |
| createdAt | datetime | Y | เวลาที่เกิดการเปลี่ยนแปลงสถานะ | 2026-02-21T10:00:00Z |

###  **3\) ตาราง incident\_reports** 

ตารางเพื่อเก็บบันทึกว่าเราได้สร้าง Incident แจ้งไปยังระบบส่วนกลางแล้วหรือยัง (ป้องกันการส่งซ้ำและใช้ตรวจสอบเมื่อเน็ตหลุด)

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| incident\_id | uuid | Y (Primary Key) | รหัส Incident (Primary Key) สำหรับใช้อ้างอิงกับระบบส่วนกลาง | 550e8400-e29b-...33 |
| area\_id | string | Y (Foreign Key) | อ้างอิงรหัสพื้นที่ที่เกิดการเปลี่ยนแปลง | TH-BKK-001 |
| incident\_type | string | Y | ประเภทของภัยพิบัติ (Service นี้ "flood") | flood |
| incident\_description | string | N | คำอธิบายเหตุการณ์ | Status changed to CRITICAL due to water level reaching 155.0 cm. |
| impact\_level | integer(1-4) | Y | ระดับความรุนแรงตาม Schema กลาง | 4 |
| threshold\_water\_cm | float | Y | ค่าระดับน้ำที่เป็นเกณฑ์ทำให้ตัดสินใจเปิด Incident นี้ | 155.00 |
| threshold\_rain\_mm | float | Y | ค่าปริมาณฝนที่เป็นเกณฑ์ทำให้ตัดสินใจเปิด Incident นี้ | 120.50 |
| sync\_status | enum | Y | สถานะการส่งข้อมูลไปยังส่วนกลาง (เช่น SUCCESS, PENDING, FAILED) | SUCCESS |
| reported\_at | datetime | Y | เวลาที่ออกรายงาน Incident ฉบับนี้ | 2026-02-21T10:00:00Z |

