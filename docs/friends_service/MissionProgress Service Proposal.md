# Service Overview

ภาพรวมของบริการ (Service Overview)  
MissionProgress Service

1. Service Owner  
- นายรัฐธรรมนูญ โคสาแสง (Ratthatummanoon Kosasang)   
- รหัสนักศึกษา 6609612178  
2. Service Purpose

MissionProgress Service คือบริการสำหรับทีมกู้ภัย (Rescue Team) เพื่อใช้ในการรายงานความคืบหน้าของภารกิจที่ได้รับมอบหมาย อัปเดตสถานะของเหตุการณ์ (Incident Status) และบันทึกรายละเอียดการปฏิบัติงานหน้างาน (Action Logs) เพื่อให้ศูนย์สั่งการได้รับข้อมูลที่ถูกต้องและเป็นปัจจุบันที่สุด

3. Pain Point ที่แก้ไข

ปัจจุบันศูนย์สั่งการ (Command Center) ขาดการมองเห็นภาพรวมและการติดตามสถานะการทำงานของทีมกู้ภัยแบบเรียลไทม์ (Lack of real-time visibility) รวมถึงขาดข้อมูลประเมินความรุนแรง (Impact Assessment) ที่ถูกต้องแม่นยำจากหน้างานจริง ทำให้การตัดสินใจสั่งการหรือสนับสนุนทรัพยากรเกิดความล่าช้าและผิดพลาด  
4\. Target Users

- Rescue Team (ผู้ใช้งานหลัก): ใช้สำหรับอัปเดตสถานะ แจ้งพิกัดเมื่อถึงหน้างาน และประเมินความรุนแรง  
- Dispatcher: ใช้ดูข้อมูล Timeline การทำงานเพื่อติดตามผล (ผ่านการดึงข้อมูลไปแสดงผล)

5\. Service Boundary

* In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)  
  * รับผิดชอบการเปลี่ยนสถานะของภารกิจกู้ภัย (State Transitions) ตาม Workflow: DISPATCHED → EN\_ROUTE → ON-SITE → NEED\_BACKUP → RESOLVED  
  * บันทึก Log การปฏิบัติงาน (Timeline) เช่น เวลาที่ถึงจุดเกิดเหตุ, การกระทำที่ทำลงไป (Evacuation start, First aid applied)  
  * รับข้อมูลประเมินความรุนแรง (Impact Level) และความเร่งด่วน (Priority) ใหม่จากหน้างานเพื่อปรับปรุงข้อมูลเหตุการณ์  
  * แก้ไขรายละเอียดตำแหน่ง (Exact Location Description) หากหมุดพิกัดเดิมคลาดเคลื่อน  
* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
  * ไม่รับผิดชอบการ "สั่งการ" หรือ "มอบหมายงาน" (Assignment) ให้ทีมกู้ภัย (เป็นหน้าที่ของ *Manage Dispatch Service*)  
  * ไม่รับผิดชอบการค้นหาเส้นทาง (เป็นหน้าที่ของ *SafeRoute Service*)  
  * ไม่รับผิดชอบการจัดการทรัพยากรโรงพยาบาลหรือการส่งตัวผู้ป่วย (เป็นหน้าที่ของ *HospitalResourceStatus Service*)

6\. Autonomy / Decision Logic  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การตรวจสอบสถานะ (Status Validation): ตรวจสอบว่าการเปลี่ยนสถานะสมเหตุสมผลหรือไม่ เช่น ต้องเป็น ON-SITE ก่อนจึงจะสามารถกด RESOLVED ได้ หรือการกด NEED\_BACKUP จะต้อง Trigger การแจ้งเตือน  
* การอัปเดตข้อมูลวิกฤต (Critical Data Update): สามารถตัดสินใจปรับ Impact Level หรือ Priority ของ Incident ได้ทันทีตามข้อมูลจากหน้างานโดยไม่ต้องรอการอนุมัติ เพื่อให้ระบบอื่น ๆ (เช่น Rescue Prioritization) นำข้อมูลไปคำนวณใหม่ได้ทันที

การตัดสินใจอิงจาก:

* Input จากทีมกู้ภัยหน้างาน (User Action)  
* สถานะปัจจุบันของ Incident (Current State)

บริการสามารถตัดสินใจได้เองภายใต้ business rules ที่กำหนด โดยไม่ต้องรอ/ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ  
7\. Owned Data  
ข้อมูลที่บริการนี้เป็นเจ้าของและดูแลโดยตรง (Source of Truth)

* Mission Timeline / Action Logs: ข้อมูลประวัติการทำงานทั้งหมดที่เป็น Array of objects (เก็บ เวลา, เหตุการณ์, รายละเอียด, ผู้กระทำ)  
* Operational Context Updates: ข้อมูลบริบทหน้างานล่าสุดที่ทีมกู้ภัยส่งมา เช่น last\_update\_at, updated\_by (Rescue Unit ID)

