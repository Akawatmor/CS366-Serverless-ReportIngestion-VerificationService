# API & Event Versioning Policy

**Service:** Report Ingestion & Verification Service  
**Owner:** Akawat Moradsatian (6609681231)  
**Last Updated:** 2026-04-08

---

## 📋 Overview

This document defines how we handle versioning for:
1. **REST API endpoints** (`/v1/reports`, etc.)
2. **EventBridge events** (ReportVerifiedEvent, ReportStatusChangedEvent)

---

## 🔴 Breaking Changes Definition

A change is considered **BREAKING** if it:

| Change Type | Example | Breaking? |
|------------|---------|-----------|
| Remove a field from response | `trust_score` field removed | ✅ Yes |
| Rename a field | `report_id` → `reportId` | ✅ Yes |
| Change data type | `trust_score: string` → `trust_score: int` | ✅ Yes |
| Remove enum value | Remove `VERIFIED` status | ✅ Yes |
| Make optional field required | `reviewer_notes` now required | ✅ Yes |
| Change error response structure | Different error JSON format | ✅ Yes |
| Remove or rename endpoint | DELETE `/v1/reports/{id}` | ✅ Yes |

---

## 🟢 Non-Breaking Changes

These changes are **SAFE** and won't break existing consumers:

| Change Type | Example | Breaking? |
|------------|---------|-----------|
| Add new optional field to response | Add `ai_confidence` field | ❌ No |
| Add new enum value | Add `UNDER_INVESTIGATION` status | ❌ No |
| Add new endpoint | Add `GET /v1/reports/trending` | ❌ No |
| Add new optional query parameter | Add `?include_deleted=true` | ❌ No |
| Improve error messages | Better error descriptions | ❌ No |
| Add new event type | Add `ReportEscalatedEvent` | ❌ No |

---

## 📅 Deprecation Process

### Timeline

| Phase | Duration | Actions |
|-------|----------|---------|
| **Announcement** | Day 0 | Add `X-Deprecated-Version: true` header |
| **Grace Period** | 30 days | Both versions available |
| **Sunset** | Day 30+ | Old version returns HTTP 410 Gone |

### Step-by-Step Process

#### 1. Announcement (Day 0)

```http
HTTP/1.1 200 OK
X-Deprecated-Version: true
X-Sunset-Date: 2026-06-01
X-Next-Version-Url: https://api.example.com/v2/reports

{
  "data": [...],
  "deprecation_notice": "This API version will be sunset on 2026-06-01. Please migrate to /v2/"
}
```

**Actions:**
- Add deprecation headers to all responses
- Update API documentation with deprecation notice
- Notify all known consumers via:
  - Slack: #disaster-platform-announcements
  - Email: consumer distribution list

#### 2. Grace Period (Day 1-30)

- Keep old version running alongside new version
- Monitor usage metrics to identify slow adopters
- Provide migration support and documentation
- Log warnings for deprecated endpoint usage

#### 3. Sunset (Day 30+)

```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "error": true,
  "errorCode": "E410",
  "message": "This API version has been sunset",
  "detail": "Please migrate to /v2/reports",
  "migration_guide": "https://docs.example.com/migration/v1-to-v2"
}
```

---

## 🔢 Versioning Strategy

### REST API Endpoints

| Current | Pattern | Example |
|---------|---------|---------|
| v1 (Current) | `/v1/reports` | `POST /v1/reports` |
| v2 (Future) | `/v2/reports` | `POST /v2/reports` |

**Rules:**
- Increment major version only for breaking changes
- Keep at least 2 versions active during transition period
- Minor/patch versions handled via response fields, not URL

### EventBridge Events

All events MUST include `schemaVersion` field:

```json
{
  "schemaVersion": "1.0",
  "report_ref_id": "r-abc123",
  "suggested_incident_data": {...}
}
```

**Version Format:** `{major}.{minor}`
- Major: Breaking changes (field removed/renamed)
- Minor: Non-breaking additions

**Consumer Responsibility:**
- Check `schemaVersion` before processing
- Handle unknown versions gracefully (log & skip or use defaults)

---

## 📊 Schema Version History

### ReportVerifiedEvent

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-08 | Initial version with schemaVersion field |

### ReportStatusChangedEvent

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-08 | Initial version with schemaVersion field |

---

## 📣 Consumer Notification Channels

### How Consumers Will Be Notified

| Channel | Timing | Content |
|---------|--------|---------|
| **Slack** | Immediate | Breaking changes, sunset dates |
| **Email** | 30 days before | Migration guide, timeline |
| **API Headers** | Runtime | `X-Deprecated-Version`, `X-Sunset-Date` |
| **Changelog** | Continuous | All changes documented |

### Subscribe to Updates

1. **Slack Channel:** Join `#disaster-platform-announcements`
2. **Email List:** Contact service owner for subscription
3. **GitHub Releases:** Watch this repository for releases
4. **Changelog:** Check `docs/anti-pattern-workshop/CHANGELOG.md`

---

## 🧪 Testing New Versions

### Staging Environment

Before production deployment, all changes are available in staging:

```
Staging API: (Contact service owner for URL)
```

**Testing Checklist:**
- [ ] All existing integrations work without changes
- [ ] New features work as documented
- [ ] Error responses follow the contract
- [ ] Events include schemaVersion

---

## 📞 Contact & Support

**Service Owner:**
- Name: Akawat Moradsatian
- Student ID: 6609681231
- Email: akawar.mor@dome.tu.ac.th

**For Versioning Questions:**
- Slack: #report-verify-service
- GitHub Issues: Create issue with `versioning` label

---

## 📚 References

- [API Contract Documentation](../implement/implementation-plan.md)
- [EventBridge Schema](../others/reportingestion_proposal.txt)
- [Anti-Pattern Workshop Summary](./WORKSHOP_FIXES_NEEDED.md)
