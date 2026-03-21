# Service Overview

ภาพรวมของบริการ (Service Overview)  
Shelter Service

1. Service Owner

นายณัฐนนท์ ดวงจินดา รหัสนักศึกษา 6609611923 ภาคปกติ

2. Service Purpose

Shelter Service เป็นบริการที่รับผิดชอบการจัดการข้อมูลศูนย์พักพิง ความจุที่เหลืออยู่ พิกัดที่ตั้ง และสภาพเส้นทางการเข้าถึง (Access Level) แบบ Real-time โดยทำหน้าที่เป็นแหล่งข้อมูลหลักในการค้นหา อัปเดตสถานะ และจัดสรรผู้ประสบภัยไปยังศูนย์พักพิงที่เหมาะสมที่สุดและสามารถเดินทางไปได้จริง เพื่อสนับสนุนการทำงานของเจ้าหน้าที่ในระบบตอบสนองภัยพิบัติ

3. Pain Point ที่แก้ไข

ในภาวะฉุกเฉิน (เช่น น้ำท่วม) ข้อมูลศูนย์พักพิงมักไม่อัปเดต เจ้าหน้าที่ไม่รู้ว่าศูนย์พักพิงไหน 'เต็ม' หรือ 'ยังว่าง' รวมถึงไม่รู้ว่าที่ไหนอยู่ใกล้และเส้นทางปลอดภัยพอที่จะเข้าไปได้หรือไม่ ทำให้เกิดการส่งคนไปผิดที่ เกิดความแออัด วุ่นวาย และผู้ประสบภัยอาจติดค้างระหว่างทาง บริการนี้จึงออกแบบมาเพื่อให้การอัปเดตความจุและสภาพเส้นทางมีความถูกต้องทันที (Real-time decision support) หากไม่มี Service นี้ ระบบโดยรวม (Ecosystem) จะขาดแหล่งอ้างอิงข้อมูลความจุที่เป็นศูนย์กลาง (Single Source of Truth) ส่งผลให้ระบบประสานงานอพยพทำงานผิดพลาด สั่งการทับซ้อนกันจนเกิด Race Condition และส่งผู้ประสบภัยเข้าไปในพื้นที่อันตรายได้

4\. Target Users

* เจ้าหน้าที่ศูนย์พักพิง (Shelter Staff)  
* ทีมกู้ภัย / ผู้ประสานงาน (Rescue Team / Dispatcher)  
* ระบบประสานงานอพยพส่วนกลาง (Evacuation Coordination Service \- ใช้งานผ่าน API)

5\. Service Boundary

* In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)  
  * จัดเก็บข้อมูลศูนย์พักพิงและพิกัดที่ตั้ง (Shelter Master Data & Location)  
  * จัดการสถานะ ความจุที่เหลืออยู่ และระดับความปลอดภัยของเส้นทาง (Operational State & Access Level)  
  * คำนวณระยะทางเบื้องต้นและคัดกรองศูนย์พักพิงที่เหมาะสม (Distance & Availability Filtering)  
  * บังคับใช้กติกาการจัดสรรความจุ ป้องกันการรับคนเกินกำหนด (Capacity Allocation Rules)

* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
  * การจัดการข้อมูลเหตุการณ์ภัยพิบัติหลัก (Incident Master Data)  
  * การวางแผนระบบนำทางแบบละเอียด (Turn-by-turn Navigation)  
  * ข้อมูลส่วนบุคคลเชิงลึกของผู้เข้าพัก (Personal Identifiable Information ของผู้ประสบภัย)

6\. Autonomy / Decision Logic  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การยืนยันหรือปฏิเสธการ Check-in จะอิงจากความจุที่เหลือ (Capacity Limit) อย่างเด็ดขาดเพื่อรักษามาตรฐานความปลอดภัยและป้องกันความแออัดขั้นวิกฤตในศูนย์พักพิง โดยไม่ต้องเสียเวลารอเจ้าหน้าที่มนุษย์อนุมัติ)  
* การปรับเปลี่ยนสถานะของศูนย์พักพิงโดยอัตโนมัติ (เช่น เปลี่ยนสถานะเป็น FULL ทันทีเมื่อ current\_occupancy เท่ากับ total\_capacity)