8\. Linked Data (Reference Only)  
ข้อมูลที่บริการนี้ต้องอ้างอิงจากบริการอื่น แต่ไม่ได้เป็นเจ้าของหลัก

* Incident Master Data: อ้างอิง incident\_id, incident\_type, incident\_description จาก *IncidentTracking Service* (หรือ Core Incident Schema) เพื่อแสดงผลให้ทีมกู้ภัยดู  
* Rescue Team Info: อ้างอิง ID ของทีมกู้ภัยจากระบบจัดการทีม (เพื่อระบุว่าใครเป็นคนส่ง Log)

9\. Non-Functional Requirements

* High Availability (ความพร้อมใช้งานสูง): บริการต้องพร้อมใช้งานตลอด 24/7 (SLA 99.9%) เนื่องจากเป็นระบบกู้ภัยที่หยุดชะงักไม่ได้ หากระบบล่มจะส่งผลต่อความปลอดภัยของผู้ประสบภัย  
* Low Latency (ความหน่วงต่ำ): การส่งข้อมูลสถานะ (Update Status) และการดึงข้อมูล (Read Timeline) ต้องใช้เวลาตอบสนองไม่เกิน 500ms เพื่อให้ศูนย์สั่งการเห็นข้อมูลเป็น Real-time  
* Concurrent Handling (การรองรับผู้ใช้พร้อมกัน): รองรับการยิง Request พร้อมกันจากทีมกู้ภัยหลายร้อยทีมในช่วงวิกฤต (Spike Traffic) ได้โดยไม่ล่ม  
* Data Integrity (ความถูกต้องของข้อมูล): ข้อมูล Timeline ต้องเรียงลำดับเวลาถูกต้องเสมอ (Sequential Consistency) ห้ามข้อมูลสลับกัน  
* Resilience (ความทนทาน): หากการเชื่อมต่ออินเทอร์เน็ตของทีมกู้ภัยหลุดชั่วคราว แอปพลิเคชันควรสามารถเก็บข้อมูลไว้ในเครื่อง (Local Cache) และส่งใหม่ (Retry) เมื่อต่อเน็ตได้ (Client-side consideration แต่กระทบการออกแบบ API ให้รองรับ Idempotency)

# Sync Contract

Synchronous Function Contract  
Base URL: https://api.disaster-management.net/mission-progress/v1

# API Contract \#1: Report Progress & Update Status

(รวม Action A และ Action C: ใช้บันทึก Timeline และเปลี่ยนสถานะในครั้งเดียว)

### ข้อมูลทั่วไป

* Name: reportMissionProgress  
* Method: POST  
* Path: /incidents/{incident\_id}/progress  
* Type: Synchronous

### คำอธิบาย

### ใช้สำหรับทีมกู้ภัยเพื่อ "บันทึกการปฏิบัติงาน" (Create new record) ลงใน Timeline และ "อัปเดตสถานะ" (Update status) ของเหตุการณ์ เช่น แจ้งว่าถึงที่เกิดเหตุแล้ว หรือแจ้งปิดงาน

### Request

Path/Query Params

* incident\_id (Path, UUID): รหัสเหตุการณ์ที่กำลังปฏิบัติภารกิจ

  Headers

* Content-Type: application/json

* X-Rescue-Team-ID: \<รหัสทีมกู้ภัยที่ส่งข้อมูล\> (ใช้ระบุตัวตนผู้รายงาน)

  Body: 

  {

    "status": "ON-SITE",  // สถานะใหม่ (Enum: DISPATCHED, EN\_ROUTE, ON-SITE, NEED\_BACKUP, RESOLVED)

    "action\_description": "ถึงจุดเกิดเหตุแล้ว กำลังเริ่มปฐมพยาบาลเบื้องต้น", // รายละเอียดการทำงาน

    "current\_location": {

      "latitude": 13.7563,

      "longitude": 100.5018

    },

    "new\_impact\_level": 3 // (Optional) ส่งมาเฉพาะเมื่อต้องการปรับระดับความรุนแรงใหม่

  }


### Response

Success: 

{

  "incident\_id": "INC-12345",

  "current\_status": "ON-SITE",

  "timestamp": "2024-10-15T12:35:00Z",

  "message": "Progress reported successfully"

}

Error: 

Error (400 Bad Request): ข้อมูลไม่ถูกต้อง หรือ Status flow ผิดลำดับ

{

  "error": {

    "code": "INVALID\_STATE\_TRANSITION",

    "message": "Cannot transition from 'DISPATCHED' to 'RESOLVED' directly. Must be 'ON-SITE' first.",

    "timestamp": "2024-10-15T12:35:05Z"

  }

}

