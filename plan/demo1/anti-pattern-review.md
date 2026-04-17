from # Anti-Pattern Review Sheet
## Report Ingestion & Verification Service

> **Service**: Report Ingestion & Verification Service  
> **Reviewer**: (Your Name)  
> **Review Date**: TBD  
> **Session**: Demo 1 Preparation

---

## How to use this sheet

For each anti-pattern: 
1. **Read the "GUESS FIRST" prompt** and think about whether your service might have this issue before reading the explanation
2. **Check your service** against the self-review questions
3. **Write one specific finding** — quote the actual section, endpoint, or line where you found it (or confirm it's clean)
4. **Tick the boxes honestly** — this is for your learning, not grading

---

## Anti-Pattern #1: Distributed Monolith

### GUESS FIRST
Before reading the self-review questions below, ask yourself:
- If all other services go down, can mine still start and serve requests?
- Does my service need to "phone home" to work?

---

### SELF-REVIEW
**Questions to ask:**
1. Can your service start if everything else is offline?
2. Does it call anything before it's ready to accept traffic?
3. Any shared config files that multiple services read from?

**What to check:**
- Lambda initialization code (before handler runs)
- Any synchronous calls to other services during startup
- Shared DynamoDB tables, S3 buckets, or config stores
- Hard dependencies in environment variables

---

### Your Finding

**Quote specific evidence or confirm it's clean:**

```
Example findings:
- "CLEAN: Service can start with only DynamoDB and SQS (owned resources). 
  Gemini AI call happens async in worker, not during startup."
  
OR

- "VIOLATION: src/handlers/submit_report.py:45 - makes sync call to 
  Incident Service GET /incidents/validate before accepting report"
```

_(Write your finding here)_

---

### Status

**Detected?**
- ☐ Yes
- ☐ No
- ☐ Unsure

**Fixed?**
- ☐ Yes
- ☐ Partial
- ☐ Not yet
- ☐ N/A (not detected)

---

### KEY IDEA
✨ **Your service should survive the complete absence of every other service.**

A true microservice owns its own data and doesn't need synchronous calls to other services to start or handle basic requests. External dependencies should be async (queues/events) or gracefully degradable.

---

## Anti-Pattern #2: Shared Database

### GUESS FIRST
Before reading the self-review questions below, ask yourself:
- Who owns each database table I use?
- Am I reading or writing to tables that another service "owns"?

---

### SELF-REVIEW
**Questions to ask:**
1. Is your database yours alone?
2. Do you connect to anything you don't own?
3. Does anything in your contract hint at reaching into someone else's data?

**What to check:**
- DynamoDB table names — do they belong to your service?
- Any direct queries to tables owned by Incident Service, User Service, etc.?
- Connection strings or table ARNs in environment variables
- Comments that mention "shared table" or "joint ownership"

---

### Your Finding

**Quote specific evidence or confirm it's clean:**

```
Example findings:
- "CLEAN: terraform/dynamodb.tf defines 2 tables (Reports, ReportStats) 
  with prefix 'report-verify-*'. No references to external tables."
  
OR

- "VIOLATION: src/repositories/report_repo.py:89 - queries table 
  'incident-tracking-incidents' directly instead of calling Incident API"
```

_(Write your finding here)_

---

### Status

**Detected?**
- ☐ Yes
- ☐ No
- ☐ Unsure

**Fixed?**
- ☐ Yes
- ☐ Partial
- ☐ Not yet
- ☐ N/A (not detected)

---

### KEY IDEA
✨ **One service, one database. Everyone else goes through the API.**

Each service owns its database exclusively. If you need data from another service, call their API or subscribe to their events. Never query their tables directly — you break encapsulation and coupling.

---

## Anti-Pattern #3: Chatty Services

### GUESS FIRST
Before reading the self-review questions below, ask yourself:
- If a client wants to display a list of reports, how many API calls do they need?
- Do my responses contain just IDs, forcing callers to make another round-trip?

---

### SELF-REVIEW
**Questions to ask:**
1. Does your list response have everything a caller would need?
2. Pick one journey through your service — how many hops?
3. Any endpoints that just return IDs (making the caller fetch details separately)?

**What to check:**
- GET /reports response — does it include location, category, trust_score inline?
- Any response that returns `{"user_id": "123"}` without user details?
- Check frontend/dashboard code — does it loop over IDs calling GET /reports/{id}?
- Count API calls needed for common workflows (e.g., "show unverified reports")

---

### Your Finding

**Quote specific evidence or confirm it's clean:**

```
Example findings:
- "CLEAN: GET /reports returns full report objects with embedded location, 
  category, ai_analysis. Caller needs only 1 call to render list view."
  
OR

- "VIOLATION: Contract #2 GET /reports returns array of IDs only. 
  Dashboard makes N+1 calls (1 for list + N for details). See frontend/app.js:145"
```

_(Write your finding here)_

---

### Status

**Detected?**
- ☐ Yes
- ☐ No
- ☐ Unsure

**Fixed?**
- ☐ Yes
- ☐ Partial
- ☐ Not yet
- ☐ N/A (not detected)

---

### KEY IDEA
✨ **If your caller needs multiple calls to get what they need, your response isn't giving enough.**

Design responses for the caller's use case, not your database schema. Include related data inline (embed it) or provide bulk endpoints. Avoid responses that force N+1 queries or multi-hop journeys.

---

## Overall Reflection

### Which anti-pattern was hardest to evaluate in your service, and why?

```
Example:
"Shared Database was hardest because our EventBridge events contain data 
that might feel like 'sharing' — but after thinking, it's actually just 
publishing our own data for others to consume, which is correct."
```

_(Write your reflection here)_

---

### What one thing will you fix or document before Session 2?

```
Example:
"Add pagination to GET /reports endpoint to avoid returning all 10,000 
reports in one response (performance issue, not exactly 'chatty' but related)"
```

_(Write your commitment here)_

---

## 📋 Before Session 2

**Action Items:**
1. ✅ Transfer your findings to the **Remediation Log** (one row per anti-pattern)
2. ✅ If you detected a violation and couldn't fix it, write the **proposed resolution**
3. ✅ Bring the log to Session 2 for discussion
4. ✅ Be ready to explain your "one thing to fix" and show progress

**Remediation Log Template:**
| Anti-Pattern | Detected? | Location | Proposed Fix | Status |
|--------------|-----------|----------|--------------|---------|
| Distributed Monolith | Yes/No | (file:line) | (description) | Pending/Done |
| Shared Database | Yes/No | (file:line) | (description) | Pending/Done |
| Chatty Services | Yes/No | (file:line) | (description) | Pending/Done |

---

## 📚 Quick Reference: Your Service

**Service Name**: Report Ingestion & Verification Service  
**Key Endpoints**:
- POST /reports (async via SQS)
- PATCH /reports/{id} (verify/reject)
- GET /reports (list with filters)
- GET /reports/{id} (details)
- GET /stats (dashboard metrics)
- GET /health (deep health check)

**External Dependencies**:
- Google Gemini AI (async, called by worker)
- EventBridge (publishes ReportVerifiedEvent)
- Consumer: Incident Tracking Service (receives events)

**Owned Resources**:
- DynamoDB: Reports table, ReportStats table
- SQS: SubmitReportQueue
- S3: Media attachments

**Tech Stack**: AWS Lambda (Python 3.12), API Gateway, DynamoDB, SQS, EventBridge, Terraform

---

## Tips for Your Review

1. **Be specific**: Don't just say "found chatty pattern" — quote the endpoint or line number
2. **Context matters**: EventBridge events are NOT shared database (they're messages)
3. **Think about startup**: If DynamoDB is down, can your Lambda still initialize? (Yes, boto3 is lazy)
4. **Check both sync and async paths**: Submit flow is async (clean), but verify might call other services (check it!)
5. **Look at frontend code**: Dashboard calls reveal chattiness better than backend code

---

**Good luck with your review! Be honest — finding anti-patterns is how we learn.** 🚀
