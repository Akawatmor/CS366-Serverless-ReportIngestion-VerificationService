# Service Overview

**ภาพรวมของบริการ (Service Overview)**  
**Trace Missing Service**

1. **Service Owner**

นางสาวปัฐยาวัต พูลสวัสดิ์ 

2. **Service Purpose**

เป็นระบบบริการที่ช่วยสนับสนุนทั้งผู้ประสบภัยและเจ้าหน้าที่กู้ภัยในการติดตามและค้นหาบุคคลสูญหายในช่วงเกิดเหตุการณ์ภัยพิบัติ โดยระบบทำหน้าที่รับแจ้งข้อมูลผู้สูญหาย บันทึกและจัดเก็บรายละเอียดที่เกี่ยวข้อง พร้อมทั้งอำนวยความสะดวกให้เจ้าหน้าที่สามารถสืบค้นข้อมูลหรือประสานงานเพื่อตามหาญาติของผู้ประสบภัยที่ยังไม่ทราบตัวตนได้

3. **Pain Point ที่แก้ไข**

ในขณะที่เกิดเหตุการณ์ภัยพิบัติ ผู้ประสบภัยมักเร่งอพยพเพื่อความปลอดภัย ส่งผลให้เกิดการพลัดหลงกันระหว่างสมาชิกในครอบครัวได้ง่าย อีกทั้งในกรณีที่มีญาติหรือคนใกล้ชิดอยู่ในพื้นที่ประสบภัยแต่ไม่สามารถติดต่อได้ ผู้ที่อยู่นอกพื้นที่มักไม่ทราบว่าจะเริ่มต้นติดตามหรือค้นหาข้อมูลจากช่องทางใดนอกจากนี้ ยังมีกรณีผู้ประสบภัยที่ถูกส่งตัวเข้ารับการรักษาในโรงพยาบาลโดยไม่สามารถระบุตัวตนได้ ทำให้เจ้าหน้าที่ไม่สามารถประสานงานติดต่อญาติได้อย่างรวดเร็วปัญหาเหล่านี้สะท้อนถึงการขาดระบบกลางสำหรับรวบรวมข้อมูลผู้สูญหายและผู้ประสบภัยที่ไม่ทราบตัวตน ส่งผลให้การค้นหาและการประสานงานล่าช้า และเพิ่มความกังวลให้กับครอบครัวของผู้ประสบภัย

4. **Target Users**  
   1. เจ้าหน้าที่กู้ภัย  
   2. เจ้าหน้าที่โรงพยาบาล  
   3. ศูนย์ประสานงานเหตุฉุกเฉิน   
      (ระบบถูกออกแบบให้เป็น ศูนย์กลางข้อมูลผู้สูญหายและผู้ประสบภัยนิรนาม เพื่อให้เจ้าหน้าที่สามารถบันทึกตรวจสอบ และจับคู่ข้อมูลได้อย่างรวดเร็ว)  
   4. ครอบครัวหรือญาติของผู้ประสบภัย   
      (โดยครอบครัวสามารถแจ้งข้อมูลหรือค้นหาข้อมูลผ่านระบบที่เชื่อมต่อกับบริการนี้)  
5. **Service Boundary**  
   1. In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)  
      1. จัดเก็บข้อมูลผู้สูญหาย เช่น รูปร่างหน้าตา เพศ ลักษณะเสื้อผ้า ช่วงอายุ  
      2. จัดเก็บข้อมูลผู้ประสบภัยที่ยังไม่สามารถระบุตัวตนได้  
      3. จัดเก็บสถานะผู้สูญหาย เช่น สูญหาย, อยู่ระหว่างตรวจสอบ, พบตัวแล้ว, ยืนยันตัวตนแล้ว  
      4. รองรับการค้นหาและจับคู่ข้อมูล  
      5. บันทึกประวัติการอัปเดตข้อมูล  
   2. Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
      1. เข้าช่วยเหลือผู้สูญหาย  
      2. การวางแผนจัดการเหตุการณ์ภัยพิบัติ   
      3. การจัดสรรทรัพยากรหรือบุคลากรกู้ภัย  
      4. การให้บริการทางการแพทย์  
6. **Autonomy / Decision Logic**

บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การจัดลำดับความสำคัญของเคสผู้สูญหาย (priority-based case handling)  
* การประเมินและจัดอันดับความเป็นไปได้ของการจับคู่ข้อมูล (match ranking)  
* การแจ้งเตือนเจ้าหน้าที่เมื่อพบข้อมูลที่มีความสอดคล้องสูง  
* การเปลี่ยนสถานะเคสอัตโนมัติ เช่น Potential Match หรือ Under Review

การตัดสินใจอิงจาก:

* ข้อมูลลักษณะบุคคล (เพศ, ช่วงอายุ, ลักษณะทางกายภาพ)  
* สถานที่และเวลาที่พบล่าสุด  
* คะแนนความสอดคล้องของข้อมูล (matching score / confidence level)  
* ระดับความเปราะบางของผู้สูญหาย (เช่น เด็ก ผู้สูงอายุ ผู้พิการ)  
* ระยะเวลาที่เคสเปิดค้างอยู่

บริการสามารถตัดสินใจได้เองภายใต้ business rules ที่กำหนด โดยไม่ต้องรอ/ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ

7. **Owned Data**  
* Missing Person Records

  ข้อมูลผู้สูญหาย เช่น ชื่อ–นามสกุล (ถ้ามี), เพศ, ช่วงอายุ, ลักษณะทางกายภาพ, เสื้อผ้า, รูปภาพ, สถานที่พบล่าสุดข้อมูลชุดนี้เป็นแกนหลักของ domain และเป็น input หลักของ decision logic (matching & prioritization)

* Unidentified Victim Records

  ข้อมูลผู้ประสบภัยที่ยังไม่สามารถระบุตัวตนได้ เช่น หมายเลขเคส, สถานพยาบาลที่รับตัว, สภาพร่างกายโดยสังเขป

  ข้อมูลนี้ใช้โดยตรงในกระบวนการจับคู่ (matching process)  
  บริการต้องควบคุม state และการเปลี่ยนแปลงสถานะ เช่น Under Review, Potential Match, Confirmed

* Case Status State

  สถานะของแต่ละเคส เช่น MISSING, POTENTIAL\_MATCH, CONFIRMED, CLOSED เนื่องจากสถานะเป็นส่วนหนึ่งของ decision logic และ workflow ภายในบริการ  
  จึงต้องอยู่ภายใต้การควบคุมของบริการนี้

* Matching Results / Match Scores

  ผลลัพธ์จาก algorithm หรือ rule-based matching

  ใช้สำหรับ audit, การจัดอันดับ และป้องกันการประมวลผลซ้ำ

8.  **Linked Data (Reference Only)**  
   1. ระบบจะดูว่าข้อมูลผู้สูญหายที่แจ้งเข้ามามาจากเหตุการณ์ภัยพิบัติใดจาก IncidentId และดูสถานะของเหตุการณณ์ภัยพิบัตินั้นว่าเป็นเหตุการณ์ที่ Active หรือ Resolve  
   2. ระบบจะดูว่าข้อมูลผู้ประสบภัยนิรนามที่แจ้งเข้ามามาจากที่ใด HospitalId หรือ ShelterId

บริการนี้ไม่เก็บสำเนาข้อมูล Incident หรือ Hospital และ Shelter  อย่างถาวร แต่จะอ้างอิงผ่าน API หรือ Event เท่านั้น

9. **Non-Functional Requirements**  
   1. ใช้รูปแบบ message delivery แบบ at-least-once  
   2. ต้องมีการตรวจสอบ messageId เพื่อป้องกันการประมวลผลซ้ำ (idempotency)  
   3. Retry ไม่เกิน 3 ครั้ง พร้อม exponential backoff

   หาก Incident Service หรือ Hospital Service ไม่ตอบสนอง:

   1. ให้ retry 1 ครั้ง  
   2. หากยังไม่สำเร็จ ให้ mark เคสเป็น “PENDING\_EXTERNAL\_VALIDATION”  
   3. ระบบต้องไม่ crash เมื่อได้รับ message ผิดรูปแบบ และต้อง log error อย่างเหมาะสม  
   4. ข้อมูลส่วนบุคคลต้องถูกเข้ารหัส (encryption at rest & in transit)  
   5. ต้องมี audit trail สำหรับทุกการเปลี่ยนสถานะ

# Sync Contract

**Synchronous Function Contract**  
**Base URL:** *http://TMS.com*

