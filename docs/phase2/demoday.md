# Demoday Mapping: Service ผมทำตรงไหนบ้างใน Flood Evacuation Simulator

เอกสารนี้สรุปจากการเช็ค simulator ที่ลิงก์ `https://v0-flood-evacuation-routes-rho.vercel.app/` เทียบกับ implementation จริงของ repo นี้ ซึ่งเป็น **Report Ingestion & Verification Service** ไม่ใช่ route engine หรือ shelter management service โดยตรง

## สรุปสั้นที่สุด

service นี้รับผิดชอบ 4 ขั้นหลักใน simulator:

1. **รับรายงาน/สัญญาณเหตุการณ์เข้า system** ผ่าน `POST /reports`
2. **วิเคราะห์และคัดกรองรายงาน** ด้วย AI + trust score + dedup
3. **ให้เจ้าหน้าที่ verify/reject/merge** ผ่าน `PATCH /reports/{report_id}`
4. **publish verified event ออกไปให้ service downstream ใช้ต่อ** เช่น Incident Tracking, Notification, SafeRoute

ดังนั้นใน simulator นี้ service ของผมจะอยู่ในบทบาท **verified-intake layer** สำหรับข้อมูลภาคสนาม เช่น น้ำเพิ่ม, ถนนปิด, ขอความช่วยเหลือ, หรือประกาศจากหน่วยงาน ก่อนที่ระบบ route / shelter / dispatch จะนำข้อมูลนั้นไปใช้งานต่อ

## สิ่งที่เช็คเจอจาก simulator

จากหน้า simulator พบองค์ประกอบหลักดังนี้:

1. มีเหตุการณ์จำลองแบบ `ขอความช่วยเหลือ`
2. มี action `แจ้งถนนถูกปิดกั้น`
3. มี action `เพิ่มระดับน้ำ +0.5m`
4. มี log เช่น `เตือนภัย: ระดับน้ำสูงกว่าปกติ` และ `พื้นที่เสี่ยง`
5. มี action `ตั้งศูนย์พักพิงทั้งหมด` และเปิดศูนย์พักพิงหลายจุด
6. มีแผนที่, ถนน, ระดับน้ำ, สถานะพื้นที่, และเวลา simulation

## Mapping ว่า service ผมทำตรงไหนบ้าง

| ส่วนใน simulator | service นี้เกี่ยวอย่างไร | สถานะ |
| --- | --- | --- |
| `ขอความช่วยเหลือ` เช่น คนติดอยู่ในบ้าน อพยพเองไม่ได้ | รับเป็น citizen report ได้โดยตรงผ่าน `POST /reports` โดยใช้ `raw_content`, `geo_location`, `media_urls` หรือข้อมูลประกอบอื่น แล้ว worker จะวิเคราะห์ trust score, suggested category, priority ก่อนส่งให้เจ้าหน้าที่ review | **ทำโดยตรง** |
| `แจ้งถนนถูกปิดกั้น` | รับเป็น field report หรือ official update ได้ แล้วให้เจ้าหน้าที่ verify ว่าเป็นข้อมูลจริง จากนั้น publish เป็น verified update เพื่อให้ Incident Tracking / SafeRoute ใช้ต่อ | **ทำโดยตรงในฐานะ verified update** |
| `เพิ่มระดับน้ำ`, `เตือนภัย`, `พื้นที่เสี่ยง` | รับได้ทั้งแบบข้อความจาก `OFFICIAL_APP` และแบบ structured alert จาก `IOT_SENSOR` ผ่าน `sensor_data` จากนั้น AI + rules จะช่วยจัดหมวดเป็น `FLOOD` และคำนวณ trust score ก่อน human verify | **ทำโดยตรง** |
| การ merge ข้อมูลเข้ากับ incident เดิม | รองรับตอน verify ผ่าน `PATCH /reports/{report_id}` โดยใส่ `link_to_incident_id` เพื่อบอกว่านี่เป็น update ของ incident เดิม ไม่ใช่เหตุใหม่ | **ทำโดยตรง** |
| การส่งต่อข้อมูลให้ระบบ route หรือ notification | หลัง verify แล้วจะ publish `ReportVerifiedEvent` และ `ReportStatusChangedEvent` ไป EventBridge เพื่อให้ service ปลายทาง subscribe ไปใช้ต่อ | **ทำโดยตรง** |
| การแสดง list/report detail/stats ให้คนเดโมดู | repo นี้มี `GET /reports`, `GET /reports/{id}`, `GET /reports/stats` สำหรับดูรายการ pending review, รายละเอียด AI analysis, และสถิติภาพรวม | **ทำโดยตรง** |
| การคำนวณเส้นทางอพยพปลอดภัย | ไม่ใช่หน้าที่ของ service นี้ แต่เป็นหน้าที่ของ SafeRoute หรือ simulator logic ฝั่ง route โดย service นี้เป็นเพียงต้นทางของข้อมูล hazard ที่ผ่านการ verify แล้ว | **ไม่ใช่ scope หลัก** |
| การ render แผนที่, road graph, water animation, simulation timeline | เป็นหน้าที่ของตัว simulator/UI ไม่ใช่ repo นี้ | **ไม่ใช่ scope** |
| การเปิดศูนย์พักพิง, จัดการความจุ, ติดตาม occupancy | service นี้อาจรับ "รายงาน/ประกาศ" เรื่อง shelter readiness ได้ แต่ไม่ได้เป็น owner ของ shelter state หรือ capacity management | **ทำได้แค่รับและ verify ข้อมูล ไม่ได้บริหาร shelter เอง** |