Error (404 Not Found): ไม่พบ incident\_id ในระบบ

{

  "error": {

    "code": "INCIDENT\_NOT\_FOUND",

    "message": "Incident ID INC-12345 does not exist.",

    "timestamp": "2024-10-15T12:35:05Z"

  }

}

### Dependency / Reliability

* Internal Data: บันทึกข้อมูลลงฐานข้อมูลของ MissionProgress Service (Timeline Table)  
* External Service (Notification): หาก status เป็น NEED\_BACKUP หรือ RESOLVED บริการนี้อาจต้องเรียกไปที่ Rescue Prioritization Service หรือ IncidentTracking Service เพื่อแจ้งเตือนทันที (แต่ถ้าออกแบบเป็น Asynchronous จะไประบุใน Async Contract แทน)  
* Validation: ตรวจสอบว่า status ที่ส่งมาถูกต้องตาม Flow หรือไม่ (เช่น จาก DISPATCHED ข้ามไป RESOLVED เลยไม่ได้)

# API Contract \#2:  View Incident Mission Details

(Action B: ดูข้อมูลเหตุการณ์)

### ข้อมูลทั่วไป

* Name: getMissionDetails  
* Method: GET  
* Path: /incidents/{incident\_id}  
* Type: Synchronous

### คำอธิบาย

### ใช้ดึงข้อมูลรายละเอียดของเหตุการณ์ รวมถึง "ประวัติการทำงานทั้งหมด (Timeline)" เพื่อให้ทีมกู้ภัยดูย้อนหลังหรือตรวจสอบข้อมูลก่อนเริ่มงาน

### Request

Path/Query Param

* incident\_id (Path, UUID): รหัสเหตุการณ์ที่ต้องการดู

  Headers

* X-Rescue-Team-ID: \<รหัสทีมกู้ภัย\>

  Body


  ไม่มี

  Validation

* ตรวจสอบว่า incident\_id มีอยู่จริงหรือไม่

### Response

Success: 

{

  "incident\_id": "INC-12345",

  "description": "น้ำท่วมสูง 2 เมตร ติดค้างในบ้าน 3 คน", // ดึงจาก IncidentTracking หรือ Cache

  "current\_status": "ON-SITE",

  "exact\_location": "13.7563, 100.5018",

  "timeline": \[

    {

      "time": "2024-10-15T12:00:00Z",

      "action": "Mission Assigned",

      "by": "Dispatcher"

    },

    {

      "time": "2024-10-15T12:10:00Z",

      "action": "En Route",

      "detail": "ออกจากฐาน กำลังเดินทาง",

      "by": "Rescue Team A"

    }

  \]

}

Error: 

Error (404 Not Found): ไม่พบข้อมูลเหตุการณ์

{

  "error": {

    "code": "INCIDENT\_NOT\_FOUND",

    "message": "Incident ID INC-12345 not found.",

    "timestamp": "2024-10-15T12:10:05Z"

  }

}

### Dependency / Reliability

* Dependency (Critical): ต้องดึงข้อมูล Master Data (Description, Location) จาก IncidentTracking Service  
  * *Failure Handling:* หาก IncidentTracking Service ล่ม ให้แสดงข้อมูลล่าสุดที่ Cache ไว้ใน MissionProgress Service แทน หรือแสดงเฉพาะ Timeline ที่ตนเองถืออยู่เพื่อให้งานเดินต่อได้




# Async Contract

Asynchronous Function Contract

## Message Contract \#1: Mission Status Changed

ใช้แจ้งระบบอื่น ๆ เมื่อสถานะของภารกิจเปลี่ยนแปลง (เช่น ทีมกู้ภัยถึงหน้างาน หรือ ปิดงานแล้ว)

### ข้อมูลทั่วไป 

* Message Name: MissionStatusChangedEvent  
* Interaction Style: Asynchronous (Publish/Subscribe)  
* Producer: MissionProgress Service  
* Consumer: IncidentTracking Service, Rescue Prioritization Service, Dispatch Management Service  
* Channel/Queue: mission.status.updates.v1  
* Version: v1

### คำอธิบาย

### Event นี้จะถูกส่งออกมาเมื่อทีมกู้ภัยทำการเปลี่ยนสถานะ (Update Status) สำเร็จ เพื่อให้ระบบ Incident Tracking อัปเดตสถานะรวมของเหตุการณ์ และระบบ Dispatch ทราบสถานะล่าสุดของทีม

### Request 

### Message Headers

* Event-ID: evt-889900  
* Source: MissionProgressService  
* Content-Type: application/json  
* Timestamp: 2024-10-15T12:30:05Z

  Message Body

  {

    "incident\_id": "INC-12345",

    "rescue\_team\_id": "TEAM-01",

    "previous\_status": "EN\_ROUTE",

    "current\_status": "ON-SITE",

    "changed\_at": "2024-10-15T12:30:00Z",

    "location\_snapshot": {

      "lat": 13.7563,

      "lng": 100.5018

    }

  }