# **API Contract \#1: Create Missing People Case**

### **ข้อมูลทั่วไป**

* **Name:** Create Missing People Case  
* **Method:** POST  
* **Path:** /v1/missing-people  
* **Type:** Synchronous

### **คำอธิบาย**

### ใช้สำหรับบันทึกข้อมูลผู้สูญหายเข้าสู่ระบบผู้แจ้งเหตุจำเป็นต้องได้รับ caseId กลับทันทีเพื่อใช้อ้างอิงติดตามสถานดังนั้นจึงออกแบบเป็น Synchronous API เพื่อให้ทราบผลการสร้างเคสแบบ real-time

### **Request**

**Headers**

* Accept: application/json

  **Body:** 

  {

  	"incident\_id": "INC-2026-001",

    "reported\_by": {

      "fullname": "สมชาย รักดี",

      "contact\_number": "0999999999",

      "relation": "FATHER"

    },

    "person\_detail": {

      "first\_name": "มะลิ",

      "last\_name": "จันทร์ดี",

      "age": 25,

      "gender": "FEMALE",

      "height\_cm": 163,

      "weight\_kg": 52,

      "skin\_color": "ผิวขาวเหลือง",

      "hair\_color": "สีดำ",

      "hair\_type": "SHORT",

      "physical\_marks": "มีรอยสักดอกไม้ที่แขนขวา"

    },

    "last\_seen": {

      "datetime": "2026-02-14T09:30:00Z",

      "location": {

        "lat": 13.7563,

        "lng": 100.5018,

        "description": "ตลาดบางกอกน้อย"

      },

      "clothes\_description": "ใส่กางเกงยีนส์และเสื้อลายจุดสีดำ"

    },

    "special\_condition": "ไม่มี",

    "priority\_level": "NORMAL"

  }

**Validation Rules**

1. incident\_id ต้องไม่ว่าง และต้องเป็น UUID format ที่ถูกต้องและมีอยู่จริง  
2. relation ต้องเป็นค่า FATHER, MOTHER, SIBLING, FRIEND, GUARDIAN, OTHER  
3. gender ต้องเป็นค่า MALE, FEMALE, OTHER

### **Response**

**Success:**

{

  "success": true,

  "message": "Missing person case created successfully",

  "data": {

    "missing\_id": "MID-2026-002",

    "incident\_id": "INC-2026-001",

    "status": "OPEN",

    "priority\_level": "NORMAL",

    "created\_at": "2026-02-20T10:00:00Z"

  }

}

**Error:** 

**400 Bad Request**

{

  "success": false,

  "code": "VALIDATION\_ERROR",

  "message": "Request validation failed",

  "errors": \[

    {

    	  "field": "person\_detail.age",

   	   "message": "Age must be between 0 and 120"

   	 }

     \]

}

**404 Not Found**

{

  "success": false,

  "code": "INCIDENT\_NOT\_FOUND",

  "message": "Incident ID INC-2026-001 does not exist"

}

### **Dependency / Reliability**

* External call timeout: 3 seconds  
* Retry: 3 times (exponential backoff)  
* Circuit breaker: enabled

# 

# **API Contract \#2: Create Found Victim Case**

### **ข้อมูลทั่วไป**

* **Name:** Create Found Victim Case  
* **Method:** POST  
* **Path:** /v1/found-victims  
* **Type:** Synchronous

### **คำอธิบาย**

### ใช้สำหรับบันทึกข้อมูลผู้ประสบภัยนิรนามที่ถูกพบเข้าสู่ระบบ เพื่อใช้ในการจับคู่กับข้อมูลผู้สูญหายเจ้าหน้าที่จำเป็นต้องได้รับ `found_id` กลับทันทีเพื่อนำไปอ้างอิงในกระบวนการ matching ดังนั้นจึงออกแบบเป็น Synchronous API เพื่อให้ทราบผลการสร้างข้อมูล

### **Request**

**Headers**

