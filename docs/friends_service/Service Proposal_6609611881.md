# Service Overview

**ภาพรวมของบริการ (Service Overview)**  
SafeRoute Service  
*Li nk Github : [https://github.com/Narongkornn/SafeRoute-Service](https://github.com/Narongkornn/SafeRoute-Service)*

1. **Service Owner**  
   

นาย ณรงค์กรณ์ มงคลสวะไชย   รหัสนักศึกษา 6609611881   ภาคปกติ

2. **Service Purpose**

SafeRoute Service เป็นบริการที่รับผิดชอบการคำนวณเส้นทางที่ปลอดภัยจากตำแหน่งผู้ใช้ไปยังปลายทาง (เช่น shelter / hospital) โดยนำข้อมูลเหตุการณ์ที่ถูกยืนยันแล้วจาก Service อื่นมาใช้เป็น hazard (จุด/พื้นที่เสี่ยง) แล้วเลือกเส้นทางที่ปลอดภัยที่สุดจากเส้นทางหลายตัวเลือกของ OSRM ภายใต้เงื่อนไขว่าอ้อมได้ไม่มากเกินไป

3. **Pain Point ที่แก้ไข**

ตอนเกิดเหตุจริง คนหรือทีมกู้ภัยอยากไปถึงจุดหมายเร็วแต่ก็ต้องปลอดภัยด้วยเพราะเส้นทางที่เร็วที่สุดอาจพาไปเจอน้ำท่วม ถนนขาด ไฟไหม้ หรือพื้นที่ที่ถูกปิดกั้น ซึ่งแอปนำทางทั่วไปอาจไม่รู้ข้อมูลเหตุการณ์ล่าสุดที่ขึ้นตรงกับ Central Incident Schema เลยทำ SafeRoute เพื่อช่วยลดความเสี่ยงนี้ด้วยการเอา hazards มาช่วยตัดสินใจเลือกเส้นทาง โดยคำนึงถึงความปลอดภัยเป็นอันดับแรก

4. **Target Users**  
     
* Dispatcher  
* Manage Dispatch Service  
* Victim

5. **Service Boundary**  
* In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)  
  * รับ input: user → destination แล้วคำนวณเส้นทางผ่าน API `/v1/route/safe`  
  * ดึงข้อมูล Incident จาก IncidentTracking Service (Central Schema)  
  * แปลงตำแหน่ง incident เป็น hazard zones แบบ dynamic  
  * ใช้ OSRM คำนวณเส้นทางหลายๆแบบ  
  * ประเมินความเสี่ยงแต่ละเส้น \+ detour limits แล้วเลือกเส้นที่เหมาะสมที่สุด  
  * ส่งกลับ polyline \+ metrics \+ warning (ถ้ามี)  
  * ดึงตำแหน่ง Shelter จาก Shelter Service เพื่อแสดงบน UI

* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
  * ไม่เก็บและแก้ไขข้อมูล Incident Master Data / shelter  
  * ไม่รับผิดชอบการ verify incident  
  * ไม่รับผิดชอบการหา nearest shelter (เป็นหน้าที่ service อื่นในระบบ)  
  * ไม่ทำระบบผู้ใช้/สิทธิ์ของ citizen (แค่ให้ API สำหรับระบบอื่น)

6. **Autonomy / Decision Logic**

บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การเลือกเส้นทางที่เหมาะสมที่สุดจากหลายตัวเลือก (alternatives)  
* การประเมินระดับความเสี่ยงของแต่ละเส้นทาง  
* การตัดสินใจว่าจะยอมอ้อมมากน้อยแค่ไหนภายใต้ข้อจำกัดที่กำหนด  
* การ downgrade เป็น fallback mode หาก dependency ไม่พร้อมใช้งาน

การตัดสินใจอิงจาก:

* เส้นทางหลายตัวเลือกที่ได้จาก OSRM Routing Engine  
* ข้อมูลพิกัดเหตุการณ์ที่ผ่านการตรวจสอบแล้วจาก Central Incident Schema  
* จำนวน incident ที่เส้นทางตัดผ่าน  
* ระดับ impact\_level ของ incident  
* detour limits ระยะทางและเวลาที่เพิ่มขึ้นเมื่อเทียบกับ baseline route  
* Business rules เช่น หาก   
  * hazard level \= high → ให้ penalty สูง  
  * หากอ้อมเกินสัดส่วนที่กำหนด → ตัดออก  
  * หากทุกเส้นทางมี hazard → เลือกเส้นที่มี exposure ต่ำที่สุด  
  * หากไม่สามารถดึง hazard ได้ → route ต่อในโหมด fallback พร้อม warning

