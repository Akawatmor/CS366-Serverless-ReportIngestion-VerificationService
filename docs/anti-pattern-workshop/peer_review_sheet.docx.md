

| MICROSERVICES ANTI-PATTERNS WORKSHOP Peer Review Assignment Sheet Sessions 2 & 3  ·  Use one sheet per service you review |
| :---- |

| Your name |  Akawat Moradsatian 1231 | Your service | Report Ingestion & Verification Service |
| :---- | :---- | :---- | :---- |
| **Service you are reviewing** |  Trace missing Service | **Owner of that service** |  Pattayawat Poolsawat 2111 |

**How to use this sheet**

For each anti-pattern: (1) apply it to your own service first, (2) then apply it to your assigned peer's service. Write one specific finding for each — quote the exact section, endpoint, or line where you found it. If you find no violation, write what evidence confirms it's clean.

**SESSION 2**  Anti-Patterns \#4 – \#7  ·  Self-Review \+ Random Peer Review

| \# | Anti-Pattern | Self-Review — your service | Peer Review — their service |
| ----- | :---- | :---- | :---- |
| **\#4** | **Over-Microservices** | Can you describe your service in one sentence without naming another service? **Finding:**   บริการนี้มีขอบเขตที่ชัดเจน ทำหน้าที่แค่ Ingestion & Verification ไม่ก้าวก่ายการจัดการทรัพยากร หรือการบริหารสถานการณ์ อ้างอิงจากหัวข้อ Out-of-scope ใน Proposal ระบุชัดเจนว่าไม่รับผิดชอบการสร้าง Official Incident ทำแค่ส่งคำขอ ไม่รับผิดชอบการสั่งการทีมกู้ภัย และไม่บริหารจัดการทรัพยากร | Does this service have genuine standalone value, or does it only make sense alongside another? **Finding:**   ใช่ service trace missing มีคุณค่าพอที่จะสร้างเป็น service แยก เนื่องจากจัดการแค่เกี่ยวกับคนหายอย่างเดียว |
| **\#5** | **God Service** | Does your out-of-scope section exist and is it specific? Can you describe the service without using 'and' more than once? **Finding:**  1.มีอยู่จริงและระบุไว้เจาะจงมาก หลักฐานจากเอกสาร Proposal ในหัวข้อ Out-of-scope มีการขีดเส้นแบ่งความรับผิดชอบตัดกับ Service อื่นๆ อย่างชัดเจน ได้แก่ ไม่รับผิดชอบการทำ Active Web Scraping" ระบุชัดเจนว่าไม่เขียน Bot ไปดูดข้อมูลเอง แต่จะรอรับผ่าน API ไม่รับผิดชอบการสร้าง Official Incident" ระบุชัดเจนว่าเป็นหน้าที่ของ Incident Service เราทำแค่ส่ง Event ไปบอก      ไม่รับผิดชอบการสั่งการทีมกู้ภัย หรือจัดการทรัพยากร ตัดขาดจาก Rescue/Emergency Resource Service 2\. Can you describe the service without using 'and' more than once? ทำได้ครับ บริการนี้ทำหน้าที่คัดกรองรายงานภัยพิบัติดิบจากแหลงภายนอก และส่งต่อเฉพาะข้อมูลที่ได้รับการยืนยันแล้วไปให้ระบบอื่นใช้งานต่อ และ 1 ตัว | Does every endpoint in their contract relate to their stated service purpose? **Finding:**   ไม่ใช่ God Service แน่นอนเนื่องจากมี endpoint ตรงตาม proposal ชัดเจน เป็น CRUD operation ชัดเจน |
| **\#6** | **Tight Coupling** | What happens to your service if every synchronous dependency goes down? Is a fallback defined for each? **Finding:**   ระบบของเรามี Synchronous Dependency ภายนอกอยู่ 1 ตัว และได้กำหนด Fallback ไว้ชัดเจนในหัวข้อ Dependency Mapping คือ Google Gemini API (AI Service ล่ม) ระบบจะไม่ล่มและไม่หยุดรับข้อมูล แต่จะตั้งค่า Trust Score อัตโนมัติให้เป็น 50 (Unknown) และติดป้ายกำกับ "AI Analysis Failed" เพื่อส่งรายงานนั้นเข้าสู่คิว Manual Review ให้มนุษย์ตรวจสอบ 100% | Is a circuit breaker or fallback defined for every synchronous outbound call in their contract? **Finding:**  มีการทำระบบไว้เบื้องต้น แต่ยังไม่ชัดเจนว่าหากเกิดไม่มี incident ให้เรียกใช้ เมื่อไม่ได้เก็บไว้จะทำอย่างไร (ในตินนี้ยัง 404 ให้ผู้ใช้ตีกันเอง) |
| **\#7** | **Lack of Observability** | Is X-Trace-Id in every response header? Are error responses structured with traceId and message? **Finding:**  Currently updating the API Contract to include X-Trace-Id in all response headers and standardizing the error payload structure to {"traceId": "...", "message": "...", "error\_code": "..."} for better observability across microservices. | Find one response in their contract that is missing traceId or has an unstructured error format. **Finding:**   ยังไม่มีในตอนนี้ในทุก request { Error: “404”, “Message”: “Bad Request" } |