* Accept: application/json

  **Body:** 

  {

    "incident\_id": "550e8400-e29b-41d4-a716-446655440000",

    "reported\_by": "Rescue Team A",

    "found\_location": {

      "lat": 13.7563,

      "lng": 100.5018,

      "description": "บริเวณตลาดบางกอกน้อย"

    },

    "found\_datetime": "2026-02-14T11:45:00Z",

    "person\_detail": {

      "gender": "FEMALE",

      "estimated\_age\_range": "50-60",

      "height\_cm": 165,

      "weight\_kg": 55,

      "skin\_color": "ผิวขาวเหลือง",

      "hair\_color": "สีดำ",

      "hair\_type": "SHORT",

      "physical\_marks": "มีไฝที่แก้มซ้าย"

    },

    "clothes\_description": "ใส่เดรสลายดอกไม้สีฟ้า",

    "current\_location": "โรงพยาบาลชุมชน",

    "priority\_level": "NORMAL"

  }

**Validation Rules**

1. incident\_id ต้องไม่ว่าง และต้องเป็น UUID format ที่ถูกต้องและมีอยู่จริง  
2. gender ต้องเป็นค่า MALE, FEMALE, OTHER

### **Response**

**Success:**

{

  "success": true,

  "message": "Found victim case created successfully",

  "data": {

    "found\_id": "FID-2026-002",

    "incident\_id": "550e8400-e29b-41d4-a716-446655440000",

    "status": "UNMATCHED",

    "priority\_level": "NORMAL",

    "created\_at": "2026-02-20T10:00:00Z"

  	}

}

**Error:** 

**400 Bad Request**

{

  "success": false,

  "code": "VALIDATION\_ERROR",

  "message": "Request validation failed",

  "errors": \[

    {

      "field": "person\_detail.height\_cm",

      "message": "Height must be between 30 and 250 cm"

    	}

  \]

}

**404 Not Found**

{

  "success": false,

  "code": "INCIDENT\_NOT\_FOUND",

  "message": "Incident ID 550e8400-e29b-41d4-a716-446655440000 does not exist"

}

### **Dependency / Reliability**

* External call timeout: 3 seconds  
* Retry: 3 times (exponential backoff)  
* Circuit breaker: enabled  
* ไม่มีการเรียก external matching engine แบบ synchronous  
* การ matching จะทำผ่าน asynchronous process ภายหลัง

# **API Contract \#3: Update Found Victim Case Status**

### **ข้อมูลทั่วไป**

* **Name:** Update Found Victim Status  
* **Method:** PUT  
* **Path:** /v1/found-victims/{found\_id}  
* **Type:** Synchronous

### **คำอธิบาย**

### 	ใช้สำหรับอัปเดตสถานะของผู้ประสบภัยนิรนาม เช่น อยู่ระหว่างรอการจับคู่, จับคู่สำเร็จ หรือยืนยันตัวตนเรียบร้อย

### **Request**

**Path/Query Param**

* found\_id (string, required)

  **Headers**

* Accept: application/json

  **Body**

**กรณีมี Matching กับข้อมูลผู้ประสบภัยนิรนาม**

	{

  "status": "MATCHED",

  "missing\_id": "MID-2026-002",

  "updatedBy": "OFFICER-204"

}

**Validation**

* ถ้า status \= MATCHED:  
  * missing\_id ต้องไม่ว่าง  
  * missing\_id ต้องมีอยู่จริง  
  * ห้ามส่ง reported\_detail  
  * ระบบจะดึงข้อมูลจาก Missing table อัตโนมัติ  
* updatedBy ต้องไม่เป็นค่าว่าง

**กรณีไม่มี Matching กับข้อมูลผู้ประสบภัยนิรนาม**

{

  "status": "UNMATCHED",

  "reported\_detail": {

    "fullname": "ไม่ทราบชื่อ",

    "estimated\_age": 60,

    "gender": "FEMALE",

    "found\_location": {

      "lat": 13.7563,

      "lng": 100.5018

    },

    "current\_location": "โรงพยาบาลชุมชน"

  },

  "updatedBy": "OFFICER-204"

}

**Validation**

* ถ้า status ≠ MATCHED:  
  * reported\_detail ต้องไม่ว่าง  
  * missing\_id ห้ามส่งมา  
  * ต้อง validate field ภายใน reported\_detail

### **Response**

**Success:** 

**MATCH**

