# Service Overview

**ภาพรวมของบริการ (Service Overview)**  
HospitalResourceMonitoring Service  
Github: [https://github.com/fainatakorn17/hospital\_resource\_monitoring](https://github.com/fainatakorn17/hospital_resource_monitoring.git)

1. **Service Owner**

	นางสาว ณฐกร โลหะสุวรรณ 6609611873 ภาคปกติ

2. **Service Purpose**

	HospitalResourceMonitoring Service ระบบนี้จะดูแลและจัดการข้อมูลทรัพยากรของโรงพยาบาลโดยเฉพาะ เช่น เตียง เลือด และเครื่องช่วยหายใจ ทำหน้าที่รับข้อมูลอัปเดตจากโรงพยาบาลและประเมินสถานะความพร้อมของทรัพยากรตามเกณฑ์ที่กำหนด เมื่อระดับทรัพยากรต่ำกว่าค่าที่กำหนด ระบบจะเปลี่ยนสถานะและแจ้งข้อมูลไปยังบริการที่เกี่ยวข้องโดยอัตโนมัติ

3. **Pain Point ที่แก้ไข**

	ในช่วงการประสานงานและส่งต่อผู้ป่วย หน่วยงานที่เกี่ยวข้องมักไม่ทราบสถานะทรัพยากรของแต่ละโรงพยาบาลแบบทันที เช่น จำนวนเตียง ICU หรือเครื่องช่วยหายใจที่ยังว่างอยู่ ทำให้การตัดสินใจส่งผู้ป่วยฉุกเฉินอาจไม่เหมาะสม

ผลกระทบคือ ผู้ป่วยอาจถูกส่งไปยังโรงพยาบาลที่ทรัพยากรไม่เพียงพอ ต้องรอคิวหรือถูกส่งต่อไปที่อื่นอีก ทำให้เสียเวลาในการรักษา และเพิ่มความเสี่ยงต่อชีวิตผู้ป่วย นอกจากนี้ยังส่งผลต่อการทำงานโดยรวมของระบบ ทำให้การจัดสรรผู้ป่วยและทรัพยากรระหว่างโรงพยาบาลไม่สมดุลและไม่ทันต่อสถานการณ์

**4\. Target Users**

1. **Dispatcher** (เจ้าหน้าที่ศูนย์สั่งการเหตุฉุกเฉิน) : ใช้ข้อมูลทรัพยากรเพื่อช่วยตัดสินใจส่งผู้ป่วยไปยังโรงพยาบาลที่ยังมีทรัพยากรเพียงพอ และลดความแออัดของโรงพยาบาลที่ใกล้เต็ม  
2. **Hospital Staff** : อัปเดตและตรวจสอบข้อมูลทรัพยากรของโรงพยาบาล เพื่อให้ข้อมูลในระบบถูกต้องและเป็นปัจจุบัน

**5\. Service Boundary**

* In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)  
  * รับและบันทึกข้อมูลอัปเดตทรัพยากรของโรงพยาบาล  
  * ประเมินและกำหนดสถานะความพร้อมของทรัพยากร (เช่น NORMAL, WARNING, CRITICAL)  
  * Publish event เมื่อทรัพยากรต่ำกว่าเกณฑ์ที่กำหนด

* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
  * ไม่ทำการร้องขอหรือจัดสรรทรัพยากรแทนโรงพยาบาลเมื่อมีทรัพยากรเหลือต่ำ  
  * ไม่ส่งการแจ้งเตือนในรูปแบบ SMS, Email หรือ UI notification (ทำหน้าที่เพียง publish event)  
  * ไม่ทำหน้าที่ตัดสินใจเลือกโรงพยาบาลเพื่อส่งผู้ป่วย (เป็นหน้าที่ของ Dispatcher หรือ Incident/Dispatch Service)

**6\. Autonomy / Decision Logic**  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การประเมินและกำหนดสถานะความพร้อมของทรัพยากร (NORMAL, WARNING, CRITICAL)  
* การตรวจจับการเปลี่ยนแปลงสถานะของทรัพยากร  
* การ publish event แจ้งเตือนเมื่อทรัพยากรต่ำกว่าเกณฑ์ที่กำหนด