การตัดสินใจอิงจาก:

* ระยะทางจากพิกัดผู้ประสบภัย (Distance)  
* จำนวนความจุที่ยังว่าง (Available Capacity)  
* ความปลอดภัยของเส้นทางเข้าถึง (Access Level เช่น SAFE \> DIFFICULT)

บริการสามารถตัดสินใจได้เองภายใต้ business rules ที่กำหนด โดยไม่ต้องรอ/ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ

7\. Owned Data

* Shelter Master Data: ข้อมูลพื้นฐานและพิกัด (Lat/Long) ของศูนย์พักพิง บริการนี้ต้องเป็นเจ้าของเพราะเป็นแกนหลักของการค้นหา  
* Operational Capacity State: ข้อมูลความจุ จำนวนผู้เข้าพักปัจจุบัน (Occupancy) และสถานะ (Status) ซึ่งเปลี่ยนแปลงตลอดเวลาและต้องใช้ตัดสินใจรับคน  
* Access Condition: ข้อมูลสภาพเส้นทางเข้าสู่ศูนย์ (access\_level, access\_note) เพื่อป้องกันการส่งคนเข้าไปในพื้นที่อันตราย

8\. Linked Data (Reference Only)

* User/Staff ID: เพื่อตรวจสอบสิทธิ์ว่าใครเป็นผู้อัปเดตสถานะหรือสภาพเส้นทาง  
* Incident ID (ถ้ามีระบบส่วนกลาง): อ้างอิงว่าการเปิดศูนย์พักพิงนี้ผูกกับเหตุการณ์ภัยพิบัติใด (เช่น รหัสเหตุการณ์น้ำท่วมเชียงราย) โดยบริการนี้จะไม่เก็บรายละเอียดของเหตุการณ์ไว้เอง

9\. Non-Functional Requirements

* การทำรายการที่ส่งผลต่อความจุ (Occupancy Update) ต้องใช้กลไกป้องกัน Race Condition (เช่น Database Transaction หรือ Optimistic Locking) เพื่อป้องกันการส่งคนไปพร้อมกันจนเกินความจุ  
* API สำหรับการค้นหาศูนย์ (Find Available Shelter) แบบ Synchronous ต้องตอบสนองอย่างรวดเร็ว (Low Latency) และมีการ Authentication  
* ระบบต้องไม่ Crash เมื่อได้รับข้อมูลพิกัด (Lat/Long) ที่ผิดรูปแบบ หรือข้อมูลสถานะที่ไม่ถูกต้อง และตอบกลับด้วย Error Code ที่เหมาะสม (เช่น 409 Conflict เมื่อที่พักเต็ม)  
* รองรับการ Retry ไม่เกิน 3 ครั้ง ในกรณีที่ระบบ Network มีปัญหาขณะอัปเดตข้อมูลความจุ

# Sync Contract

Synchronous Function Contract  
Base URL:

# API Contract \#1: Find Available Shelter

### ข้อมูลทั่วไป

* Name: Find available shelters by location  
* Method: GET  
* Path: /v1/shelters  
* Type: Synchronous

### คำอธิบาย

### ใช้ค้นหาและกรองศูนย์พักพิงที่ยังมีสถานะเปิดรับ (OPEN) โดยคำนวณระยะทางจากพิกัดผู้ประสบภัย

เนื่องจากผู้เรียกต้องการผลลัพธ์แบบ Real-time เพื่อใช้ตัดสินใจช่วยเหลือหน้างานทันที โดยยอมรับข้อจำกัดเรื่อง Timeout (30s) ได้หากเครือข่ายมีปัญหา ดีกว่าการได้รับข้อมูลที่ไม่อัปเดต

### Request

Path/Query Params

* user\_lat (decimal, required): พิกัดละติจูดของผู้ประสบภัย  
* user\_long (decimal, required): พิกัดลองจิจูดของผู้ประสบภัย  
* radius\_km (number, optional, default \= 10): รัศมีการค้นหา

  Headers

* Accept: application/json

  Body: ไม่มี

