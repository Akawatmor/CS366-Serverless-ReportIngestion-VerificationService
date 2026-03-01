#!/usr/bin/env python3
"""
seed_data.py — สร้าง mock disaster reports ลง DynamoDB สำหรับทดสอบ

Usage:
  python scripts/seed_data.py                         # ใช้ default table name
  python scripts/seed_data.py --table report-verify-dev-reports
  python scripts/seed_data.py --count 20              # สร้าง 20 records
  python scripts/seed_data.py --api-url https://xxx   # ส่งผ่าน API แทน DB ตรง
"""
import argparse
import json
import random
import sys
import uuid
from datetime import datetime, timezone, timedelta

try:
    import boto3
except ImportError:
    print("ERROR: boto3 not installed. Run: pip install boto3")
    sys.exit(1)

# --- Sample data ---

SAMPLE_REPORTS = [
    {
        "source": "TWITTER",
        "reporter_id": "@somchai_123",
        "content": "ไฟไหม้ร้านทอง เยาวราช ตอนนี้เลย! ควันขึ้นสูงมาก #BKKFire",
        "category": "FIRE",
        "lat": 13.7411, "lon": 100.5104,
    },
    {
        "source": "FACEBOOK",
        "reporter_id": "user_456",
        "content": "น้ำท่วมหนักที่ถนนรัชดาภิเษก รถติดหมดเลย น้ำสูงถึงเอว",
        "category": "FLOOD",
        "lat": 13.7649, "lon": 100.5736,
    },
    {
        "source": "OFFICIAL_APP",
        "reporter_id": "reporter_789",
        "content": "Fire reported near Central World! Smoke visible from 5km away.",
        "category": "FIRE",
        "lat": 13.7466, "lon": 100.5391,
    },
    {
        "source": "LINE",
        "reporter_id": "line_user_001",
        "content": "แผ่นดินไหวรู้สึกได้ที่เชียงราย ของในบ้านล้มหมด ช่วยด้วย!",
        "category": "EARTHQUAKE",
        "lat": 19.9105, "lon": 99.8406,
    },
    {
        "source": "IOT_SENSOR",
        "reporter_id": "sensor_bkk_042",
        "content": "Water level alert: Chao Phraya river gauge exceeded 2.5m threshold",
        "category": "FLOOD",
        "lat": 13.7563, "lon": 100.5018,
    },
    {
        "source": "TWITTER",
        "reporter_id": "@rescue_bkk",
        "content": "คนติดอยู่บนหลังคาบ้าน ซอยสุขุมวิท 71 ต้องการเรือกู้ภัยด่วน SOS",
        "category": "FLOOD",
        "lat": 13.7234, "lon": 100.5876,
    },
    {
        "source": "FACEBOOK",
        "reporter_id": "user_reporter_321",
        "content": "สะพานข้ามคลองพังถล่ม มีคนบาดเจ็บหลายราย ตรงแยกรามคำแหง",
        "category": "ACCIDENT",
        "lat": 13.7590, "lon": 100.6367,
    },
    {
        "source": "OFFICIAL_APP",
        "reporter_id": "officer_007",
        "content": "Confirmed landslide blocking Highway 118, Chiang Mai. Road impassable.",
        "category": "EARTHQUAKE",
        "lat": 18.7883, "lon": 98.9853,
    },
    {
        "source": "TWITTER",
        "reporter_id": "@spam_bot_999",
        "content": "Buy cheap watches at www.fakeshop.com! Best prices! Click now!",
        "category": "OTHER",
        "lat": 0.0, "lon": 0.0,
    },
    {
        "source": "LINE",
        "reporter_id": "line_aid_002",
        "content": "ถนนขาดตรงทางเข้าหมู่บ้าน ตำบลบ้านด่านนอก รถผ่านไม่ได้แล้ว",
        "category": "DAMAGE",
        "lat": 14.0923, "lon": 101.3657,
    },
]

STATUSES = ["PENDING_REVIEW", "PENDING_REVIEW", "PENDING_REVIEW", "SPAM", "VERIFIED", "RECEIVED"]