การตัดสินใจอิงจาก:

* จำนวนทรัพยากรที่เหลืออยู่ (availableQuantity)  
* ค่า warningThreshold และ criticalThreshold

บริการสามารถตัดสินใจได้เองภายใต้ business rules ที่กำหนด โดยไม่ต้องรอ/ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ

**7\. Owned Data**

* **HospitalResource (Current Resource State)** เป็นข้อมูลสถานะปัจจุบันของทรัพยากรแต่ละประเภทในแต่ละโรงพยาบาล เช่น จำนวนที่เหลืออยู่ ค่า threshold และสถานะ (NORMAL/WARNING/CRITICAL) ข้อมูลนี้ใช้ในการประเมินความพร้อมของทรัพยากรและเป็นแหล่งข้อมูลหลัก (Single Source of Truth) ของบริการนี้  
* **ResourceStatusChangeLog (Status Transition History)** เป็นข้อมูลประวัติการเปลี่ยนแปลงสถานะทรัพยากร โดยบันทึกเฉพาะเมื่อเกิดการเปลี่ยนสถานะ ข้อมูลนี้ใช้สำหรับการตรวจสอบย้อนหลัง (audit) และวิเคราะห์แนวโน้มความพร้อมของทรัพยากรในระยะยาว

**8\. Linked Data (Reference Only)**

* **hospitalId** ที่ใช้เชื่อมโยงทรัพยากรกับ Hospital Service โดยบริการนี้ไม่ได้เป็นเจ้าของหรือจัดเก็บรายละเอียดของโรงพยาบาล เพื่อรักษาหลักการ Data Ownership และลดความซ้ำซ้อนของข้อมูลระหว่างบริการ

**9\. Non-Functional Requirements**

* **Idempotency**: ระบบต้องรองรับการเรียก API ซ้ำในกรณีที่คำขอเดียวกันถูกส่งหลายครั้ง เช่น จากปัญหาเครือข่าย โดยต้องไม่สร้าง Incident ซ้ำ หรือปรับลดจำนวนทรัพยากรซ้ำจากคำขอเดิม  
* **Performance**: เมื่อมีการแจ้งเหตุฉุกเฉิน ระบบต้องบันทึก Incident ได้ทันที และแสดงสถานะทรัพยากรของโรงพยาบาลโดยไม่ล่าช้า เพื่อให้ตัดสินใจเลือกโรงพยาบาลได้อย่างรวดเร็ว  
* **Availability**: หาก Service ใดมีปัญหา เช่น Hospital Service ระบบส่วนอื่นยังต้องทำงานต่อได้ และต้องแสดงข้อผิดพลาดอย่างเหมาะสมโดยไม่ทำให้ทั้งระบบล่ม  
* **Data Intrigity**: การอัปเดตจำนวนทรัพยากรหรือการเปลี่ยนสถานะ Incident ต้องไม่ทำให้ข้อมูลขัดแย้งกัน เช่น จำนวนทรัพยากรต้องไม่ติดลบ และสถานะต้องสอดคล้องกับข้อมูลจริง


# Sync Contract

**Synchronous Function Contract**  
**Base URL: https://api.emergency-system.com**

# **API Contract \#1: Hospital Updates Resource Availability**

### **ข้อมูลทั่วไป**

* **Name:** Hospital Update Resource Availability  
* **Method:** PUT  
* **Path:** /v1/hospitals/{hospitalId}/resources/{resourceType}  
* **Type:** Synchronous (REST API)

### **คำอธิบาย**

ใช้สำหรับอัปเดตจำนวนทรัพยากรที่พร้อมใช้งานของโรงพยาบาล

### **Request**

**Path/Query Params**

* hospitalId (string, required)  
* resourceType (enum, required)

  **Headers**

* Authorization (string, required)  
* Content-Type (required, value="application/json")  
  **Body**  
  {  
    "availableQuantity": 8  
  }

  **Validation:** 

