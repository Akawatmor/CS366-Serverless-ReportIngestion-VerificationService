# ============================================================
# DynamoDB Tables
# ============================================================

# ----------------------------------------------------------
# 1) Reports Table — primary data store
# ----------------------------------------------------------
resource "aws_dynamodb_table" "reports" {
  name         = "${local.prefix}-reports"
  billing_mode = "PAY_PER_REQUEST" # On-demand for Learner Lab
  hash_key     = "report_id"

  attribute {
    name = "report_id"
    type = "S"
  }

  attribute {
    name = "validation_status"
    type = "S"
  }

  attribute {
    name = "ingested_at"
    type = "S"
  }

  attribute {
    name = "source_external_id"
    type = "S"
  }

  attribute {
    name = "reporter_id"
    type = "S"
  }

  # GSI 1: Query by status + time (for GET /reports?status=PENDING_REVIEW)
  global_secondary_index {
    name            = "gsi_status_ingested"
    hash_key        = "validation_status"
    range_key       = "ingested_at"
    projection_type = "ALL"
  }

  # GSI 2: Idempotency check by source_external_id
  global_secondary_index {
    name            = "gsi_source_external_id"
    hash_key        = "source_external_id"
    projection_type = "KEYS_ONLY"
  }

  # GSI 3: Reporter history lookup (for SPAM detection)
  global_secondary_index {
    name            = "gsi_reporter"
    hash_key        = "reporter_id"
    range_key       = "ingested_at"
    projection_type = "INCLUDE"
    non_key_attributes = ["validation_status", "trust_score"]
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${local.prefix}-reports"
  }
}

# ----------------------------------------------------------
# 2) Audit Logs Table — append-only change history
# ----------------------------------------------------------
resource "aws_dynamodb_table" "audit_logs" {
  name         = "${local.prefix}-audit-logs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "log_id"

  attribute {
    name = "log_id"
    type = "S"
  }

  attribute {
    name = "report_ref_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  # GSI: Query all logs for a specific report
  global_secondary_index {
    name            = "gsi_report_timestamp"
    hash_key        = "report_ref_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name = "${local.prefix}-audit-logs"
  }
}

# ----------------------------------------------------------
# 3) Stats Counter Table — atomic counters for dashboard
# ----------------------------------------------------------
resource "aws_dynamodb_table" "stats" {
  name         = "${local.prefix}-stats"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "stat_key"

  attribute {
    name = "stat_key"
    type = "S"
  }

  tags = {
    Name = "${local.prefix}-stats"
  }
}
