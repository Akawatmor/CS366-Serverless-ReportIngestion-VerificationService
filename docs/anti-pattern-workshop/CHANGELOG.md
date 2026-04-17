# Workshop Files - Changelog

## 2026-04-07 - แก้ไข Consumer Review Sheet

### Changes Made
- ✅ แก้ไข `consumer_review_sheet.docx.md` ทั้งหมดให้ถูกต้อง
- เปลี่ยนจากการ review service ของตัวเอง → review MonitorDisaster Service ของเพื่อน

### Background
Consumer Review Sheet คือการ review **service ของเพื่อนที่เราเป็น consumer**:
- **My Service:** Report Ingestion & Verification Service (Akawat 6609681231)
- **Service I'm Reviewing:** MonitorDisaster Service (Tanat Kerdtip 6609611980)
- **Relationship:** MonitorDisaster calls me (POST /v1/reports) เพื่อส่งข้อมูล IoT sensors

### Key Findings from MonitorDisaster Service Review

#### ✅ Strengths
1. Error responses มี structured format พร้อม traceId
2. มี Idempotency checks (timestamp validation)
3. มี is_outdated flag สำหรับ data staleness
4. มี Manual Override capability

#### ⚠️ Gaps Found
1. 🔴 **External API timeout ไม่ระบุ** (CRITICAL)
   - Proposal บอกว่า "รับข้อมูลจาก API ภายนอก" แต่ไม่ระบุ timeout config
   - ถ้า external API hang → Lambda hang → disaster warning fail
   
2. 🟡 **ไม่มี versioning policy**
   - API paths ไม่มี /v1/ prefix
   - Async events ไม่มี schemaVersion ใน message body
   - ไม่มีเอกสาร breaking change definition
   
3. 🟡 **ไม่มี change notification mechanism**
   - Consumer จะรู้เมื่อ production fail เท่านั้น

### Updated Files
- `consumer_review_sheet.docx.md` - แก้ไขทั้งหมด (lines 19-28)
- `README_SUMMARY.md` - อัปเดตคำอธิบาย section 3

### References
- MonitorDisaster Service Proposal: `docs/friends_service/MonitorDisaster Service_Proposal_6609611980.md`
- Timeout specs: lines 168, 225, 299
- Version metadata: line 314
- API paths: lines 100-106

---

**Updated by:** Copilot  
**Date:** 2026-04-07