1. availableQuantity ต้องเป็นตัวเลขจำนวนเต็ม ≥ 0  
2. availableQuantity ต้องไม่เกิน totalCapacity

### **Response**

**Success:** 200 OK

{  
  "message": "Resource availability updated successfully"  
}

**Error:** 400 Bad Request

{  
  "errorCode": "INVALID\_QUANTITY",  
  "message": "Available quantity cannot exceed total capacity"  
}

### **Dependency / Reliability**

* การอัปเดตทำงานแบบ transactional (atomic update)  
* รองรับ retry ได้ เนื่องจากเป็น idempotent operation (ใช้ HTTP PUT)

# **API Contract \#2: Get Resource by Hospital** 

### **ข้อมูลทั่วไป**

* **Name:**  Get Hospital Resources by Status  
* **Method:** GET  
* **Path:** /v1/hospitals/{hospitalId}/resources  
* **Type:** Synchronous (REST API)

### **คำอธิบาย**

### Endpoint นี้ใช้สำหรับดึงข้อมูลทรัพยากรทั้งหมดของโรงพยาบาลที่ระบุ โดยสามารถกรองตามสถานะทรัพยากร (NORMAL / WARNING / CRITICAL) ได้ เพื่อให้ Dispatcher หรือระบบอื่นใช้ประกอบการตัดสินใจ

### **Request**

**Path/Query Param**

* hospitalId (string, required)  
* status (enum: NORMAL, WARNING, CRITICAL, optional)  
  **Headers**

* Authorization (string, required)  
* Accept (string, required, value="application/json")

  **Body**: None


  **Validation**

1. hospitalId ต้องไม่เป็นค่าว่าง  
2. status ต้องอยู่ในค่า enum ที่กำหนด (NORMAL, WARNING, CRITICAL)  
3. hospitalId ต้องมีอยู่ในระบบ มิฉะนั้นให้คืน 404

### **Response**

**Success: 200 OK**

{  
    "hospitalId": "H001",  
    "resources": \[  
      {  
          "resourceType": "ICU\_BED",  
          "totalCapacity": 20,  
          "availableQuantity": 5,  
          "resourceStatus": "WARNING",  
          "lastUpdatedTime": "2026-02-27T14:30:00Z"  
      },  
      {  
          "resourceType": "VENTILATOR",  
          "totalCapacity": 15,  
          "availableQuantity": 4,  
          "resourceStatus": "WARNING",  
          "lastUpdatedTime": "2026-02-27T14:32:10Z"  
      },  
      {  
          "resourceType": "BLOOD\_A",  
          "totalCapacity": 30,  
          "availableQuantity": 8,  
          "resourceStatus": "WARNING",  
          "lastUpdatedTime": "2026-02-27T14:35:45Z"  
      }  
    \]  
}

**Error:**

**400 Bad Request**

{  
  "errorCode": "INVALID\_STATUS\_FILTER",  
  "message": "Status must be NORMAL, WARNING, or CRITICAL"  
}

**404 Not Found**

{  
  "errorCode": "HOSPITAL\_NOT\_FOUND",  
  "message": "Hospital not found"  
}

### **Dependency / Reliability**

* ไม่มี synchronous dependency กับ service อื่น  
* ใช้ข้อมูลจากฐานข้อมูลภายในของ HospitalResourceMonitoring Service เท่านั้น

# **API Contract \#3: Hospital Resource Status Override**

### **ข้อมูลทั่วไป**

* **Name:**   Hospital Resource Status Override  
* **Method:** PATCH  
* **Path:** /v1/hospitals/{hospitalId}/resources/{resourceType}/status  
* **Type:** Synchronous (REST API)

### **คำอธิบาย**

### ใช้สำหรับอัปเดตสถานะของทรัพยากร (NORMAL / WARNING / CRITICAL) โดยระบบหรือ Admin สามารถแก้ไขสถานะได้โดยตรงในกรณีพิเศษ

### **Request**