7.  **Owned Data (data ที่ได้ผ่าน analyzed ใช้เพื่อ audit และ performance analysis)**  
* **Route Metadata**: ข้อมูลเส้นทางที่ระบบคำนวณ เช่น route\_id, origin, destination, total\_distance, total\_duration และ polyline service นี้เป็นผู้สร้างและจัดการข้อมูลเส้นทางเองทั้งหมด  
* **Routing Strategy Configuration**: ข้อมูลพารามิเตอร์ที่ใช้กำหนดวิธีเลือกเส้นทาง เช่น avoid\_level, weight\_factor, fallback\_mode เพื่อควบคุม policy การคำนวณเส้นทาง

8.  **Linked Data (Reference Only)**  
     
1.  เรียก IncidentTracking Service เพื่อดึงข้อมูลเหตุการณ์ที่ยัง ACTIVE จาก Central Incident Schema เช่น exact\_location และ impact\_level มาใช้ประเมินความเสี่ยงของเส้นทาง  
2. เรียก Shelter Service เพื่อดึงข้อมูลพิกัดของศูนย์พักพิงมาแสดงบนแผนที่ และใช้เป็น destination ในการคำนวณเส้นทาง

9.  **Non-Functional Requirements**

* ต้องไม่ล่มเมื่อ dependency ภายนอกไม่พร้อมใช้งาน  
* ต้องตั้ง timeout สำหรับการเรียก IncidentTracking และ Shelter Service  
* ต้องรองรับ concurrent requests ในสถานการณ์วิกฤต  
* ต้องสามารถ deploy และทำงานได้จริงบน Cloud

# Sync Contract

**Synchronous Function Contract**  
**Base URL:**

# **API Contract \#1:** Calculate Safe Route

### **ข้อมูลทั่วไป**

* **Name:** Calculate Safe Route  
* **Method:** POST  
* **Path:** /v1/route/safe  
* **Type:** Synchronous

### **คำอธิบาย**

### คำนวณเส้นทางที่ปลอดภัยจากตำแหน่งต้นทางไปยังปลายทาง โดยใช้ข้อมูล Incident จาก Central Schema เพื่อประเมินความเสี่ยงและเลือกเส้นทางที่เหมาะสมที่สุด

### **Request**

	**Validation**

* lat อยู่ในช่วง \[-90,90\]  
* lon อยู่ในช่วง \[-180,180\]

  **Headers**

* Content-Type: application/json  
  **Body:** 

  {  
    "incidentId": "INC-001",  
    "user": { "lat": 13.7563, "lon": 100.5018 },  
    "destination": { "lat": 13.7367, "lon": 100.5231 },  
    "alternatives": true,  
    "optimizeBy": "duration"  
  }

### 

### **Response**

**Success: (200 OK)**

{

  "routeId": "uuid-123",

  "distanceMeters": 5200,

  "durationSeconds": 840,

  "incidentHitCount": 1,

  "highestImpactLevel": 3,

  "routeStatus": "ROUTE\_RECOMMENDED",

  "warning": null,

  "polyline": "encoded\_polyline\_string"

}

**Error:** 

**400 Bad Request – invalid input**

**404 Not Found – incidentId ไม่พบ**

**503 Service Unavailable – routing engine ไม่พร้อมใช้งาน**

{

  "error": "Invalid coordinates",

  "traceId": "abc-123"

}

### **Dependency / Reliability**

* เรียก IncidentTracking Service เพื่อดึง incident ที่ ACTIVE  
* หาก IncidentTracking ล่ม → fallback mode (route ได้ แต่มี warning)

# 

# **API Contract \#2:** Get Route Details 

### **ข้อมูลทั่วไป**

* **Name:** Get Route Details  
* **Method:** GET  
* **Path:** /v1/routes/{routeId}  
* **Type:** Synchronous

### **คำอธิบาย**

### **ดึงรายละเอียดเส้นทางที่เคยคำนวณไว้จาก routeId**

### **Request**

**Path/Query Param**

* routeId (string, required) – รหัสของเส้นทาง

  **Validation**

* routeId ต้องเป็น UUID  
* routeId ต้องมีอยู่ในระบบ

### **Response**

**Success: (200 OK)**

{

  "routeId": "uuid-123",

  "origin": { "lat": 13.7563, "lon": 100.5018 },

  "destination": { "lat": 13.7367, "lon": 100.5231 },

  "distanceMeters": 5200,

  "durationSeconds": 840,

  "incidentHitCount": 1,

  "highestImpactLevel": 3,

  "routeStatus": "COMPLETED",

  "createdAt": "2026-02-15T10:10:00Z"

}

**Error: 404 Not Found – routeId ไม่พบ**