{

  "success": true,

  "code": "FOUND\_STATUS\_UPDATED",

  "message": "Found victim successfully matched with missing case",

  "data": {

    "found\_id": "FID-2026-002",

    "previous\_status": "MATCHING",

    "current\_status": "MATCHED",

    "missing\_id": "MID-2026-002",

    "match\_snapshot": {

      "missing\_name": "มะลิ จันทร์ดี",

      "age": 25,

      "gender": "FEMALE"

    },

    "updated\_by": "OFFICER-204",

    "updated\_at": "2026-03-23T10:13:00Z"

  	}

}

UNMATCHED

{

  "success": true,

  "code": "FOUND\_STATUS\_UPDATED",

  "message": "Found victim updated without matching",

  "data": {

    "found\_id": "FID-2026-002",

    "previous\_status": "MATCHING",

    "current\_status": "UNMATCHED",

    "reported\_detail": {

      "fullname": "ไม่ทราบชื่อ",

      "estimated\_age": 60,

      "gender": "FEMALE",

      "current\_location": "โรงพยาบาลชุมชน"

    },

    "updated\_by": "OFFICER-204",

    "updated\_at": "2026-03-23T10:13:00Z"

  }

}

**Error:** 

## **400 Bad Request**

## {

##   "success": false,

##   "code": "VALIDATION\_ERROR",

##   "message": "Validation failed",

##   "errors": \[

##     {

##       "field": "missing\_id",

##       "message": "missing\_id is required when status \= MATCHED"

##     }

##   \]

## }

### **Dependency / Reliability**

* ไม่มีการเรียก external service แบบ synchronous  
* การทำงานทั้งหมดอยู่ภายใน domain ของ Trace Missing Service  
* การอัปเดตฐานข้อมูลมี retry ไม่เกิน 3 ครั้ง   
* เปิดใช้งาน circuit breaker เพื่อป้องกัน cascading failure เมื่อฐานข้อมูลมีปัญหา  
* ใช้ optimistic locking (version control) เพื่อป้องกัน concurrent update จากหลายคำขอพร้อมกัน  
* การอัปเดตสถานะเป็น idempotent operation หากมีการส่งคำขอซ้ำ ระบบจะไม่ก่อให้เกิด side-effect ซ้ำ

# **API Contract \#4: Update Missing Persons Case Status**

### **ข้อมูลทั่วไป**

* **Name:** Update Missing Person Status  
* **Method:** PUT  
* **Path:**/v1/missing-people/{missing\_id}  
* **Type:** Synchronous

### **คำอธิบาย**

### 	ใช้สำหรับอัปเดตสถานะของผู้สูญหาย 

### **Request**

**Path/Query Param**

* missing\_id  (string, required)

  **Headers**

* Accept: application/json

  **Body**

	{

  "status": "MATCHED",

  "found\_id": "FID-2026-002",

  "updatedBy": "OFFICER-204"

}

**Validation**

* ถ้า status \= MATCHED:  
  * found\_id ต้องไม่ว่าง  
  * found\_id ต้องมีอยู่จริง  
  * found victim ต้องมี status \= UNMATCHED หรือ MATCHING  
* ถ้า status ≠ MATCHED:  
  * ห้ามส่ง found\_id

### **Response**

**Success:** 

{

  "success": true,

  "message": "Case matched successfully",

  "data": {

    "missing\_id": "MID-2026-002",

    "found\_id": "FID-2026-002",

    "match\_score": 89,

    "found\_location": {

      "lat": 13.7563,

      "lng": 100.5018

    		},

    "current\_location": "โรงพยาบาลชุมชน",

    "updated\_by": "OFFICER-204",

    "updated\_at": "2026-03-23T10:13:00Z"

 	 }

}

**Error:** 

## **400 Bad Request**

## {

##   "success": false,

##   "code": "VALIDATION\_ERROR",

##   "message": "Request validation failed",

##   "errors": \[

##     {

##       "field": "status",

##       "message": "Status must be one of: UNMATCHED, MATCHING, MATCHED, 

## IDENTIFIED"

##     }

##   \]

## }

## **404 Not Found**

{  
  "success": false,  
  "code": "FOUND\_CASE\_NOT\_FOUND",  
  "message": "Found victim case with ID FID-2026-002 not found"  
}

### **Dependency / Reliability**

* ไม่มี external synchronous call  
* ทำงานภายใน Trace Missing Service domain  
* Database update retry 3 ครั้ง (exponential backoff)  
* Circuit breaker enabled  
* ใช้ optimistic locking เพื่อป้องกัน concurrent update