**Path/Query Param**

* hospitalId (string, required)  
* resourceType (enum, required)  
  **Headers**

* Authorization (string, required)  
* Content-Type (required, value="application/json")

  **Body**:

  {

    "resourceStatus": "CRITICAL",

    "overrideReason": "Manual emergency correction"

  }


  

  **Validation**

1. resourceStatus ต้องเป็น NORMAL / WARNING / CRITICAL เท่านั้น  
2. ผู้เรียกต้องมีสิทธิ์ Admin  
3. ต้องมี overrideReason

### **Response**

**Success:** 200 OK

{

  "message": "Resource status overridden successfully",  
  "hospitalId": "H001",  
  "resourceType": "ICU\_BED",  
  "resourceStatus": "CRITICAL"  
}

**Error:** 

**400 Bad Request**

{  
  "errorCode": "INVALID\_STATUS",  
  "message": "Status must be NORMAL, WARNING, or CRITICAL"  
}

**403 Forbidden**

{  
  "errorCode": "INSUFFICIENT\_PERMISSION",  
  "message": "Admin privilege is required"  
}

**404 Not Found**

{  
  "errorCode": "RESOURCE\_NOT\_FOUND",  
  "message": "Hospital or resource type not found"  
}

### **Dependency / Reliability**

* ระบบบันทึก audit log สำหรับทุก override  
* Override จะไม่แก้ไข availableQuantity

# Async Contract

**Asynchronous Function Contract**

## **Message Contract \#1: ResourceAvailabilityUpdatedEvent**

### **ข้อมูลทั่วไป** 

* **Message Name:** ResourceAvailabilityUpdatedEvent  
* **Interaction Style:** Asynchronous (Event-Driven, Publish/Subscribe)  
* **Producer:** HospitalResourceMonitoring Service  
* **Consumer:** Dispatcher Service, Notification Service, Analytics Service  
* **Channel/Queue:** hospital.resource.availability.updated  
* **Version:** v1

### **คำอธิบาย**

### Message นี้ถูก publish เมื่อมีการอัปเดตจำนวนทรัพยากร (availableQuantity) และระบบได้คำนวณ resourceStatus ใหม่เรียบร้อยแล้ว

### **Request** 

### **Message Headers**

* messageId (string)  
* timestamp (ISO 8601\)  
* eventType \= ResourceAvailabilityUpdatedEvent  
* version \= v1

  **Message Body**

  {

    "hospitalId": "H001",

    "resourceType": "ICU\_BED",

    "totalCapacity": 20,

    "availableQuantity": 1,

    "resourceStatus": "CRITICAL",

    "lastUpdatedTime": "2026-02-27T15:10:00Z"

  }


  


  


  

  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| hospitalId | string | Y | รหัสโรงพยาบาล |
| resourceType | enum | Y | ประเภททรัพยากร |
| totalCapacity | integer | Y | จำนวนทรัพยากรทั้งหมด |
| availableQuantity | integer | Y | จำนวนที่พร้อมใช้งาน |
| resourceStatus | enum | Y | สถานะหลังคำนวณ |
| lastUpdatedTime | datetime | Y | เวลาที่อัปเดตล่าสุด |

**Validation Rules**

1. hospitalId ต้องไม่ว่าง  
2. resourceType ต้องอยู่ใน enum  
3. availableQuantity ≥ 0  
4. resourceStatus ต้องสอดคล้องกับ threshold  
5. totalCapacity \> 0  
6. availableQuantity ≤ totalCapacity

**Response**

	ไม่มี Business Response เนื่องจากเป็น Event-Driven แบบ Publish/Subscribe  
Producer ไม่รอผลจาก Consumer

## **Message Contract \#2:  ResourceStatusAlertEvent**

### **ข้อมูลทั่วไป** 

* **Message Name:**  ResourceStatusAlertEvent  
* **Interaction Style:** Asynchronous (Event-Driven)  
* **Producer:** HospitalResourceMonitoring Service  
* **Consumer:** EmergencyCoordination Service, Notification Service  
* **Channel/Queue:** hospital.resource.status.alert  
* **Version:** v1