### Response

Success: 200

`{`

  `"items": [`

    `{`

      `"shelterId": "SHE-1234",`

      `"name": "โรงเรียนวัดเวฬุวัน",`

      `"distanceKm": 1.2,`

      `"accessLevel": "DIFFICULT",`

      `"accessNote": "รถเล็กเข้าไม่ได้ น้ำท่วม 30cm",`

      `"capacityAvailable": 55,`

      `"status": "OPEN"`

    `}`

  `]`

`}`

Error:  400

`{`

  `"error": {`

    `"code": "VALIDATION_ERROR",`

    `"message": "user_lat and user_long are required",`

    `"traceId": "uuid-112233"`

  `}`

`}`

### Dependency / Reliability

* ไม่เรียก service อื่น  
* Idempotent  
* Timeout: 30s

# API Contract \#2: Update Shelter Access & Status

### ข้อมูลทั่วไป

* Name: Update shelter condition  
* Method: PATCH  
* Path: /v1/shelters/{shelterId}  
* Type: Synchronous


### คำอธิบาย

### ใช้สำหรับเจ้าหน้าที่หน้างานในการปรับสถานะความจุ (กรณีฉุกเฉิน) และอัปเดตสภาพเส้นทางการเข้าถึง (Access Level) ระหว่างเกิดเหตุการณ์ เพื่อป้องกันการส่งคนไปในพื้นที่อันตราย

### Request

Path/Query Param

* shelterId (string, required)

  Headers

* Content-Type: application/json  
* Authorization: Bearer \<token\>

  Body

  `{`

    `"capacityAvailable": 40,`

    `"status": "OPEN",`

    `"accessLevel": "DANGEROUS",`

    `"accessNote": "สะพานหลักขาด ให้เข้าทางซอย 2"`

  `}`


  

  Validation

* capacityAvailable \>= 0  
* status ต้องเป็น \[OPEN, FULL, CLOSED, MAINTENANCE\]  
* accessLevel ต้องเป็น \[SAFE, DIFFICULT, DANGEROUS\]

### Response

Success: 200

`{`

  `"shelterId": "SHE-1234",`

  `"capacityAvailable": 40,`

  `"status": "OPEN",`

  `"accessLevel": "DANGEROUS",`

  `"updatedAt": "2026-02-16T11:20:00Z"`

`}`

Error: 404

`{`

  `"error": {`

    `"code": "NOT_FOUND",`

    `"message": "Shelter not found",`

    `"traceId": "uuid-445566"`

  `}`

`}`

### Dependency / Reliability

* ไม่เรียก service อื่น  
* ถือเป็น Idempotent update




# Async Contract

Asynchronous Function Contract

## Message Contract \#1: \<ชื่อฟังก์ชัน\>

### ข้อมูลทั่วไป 

* Message Name: ShelterReservationRequested  
* Interaction Style: Request-Async Response (via Message Broker)  
* Producer: Evacuation Service  
* Consumer: Shelter Service  
* Channel/Queue: shelter.reservation.commands.v1  
* Version: v1

### คำอธิบาย

### ส่งคำขอจองความจุศูนย์พักพิงสำหรับผู้ประสบภัยแบบ Asynchronous โดยระบบจะนำคำขอเข้าคิวเพื่อประมวลผลตามลำดับ (ช่วยป้องกันปัญหา Race Condition) และจะส่งผลการจอง (ยืนยัน/ปฏิเสธ) กลับไปให้ผู้ส่งในภายหลังผ่านช่องทาง Event Notification

Reliability & Failure Handling: ออกแบบโดยคิดเผื่อกรณีระบบล้มเหลว หากการประมวลผลคำขอขัดข้อง ระบบจะมีกลไก Retry และหากล้มเหลวซ้ำจะนำข้อความส่งเข้า Dead Letter Queue (DLQ) เพื่อไม่ให้ระบบรวมหยุดชะงัก

### Request 

### Message Headers (required)