# **API Contract \#5: Search Missing Reports**

### **ข้อมูลทั่วไป**

* **Name:** Search Missing Reports  
* **Method:** GET  
* **Path:** /v1/missing-reports  
* **Type:** Synchronous

### **คำอธิบาย**

### ใช้สำหรับค้นหาและกรองข้อมูลผู้สูญหายตามเงื่อนไขต่าง ๆ เช่น ชื่อ เพศ อายุ สถานะ หรือช่วงวันที่

### **Request**

**Path/Query Param**

* firstName (string)

* lastName (string)

* gender(string)

* status(string)

* incident\_id

  **Headers**

* Accept: application/json

  **Validation**

* gender ต้องเป็น MALE, FEMALE, OTHER  
* status ต้องเป็น OPEN, MATCHING, REUNION

### **Response**

**Success:** 

{

  "success": true,

  "data": {

    "total": 25,

    "page": 1,

    "size": 10,

    "items": \[

      {

        "missing\_id": "MID-2026-002",

        "first\_name": "มะลิ",

        "last\_name": "จันทร์ดี",

        "age": 25,

        "gender": "FEMALE",

        "status": "OPEN",

        "incident\_id": "550e8400-e29b-41d4-a716-446655440000",

        "created\_at": "2026-02-20T10:00:00Z"

      }

    \]

  }

}

**Error: 404 Not Found (ไม่พบ caseId)**

{

  "success": false,

  "code": "INVALID\_QUERY\_PARAMETER",

  "message": "Invalid query parameter value"

}

### **Dependency / Reliability**

* ไม่มี external synchronous call  
* ใช้ database index สำหรับค้นหา  
* Pagination required เพื่อลด load

# **API Contract \#6: Get Missing Report Detail**

### **ข้อมูลทั่วไป**

* **Name:** Get Missing Report Detail  
* **Method:** GET  
* **Path:** /v1/missing-reports/{missing\_id}  
* **Type:** Synchronous

### **คำอธิบาย**

### ใช้สำหรับดึงรายละเอียดข้อมูลผู้สูญหายรายเคสตาม missing\_id

### **Request**

**Path/Query Param**

* missing\_id (string,required)

  **Headers**

* Accept: application/json

  **Validation**

* missing\_id ต้องไม่เป็นค่าว่าง  
* missing\_id ต้องมีอยู่ในระบบ

### **Response**

**Success:** 

{

  "success": true,

  "data": {

    "missing\_id": "MID-2026-002",

    "first\_name": "มะลิ",

    "last\_name": "จันทร์ดี",

    "age": 25,

    "gender": "FEMALE",

    "status": "MATCHING",

    "incident\_id": "550e8400-e29b-41d4-a716-446655440000",

    "last\_seen\_location": {

      "lat": 13.7563,

      "lng": 100.5018

    },

    "description": "สวมเสื้อสีแดง กางเกงยีนส์",

    "created\_at": "2026-02-20T10:00:00Z",

    "updated\_at": "2026-02-21T09:30:00Z"

  }

}

**Error: 404 Not Found (ไม่พบ caseId)**

{

  "success": false,

  "code": "CASE\_NOT\_FOUND",

  "message": "Missing report not found"

}

### **Dependency / Reliability**

* ไม่มี external synchronous call  
* ใช้ primary key lookup (indexed query)  
* Read-only operation  
* รองรับ high read traffic  
* ใช้ caching layer ได้ในอนาคต (เช่น Redis)

# Async Contract

**Asynchronous Function Contract**

## **Message Contract \#1: MissingCaseCreatedEvent**

### **ข้อมูลทั่วไป** 

* **Message Name:** MissingCaseCreated  
* **Interaction Style:** Event-Driven (Publish/Subscribe)  
* **Producer:** Trace Missing Service  
* **Consumer:**   
  * **IncidentTracking Service**  
  * **DisasterMonitoring Service**  
  * **Rescue Prioritization Service**  
* **Channel/Queue: missing.case.created**  
* **Version:** v1

### **คำอธิบาย**

### Event นี้จะถูก publish เมื่อมีการสร้าง Missing Case ใหม่ในระบบ เพื่อให้บริการอื่นรับทราบและเริ่มกระบวนการที่เกี่ยวข้อง