### **คำอธิบาย**

### Message นี้ถูก publish เมื่อสถานะทรัพยากร เปลี่ยนเป็น WARNING หรือ CRITICAL เพื่อแจ้งเตือนระบบอื่นให้ดำเนินการทันที

### **Request** 

### **Message Headers**

* messageId (string)  
* timestamp  
* eventType \= ResourceStatusAlertEvent  
* version \= v1

  **Message Body**

  {

    "hospitalId": "H001",

    "resourceType": "ICU\_BED",

    "totalCapacity": 20,

    "availableQuantity": 3,

    "resourceStatus": "WARNING",

    "lastUpdatedTime": "2026-02-27T15:30:00Z"

  }




  **Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| hospitalId | string | Y | รหัสโรงพยาบาล |
| resourceType | enum | Y | ประเภททรัพยากร |
| totalCapacity | integer | Y | จำนวนทรัพยากรทั้งหมด |
| availableQuantity | integer | Y | จำนวนที่พร้อมใช้งาน |
| resourceStatus | enum | Y | สถานะใหม่ (WARNING หรือ CRITICAL) |
| lastUpdatedTime | datetime | Y | เวลาที่เปลี่ยนสถานะ |

**Validation Rules**

1. hospitalId ต้องไม่ว่าง  
2. resourceType ต้องอยู่ใน enum  
3. totalCapacity \> 0  
4. availableQuantity ≥ 0  
5. availableQuantity ≤ totalCapacity  
6. resourceStatus ต้องเป็น WARNING หรือ CRITICAL เท่านั้น  
7. resourceStatus ต้องมีค่าเปลี่ยนจากสถานะก่อนหน้า

   

**Response**

	ไม่มี Business Response เนื่องจากเป็น Event-Driven แบบ Publish/Subscribe  
Producer ไม่รอผลจาก Consumer

# Service Data

# **Service Data**

# **1\) HospitalResource Data (Owned by this service)**

# 

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| resourceStatusId | string | Y | (PK) รหัสสถานะทรัพยากร | RS001 |
| hospitalId | string | Y | (Ref) รหัสโรงพยาบาลที่เป็นเจ้าของทรัพยากร  | H001 |
| resourceType | enum | Y | ประเภททรัพยากรที่ระบบรองรับ | ICU\_BED |
| totalCapacity | integer | Y | จำนวนทรัพยากรทั้งหมด | 20 |
| availableQuantity | integer | Y | จำนวนทรัพยากรที่ยังว่างใช้งานได้ | 5 |
| warningThreshold | integer | Y | ค่าขั้นต่ำที่เมื่อ availableQuantity ต่ำกว่าจะเปลี่ยนเป็น WARNING | 6 |
| criticalThreshold | integer | Y | ค่าขั้นต่ำที่เมื่อ availableQuantity ต่ำกว่าจะเปลี่ยนเป็น CRITICAL | 2 |
| resourceStatus | enum | Y | สถานะปัจจุบันของทรัพยากร ( NORMAL, WARNING, CRITICAL) | WARNING |
| lastUpdatedTime  | datetime | Y | วันที่และเวลาที่อัปเดตล่าสุด | 2026-02-27T14:30:00Z |

# 

# 

# **2\) HospitalInformation Data (Owned by this service)**

# 

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| hospitalId | string | Y | (PK) รหัสเฉพาะของโรงพยาบาล | H001 |
| hospitalName | string | Y | ชื่อโรงพยาบาล | Bangkok General Hospital |
| address | string | Y | ที่อยู่ของโรงพยาบาล |  Bangkok, Thailand |
| latitude | float | Y | ค่าพิกัดละติจูดของโรงพยาบาล | 13.7563 |
| longtitude | float | Y | ค่าพิกัดลองจิจูดของโรงพยาบาล | 100.5018 |
| contactNumber | string | Y | เบอร์โทรศัพท์ติดต่อ | 02-123-4567 |

# 

# 

# 