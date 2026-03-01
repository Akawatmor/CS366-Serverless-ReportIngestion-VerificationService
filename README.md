# CS366 — Report Ingestion & Verification Service

> Serverless Microservice สำหรับรับรายงานภัยพิบัติ (Disaster Reports) ประมวลผลด้วย AI แล้วให้เจ้าหน้าที่ Verify ก่อนสร้าง Incident

## Overview

ระบบนี้ทำหน้าที่เป็น **Central Gateway** สำหรับรับข้อมูลเหตุภัยพิบัติจากแหล่งต่างๆ (Social Media, Mobile Apps, IoT Sensors) แล้วทำการ:

1. **Ingest** — รับ raw report ผ่าน REST API → คิวด้วย SQS
2. **Analyze** — ใช้ Google Gemini AI วิเคราะห์ trust score
3. **Deduplicate** — ตรวจจับรายงานซ้ำด้วย Haversine distance + time window
4. **Verify** — เจ้าหน้าที่กด approve/reject ผ่าน API
5. **Publish** — ส่ง Event ผ่าน EventBridge ไปสร้าง Incident

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Runtime | Python 3.12 |
| Compute | AWS Lambda (4 functions) |
| API | API Gateway (REST) |
| Database | DynamoDB (3 tables) |
| Queue | SQS + Dead Letter Queue |
| Events | EventBridge (custom bus) |
| AI | Google Gemini (gemini-2.0-flash) |
| IaC | Terraform |
| Auth | API Key (Usage Plan) |

## Prerequisites

- AWS Learner Lab — active session with credentials
- [Terraform](https://www.terraform.io/downloads) ≥ 1.5
- Python 3.12+
- Google Gemini API Key ([get one](https://aistudio.google.com/apikey))

## Quick Start

```bash
# 1. Clone repository
git clone <repo-url>
cd CS366-Serverless-RequestVerifyService

# 2. ตั้งค่า AWS Credentials (จาก Learner Lab)
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...

# 3. Deploy ทั้งหมดด้วยคำสั่งเดียว
chmod +x scripts/deploy.sh
./scripts/deploy.sh
#   → ระบบจะถาม Gemini API Key ระหว่าง terraform apply

# 4. ดู API URL + API Key
cd terraform
terraform output api_url
terraform output -raw api_key
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/reports` | Submit raw report (202 Accepted) |
| `GET` | `/v1/reports` | List reports with status filter |
| `GET` | `/v1/reports/{id}` | Get report detail + AI analysis |
| `PATCH` | `/v1/reports/{id}` | Verify / Reject / Request more info |
| `DELETE` | `/v1/reports/{id}` | Soft delete a report |
| `GET` | `/v1/reports/stats` | Aggregated statistics |
| `GET` | `/v1/health` | System health check |

### Example — Submit a report

```bash
API_URL="https://xxx.execute-api.us-east-1.amazonaws.com/dev/v1"
API_KEY="your-api-key"

curl -X POST "$API_URL/reports" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $API_KEY" \
  -d '{
    "reporter_source": "TWITTER",
    "reporter_id": "@somchai",
    "raw_content": "ไฟไหม้ร้านทอง เยาวราช ตอนนี้เลย!",
    "geo_location": {"lat": 13.7422, "lon": 100.5108}
  }'
```

Response:
```json
{
  "status": "QUEUED",
  "report_id": "r-550e8400-e29b-...",
  "message": "Report accepted and queued for processing."
}
```

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run unit + integration tests (no AWS needed)
pytest tests/unit/ tests/integration/ -v

# Run with coverage
pytest tests/unit/ tests/integration/ --cov=src --cov-report=term-missing

# Run E2E tests (requires deployed API)
API_URL=https://xxx.execute-api.../dev API_KEY=xxx pytest tests/e2e/ -v
```

## Project Structure

```
src/
├── config.py                 # Environment config
├── models/                   # Enums, dataclasses
├── utils/                    # Logger, response builders, validators
├── services/                 # Gemini AI, dedup, audit, events
└── handlers/                 # Lambda entry points (4 handlers)

terraform/                    # All infrastructure-as-code
scripts/                      # deploy.sh, destroy.sh, seed_data.py
tests/                        # unit/ + integration/ + e2e/
docs/                         # Service Proposal
plan/                         # Implementation plan
```

## Tear Down

```bash
./scripts/destroy.sh
```

## External Resources

- [Service Proposal](docs/Service%20Proposal.md)
- [Implementation Plan](plan/implementation-plan.md)