### **Request** 

### **Message Headers**

* messageId  
* eventType  
* occurredAt  
* version  
* producer

  **Message Body**

  {

    "missing\_id": "MID-20260220-001",

    "incident\_id": "INC-20260220-001",

    "firstName": "มะลิ",

    "lastName": "จันทร์ดี",

    "age": 25,

    "gender": "FEMALE",

    "lastSeenLocation": {

      "lat": 13.7563,

      "lng": 100.5018

    },

    "status": "OPEN",

    "reportedAt": "2026-02-20T09:00:00Z"

  }


  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | :---: | ----- |
| missing\_id | string | YES✅ | รหัสผู้สูญหาย |
| incident\_id | string | YES✅ | รหัส Incident |
| status | string | YES✅ | สถานะ |
| age | string | YES✅ | อายุ |
| lastSeenLocation | object | YES✅ | ละติดจูดลองจิดจูดที่พบล่าสุด |
| gender | string | YES✅ | เพศ |
| confirmedRole | string | YES✅ | OFFICER/NURSE |
| confirmedAt | datetime | YES✅ | เวลายืนยัน |
| reportedAt | datetime | YES✅ | วันเวลายืนยัน |

**Validation Rules**

* status ต้องเป็น `REUNION` เท่านั้น  
* messageId ต้องไม่ซ้ำ (idempotency)  
* confirmedAt ต้องไม่เป็น future time  
* ทุก required field ต้องไม่เป็น null

**Response**

	**Message Headers** 

* correlationId  
* status


  **Success Message Body**

  {

    "message": "Event processed successfully",

    "processedAt": "2026-02-19T10:15:02Z"

  }


  **Reject/Error Message Body**

  {

    "errorCode": "INVALID\_STATUS",

    "errorMessage": "Status must be REUNION"

  }


  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| errorCode | string | YES | รหัสข้อผิดพลาดเชิงระบบ ใช้สำหรับระบุประเภทของ error |
| errorMessage | string | YES | ข้อความอธิบายรายละเอียดของข้อผิดพลาด |

	**Validation Rules**

* ต้องรองรับ At-Least-Once Delivery  
* ต้องทำ idempotent processing  
* หาก processing ล้มเหลว → retry ตาม policy ของ broker  
* หากเกิน retry limit → ส่งเข้า Dead Letter Queue (DLQ)

# Service Data

# **Service Data**

# **1\) Missing-Person Case (Owned by this service)**

| Field Name | Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | :---: | :---- | :---- |
| reportedBy |  | Objects | YES✅ | ข้อมูลผู้แจ้ง |  |
|  | fullname | string | YES✅ | ชื่อผู้แจ้ง | สมชาย รักดี |
|  | contactNumber | string | YES✅ | เบอร์โทรศัพท์ผู้แจ้ง | 099-999-9999 |
|  | relation | string (enum) | YES✅ | ความสัมพันธ์กับ ผู้สูยหาย | FATHER, MOTHER, SIBLING, FRIEND, GUARDIAN, OTHER |
| firstName |  | string | YES✅ | ชื่อผู้สูญหาย | มะลิ  |
| lastName |  | string | YES✅ | นามสกุลผู้สูญหาย | จันทร์ดี |
| age |  | integer | YES✅ | อายุผู้สูญหาย | 25 |
| gender |  | string | YES✅ | เพศสภาพผู้สูญหาย | FEMALE, MALE |
| height |  | integer | YES✅ | ส่วนสูงผู้สูญหาย | 163 |
| weight |  | integer | YES✅ | น้ำหนักผู้สูญหาย | 52 |
| skinColor |  | string | YES✅ | สีผิวผู้สูญหาย | ผิวขาวเหลือง |
| hairColor |  | string | YES✅ | สีผมผู้สูญหาย | สีแดง |
| hair |  | string | YES✅ | ประเภทผู้สูญหาย | ผมสั้น |
| physical\_mark |  | string | NO❌ | จุดสังเกตุบนร่างกายเช่น ไฝ, รอยแผลเป็น, รอยสัก | มีรอยสักดอกไม้อยู่ที่แขนขวา |
| clothesDescription |  | string | YES✅ | เสื้อผ้าที่ผู้สูญหายใส่ล่าสุด | ใส่กางเกงยีนส์และเสื้อลายจุดสีดำ |
| lastSeenLocation |  | object | YES✅ | สถานที่ที่พบล่าสุด | lat/lng |
|  | lat | decimal | YES✅ |  | 12.435 |
|  | lng | decimal | YES✅ |  | 100.4355 |
| special\_condition |  | string | NO❌ | เงื่อนไขพิเศษหรือ ความต้องการพิเศษสำหรับผู้สูญหาย เช่นตาบอด  | ไม่มี |
| status |  | string | YES✅ | สถานะ | สูญหาย |
| create\_at |  | datetime | YES✅ | วันและเวลาที่สร้าง | 2026-02-14T10:00:00Z |
| update\_at |  | datetime | YES✅ | วันและเวลาที่อัพเดท | 2026-02-14T10:00:00Z |
| missing\_id |  | uuid | YES✅ | รหัสประจำตัวผู้สูญหาย | MID-2026-002  |
| photoUrl |  |  | NO❌ | รูปภาพผู้สูญหาย |  |