Field Definition:

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| incident\_id | UUID | Yes | รหัสของเหตุการณ์ที่ถูกอัปเดต |
| rescue\_team\_id | String | Yes | รหัสทีมกู้ภัยที่ปฏิบัติงาน |
| current\_status | String | Yes | สถานะใหม่ (Enum: DISPATCHED, EN\_ROUTE, ON-SITE, NEED\_BACKUP, RESOLVED) |
| changed\_at | DateTime | Yes | เวลาที่เกิดการเปลี่ยนแปลงสถานะ |
| location\_snapshot | Object | No | พิกัดล่าสุดขณะเปลี่ยนสถานะ |

Validation Rules

- incident\_id (UUID, Required): รหัสเหตุการณ์  
- current\_status (String, Required): สถานะใหม่ (EN\_ROUTE, ON-SITE, RESOLVED)

Response

ในกรณีที่เป็น Event ส่วนใหญ่จะไม่มีการตอบกลับ แต่ถ้าใน Template มีช่องให้ใส่ จะหมายถึง Acknowledge หรือ Confirmation จากระบบรับ

	Message Headers

- Correlation-ID: evt-889900 (อ้างอิง ID เดิม)  
-  Status: PROCESSED


  Success Message Body

  {

    "status": "SUCCESS",

    "message": "Event received and processed.",

    "processed\_at": "2024-10-15T12:30:06Z"

  }

  Reject/Error Message Body

  {

    "status": "FAILED",

    "error\_code": "INVALID\_SCHEMA",

    "message": "Missing required field: rescue\_team\_id"

  }


  Field Definition:

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| status | String | Yes | ผลลัพธ์การรับข้อความ (SUCCESS / FAILED) |
| message | String | Yes | รายละเอียดผลลัพธ์ |
| error\_code | String | No | รหัสข้อผิดพลาด (กรณี Failed) |

	Validation Rules

- incident\_id: ต้องเป็นรูปแบบ UUID ที่ถูกต้องและมีอยู่ในระบบจริง  
- current\_status: ต้องเป็นค่าที่กำหนดไว้ใน State Machine เท่านั้น (DISPATCHED, EN\_ROUTE, ON-SITE, NEED\_BACKUP, RESOLVED)  
- rescue\_team\_id: ห้ามเป็นค่าว่าง (Null/Empty) ต้องระบุตัวตนทีมกู้ภัยเสมอ  
- changed\_at: ต้องเป็นรูปแบบ Timestamp (ISO 8601\) และห้ามเป็นเวลาในอนาคต

# Service Data

# Service Data

# 1\) Mission Timeline Data (Owned by this service)

ข้อมูลประวัติการทำงานอย่างละเอียดของทีมกู้ภัย (Log) ที่เกิดขึ้นในแต่ละภารกิจ ใช้สำหรับสร้าง Timeline

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| log\_id | UUID | Yes | รหัสอ้างอิงของรายการ Log (Primary Key) | LOG-556677 |
| mission\_id | UUID | Yes | รหัสภารกิจ (เชื่อมโยงกับทีมและเหตุการณ์) | MIS-998800 |
| action\_type | String | Yes | ประเภทการกระทำ เช่น "STATUS\_CHANGE", "COMMENT", "UPLOAD" | STATUS\_CHANGE |
| description | String | Yes | รายละเอียดของสิ่งที่ทำ | Arrived at location, setting up perimeter. |
| performed\_by | String | Yes | ID ของทีมกู้ภัยหรือเจ้าหน้าที่ที่ทำรายการ | TEAM-01 |
| timestamp | DateTime | Yes | เวลาที่เกิดเหตุการณ์จริง | 2024-10-15T12:30:00Z |
| gps\_location | String | No | พิกัด GPS ณ จุดที่บันทึกข้อมูล (Lat, Long) | 13.7563, 100.5018 |

# 

#  

# 2\) Mission Assignment State (Owned by this service)

ข้อมูลสถานะปัจจุบันของภารกิจที่ทีมกู้ภัยแต่ละทีมรับผิดชอบ (Current State)

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| mission\_id | UUID | Yes | รหัสภารกิจ (Primary Key) | MIS-998800 |
| incident\_id | UUID | Yes | รหัสเหตุการณ์ที่เชื่อมโยง (Foreign Key) | INC-12345 |
| rescue\_team\_id | String | Yes | รหัสทีมกู้ภัยที่รับผิดชอบภารกิจนี้ | TEAM-01 |
| current\_status | String | Yes | สถานะปัจจุบันของภารกิจ | ON-SITE |
| latest\_impact\_level | Integer | No | ระดับความรุนแรงล่าสุดที่ประเมินโดยทีมนี้ (1-4) | 3 |
| started\_at | DateTime | Yes | เวลาที่เริ่มรับภารกิจ | 2024-10-15T12:00:00Z |
| last\_updated\_at | DateTime | Yes | เวลาที่อัปเดตข้อมูลล่าสุด | 2024-10-15T12:35:00Z |

