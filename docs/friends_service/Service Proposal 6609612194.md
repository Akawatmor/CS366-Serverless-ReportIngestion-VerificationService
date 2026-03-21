# Service Overview

**ภาพรวมของบริการ (Service Overview)**  
Pre-Arrival Notification Service  
Github: [https://github.com/Bommxun2/songtor](https://github.com/Bommxun2/songtor)

1. **Service Owner**

นายวชิรกรณ์ ชิน รหัสนักศึกษา 6609612194 ภาคปกติ

2. **Service Purpose**

Pre-Arrival Notification Service เป็นบริการรับผิดชอบเรื่องจัดการข้อมูลของผู้ป่วยที่กำลังเดินทางมาที่โรงพยาบาล โดยทำหน้าที่เป็นศูนย์กลางการสื่อสารระหว่างรถพยาบาลและโรงพยาบาล เพื่อแจ้งเตือนอาการ ความร้ายแรง และส่งต่อข้อมูลมัลติมีเดียล่วงหน้า สนับสนุนให้ทีมแพทย์เตรียมความพร้อมและเครื่องมือเฉพาะทางได้ทันท่วงที

3. **Pain Point ที่แก้ไข**

ห้องฉุกเฉินและทีมแพทย์เฉพาะทางเตรียมการรับมือผู้ป่วยฉุกเฉินไม่ทัน เพราะไม่ทราบข้อมูลอาการและเวลาที่จะมาถึงล่วงหน้า ทำให้เสียเวลาในการเตรียมทีมและอุปกรณ์เมื่อรถพยาบาลมาถึง

**3️. Target Users**

* Hospital staff

**4️. Service Boundary**

* In-scope Responsibilities  
  * การบันทึกข้อมูลผู้ป่วยใหม่ อาการ และสัญญาณชีพ  
  * การรับและจัดการไฟล์มัลติมีเดีย เช่น รูปภาพบาดแผล  
  * การอัปเดตสถานะการเดินทางและการส่งมอบผู้ป่วย

* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
  * การสั่งการ จัดสรร หรือติดตามเวรของรถพยาบาล  
  * การจัดการและประมวลผลข้อมูลพิกัด  
  * การบริหารจัดการคลังเลือด หรือเตียงในโรงพยาบาล  
  * การจัดการข้อมูลประวัติการรักษาผู้ป่วยระยะยาว

**5️. Autonomy / Decision Logic**  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การติดแท็กระดับความวิกฤตเพื่อยกระดับการแจ้งเตือน  
* การแจ้งเตือนความผิดปกติของสัญญาณและสลับไปใช้พิกัดล่าสุดแทน

การตัดสินใจอิงจาก:

* ระดับความฉุกเฉินและอาการ  
* จำนวนผู้ป่วยที่กำลังเดินทางมา  
* Timestamp ของข้อมูลพิกัดล่าสุดที่ได้รับ  
* ระยะห่างจากพิกัดปัจจุบันถึงโรงพยาบาลปลายทาง

บริการสามารถตัดสินใจได้เองภายใต้ business rules ที่กำหนด โดยไม่ต้องรอ/ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ

**6️. Owned Data**

* Pre-Arrival Notification Record   
  ข้อมูลพื้นฐานของการแจ้งเตือนควรอยู่ภายใต้บริการนี้เพราะเป็นข้อมูลแกนหลักของ domain และบริการนี้เป็นผู้สร้างข้อมูลดังกล่าวโดยตรงเมื่อได้รับคำขอจากรถพยาบาล  
* Clinical & Vitals Data   
  ข้อมูลอาการและสัญญาณชีพเป็น state ที่สามารถเปลี่ยนแปลงได้ตลอดเวลาระหว่างทาง จึงต้องอยู่ภายใต้บริการนี้เพื่อให้สามารถควบคุมความถูกต้องของข้อมูลที่ส่งให้โรงพยาบาลดู

**7️. Linked Data (Reference Only)**

* ก่อนบันทึกการแจ้งเตือนและระหว่างการเดินทาง ระบบจะเชื่อมโยงกับข้อมูลจาก Service อื่นๆ  
  * hospital\_id เพื่อระบุปลายทาง  
  * ambulance\_id หรือ dispatcher\_id เพื่อระบุแหล่งที่มา  
  * location และ eta\_timestamp เพื่อระบุการเดินทาง  
* บริการจะไม่เก็บข้อมูลพิกัดทุกๆวินาทีลง database แต่จะทำการ request ไปที่ Tracking Service เพื่อดึงเวลาที่คาดว่าจะมาถึงล่าสุดมาเก็บลง cache และแสดงผลให้หน้าจอของโรงพยาบาลทราบ  
* หาก Tracking Service ตรวจพบว่าสัญญาณรถพยาบาลหายไป Tracking Service จะทำหน้าที่แค่อัปเดตสถานะแจ้งเตือนบนหน้าจอให้พยาบาลทราบ

**8\. Non-Functional Requirements**

* ต้องมีการตรวจสอบ notification\_id จาก request เพื่อป้องกันการสร้างเคสซ้ำซ้อนในกรณีที่แอปพลิเคชันฝั่งรถพยาบาลเกิดการ retry  
* การรับส่งข้อมูลพิกัดมีการใช้ message delivery แบบ at-most-once ที่ยอมรับการสูญหายบางส่วนเพื่อให้รองรับ throughput สูงสุดและลด latency  
* หากสัญญาณอินเทอร์เน็ตของรถพยาบาลขาดหายเกิน 5 นาที ให้เปลี่ยนสถานะเป็น Connection Lost อัตโนมัติ พร้อมตอบกลับพิกัดสุดท้ายที่บันทึกไว้  
* ระบบต้องไม่ crash เมื่อได้รับ payload สัญญาณชีพ หรือ GPS ที่ขาดหายหรือไม่ผิดรูปแบบ  
* API แบบ synchronous ต้องมีการ authentication อย่างเข้มงวด เนื่องจากมีการรับส่งข้อมูลด้านสุขภาพที่อ่อนไหว

# Sync Contract

**Synchronous Function Contract**  
**Base URL:** http://api.hospital-net.com

# **API Contract \#1: Create Notification**

### **ข้อมูลทั่วไป**

* **Name:** Create new pre-arrival notification  
* **Method:** POST  
* **Path:** /v1/notifications  
* **Type:** Synchronous

### **คำอธิบาย**

### ใช้สร้างบันทึกการแจ้งเตือนล่วงหน้าเมื่อรถพยาบาลรับผู้ป่วยและเริ่มออกเดินทาง เพื่อส่งข้อมูลอาการและสัญญาณชีพให้ห้องฉุกเฉินปลายทางเตรียมตัว

### **Request**

**Path/Query Params:** None

**Headers**

* Content-Type: application/json  
* Authorization: Bearer \<token\>  
* Idempotency-Key: \<uuid\>  
  **Body:**

  {

  "hospital\_Id": "HOS-001",

  "ambulance\_Id": "AMB-BKK-009",

  "patient\_info": 

  {

  "age": 45,

  "gender": "M"

  },

  "triage\_level": "RED",

  "symptom": "Cardiac Arrest",

  "vitals":

  {

  "bp": "80/50",

  "hr": 120,

  "spo2": 85

  },

  attachment\_urls: \[

  	“https://example.png”

  \]

  }

**Validation**

* hospital\_id and triage\_level and symptom required  
* triage\_level ∈ {RED, YELLOW, GREEN, BLACK}


### **Response**

**Success: 201 Created**

	{

"notification\_id": "NOTIF-20261027-005",

"status": "EN\_ROUTE",

"message": "Notification received. ER team alerted."

}

**Error: 400 Bad Request**

{

"error": 

{

"code": "VALIDATION\_ERROR",

"message": "hospital\_id required",

"trace\_id": "uuid"

}

}

### **Dependency / Reliability**

* เรียก Service เพื่อตรวจสอบว่า hospital\_id และ ambulance\_Id มีอยู่จริงและเปิดรับเคสอยู่  
* มีการตรวจสอบ Idempotency-Key เพื่อป้องกันข้อมูลซ้ำซ้อน

# **API Contract \#2: List Incoming Patients**

### **ข้อมูลทั่วไป**

* **Name:** List incoming notifications  
* **Method:** GET  
* **Path:** /v1/hospitals/{hospital\_id}/incoming-notifications  
* **Type:** Synchronous

### **คำอธิบาย**

### ใช้ดึงข้อมูลรายการผู้ป่วยทั้งหมดที่กำลังเดินทางมายังโรงพยาบาลเป้าหมาย เพื่อให้ระบบ Dashboard ของห้องฉุกเฉิน (ER) ดึงไปแสดงผลแบบเรียลไทม์

### **Request**

**Path/Query Param**

* hospital\_id (string, required)  
* ?status (string, optional, default="EN\_ROUTE") 

  **Headers**

* Content-Type: application/json  
* Authorization: Bearer \<token\>

  **Body:** None

  **Validation:** None


### **Response**

**Success: 200 ok**

{

"hospital\_id": "HOS-001",

"items": \[

{

"notification\_id": "NOTIF-20261027-005",

"ambulance\_id": "AMB-BKK-009",

"patient\_info": 

{

"age": 45,

"gender": "M"

},

"triage\_level": "RED",

"symptom": "Cardiac Arrest",

"vitals":

{

"bp": "80/50",

"hr": 120,

"spo2": 85

},

attachment\_urls: \[

	“https://example.png”

\],

"status": "EN\_ROUTE"

}

\]

}

**Error: 404 Not Found**

{

"error": {

"code": "NOT\_FOUND",

"message": "Hospital ID not found",

"trace\_id": "uuid"

}

}

### **Dependency / Reliability**

* ไม่เรียก service อื่น  
* เป็น Idempotent

# **API Contract \#3: Update Status**

### **ข้อมูลทั่วไป**

* **Name:** Update notification status  
* **Method:** PATCH  
* **Path:** /v1/notifications/{notification\_id}/status  
* **Type:** Synchronous

### **คำอธิบาย**

### ใช้อัปเดตสถานะของการแจ้งเตือน เช่น เมื่อรถพยาบาลเดินทางมาถึงโรงพยาบาลแล้ว หรือเมื่อมีการยกเลิกเคสระหว่างทาง

### **Request**

**Path/Query Param**

* notification\_id (string, required)

  **Headers**

* Content-Type: application/json  
* Authorization: Bearer \<token\>

  **Body:** 

  {

  "status": "ARRIVED",

  "arrival\_time": "2026-10-27T14:28:00Z"

  }

  **Validation:**

* status required  
* status ∈ {EN\_ROUTE, ARRIVED, HANDOVER\_COMPLETED, CANCELLED}


### **Response**

**Success: 200 ok**

{

"notification\_id": "NOTIF-20261027-005",

"status": "ARRIVED",

"arrival\_time": "2026-10-27T14:28:00Z",

"message": "success"

}

	

**Error: 400 Bad Request**

{

"error": {

"code": "INVALID\_STATE\_TRANSITION",

"message": "Cannot change status",

"trace\_id": "uuid"

}

}

### **Dependency / Reliability**

* ไม่เรียก service อื่น  
* ถือเป็น Idempotent update  
* Timeout: 10s




# Async Contract

**Asynchronous Function Contract**

## **Message Contract \#1: RequestAmbulanceDivert**

### **ข้อมูลทั่วไป** 

* **Message Name:** RequestAmbulanceDivert  
* **Interaction Style:** Request–Async Response (via Message Broker)  
* **Producer:** Hospital Resource Service  
* **Consumer:** Pre-Arrival Notification Service  
* **Channel/Queue:** prearrival.commands.v1  
* **Version:** v1

### **คำอธิบาย**

### ส่งคำสั่งเพื่อขอเปลี่ยนเส้นทางโรงพยาบาลปลายทางของรถพยาบาลในกรณีที่ห้องฉุกเฉินเต็มหรือล้นทะลักแบบ asynchronous โดยผู้ส่งจะได้รับแจ้งผลลัพธ์ว่าเปลี่ยนข้อมูลสำเร็จหรือไม่ผ่าน result event

### **Request** 

### **Message Headers**

* message\_type: RequestAmbulanceDivert  
* message\_id: UUID  
* reply\_to: hospital.resource.results.v1  
* sent\_at: ISO-8601 datetime

  **Message Body**

  {

  "notification\_id": "NOTIF-20261027-005",

  "request\_id": "REQ-DIV-8899",

  "current\_hospital\_id": "HOS-001",

  "new\_hospital\_id": "HOS-002",

  "reason": "ER\_CAPACITY\_FULL",

  "requested\_by": "HospitalResourceService"

  }


  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| notification\_id | string | Y | รหัสการแจ้งเตือนของเคสที่ต้องการเปลี่ยนเส้นทาง |
| request\_id | string | Y | รหัสคำขอจากฝั่งต้นทาง |
| current\_hospital\_id | string | Y | รหัสโรงพยาบาลเดิม |
| new\_hospital\_id | string | Y | รหัสโรงพยาบาลปลายทางแห่งใหม่ |
| reason | string | Y | เหตุผลที่ต้องเปลี่ยนเส้นทาง |
| requested\_by | string | Y | ชื่อ service ผู้ส่ง |

**Validation Rules**

* notification\_id, currentHospital\_id, newHospital\_id ต้องไม่ว่าง  
* newHospital\_id ต้องไม่ตรงกับ current\_hospital\_id  
* message\_id ต้องไม่ซ้ำกับ message ที่เคยประมวลผลแล้ว (idempotency check)

**Response**

	**Message Headers** 

* message\_type: AmbulanceDivertConfirmed  
* message\_id: UUID ของข้อความนี้  
* correlation\_id: request.message\_id  
* sent\_at: ISO-8601 datetime

  **Success Message Body**

  {

  "notification\_id": "NOTIF-20261027-005",

  "request\_id": "REQ-DIV-8899",

  "new\_hospital\_id": "HOS-002",

  "status": "CONFIRMED"

  }


  **Reject/Error Message Body**

  {

  "notification\_id": "NOTIF-20261027-005",

  "request\_id": "REQ-DIV-8899",

  "status": "REJECTED",

  "reason\_code": "TOO\_LATE",

  "reason\_message": "Cannot divert. Ambulance has already arrived."

  }


  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| notification\_id | string | Y | รหัสการแจ้งเตือนที่เกี่ยวข้อง |
| request\_id | string | Y | รหัสคำขอจากระบบต้นทาง ใช้เชื่อมโยง workflow |
| new\_hospital\_id | string | Y | รหัสโรงพยาบาลแห่งใหม่ที่อัปเดตสำเร็จ |
| status | string | Y | สถานะผลลัพธ์ของคำสั่งย้าย |
| reason\_code | string | Y | รหัสเหตุผล |
| reason\_message | string | Y | ข้อความอธิบาย |

	**Validation Rules**

* correlation\_id ต้องตรงกับ message\_id ของ request ที่เคยได้รับ  
* ถ้า status \= CONFIRMED ต้องมี new\_hospital\_id  
* ถ้า status \= REJECTED ต้องมี reason\_code และ reason\_message  
* reason\_code ต้องเป็นค่าที่กำหนดไว้ล่วงหน้า (เช่น TOO\_LATE, NOT\_FOUND)

**Asynchronous Function Contract**

## **Message Contract \#2: HospitalInboundLoadRequested**

### **ข้อมูลทั่วไป** 

* **Message Name:** HospitalInboundLoadRequested  
* **Interaction Style:** Request–Async Response (via Message Broker)  
* **Producer:** Dispatcher Service  
* **Consumer:** Pre-Arrival Notification Service  
* **Channel/Queue:** prearrival.dispatch.queries.v1  
* **Version:** v1

### **คำอธิบาย**

ศูนย์สั่งการส่งคำขอแบบ asynchronous เพื่อดึงข้อมูลประเมินภาพรวมของผู้ป่วยฉุกเฉินทั้งหมดที่กำลังเดินทางไปยังแต่ละโรงพยาบาล เพื่อให้เจ้าหน้าที่ศูนย์สั่งการตัดสินใจจัดส่งย้ายเคสถ้ากระจุกตัวที่โรงพยาบาลเดียว และประเมินว่าโรงพยาบาลในโซนนั้นกำลังจะล้นหรือไม่ และต้องสั่งตั้งโรงพยาบาลสนามด่วนหรือไม่

### **Request** 

### **Message Headers**

* message\_type: HospitalInboundLoadRequested  
* message\_id: UUID  
* reply\_to: dispatch.load.results.v1  
* sent\_at: ISO-8601 datetime

  **Message Body**

  {

  "request\_id": "REQ-LOAD-8812", 

  "target\_hospital\_id": \["HOS-001", "HOS-002", "HOS-005"\], 

  "requested\_by": "DispatcherService"

  }


  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| request\_id | string | Y | รหัสคำขอจากระบบศูนย์สั่งการ |
| target\_hospital\_id | array | Y | รายชื่อรหัสโรงพยาบาลที่ศูนย์สั่งการต้องการเช็คยอดผู้ป่วยที่กำลังไป |
| requested\_by | string | Y | ชื่อ service ผู้ส่ง |

**Validation Rules**

* request\_id, target\_hospital\_ids, requested\_by ต้องไม่ว่าง  
* target\_hospital\_ids ต้องเป็น Array ที่มีค่าอย่างน้อย 1 รายการ  
* message\_id ต้องไม่ซ้ำกับ message ที่เคยประมวลผลแล้ว (idempotency check)

**Response**

	**Message Headers** 

* message\_type: HospitalInboundLoadProvided  
* message\_id: UUID ของข้อความนี้  
* correlation\_td: request.message\_id  
* sent\_at: ISO-8601 datetime

  **Success Message Body**

  {

  "request\_id": "REQ-LOAD-8812", 

  "inbound\_loads": \[ 

  {

  "hospital\_id": "HOS-001",

  "total\_en\_route": 12, 

  "triage\_summary": { "RED": 5, "YELLOW": 4, "GREEN": 3 } 

  }, 

  { 

  "hospital\_id": "HOS-002", 

  "total\_en\_route": 2, 

  "triage\_summary": { "RED": 0, "YELLOW": 2, "GREEN": 0 }

  }

  \],

  "status": "CONFIRMED",

  }

  **Reject/Error Message Body**

  {

  "request\_id": "REQ-LOAD-8812", 

  "status": "REJECTED",

  "reason\_code": "INVALID\_HOSPITAL\_LIST", 

  "reason\_message": "Contains invalid data formats."

  }


  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| request\_id | string | Y | รหัสคำขอจากระบบต้นทาง ใช้เชื่อมโยง workflow |
| inbound\_loads | array | Y | สรุปจำนวนผู้ป่วยที่กำลังเดินทาง แยกตามโรงพยาบาล |
| status | string | Y | สถานะผลลัพธ์ของการอัปเดตข้อมูล |
| reason\_code | string | Y | รหัสเหตุผล |
| reason\_message | string | Y | ข้อความอธิบาย |

	**Validation Rules**

* correlation\_id ต้องตรงกับ message\_id ของ request ที่เคยได้รับ  
* ถ้า status \= CONFIRMED ต้องมี inbound\_loads

# Service Data

# **Service Data**

# **1\) Pre-Arrival Notification Record (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| notification\_id | string | Y (Primary Key) | รหัสการแจ้งเตือน | NOTIF-20261027-005 |
| hospital\_id | string | Y  (Reference only) | รหัสโรงพยาบาลปลายทาง | HOS-001 |
| ambulance\_id | string | Y  (Reference only) | รหัสรถพยาบาล | AMB-BKK-009 |
| arrival\_time | datetime | N | เวลาที่เดินทางมาถึง | 2026-10-27T14:30:00Z |
| status | enum | Y | EN\_ROUTE / ARRIVED / HANDOVER\_COMPLETED / CANCELLED | EN\_ROUTE |
| idempotency\_key | uuid | Y | ป้องกันการสร้างเคสซ้ำซ้อน | 3f1e2a7c-... |
| created\_at | datetime | Y | เวลาที่สร้างการแจ้งเตือน | 2026-10-27T14:00:00Z |
| updated\_at | datetime | Y | เวลาที่แก้ไขข้อมูลล่าสุด | 2026-10-27T14:28:00Z |

# **2\) Clinical & Patient Data (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| notification\_id | string | Y (Foreign Key) | อ้างอิงรหัสการแจ้งเตือน  | NOTIF-20261027-005 |
| triage\_level | enum | Y | ระดับความฉุกเฉิน (RED, YELLOW, GREEN, BLACK)  | RED |
| symptom | string | Y | อาการเบื้องต้น | Cardiac Arrest |
| patient\_age | integer | N | อายุผู้ป่วยโดยประมาณ | 45 |
| patient\_gender | enum | N | เพศผู้ป่วย (M / F / U) | M |
| bp | string | N | ความดันโลหิต  | 80/50 |
| hr | integer | N | อัตราการเต้นหัวใจ | 120 |
| spo2 | integer | N | ค่าออกซิเจนในเลือด  | 85 |
| attachment\_urls | json | N | ลิงก์รูปภาพบาดแผล | \["https://example.png"\] |

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