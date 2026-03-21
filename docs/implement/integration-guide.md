# Integration Guide — Report Ingestion & Verification Service

> **Version:** 1.0  
> **Last updated:** 2025-01  
> **Service:** CS366 Serverless RequestVerifyService

This guide explains how **other services** can interact with the Report Ingestion & Verification Service — including REST API usage, EventBridge async event subscriptions, and media uploads.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [REST API Endpoints](#rest-api-endpoints)
3. [Authentication](#authentication)
4. [Async Event Contracts (EventBridge)](#async-event-contracts-eventbridge)
5. [Media Upload Flow](#media-upload-flow)
6. [Integration Patterns](#integration-patterns)
7. [Error Handling](#error-handling)

---

## Architecture Overview

```
                 ┌──────────────────────────────────────────────┐
                 │           API Gateway (REST)                 │
                 │   /v1/reports, /v1/health, /v1/reports/*     │
                 └──────┬──────────┬──────────┬────────────────┘
                        │          │          │
                   POST /reports   │      GET/PATCH/DELETE
                        │          │          │
                  ┌─────▼───┐  ┌───▼───┐  ┌──▼──────────┐
                  │ Ingest  │  │Health │  │ API Handler  │
                  │ Handler │  │Handler│  │ (CRUD+Stats) │
                  └────┬────┘  └───────┘  └──────┬───────┘
                       │                         │
                  ┌────▼────┐             ┌──────▼───────┐
                  │   SQS   │             │  DynamoDB    │
                  │  Queue  │             │  (3 tables)  │
                  └────┬────┘             └──────────────┘
                       │
                 ┌─────▼──────┐     ┌─────────────────┐
                 │ Ingestion  │────▶│  EventBridge     │
                 │  Worker    │     │  (Custom Bus)    │
                 └────────────┘     └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  Your Service   │
                                    │  (subscriber)   │
                                    └─────────────────┘
```

---

## REST API Endpoints

Base URL: `https://<api-id>.execute-api.us-east-1.amazonaws.com/dev/v1`

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/reports` | Submit a new disaster report | API Key |
| `GET` | `/reports` | List reports (filterable) | Open |
| `GET` | `/reports/stats` | Dashboard statistics | Open |
| `GET` | `/reports/audit` | View audit trail | Open |
| `GET` | `/reports/events` | View EventBridge events | Open |
| `POST` | `/reports/upload-url` | Get presigned S3 URL for media | API Key |
| `GET` | `/reports/{report_id}` | Report detail | Open |
| `PATCH` | `/reports/{report_id}` | Verify/reject a report | Open |
| `DELETE` | `/reports/{report_id}` | Soft-delete a report | Open |
| `GET` | `/health` | Health check | Open |

### Example: Submit a Report

```bash
curl -X POST "${API_URL}/reports" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${API_KEY}" \
  -d '{
    "title": "Flooding on Highway 7",
    "description": "Water level rising rapidly near km 42",
    "disaster_type": "FLOOD",
    "location": { "latitude": 13.7563, "longitude": 100.5018, "address": "Highway 7, Bangkok" },
    "reporter_id": "user-001",
    "severity": "HIGH",
    "media_urls": ["https://bucket.s3.amazonaws.com/media/photo1.jpg"]
  }'
```

### Example: List Reports with Filters

```bash
# List pending reports
curl "${API_URL}/reports?status=PENDING_REVIEW&limit=10"

# List by disaster type
curl "${API_URL}/reports?disaster_type=FLOOD"
```

---

## Authentication

The service uses **API Gateway API Keys** for write operations.

| Header | Value |
|--------|-------|
| `X-Api-Key` | Your assigned API key |
| `Content-Type` | `application/json` |

GET endpoints are open (no API key needed) to allow dashboard access.

---

## Async Event Contracts (EventBridge)

The service publishes events to a **custom EventBridge bus** whenever a report status changes. This is the primary mechanism for other services to react to verification outcomes.

### Event Bus Details

| Property | Value |
|----------|-------|
| **Bus Name** | `ingestverify-366-dev-disaster-event-bus` |
| **Source** | `service.report-verify` |
| **Region** | `us-east-1` |

### Event Types

#### 1. `ReportVerifiedEvent`

Published when a report is verified (PATCH with `action: "VERIFY"`).

```json
{
  "version": "0",
  "source": "service.report-verify",
  "detail-type": "ReportVerifiedEvent",
  "detail": {
    "report_ref_id": "550e8400-e29b-41d4-a716-446655440000",
    "suggested_incident_data": {
      "category": "FLOOD",
      "trust_score": 85,
      "ai_analysis_tags": ["flooding", "highway", "water-level"],
      "suggested_severity": "HIGH"
    },
    "verified_by": "admin-001",
    "verification_notes": "Confirmed via CCTV footage"
  }
}
```

#### 2. `ReportStatusChangedEvent`

Published on **any** status transition (verify, reject, delete, etc.).

```json
{
  "version": "0",
  "source": "service.report-verify",
  "detail-type": "ReportStatusChangedEvent",
  "detail": {
    "report_id": "550e8400-e29b-41d4-a716-446655440000",
    "old_status": "PENDING_REVIEW",
    "new_status": "VERIFIED",
    "reason": "Verified by field team",
    "changed_by": "admin-001",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

### How to Subscribe

#### Option A: Terraform (recommended)

Add an EventBridge rule in your service's Terraform config that targets the custom bus:

```hcl
# Reference the existing event bus
data "aws_cloudwatch_event_bus" "disaster_bus" {
  name = "ingestverify-366-dev-disaster-event-bus"
}

# Subscribe to ReportVerifiedEvent
resource "aws_cloudwatch_event_rule" "on_report_verified" {
  name           = "my-service-on-verified"
  event_bus_name = data.aws_cloudwatch_event_bus.disaster_bus.name

  event_pattern = jsonencode({
    source      = ["service.report-verify"]
    detail-type = ["ReportVerifiedEvent"]
  })
}

# Route events to your Lambda
resource "aws_cloudwatch_event_target" "my_lambda" {
  rule           = aws_cloudwatch_event_rule.on_report_verified.name
  event_bus_name = data.aws_cloudwatch_event_bus.disaster_bus.name
  arn            = aws_lambda_function.my_handler.arn
}

# Grant EventBridge permission to invoke your Lambda
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.my_handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.on_report_verified.arn
}
```

#### Option B: AWS Console

1. Go to **Amazon EventBridge → Rules**
2. Select the custom event bus: `ingestverify-366-dev-disaster-event-bus`
3. Create a rule with this event pattern:
   ```json
   {
     "source": ["service.report-verify"],
     "detail-type": ["ReportVerifiedEvent"]
   }
   ```
4. Set your target (Lambda, SQS, SNS, HTTP, etc.)

#### Option C: AWS CLI

```bash
aws events put-rule \
  --name "my-service-on-verified" \
  --event-bus-name "ingestverify-366-dev-disaster-event-bus" \
  --event-pattern '{
    "source": ["service.report-verify"],
    "detail-type": ["ReportVerifiedEvent"]
  }'

aws events put-targets \
  --rule "my-service-on-verified" \
  --event-bus-name "ingestverify-366-dev-disaster-event-bus" \
  --targets "Id=MyTarget,Arn=arn:aws:lambda:us-east-1:ACCOUNT:function:my-handler"
```

### Supported Targets

EventBridge rules can route events to:
- **Lambda** — Run your handler function
- **SQS** — Buffer events in a queue
- **SNS** — Fan-out notifications
- **Step Functions** — Orchestrate workflows
- **HTTP (API Destination)** — Webhook to external services

### Viewing Events (Dashboard)

The Dashboard includes an **Events** tab (`GET /reports/events`) that reads events from CloudWatch Logs, allowing real-time visibility into published events.

---

## Media Upload Flow

The service supports **evidence file uploads** (images, video, PDF) via presigned S3 URLs.

### Upload Flow

```
1. Client → POST /reports/upload-url      { filename, content_type, report_id? }
2. Server → 200 OK                        { upload_url, media_url, expires_in }
3. Client → PUT  upload_url (S3)          [file body, Content-Type header]
4. Client → POST /reports                 { ..., media_urls: [media_url] }
```

### Step 1: Get Presigned URL

```bash
curl -X POST "${API_URL}/reports/upload-url" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${API_KEY}" \
  -d '{
    "filename": "evidence_photo.jpg",
    "content_type": "image/jpeg",
    "report_id": "optional-existing-report-id"
  }'
```

Response:
```json
{
  "upload_url": "https://bucket.s3.amazonaws.com/media/temp/abc12345_evidence_photo.jpg?X-Amz-...",
  "media_url": "https://bucket.s3.us-east-1.amazonaws.com/media/temp/abc12345_evidence_photo.jpg",
  "s3_key": "media/temp/abc12345_evidence_photo.jpg",
  "expires_in": 900,
  "method": "PUT",
  "content_type": "image/jpeg"
}
```

### Step 2: Upload File to S3

```bash
curl -X PUT "${UPLOAD_URL}" \
  -H "Content-Type: image/jpeg" \
  --data-binary @evidence_photo.jpg
```

### Step 3: Include in Report

```bash
curl -X POST "${API_URL}/reports" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${API_KEY}" \
  -d '{
    "title": "...",
    "description": "...",
    "media_urls": ["https://bucket.s3.us-east-1.amazonaws.com/media/temp/abc12345_evidence_photo.jpg"]
  }'
```

### Supported File Types

| MIME Type | Extension |
|-----------|-----------|
| `image/jpeg` | .jpg, .jpeg |
| `image/png` | .png |
| `image/gif` | .gif |
| `image/webp` | .webp |
| `video/mp4` | .mp4 |
| `video/quicktime` | .mov |
| `video/x-msvideo` | .avi |
| `application/pdf` | .pdf |

### Storage Details

- **Bucket:** Private S3 bucket (no public access)
- **Lifecycle:** Files auto-expire after **90 days**
- **Access:** Via presigned URLs only (time-limited)

---

## Integration Patterns

### Pattern 1: Notification Service

Subscribe to events for real-time alerts:

```python
# Lambda handler for EventBridge events
def handler(event, context):
    detail_type = event["detail-type"]
    detail = event["detail"]

    if detail_type == "ReportVerifiedEvent":
        send_notification(
            channel="emergency-ops",
            message=f"🚨 Verified: {detail['suggested_incident_data']['category']} "
                    f"(trust: {detail['suggested_incident_data']['trust_score']})"
        )
    elif detail_type == "ReportStatusChangedEvent":
        if detail["new_status"] == "REJECTED_SPAM":
            log_spam_attempt(detail["report_id"])
```

### Pattern 2: Analytics/BI Pipeline

Use SQS as a buffer for batch processing:

```hcl
resource "aws_cloudwatch_event_target" "analytics_queue" {
  rule           = aws_cloudwatch_event_rule.all_events.name
  event_bus_name = "ingestverify-366-dev-disaster-event-bus"
  arn            = aws_sqs_queue.analytics.arn
}
```

### Pattern 3: Dashboard/Frontend Polling

For front-end apps, poll the REST API periodically:

```javascript
// Check for new verified reports every 30 seconds
setInterval(async () => {
    const resp = await fetch(`${API_URL}/reports?status=VERIFIED&limit=5`);
    const data = await resp.json();
    updateDashboard(data);
}, 30000);
```

---

## Error Handling

### API Error Format

All API errors follow this structure:

```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "request_id": "uuid"
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `202` | Accepted (async processing) |
| `400` | Bad Request (validation error) |
| `404` | Not Found |
| `409` | Conflict (invalid state transition) |
| `429` | Rate Limit (50 req/s burst 100) |
| `500` | Internal Server Error |

### Rate Limits

| Setting | Value |
|---------|-------|
| Sustained rate | 50 requests/sec |
| Burst limit | 100 requests |

---

## Quick Reference

```bash
# Set variables
export API_URL="https://xxx.execute-api.us-east-1.amazonaws.com/dev/v1"
export API_KEY="your-api-key"

# Health check
curl "${API_URL}/health"

# Submit report
curl -X POST "${API_URL}/reports" -H "X-Api-Key: ${API_KEY}" \
  -H "Content-Type: application/json" -d '{"title":"Test","description":"Test report","disaster_type":"OTHER","location":{"latitude":0,"longitude":0},"reporter_id":"test"}'

# List reports
curl "${API_URL}/reports?limit=10"

# Get stats
curl "${API_URL}/reports/stats"

# View audit logs
curl "${API_URL}/reports/audit?limit=10"

# View events
curl "${API_URL}/reports/events?type=all&limit=10"
```