# Service Architecture

**Service Architecture**  
**![][image1]**

\# Service Architecture

\*\*Architecture Diagram\*\* \*(แสดงการทำงานและ Component ภายใน MissionProgress Service)\*

\`\`\`mermaid  
graph TD  
    %% \--- External User \---  
    User((Rescue\<br\>Team))

    %% \--- Internal Service Components \---  
    subgraph MissionProgress\_Service \[MissionProgress Service (Internal Architecture)\]  
        UI\[Web Client\<br\>Next.js on S3\]  
        AGW\[Amazon API Gateway\]  
        Auth\[Lambda Authorizer\]  
        API\[Core API\<br\>AWS Lambda \- Go\]  
        DB\[(Amazon DynamoDB\<br\>Timeline & State)\]  
        Storage\[(Amazon S3\<br\>Evidence Bucket)\]  
    end

    %% \--- User to Frontend \---  
    User \--\>|Access Web App| UI

    %% \--- Frontend Interactions \---  
    UI \--\>|1. Request Presigned URL| AGW  
    UI \--\>|3. Direct Image Upload| Storage  
    UI \--\>|4. Submit Status & Image Key\<br\>(with x-api-key)| AGW

    %% \--- Backend Processing \---  
    AGW \--\>|Verify API Key| Auth  
    AGW \--\>|Route Valid Request| API

    API \--\>|2. Generate Presigned URL| Storage  
    API \--\>|5. Read/Write State & Log| DB

    %% \--- Styling \---  
    style UI fill:\#eceff1,stroke:\#607d8b,stroke-width:2px  
    style AGW fill:\#e8eaf6,stroke:\#3f51b5,stroke-width:2px  
    style Auth fill:\#e1f5fe,stroke:\#0288d1,stroke-width:2px  
    style API fill:\#f9f9f9,stroke:\#333,stroke-width:2px  
    style DB fill:\#e8f5e9,stroke:\#388e3c,stroke-width:2px  
    style Storage fill:\#fff3e0,stroke:\#f57c00,stroke-width:2px  
\`\`\`

**Components**

**1\. MissionProgress Web Client (Frontend):**

* พัฒนาด้วย Next.js ควบคู่กับ Tailwind CSS ให้เป็น Responsive Web App  
* **หน้าที่:** เป็นหน้าจอหลักให้ทีมกู้ภัยกดอัปเดตสถานะและถ่ายรูปหลักฐาน โดยโฮสต์ไฟล์ Static บน Amazon S3 (Static Website Hosting) ซึ่งเหมาะกับ AWS Student Lab

**2\. Amazon API Gateway \+ Lambda Authorizer (Authentication):**

* **หน้าที่:** เป็นประตูด่านแรกรับ Request ตรวจสอบสิทธิ์การใช้งานผ่าน API Key ควบคู่กับ Lambda Authorizer เพื่อความปลอดภัยและทำได้ง่ายใน Lab

**3\. AWS Lambda \- Go Runtime (Backend API):**

* **หน้าที่:** ประมวลผล Business Logic หลัก ตรวจสอบลำดับการเปลี่ยนสถานะ (State Machine) สร้าง Presigned URL และจัดเตรียมข้อมูลก่อนลงฐานข้อมูล (ทำงานรวดเร็วด้วย Go)

**4\. Amazon S3 (Image Storage):**

* **หน้าที่:** เก็บไฟล์รูปภาพหลักฐาน โดยให้ Frontend อัปโหลดตรงเข้า S3 ผ่าน Presigned URL เพื่อไม่ให้เป็นคอขวดที่ Lambda

**5\. Amazon DynamoDB (Database):**

* **หน้าที่:** เก็บข้อมูล Timeline การปฏิบัติงาน และ Status ล่าสุดของแต่ละภารกิจ ด้วยโครงสร้าง NoSQL ที่อ่านเขียนได้เร็ว

**Explanation**  
1\. **User Access & Authentication (การเข้าถึงและยืนยันตัวตน):**

* ทีมกู้ภัยเข้าใช้งานผ่าน **Web Browser** บนมือถือ (ไม่ต้องลงแอป)  
* ทีมกู้ภัยเข้าใช้งานโดยระบบจะแนบค่า `x-api-key` และ `X-Rescue-Team-ID` ไปกับ Header เพื่อให้ Lambda Authorizer ตรวจสอบสิทธิ์และยืนยันตัวตน

2\. **Evidence Upload Flow (การอัปโหลดหลักฐานหน้างาน):**

* เมื่อทีมกู้ภัยต้องการส่งรูปภาพหน้างาน (Evidence) เพื่อลดภาระของ Server ระบบใช้เทคนิค **Direct Upload**:  
  * Frontend ขอ "Presigned URL" จาก API  
  * Frontend อัปโหลดไฟล์รูปภาพตรงไปยัง **Amazon S3**  
  * เมื่ออัปโหลดเสร็จ จะได้ "Image Key" (ที่อยู่ไฟล์) มาเพื่อเตรียมส่งพร้อมข้อมูลข้อความ

3\. **Core Transaction Processing (การประมวลผลคำสั่งหลัก):**

* User ส่งข้อมูลสถานะ (Status) และรายละเอียด (Logs) ผ่าน **Amazon API Gateway** (REST API)  
* **AWS Lambda (Business Logic)** ถูกปลุกขึ้นมาทำงาน เพื่อตรวจสอบกฎทางธุรกิจ (Business Rules) เช่น *“สถานะปัจจุบันคือ En-route จะข้ามไป Resolved เลยไม่ได้ ต้องเป็น On-site ก่อน”*  
* หากตรวจสอบผ่าน Lambda จะบันทึกข้อมูล State ล่าสุดและ Timeline ลงใน **Amazon DynamoDB** ซึ่งออกแบบมาให้รับแรงกระแทกจากการเขียนข้อมูลจำนวนมาก (Write-heavy) ได้ดี

4\. **Asynchronous Event Propagation (การกระจายข่าวแบบอะซิงโครนัส):**

* ทันทีที่บันทึกข้อมูลสำเร็จ Lambda จะทำหน้าที่เป็น Producer ส่ง Event ชื่อ `MissionStatusChangedEvent` ไปยัง **Amazon EventBridge**  
* **EventBridge** จะทำหน้าที่เป็น Router กระจายข่าวสารไปยัง Service ปลายทางที่ Subscribe ไว้:  
  * ส่งไป **IncidentTracking Service** เพื่ออัปเดตสถานะภาพรวมของเหตุการณ์  
  * ส่งไป **Dispatch Management Service** (กรณีสถานะเป็น Resolved) เพื่อปลดล็อกทีมกู้ภัยให้ว่างพร้อมรับงานใหม่

5\. **Reliability & Failure Handling (ความทนทาน):**

* หากระบบปลายทาง (เช่น IncidentTracking) ล่ม หรือส่ง Event ไม่ผ่าน ระบบจะส่ง Message นั้นเข้าสู่ **Dead Letter Queue (DLQ)** โดยอัตโนมัติ เพื่อให้ Admin หรือระบบ Retry มาตามเก็บตกข้อมูลทีหลัง ทำให้ข้อมูลสถานะภารกิจไม่มีวันสูญหาย

# Service Interaction

**\# Service Interaction**

**\*\*Interaction Diagram\*\* \*(แสดงการสื่อสารระหว่าง MissionProgress กับ Service อื่นๆ ในระบบรวม)\***

**\`\`\`mermaid**  
**graph LR**  
    **%% \--- Clients \---**  
    **subgraph Upstream \[Upstream Clients / Users\]**  
        **App(\[Rescue Team App\])**  
        **Dash(\[Command Center Dashboard\])**  
    **end**

    **%% \--- Our Service \---**  
    **subgraph Our\_Service \[Our Domain\]**  
        **MS\[MissionProgress\<br\>Service\]**  
        **EventBus{Amazon\<br\>EventBridge}**  
    **end**

    **%% \--- External Downstream Services \---**  
    **subgraph Downstream \[External Services\]**  
        **Incident\[IncidentTracking\<br\>Service\]**  
        **Dispatch\[Dispatch Management\<br\>Service\]**  
        **Priority\[Rescue Prioritization\<br\>Service\]**  
    **end**

    **%% \--- Inbound Interactions (Synchronous) \---**  
    **App \== "1. POST Status & Evidence" \==\> MS**  
    **Dash \== "2. GET Mission Timeline" \==\> MS**

    **%% \--- Internal Event Routing \---**  
    **MS \-. "3. Publish Events" .-\> EventBus**

    **%% \--- Outbound Interactions (Asynchronous) \---**  
    **EventBus \-. "Event: MissionStatusChanged\<br\>(e.g. ON-SITE)" .-\> Incident**  
    **EventBus \-. "Event: MissionResolved\<br\>(Free up team)" .-\> Dispatch**  
    **EventBus \-. "Event: ImpactAssessmentUpdated" .-\> Priority**

    **%% \--- Styling \---**  
    **linkStyle 0,1 stroke:\#333,stroke-width:2px; %% Sync Calls (Solid)**  
    **linkStyle 2,3,4,5 stroke:\#d4a017,stroke-width:2px,stroke-dasharray: 5 5; %% Async Events (Dashed)**

    **style MS fill:\#e3f2fd,stroke:\#1565c0,stroke-width:2px**  
    **style EventBus fill:\#fff8e1,stroke:\#ff8f00,stroke-width:2px**  
    **style Incident fill:\#fce4ec,stroke:\#c2185b,stroke-width:2px**  
    **style Dispatch fill:\#fce4ec,stroke:\#c2185b,stroke-width:2px**  
    **style Priority fill:\#fce4ec,stroke:\#c2185b,stroke-width:2px**

**คำอธิบาย Flow:**

* **เส้นทึบ (Solid Lines):** คือการเรียกแบบ **Synchronous** (รอผลตอบกลับทันที) เช่น การรายงานความคืบหน้า หรือการดึงข้อมูลไปแสดง  
* **เส้นประ (Dotted Lines):** คือการส่ง **Asynchronous Events** (ไม่รอผล) ผ่าน EventBridge เพื่อกระจายข่าวไปยัง Service อื่นๆ (Incident, Dispatch, Prioritization)

**Upstream Services (บริการต้นทางที่เรียกใช้งาน MissionProgress Service)**

* **Rescue Team Web Application (Frontend)**  
  * เรียกใช้งาน `POST /missions/{incident_id}/progress` แบบ synchronous เพื่อรายงานสถานะล่าสุด (เช่น En-route, On-site) อัปโหลดรูปภาพหลักฐาน และบันทึก Log การปฏิบัติงาน  
  * เรียกใช้งาน `GET /missions/{incident_id}` แบบ synchronous เพื่อดึงประวัติการทำงาน (Timeline) ทั้งหมดของภารกิจนั้นมาแสดงผลบนหน้าจอมือถือของทีมกู้ภัย  
* **Command Center Dashboard Service**  
  * เรียกใช้งาน `GET /missions/{incident_id}` แบบ synchronous เพื่อดึงข้อมูล Timeline และสถานะปัจจุบันของภารกิจไปแสดงบนหน้าจอของผู้สั่งการ (Dispatcher) ทำให้เห็นความเคลื่อนไหวหน้างานแบบเรียลไทม์

**Downstream Services (บริการปลายทางที่ MissionProgress Service เรียกหรือส่งข้อมูลไป)**

* **IncidentTracking Service**  
  * ถูกเรียกใช้งานแบบ synchronous ผ่าน `GET /incidents/{incident_id}` เพื่อดึงข้อมูลรายละเอียดเหตุการณ์ (เช่น พิกัด, คำอธิบาย) มาแสดงให้ทีมกู้ภัยตรวจสอบความถูกต้องก่อนเริ่มงาน  
  * รับ event `MissionStatusChangedEvent` ที่ส่งออกจาก MissionProgress Service ผ่าน EventBridge แบบ asynchronous เพื่ออัปเดตสถานะรวมของเหตุการณ์ในระบบหลัก (เช่น เปลี่ยนสถานะ Incident เป็น "In Progress")  
* **Dispatch Management Service**  
  * รับ event `MissionStatusChangedEvent` (เฉพาะเมื่อสถานะเป็น **RESOLVED**) ผ่าน EventBridge แบบ asynchronous เพื่อรับทราบว่าภารกิจเสร็จสิ้น และทำการปลดล็อกสถานะของทีมกู้ภัยให้กลับมาเป็น "Available" พร้อมรับงานใหม่  
* **Rescue Prioritization Service**  
  * รับ event `MissionBackupRequestedEvent` หรือข้อมูลการอัปเดต `Impact Level` ผ่าน EventBridge แบบ asynchronous เพื่อนำค่าความรุนแรงล่าสุดจากหน้างาน ไปคำนวณลำดับความสำคัญ (Priority Score) ของเคสใหม่อีกครั้ง

# Dependency Mapping

### **Dependency Mapping – MissionProgress Service**

#### **1\. IncidentTracking Service**

* Service Owner: Krittamet Damthongkam  
* Type: Service  
* Interaction Style: Hybrid (Synchronous & Asynchronous)  
* Purpose:  
  * (Sync \- GET): ดึงข้อมูลรายละเอียดของเหตุการณ์ (`description`, `location`) เพื่อนำมาแสดงผลให้ทีมกู้ภัยดูบนหน้า Web App ก่อนเริ่มงาน  
  * (Async \- Event): รับ Event `MissionStatusChanged` เพื่ออัปเดตสถานะรวมของเหตุการณ์ในระบบหลัก  
* Criticality: Critical  
* Failure Handling:  
  * กรณีดึงข้อมูลไม่สำเร็จ (Read Fail): ระบบจะแสดงข้อความแจ้งเตือน "ไม่สามารถโหลดรายละเอียดเหตุการณ์ได้" แต่ยังอนุญาตให้ทีมกู้ภัยกดปุ่มอัปเดตสถานะได้ (Degraded Mode) โดยอิงจาก `incident_id` ที่มีอยู่  
  * กรณีส่ง Event ไม่สำเร็จ (Write Fail): ระบบจะใช้กลไก Retry ของ EventBridge และหากยังไม่สำเร็จจะส่งเข้า Dead Letter Queue (DLQ) เพื่อรอการ Re-process ภายหลัง

#### **2\. Dispatch Management Service**

* Service Owner: Noppakron Songkroh  
* Type: Service  
* Interaction Style: Asynchronous (Event-Driven)  
* Purpose: รับ Event `MissionStatusChanged` (เฉพาะสถานะ `RESOLVED`) เพื่อทำการปลดล็อกสถานะของทีมกู้ภัยในระบบจัดตารางงาน (Dispatch) ให้เปลี่ยนจาก `BUSY` เป็น `AVAILABLE` พร้อมรับงานใหม่  
* Criticality: High  
* Failure Handling:  
  * ใช้ Exponential Backoff Retry ในระดับ Infrastructure (EventBridge) หากระบบ Dispatch ล่มชั่วคราว Event จะถูกส่งซ้ำเรื่อยๆ จนกว่าจะสำเร็จ เพื่อป้องกันปัญหาสถานะทีมกู้ภัยค้าง

#### **3\. Rescue Prioritization Service**

* Service Owner: Nattasak Chonmanat  
* Type: Service  
* Interaction Style: Asynchronous (Event-Driven)  
* Purpose: รับข้อมูลระดับความรุนแรง (`Impact Level`) ที่ทีมกู้ภัยประเมินใหม่จากหน้างาน เพื่อนำไปคำนวณคะแนนความเร่งด่วน (Priority Score) ใหม่  
* Criticality: Medium (Non-blocking for rescue operation)  
* Failure Handling:  
  * Fire-and-forget: หากส่งข้อมูลไม่สำเร็จ ระบบกู้ภัยหน้างานยังคงทำงานต่อได้ตามปกติโดยไม่ต้องรอผลลัพธ์ และไม่มีการ Retry ที่ซับซ้อน เพื่อลดภาระระบบ

#### **4\. Amazon S3 (Infrastructure)**

* Type: Object Storage  
* Interaction Style: Synchronous (Direct Client Upload)  
* Purpose: เก็บไฟล์รูปภาพและวิดีโอที่เป็นหลักฐานการปฏิบัติงาน (Evidence) จากหน้างาน เพื่อลดภาระการประมวลผลของ Application Server  
* Criticality: Medium  
* Failure Handling:  
  * หากการอัปโหลดรูปภาพล่ม (Upload Fail) Frontend จะแจ้งเตือนผู้ใช้งาน และอนุญาตให้ User กด "ข้าม" (Skip) การส่งรูปภาพ เพื่อให้สามารถส่งเฉพาะสถานะ (Text Status) ที่สำคัญกว่าไปก่อนได้

#### **5\. API Gateway (API Key & Usage Plan) \+ Lambda Authorizer**

* Type: Identity Provider (Auth Service)  
* Interaction Style: Synchronous  
* Purpose: ยืนยันตัวตน (Authentication) และตรวจสอบสิทธิ์ (Authorization) ของทีมกู้ภัยก่อนที่จะอนุญาตให้ส่งข้อมูลเข้าสู่ระบบ  
* Criticality: Critical  
* Failure Handling:  
  * หาก Lambda Authorizer ล่ม หรือตั้งค่า API Key ผิดพลาด ระบบจะปฏิเสธการเข้าถึง (403 Forbidden)

#### **6\. Amazon EventBridge (Infrastructure)**

* Type: Event Bus  
* Interaction Style: Asynchronous  
* Purpose: เป็นตัวกลางในการรับและกระจาย Event (Message Broker) จาก MissionProgress Service ไปยัง Service ปลายทางอื่นๆ  
* Criticality: Critical  
* Failure Handling:  
  * หาก Event Bus มีปัญหา ระบบ Backend (Lambda) จะบันทึก Event ที่ส่งไม่ผ่านลงใน Local Database (DynamoDB \- Outbox Table) ชั่วคราว และจะมี Cron Job มาดึงไปส่งใหม่เมื่อระบบกลับมาปกติ (Outbox Pattern)





# Github Reopo

[https://github.com/Ratthatummanoon/CS366-MissionProgress-Service](https://github.com/Ratthatummanoon/CS366-MissionProgress-Service)

[image1]: <data:image/png;base64,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>