## ถ้าไล่ตาม event ใน simulator แบบทีละอัน

### 1. เหตุการณ์ `ขอความช่วยเหลือ`

service ผมทำตรงนี้:

1. รับข้อความแจ้งเหตุจากประชาชนหรือเจ้าหน้าที่
2. วิเคราะห์ความน่าเชื่อถือของข้อความ
3. ตรวจจับ keyword เร่งด่วน เช่น `ช่วยด้วย`, `ติดอยู่`, `น้ำท่วม`
4. ดันเคสเข้า `PENDING_REVIEW` หรือจัด priority ให้สูงขึ้น
5. ให้เจ้าหน้าที่กด `VERIFIED` เพื่อส่งต่อเป็น incident/update

สิ่งที่ service ผม **ไม่ได้ทำเอง**:

1. ไม่ dispatch ทีมช่วยเหลือเอง
2. ไม่คำนวณเส้นทางไปช่วยเหลือเอง
3. ไม่จัด allocation ทรัพยากรภาคสนามเอง

### 2. เหตุการณ์ `แจ้งถนนถูกปิดกั้น`

service ผมทำตรงนี้:

1. รับรายงานสถานการณ์ภาคสนามว่า route ไหนใช้ไม่ได้
2. เก็บข้อความ, พิกัด, รูปภาพหลักฐานได้
3. ให้เจ้าหน้าที่ verify ว่าเป็นข้อมูลจริง
4. merge เข้ากับ incident เดิมได้
5. publish ออกไปเป็น verified hazard/update

ความหมายเชิง integration:

ข้อมูลถนนปิดเป็นตัวอย่างชัดมากว่าระบบของผม **ไม่ใช่ตัว route engine** แต่เป็นตัวทำให้ข้อมูล hazard เชื่อถือได้ก่อนที่ SafeRoute จะใช้ข้อมูลนั้นไปเลี่ยงเส้นทางเสี่ยง

### 3. เหตุการณ์ `เพิ่มระดับน้ำ`, `เตือนภัย`, `พื้นที่เสี่ยง`

service ผมทำตรงนี้:

1. รับ alert จาก `IOT_SENSOR` ได้
2. รับประกาศจาก `OFFICIAL_APP` ได้
3. รองรับ `sensor_data` แบบ structured
4. จัดหมวดเหตุเป็น `FLOOD`
5. ประเมิน trust score จาก source, content, media, geo, reporter history
6. ส่งต่อ verified flood update ให้ downstream ใช้ต่อ

สิ่งที่ service ผม **ไม่ได้ทำเอง**:

1. ไม่จำลองระดับน้ำบนแผนที่
2. ไม่ทำ flood propagation model
3. ไม่คำนวณพื้นที่เสี่ยงบน UI เอง

### 4. เหตุการณ์ `ตั้งศูนย์พักพิงทั้งหมด`

service ผมเกี่ยวข้องได้แค่บางส่วน:

1. ถ้ามีประกาศว่า `วัดริมน้ำเปิดเป็นศูนย์พักพิง` ระบบของผมรับรายงานนี้ได้
2. เจ้าหน้าที่สามารถ verify ประกาศนั้นได้
3. หลัง verify แล้วข้อมูลนี้ส่งต่อไปยัง service owner ด้าน shelter หรือ incident context ได้

แต่ service ผม **ไม่ได้ทำเอง**:

1. ไม่เป็น owner ของศูนย์พักพิง
2. ไม่เก็บ capacity จริงของ shelter
3. ไม่บริหาร occupancy หรือ assignment คนอพยพ
4. ไม่เปิด/ปิด shelter บนแผนที่โดยตรง

## ประโยคที่ควรใช้ตอบบนเวที

ถ้ากรรมการถามว่า "ใน simulator นี้ service ของคุณทำตรงไหน" ให้ตอบประมาณนี้:

> service ของผมเป็นชั้นรับข้อมูลและตรวจสอบความน่าเชื่อถือของเหตุการณ์ครับ/ค่ะ ไม่ว่าจะเป็นคนขอความช่วยเหลือ รายงานถนนปิด หรือสัญญาณระดับน้ำสูง เรารับข้อมูลเข้า วิเคราะห์ด้วย AI + rules ให้เจ้าหน้าที่ verify แล้ว publish เป็น verified event ออกไปให้ระบบปลายทางอย่าง Incident Tracking หรือ SafeRoute ใช้ต่อ

ถ้ากรรมการถามว่า "แล้ว route อพยพกับ shelter เป็นของคุณไหม" ให้ตอบประมาณนี้:

> ไม่ใช่ owner โดยตรงครับ/ค่ะ ตัว route calculation, map simulation, และ shelter management เป็นหน้าที่ของ service หรือ simulator ฝั่งนั้น แต่ service ของผมทำให้ข้อมูล hazard/update ที่ใช้ตัดสินใจมีคุณภาพและผ่านการ verify ก่อน

## Demo flow ที่แนะนำให้โยงกับ simulator

1. กระตุ้น scenario ใน simulator เช่น `ขอความช่วยเหลือ` หรือ `ถนนถูกปิดกั้น`
2. อธิบายว่า event แบบนี้จะถูกส่งเข้า service ผมในรูป report
3. โชว์ว่า report ถูก ingest และเข้า review flow
4. โชว์ AI analysis / trust score / category / priority
5. ให้เจ้าหน้าที่กด verify
6. อธิบายว่าหลังจากนั้น downstream อย่าง Incident Tracking หรือ SafeRoute จะนำ verified data ไปใช้ต่อ

## สรุปสุดท้าย

ถ้าดูจาก simulator นี้แบบตรงไปตรงมา:

1. **ส่วนที่ service ผมทำแน่ ๆ** คือรับรายงาน, วิเคราะห์, verify, merge incident, และ publish verified event
2. **ส่วนที่ service ผมช่วยได้แบบ upstream integration** คือข้อมูลน้ำเพิ่ม, ถนนปิด, ขอความช่วยเหลือ, และประกาศจากหน่วยงาน
3. **ส่วนที่ไม่ใช่ service ผม** คือคำนวณ route, render simulation map, เปิด shelter จริง, และบริหารการอพยพปลายทาง

ดังนั้นคำตอบที่ถูกต้องที่สุดคือ:

> ใน simulator นี้ service ของผมไม่ได้เป็นตัวจำลองการอพยพเอง แต่เป็นตัวทำให้ข้อมูลเหตุการณ์ใน simulation ถูก ingest, analyzed, verified, และพร้อมส่งต่อไปให้ระบบอพยพ/route/shelter ใช้งานต่ออย่างเชื่อถือได้
