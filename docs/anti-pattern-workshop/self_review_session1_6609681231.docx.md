

| CS366 2/2568 \- MICROSERVICES ANTI-PATTERNS WORKSHOP Session 1 Self-Review Sheet Anti-Patterns \#1 – \#3  ·  Use during review pauses  ·  Session 1 only |
| :---- |

| Your name |  Akawat Moradsatian | Your service |  Report Ingestion & Verification Service |
| :---- | :---- | :---- | :---- |

**How to use this sheet**

For each anti-pattern: read the guess prompt first and think before the explanation. Then check your own service against the self-review question. Write one specific finding — quote the actual section, endpoint, or line where you found it (or confirm it's clean). Tick the boxes honestly.

| Anti-Pattern | Your finding — quote specific evidence or confirm it's clean | Status |
| :---- | :---- | :---- |
| **\#1  Distributed Monolith** |  |  |
| **GUESS FIRST** | ระบบ Microservices ที่ผูกติดกันแน่นเกินไป (Tightly Coupled) จนกลายสภาพเป็น Monolith ที่กระจายอยู่บนเครือข่าย หาก Service หนึ่งล่ม Service อื่นที่เรียกใช้ก็จะพังตามไปด้วย |  |
| **SELF-REVIEW** | **Can your service start if everything else is offline? Does it call anything before it's ready to accept traffic? Any shared config files?**   Service ของผมไม่พบปัญหานี้  โดย Service ผมสามารถทำงานรับข้อมูลได้แม้ Service อื่นจะล่มทั้งหมด เพราะเราใช้ SQS เป็น Buffer และมีการทำ Graceful Degradation อย่างชัดเจน Evidence จากหัวข้อ Dependency Mapping 1\. "หาก Incident Tracking Service ไม่ตอบสนอง ระบบจะปิดการใช้งานปุ่ม 'Link to Existing Incident' ชั่วคราว... บังคับให้เจ้าหน้าที่เลือก 'Create New Incident' หรือบันทึกสถานะเป็น VERIFIED ไว้ก่อน" รับมือ Downstream ล่ม 2\. "Fallback to Neutral: หาก API (Google Gemini) ไม่ตอบสนอง หรือติด Rate Limit ระบบจะตั้งค่า Trust Score เป็น 50 (Unknown)" รับมือ External AI ล่ม     | **Detected?** ☐  Yes ✅  No ☐  Unsure **Fixed?** ✅  Yes ☐  Partial ☐  Not yet |
| **KEY IDEA** | Your service should survive the complete absence of every other service. |  |
|   |  |  |
| **\#2  Shared Database** |  |  |
| **GUESS FIRST** | การที่ Microservices มากกว่า 1 ตัว เข้ามาอ่าน/เขียน Database หรือ Table เดียวกันโดยตรง ทำให้ละเมิดหลักการ Data Ownership และเมื่อแก้ไข Schema จะพังกันทั้งระบบ |  |
| **SELF-REVIEW** | **Is your database yours alone? Do you connect to anything you don't own? Does anything in your contract hint at reaching into someone else's data?** Service ของผมไม่พบปัญหานี้  Service ของผมมี Database เป็นของตัวเอง (DynamoDB ตาราง Reports และ Report\_Audit\_Logs) และไม่ก้าวก่าย Database ของคนอื่น การอ้างอิงข้อมูลข้าม Service ทำผ่าน ID เท่านั้น Evidence จากหัวข้อ 8\. Linked Data และ Service Data "linked\_incident\_id: (Foreign Key \- Reference Only) เก็บเพียง ID เพื่อเชื่อมโยงว่า Report นี้ถูกนำไปสร้างเป็น Incident หมายเลขอะไร... เราอ่านได้ แต่ห้ามไปแก้ข้อมูลใน Incident Service"   | **Detected?** ☐  Yes ✅  No ☐  Unsure **Fixed?** ✅  Yes ☐  Partial ☐  Not yet |
| **KEY IDEA** | One service, one database. Everyone else goes through the API. |  |
|   |  |  |
| **\#3  Chatty Services** |  |  |
| **GUESS FIRST** | การที่ Client หรือ Service ต้องยิง Request หลายๆ ครั้ง (Multiple Hops) เพื่อดึงข้อมูลประกอบกันจนครบ หรือเพื่อทำงานหนึ่งอย่างให้เสร็จ ทำให้เกิด Latency สูงและเปลือง Network |  |
| **SELF-REVIEW** | **Does your list response have everything a caller would need? Pick one journey through your service — how many hops? Any endpoints that just return IDs?** Service ของผมไม่พบปัญหานี้  การสื่อสารกับ Service ปลายทางใช้ Event-Driven (ส่งก้อนข้อมูลไปเลยทีเดียว ไม่ต้องให้เขามายิงถาม) และ API ขา GET ของเราก็แนบข้อมูลที่จำเป็นมาครบจบใน Call เดียว Evidence จากหัวข้อ Technical Rationale และ API Contract 1\. "การใช้ Asynchronous Event (ReportVerified) ส่งออกไปให้หลายๆ Service... พร้อมกัน เรียกว่ารูปแบบ Fan-out Pattern... Service นี้ไม่ต้องรู้ Logic ของเพื่อน หน้าที่จบแค่บอกว่าข่าวนี้จริง" หลีกเลี่ยง Chatty Sync Calls 2\. ใน Endpoint GET /reports/{report\_id} ได้ออกแบบให้ Return reporter\_info, content, และ analysis (trust\_score) มาครบในก้อนเดียว หน้าเว็บไม่ต้องยิงไปถาม AI Service หรือ User Service เพิ่มเติม   | **Detected?** ☐  Yes ✅  No ☐  Unsure **Fixed?** ✅  Yes ☐  Partial ☐  Not yet |
| **KEY IDEA** | If your caller needs multiple calls to get what they need, your response isn't giving enough. |  |
|   |  |  |

**Overall reflection**

| Which anti-pattern was hardest to evaluate in your service, and why?  Distributed Monolith เป็นเรื่องที่ประเมินยากและท้าทายที่สุดครับ เพราะในความเป็นจริง Service ของเรา "จำเป็น" ต้องเช็คข้อมูลกับ Incident Service (เพื่อดึงรายการ Incident ที่มีอยู่มาให้เจ้าหน้าที่กด Link) ในตอนแรกอาจดูเหมือนระบบเราผูกติด (Coupled) กับเขา แต่เราแก้ปัญหานี้ด้วยการออกแบบ Graceful Degradation ใน Dependency Mapping คืออนุญาตให้ฟีเจอร์บางส่วน (การ Link) ใช้งานไม่ได้ชั่วคราว แต่ Core Business (การรับ Report เข้า SQS และการ Verify เป็นเคสใหม่) ต้องทำงานต่อไปได้เสมอ   |
| :---- |
| **What one thing will you fix or document before Session 2?** ผมคิดว่าทบทวนและตรวจสอบ Asynchronous Event Payload (ReportVerified) ให้ละเอียดที่สุด เพื่อให้มั่นใจว่าข้อมูลที่เราแนบส่งไปหา Downstream Services (Incident, Rescue, PropertyDamage) มีฟิลด์ข้อมูลที่ครบถ้วน (Rich Payload) มากพอที่พวกเขาจะนำไปทำงานต่อได้ทันที โดยที่พวกเขาไม่ต้องย้อนกลับมาเรียก (Sync Call) GET /reports/{id} ที่ Service ของเราอีก ซึ่งจะช่วยป้องกันไม่ให้เกิดปัญหา Chatty Services ในภายหลังได้อย่างเด็ดขาด   |

| 📋  Before Session 2 Transfer your findings to the Remediation Log (one row per anti-pattern). If you detected a violation and couldn't fix it, write the proposed resolution. Bring the log to Session 2\. |
| :---- |