* messageType: ShelterReservationRequested  
* messageId: UUID (ใช้เป็น Idempotency Key ป้องกันการประมวลผลซ้ำ)  
* replyTo: evac.reservation.results.v1 (Queue/Topic ที่ให้ส่งผลลัพธ์กลับ)  
* sentAt: ISO-8601 datetime  
* traceId: string/uuid (optional)

  Message Body

  `{`

    `"incidentId": "8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10",`

    `"shelterId": "SHE-1234",`

    `"peopleCount": 15,`

    `"priority": "HIGH",`

    `"requestedBy": "RescueTeam-Alpha"`

  `}`


  

  Field Definition:

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| incidentId | UUID | Y | รหัสอ้างอิงเหตุการณ์ภัยพิบัติ (เช่น รหัสน้ำท่วมเชียงราย) |
| shelterId | string | Y | รหัสศูนย์พักพิงเป้าหมาย |
| peopleCount | integer | Y | จำนวนผู้ประสบภัยที่ต้องการจองพื้นที่ |
| priority | enum | Y | ระดับความเร่งด่วน (LOW, NORMAL, HIGH) |
| requestedBy | string | Y | ชื่อหน่วยงานหรือ Service ผู้ส่งคำขอ |

Validation Rules

1. incidentId ต้องไม่ว่าง และต้องผ่านการตรวจสอบรูปแบบ (Format Check) ให้เป็น UUID ที่ตรงกับ Central Incident Schema เท่านั้น   
2. peopleCount ต้องเป็นจำนวนเต็มบวก (มากกว่า 0\)  
3. priority ต้องเป็น LOW, NORMAL หรือ HIGH เท่านั้น  
4. messageId (จาก Header) ต้องไม่ซ้ำกับคำขอที่เคยประมวลผลไปแล้ว (Idempotency check)

Response

	Message Headers (required)

* messageType: ShelterReservationConfirmed (กรณีสำเร็จ) หรือ ShelterReservationRejected (กรณีไม่สำเร็จ)  
* messageId: UUID ของข้อความ Response นี้  
* correlationId: ตรงกับ messageId ของ Request ต้นทาง (เพื่อให้ฝั่งส่งรู้ว่าเป็นคำตอบของคำขอไหน)  
* sentAt: ISO-8601 datetime  
* traceId: string/uuid (optional)


  Success Message Body

  `{`

    `"incidentId": "8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10",`

    `"shelterId": "SHE-1234",`

    `"reservationId": "RSV-998877",`

    `"peopleReserved": 15,`

    `"capacityAvailableAfter": 25,`

    `"status": "CONFIRMED"`

  `}`

  Reject/Error Message Body

  `{`

    `"incidentId": "8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10",`

    `"shelterId": "SHE-1234",`

    `"status": "REJECTED",`

    `"reasonCode": "INSUFFICIENT_CAPACITY",`

    `"reasonMessage": "Requested capacity exceeds available capacity. Only 5 spots left."`

  `}`


  Field Definition:

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| incidentId | UUID | Y | รหัสเหตุการณ์ที่เกี่ยวข้อง |
| shelterId | string | Y | รหัสศูนย์พักพิงที่ทำการจอง |
| reservationId | string | N | รหัสการจองที่สร้างโดย Shelter Service (มีเฉพาะตอนสำเร็จ) |
| peopleReserved | integer | N | จำนวนคนที่ได้รับการจัดสรรจริง (มีเฉพาะตอนสำเร็จ) |
| capacityAvailableAfter |  integer | N | ความจุที่เหลืออยู่หลังจากการจองนี้ (มีเฉพาะตอนสำเร็จ) |
| status | enum | Y | สถานะผลลัพธ์การจอง (CONFIRMED / REJECTED) |
| reasonCode |  string | N | รหัสสาเหตุที่ถูกปฏิเสธ (Machine-readable) |
| reasonMessage | string | N | ข้อความอธิบายสาเหตุที่ถูกปฏิเสธ (Human-readable) |

	Validation Rules

1. correlationId (ใน Header) ต้องตรงกับ messageId ของ Request  
2. ถ้า status \= CONFIRMED ต้องมีข้อมูล reservationId และ peopleReserved  
3. ถ้า status \= REJECTED ต้องมีข้อมูล reasonCode และ reasonMessage  
4. reasonCode ต้องใช้โค้ดมาตรฐานที่ระบบตกลงกันไว้ เช่น INSUFFICIENT\_CAPACITY, SHELTER\_CLOSED