# 

# 

# 

# 

# 

# 

# **2\) Found Victims (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | :---: | :---: | ----- | ----- |
| found\_id | string | YES✅ | รหัสผู้ประสบภัยนิรนาม |  FID-2026-002 |
| reportedBy | string | YES✅ | หน่วยงานที่แจ้ง | Rescue Team |
| found\_lat | decimal | YES✅ | ตำแหน่งละติจูดที่พบ ผู้ประสบภัยนิรนาม | 12.3455 |
| found\_lng | decimal | YES✅ | ตำแหน่งลองจิจูดที่พบ ผู้ประสบภัยนิรนาม | 100.3445 |
| gender | string | YES✅ | เพศสภาพ | หญิง |
| estimated\_age | string | YES✅ | ช่วงอายุคาดการณ์ | 50-60 |
| height | string | YES✅ | ส่วนสูงจากการคาดการณ์ | 160-170 |
| weight | string | YES✅ | น้ำหนักจากการคาดการณ์ | 50-60 |
| skinColor | string | YES✅ | สีผิว | ผิวขาวเหลือง |
| hairColor | string | YES✅ | สีผม | ผมสีดำ |
| hair | string | YES✅ | ประเภทผมเช่น ผมยาว, ผมสั้น, ผมหยิก | ผมสั้น |
| physical\_mark | string | NO❌ | จุดสังเกตุบนร่างกายเช่น ไฝ, รอยแผลเป็น, รอยสัก | มีไฝ |
| clothes\_description | string | YES✅ | รายละเอียดเสื้อผ้าผู้ประสบภัย นิรนาม | ใส่เดรสลายดอกไม้สีฟ้า |
| location\_id  | string | YES✅ | ตำแหน่งปัจจุบันของ ผู้ประสบภัยนิรนามเช่นตำแหน่ง shelter หรือโรงพยาบาล | โรงพยาบาลชุมชุน |
| photo\_url | string | NO❌ | รูปภาพผู้ประสบภัย |  |
| status | string | YES✅ | สถานะ | ไม่พบญาติ |
| created\_at | datetime | YES✅ | วันและเวลาที่สร้าง | 2026-02-14T10:00:00Z |
| updated\_at | datetime | YES✅ | วันและเวลาที่อัพเดท | 2026-02-14T10:00:00Z |

# **3\) Case Match (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | :---: | :---: | ----- | ----- |
| caseId | string | YES✅ | รหัสผู้ประสบภัยนิรนาม |  CID-2026-002 |
| missingId | string | YES✅ | หน่วยงานที่แจ้ง | MID-2026-002 |
| foundId | string | YES✅ | รหัสผู้ประสบภัยนิรนาม | FID-2026-002 |
| match\_score | number | YES✅ | คะแนนการจับคู่ | 89 |
| match\_status | string | YES✅ | สถานะการจับคู่ | Matching |
| verified | string | YES✅ | สถานะการถูกยืนยัน | VERIFIED |
| verified\_by | string | YES✅ | ยืนยันโดย | Rescue Team |
| create\_at | datetime | YES✅ | วันและเวลาที่สร้าง | 2026-02-14T10:00:00Z |
| updated\_at | datetime | YES✅ | วันและเวลาที่อัพเดท | 2026-02-14T10:00:00Z |