**SESSION 3**  Anti-Patterns \#8 – \#9  ·  Self-Review Only (Consumer Review is separate)

| \# | Anti-Pattern | Self-Review — your service | Note |
| ----- | :---- | :---- | :---- |
| **\#8** | **Timeout** | List every outbound call. Does each have an explicit timeout? What is the fallback when it times out? **Finding:**   Yes มี timeout กำหนดไว้: Lambda API Handler=30s, Worker=60s, Gemini API มี config GEMINI\_TIMEOUT=15s ใน src/config.py แต่ **ตรวจสอบ src/services/gemini\_service.py line 165 พบว่า timeout ไม่ได้ถูก enforce จริง** ใน client.generate\_content() call จึงอาจเกิดการ hang ได้ Fallback: หาก Gemini fail จะตั้ง trust\_score=50 และ flag ai\_analysis\_failed=true (line 293-302) | N/A for this session **Finding:**   Timeout 30 Seconds (API Gateway default) แต่ Gemini timeout ยังไม่ enforce ควรแก้ไขให้มี explicit timeout parameter ใน API call |
| **\#9** | **Static Contract** | Do all endpoints use /v1/? Do async events have schemaVersion? Is there a written policy for breaking changes? **Finding:**   Yes ใช้ /v1/ ครบทุก endpoint (terraform/api\_gateway.tf) แต่ EventBridge events **ยังไม่มี schemaVersion field** ใน event payload (ตรวจสอบ src/services/event\_publisher.py lines 52-64) และ **ยังไม่มี written versioning policy** ที่อธิบาย breaking changes, deprecation process หรือ upgrade path | N/A for this session **Finding:**  มี /v1/ แล้ว แต่ versioning policy และ event schemaVersion ยังไม่มี (Not Exist yet\!) ควรสร้าง docs/VERSIONING\_POLICY.md และเพิ่ม schemaVersion ใน events |

**Overall Assessment**

| Most significant gap you found in the reviewed service (quote evidence): **Anti-Pattern #7 (Observability)** - Service ที่ peer review (Trace Missing Service) ยังไม่มี X-Trace-Id header ใน response และ error format ไม่เป็น standard (ไม่มี traceId, errorCode) ทำให้เวลา debug ใน production ลำบาก ตัวอย่าง error response ที่พบ: {"Error": "404", "Message": "Bad Request"} ควรเป็น {"traceId": "...", "errorCode": "E404", "message": "Not Found", "timestamp": "..."} เพื่อให้ correlate logs ได้ง่าย     |
| :---- |
| **One thing this service does well (quote evidence):** Service มี clear scope และ out-of-scope boundaries ชัดเจน (Anti-Pattern #4, #5 ผ่าน) มี CRUD operations ที่ตรงตาม proposal ไม่ก้าวก่าย responsibilities ของ service อื่น และมี endpoint ที่ออกแบบดี ไม่เป็น God Service ทำให้ง่ายต่อการ integrate    |
| **If you consume this service — is it safe to depend on? What would you need from the owner before integrating?** ปลอดภัยพอที่จะ integrate ได้ แต่ต้องการให้เจ้าของแก้ไขก่อน: (1) เพิ่ม X-Trace-Id header ในทุก response (2) Standardize error response format ให้มี traceId และ errorCode (3) Document versioning policy และ breaking change notification mechanism (4) เพิ่ม timeout specification ใน API contract ให้ชัดเจน (5) เพิ่ม schemaVersion ใน async events ถ้ามี (6) ให้ test/staging endpoint สำหรับ integration testing    |