# Service Data

# Service Data

# 1\) Shelter Master Data (Owned by this service)

ตารางสำหรับเก็บข้อมูลพื้นฐานและที่ตั้งของศูนย์พักพิง

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| shelterId | UUID | Y (PK) | รหัสอ้างอิงเฉพาะของศูนย์พักพิง | 123e4567-e89b-12d3-a456-426614174000 |
| name | string | Y | ชื่อศูนย์พักพิง | โรงเรียนวัดเวฬุวัน |
| latitude | decimal | Y | พิกัดละติจูดที่ตั้งศูนย์พักพิง | 13.7563 |
| longitude | decimal | Y | พิกัดลองจิจูดที่ตั้งศูนย์พักพิง | 100.5018 |
| capacityTotal | integer | Y | ความจุสูงสุดทั้งหมดที่รองรับได้ | 100 |

# 

# 

# 

# 

# 2\) Shelter Operational State (Owned by this service)

ตารางสำหรับจัดการสถานะปัจจุบัน ความจุที่เหลืออยู่ และสภาพเส้นทาง ซึ่งมีการอัปเดตตลอดเวลา

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| shelterId | UUID | Y (FK) | รหัสอ้างอิงศูนย์พักพิง (เชื่อมกับ Master) | 123e4567-e89b... |
| currentOccupancy | integer | Y | จำนวนผู้พักพิงในปัจจุบัน (ข้อมูลฟิลด์นี้มีการใช้งานพร้อมกันสูง (Concurrency) จึงต้องมีการบังคับใช้ Row-level Locking ในระดับ Database ทุกครั้งที่มีการอัปเดตเพื่อรักษาความถูกต้อง) | 45 |
| status | enum | Y | สถานะเปิด/ปิด (OPEN/FULL/CLOSED/MAINTENANCE) | OPEN |
| accessLevel | enum | Y | ระดับความปลอดภัยของเส้นทาง (SAFE/DIFFICULT/DANGEROUS) | DIFFICULT |
| accessNote | string | N | หมายเหตุอธิบายสภาพเส้นทางเพิ่มเติม | รถเล็กเข้าไม่ได้ น้ำท่วม 30cm |
| lastUpdatedBy | string | N | ชื่อหรือ ID เจ้าหน้าที่ผู้แก้ไขข้อมูลล่าสุด | staff-007 |
| lastUpdatedAt | datetime | Y | วันเวลาที่อัปเดตสถานะล่าสุด | 2026-02-17T10:30:00Z |

# 3\) Reservation Data (Owned by this service)

ตารางสำหรับเก็บข้อมูลประวัติการจองที่เข้ามาทางระบบ Asynchronous Queue

| Field Name | Type | Required | Description | Example |
| :---- | :---- | :---- | :---- | :---- |
| reservationId | string | Y (PK) | รหัสการจองที่ระบบสร้างขึ้น | RSV-00123 |
| shelterId | UUID | Y (FK) | รหัสศูนย์พักพิงที่ถูกจอง | 123e4567-e89b-12d3-a456-426614174000 |
| incidentId | UUID | Y | อ้างอิงรหัสเหตุการณ์ภัยพิบัติ (Reference Only) | 8b9e4b0d-3b7e-4a0d-9d9f-3f5c6a2a3e10 |
| peopleReserved | integer | Y | จำนวนผู้ประสบภัยที่ยืนยันการจัดสรรพื้นที่ | 15 |
| priority | enum | Y | ระดับความเร่งด่วน (LOW/NORMAL/HIGH) | HIGH |
| status | enum | Y | สถานะของคำขอจอง (CONFIRMED/REJECTED) | CONFIRMED |
| messageId | UUID | Y | รหัสอ้างอิงจากคิว เพื่อป้องกันการจองซ้ำ (Idempotency Key) | a1b2c3d4-e5f6-7g8h-9i0j-123456789abc |
| createdAt | datetime | Y | วันเวลาที่ทำการบันทึกการจอง | 2026-02-17T10:32:00Z |