{

  "error": "Route not found",

  "traceId": "xyz-789"

}

### **Dependency / Reliability**

* ไม่เรียก service ภายนอก (ใช้ owned data เท่านั้น)  
* Idempotent (GET)

# **API Contract \#3:** Get Active Incidents 

### **ข้อมูลทั่วไป**

* **Name:** Get Active Incidents  
* **Method:** GET  
* **Path:** /v1/incidents/active  
* **Type:** Synchronous

### **คำอธิบาย**

### ดึงรายการ incident ที่ยัง ACTIVE จาก IncidentTracking ใช้แสดงเป็นจุดอันตรายบนแผนที่และใช้ประกอบการคำนวณ route (วงแดง)

### **Request**

**Path/Query Param**

* limit (int, default=200) – จำนวนรายการสูงสุด  
* type (string, optional) – กรองตามประเภท incident เช่น flood/fire

**Headers**

* Accept: application/json

### **Response**

**Success: (200 OK)**

{

  "items": \[

    {

      "incident\_id": "INC-001",

      "incident\_type": "flood",

      "status": "ACTIVE",

      "impact\_level": 3,

      "exact\_location": { "lat": 13.745, "lon": 100.534 }

    }

  \],

  "count": 1

}

**Error: 502 Bad Gateway – เรียก IncidentTracking ไม่ได้**

**504 Gateway Timeout – IncidentTracking ตอบช้าเกินกำหนด**

{ "error": "IncidentTracking unavailable", "traceId": "t-123" }

### **Dependency / Reliability**

* Dependency: IncidentTracking Service (GET /incidents?status=ACTIVE)  
* ถ้าเรียกไม่ได้ให้ตอบกลับ error พร้อม message ชัดเจน (UI แสดง warning ได้)

# **API Contract \#4:** Get Shelters

### **ข้อมูลทั่วไป**

* **Name:** Get Shelters  
* **Method:** GET  
* **Path:** /v1/shelters  
* **Type:** Synchronous

### **คำอธิบาย**

### ดึงข้อมูลตำแหน่ง shelter จาก Shelter Service เพื่อแสดง marker บนแผนที่ และใช้เป็นตัวเลือก destination ในการขอ route

### **Request**

**Path/Query Param**

* limit (int, default=200) – จำนวนรายการสูงสุด

**Headers**

* Accept: application/json

### 

### **Response**

**Success: (200 OK)**

{

  "items": \[

    {

      "shelter\_id": "S-101",

      "name": "Shelter A",

      "lat": 13.7367,

      "lon": 100.5231,

      "status": "open"

    }

  \],

  "count": 1

}

**Error: 502 Bad Gateway – เรียก Shelter Service ไม่ได้**

**504 Gateway Timeout – Shelter Service ตอบช้าเกินกำหนด**

{ "error": "Shelter service unavailable", "traceId": "t-456" }

### **Dependency / Reliability**

* **Dependency:** Shelter Service (GET /shelters?status=open)  
* ถ้าเรียกไม่ได้: UI ยังให้ผู้ใช้เลือก destination ด้วยการคลิกแผนที่ได้ (fallback ที่ระดับ UI)

# Service Data

# **Service Data**

# **1\) Route Calculation Record (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| :---: | :---: | :---: | :---: | :---: |
| routeId | UUID | Y(PK) | Id route | "uuid-123" |
| incidentId | String | Y | จาก schema กลาง | "INC-001" |
| origin\_lat | Decimal | Y | ละติจูดจุดเริ่มต้น | 13.7563 |
| origin\_lon | Decimal | Y | ลองจิจูดจุดเริ่มต้น | 100.5018 |
| destination\_lat | Decimal | Y | ละติจูดปลายทาง | 13.7563 |
| destination\_lon | Decimal | Y | ลองจิจูดปลายทาง | 100.5018 |
| selected\_route\_index | Integer | Y | index ของ route ที่เลือก | 1 |
| distance\_meters | Integer | Y | ระยะทางของเส้นทางที่เลือก | 5000 |
| duration\_seconds | Integer | Y | เวลาที่ใช้โดยประมาณ | 180 |
| incident\_hit\_count | Integer | Y | จำนวน incident zones ที่ route ตัดผ่าน | 1 |
| highest\_impact\_level | Integer | Y | impact level สูงสุดที่ route ผ่าน | 3 |
| route\_status | String | Y | สถานะผลลัพธ์ของ route | "ROUTE\_RECOMMENDED" |
| warning | String | N | ข้อความเตือน | null |
| created\_at | Timestamp | Y | เวลาที่สร้าง record | "2026-02-15T10:10:00Z" |