def generate_reports(count: int) -> list[dict]:
    """Generate N random disaster reports."""
    reports = []
    now = datetime.now(timezone.utc)

    for i in range(count):
        sample = random.choice(SAMPLE_REPORTS)
        time_offset = random.randint(0, 3600 * 24)
        report_time = now - timedelta(seconds=time_offset)

        # Add slight variation to coordinates
        lat = sample["lat"] + random.uniform(-0.01, 0.01)
        lon = sample["lon"] + random.uniform(-0.01, 0.01)

        report_id = f"r-{uuid.uuid4().hex[:12]}"
        trust_score = random.randint(5, 95)
        status = random.choice(STATUSES)

        # Spam gets low trust score
        if "spam" in sample["reporter_id"].lower() or "fakeshop" in sample["content"].lower():
            trust_score = random.randint(1, 15)
            status = "SPAM"

        item = {
            "report_id": {"S": report_id},
            "source_platform": {"S": sample["source"]},
            "reporter_id": {"S": sample["reporter_id"]},
            "raw_content": {"S": sample["content"]},
            "media_urls": {"L": [{"S": f"https://s3.example.com/{report_id}/img{j}.jpg"} for j in range(random.randint(0, 2))]},
            "geo_location": {"M": {"lat": {"N": str(round(lat, 6))}, "lon": {"N": str(round(lon, 6))}}},
            "event_timestamp": {"S": report_time.isoformat()},
            "ingested_at": {"S": (report_time + timedelta(seconds=random.randint(1, 30))).isoformat()},
            "trust_score": {"N": str(trust_score)},
            "ai_analysis_tags": {"L": [{"S": sample["category"]}, {"S": "AUTO_SEEDED"}]},
            "ai_reasoning": {"S": f"Seed data — trust_score={trust_score}"},
            "suggested_category": {"S": sample["category"]},
            "ai_analysis_failed": {"BOOL": False},
            "validation_status": {"S": status},
        }
        reports.append(item)

    return reports


def seed_dynamodb(table_name: str, reports: list[dict], region: str = "us-east-1"):
    """Write reports directly to DynamoDB."""
    dynamodb = boto3.client("dynamodb", region_name=region)

    print(f"Seeding {len(reports)} reports into table '{table_name}'...")

    for i, item in enumerate(reports):
        dynamodb.put_item(TableName=table_name, Item=item)
        rid = item["report_id"]["S"]
        status = item["validation_status"]["S"]
        score = item["trust_score"]["N"]
        print(f"  [{i+1}/{len(reports)}] {rid} | {status:16s} | trust={score:>3s}")

    print(f"\nDone! {len(reports)} reports seeded.")


def seed_via_api(api_url: str, reports: list[dict], api_key: str = ""):
    """Send reports via POST /reports API."""
    try:
        import httpx
    except ImportError:
        print("ERROR: httpx not installed. Run: pip install httpx")
        sys.exit(1)

    print(f"Sending {len(reports)} reports to {api_url}/reports ...")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key

    for i, item in enumerate(reports):
        payload = {
            "reporter_source": item["source_platform"]["S"],
            "reporter_id": item["reporter_id"]["S"],
            "raw_content": item["raw_content"]["S"],
            "geo_location": {
                "lat": float(item["geo_location"]["M"]["lat"]["N"]),
                "lon": float(item["geo_location"]["M"]["lon"]["N"]),
            },
            "timestamp": item["event_timestamp"]["S"],
        }
        resp = httpx.post(f"{api_url}/reports", json=payload, headers=headers, timeout=10)
        print(f"  [{i+1}/{len(reports)}] {resp.status_code} — {resp.text[:80]}")

    print(f"\nDone! {len(reports)} reports sent via API.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed mock disaster reports")
    parser.add_argument("--table", default="report-verify-dev-reports", help="DynamoDB table name")
    parser.add_argument("--count", type=int, default=10, help="Number of reports to create")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--api-url", default="", help="API URL (use API instead of direct DB)")
    parser.add_argument("--api-key", default="", help="API Key for POST /reports")
    args = parser.parse_args()

    reports = generate_reports(args.count)

    if args.api_url:
        seed_via_api(args.api_url, reports, args.api_key)
    else:
        seed_dynamodb(args.table, reports, args.region)