# Service Architecture

**Service Architecture**  
**![][image1]**

**Components**

* **Client / Upstream Services:** ผู้เรียกใช้งานระบบ เช่น แอปพลิเคชันของเจ้าหน้าที่ศูนย์พักพิง หรือ Evacuation Service  
* **Amazon API Gateway:** จุดรับคำขอแบบ Synchronous ทำหน้าที่เป็นด่านหน้าในการรับ-ส่ง API (GET, PATCH) และตรวจสอบสิทธิ์  
* **REST API Handler (AWS Lambda):** ประมวลผลตรรกะแบบเรียลไทม์ เช่น การค้นหาพิกัดและระยะทางของศูนย์พักพิง และการอัปเดตสถานะแบบด่วน  
* **Amazon RDS (PostgreSQL):** ฐานข้อมูลเชิงสัมพันธ์ ทำหน้าที่เก็บ Master Data และสถานะความจุ **(เลือกใช้ Relational Database เพื่อประยุกต์ใช้ฟีเจอร์ Transaction และ Row-level Locking ในการป้องกันปัญหา Race Condition อย่างเด็ดขาด)**  
* **Amazon SQS (`shelter.reservation.commands.v1`):** Message Queue สำหรับรับคำขอจองพื้นที่แบบ Asynchronous ทำหน้าที่เป็น Buffer เพื่อไม่ให้ระบบล่มเมื่อมีคำขอจำนวนมาก  
* **Async Worker (AWS Lambda):** ดึงคำสั่งจาก SQS มาประมวลผลตามลำดับคิว เพื่ออัปเดตโควตาความจุใน Amazon RDS  
* **Amazon SNS (`evac.reservation.results.v1`):** ช่องทางสำหรับกระจาย Event แจ้งเตือนผลลัพธ์การจอง (CONFIRMED / REJECTED) กลับไปยังระบบต้นทาง

**Explanation**

สถาปัตยกรรมของ Shelter Service ประยุกต์ใช้ AWS Serverless Ecosystem ผสมผสานกับ Relational Database เพื่อรองรับการทำงานทั้งแบบ Synchronous และ Asynchronous

สำหรับการทำงานปกติ เช่น การค้นหาศูนย์พักพิงที่เปิดรับและอยู่ใกล้ที่สุด (GET /shelters) ผู้ใช้งานจะส่งพิกัดตำแหน่ง (Latitude/Longitude) ของตนเองเข้ามาผ่าน Amazon API Gateway ระบบจะส่ง Request ต่อให้ AWS Lambda นำพิกัดดังกล่าวไปประมวลผล โดยจะเข้าไป Query ข้อมูลจาก Amazon RDS (PostgreSQL) ซึ่งมีความสามารถในการจัดการข้อมูลเชิงพื้นที่ (Spatial Data) ทำให้ระบบสามารถคำนวณระยะทาง กรองศูนย์พักพิงที่อยู่ในรัศมีที่กำหนด และเรียงลำดับสถานที่ที่ใกล้ที่สุดพร้อมข้อมูลสภาพเส้นทางได้อย่างแม่นยำและรวดเร็ว ก่อนส่งผลลัพธ์กลับไปให้ผู้ใช้งานแบบทันที

สำหรับการจองพื้นที่ศูนย์พักพิง ซึ่งมีความเสี่ยงสูงที่จะเกิดเหตุการณ์ Race Condition ระบบจะทำงานแบบ Asynchronous โดยรับคำสั่งผ่าน Amazon SQS จากนั้น AWS Lambda (Async Worker) จะดึงคำสั่งไปประมวลผลทีละรายการ โดยอาศัยกลไก Transaction และ Locking ของ Amazon RDS เพื่อรับประกันว่าการตัดโควตาความจุจะมีความถูกต้องและไม่เกิดการรับคนเกินกำหนด เมื่อดำเนินการเสร็จสิ้น ระบบจะส่ง Event ยืนยันผลลัพธ์ผ่าน Amazon SNS เพื่อแจ้งให้ระบบต้นทางทราบต่อไป

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