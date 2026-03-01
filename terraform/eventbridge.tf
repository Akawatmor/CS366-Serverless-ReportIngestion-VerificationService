# ============================================================
# EventBridge — Custom Event Bus + Rules
# ============================================================

# ----------------------------------------------------------
# Custom Event Bus for disaster domain events
# ----------------------------------------------------------
resource "aws_cloudwatch_event_bus" "disaster_bus" {
  name = "${local.prefix}-disaster-event-bus"

  tags = {
    Name = "${local.prefix}-disaster-event-bus"
  }
}

# ----------------------------------------------------------
# Rule 1: ReportVerifiedEvent → log to CloudWatch
# (In production, this would target Incident Service Lambda)
# ----------------------------------------------------------
resource "aws_cloudwatch_event_rule" "report_verified" {
  name           = "${local.prefix}-report-verified"
  event_bus_name = aws_cloudwatch_event_bus.disaster_bus.name
  description    = "Route ReportVerifiedEvent to consumers"

  event_pattern = jsonencode({
    source      = ["service.report-verify"]
    detail-type = ["ReportVerifiedEvent"]
  })
}

# Log group for verified events (debug / mock consumer)
resource "aws_cloudwatch_log_group" "verified_events_log" {
  name              = "/events/${local.prefix}/report-verified"
  retention_in_days = 7
}

resource "aws_cloudwatch_event_target" "verified_to_log" {
  rule           = aws_cloudwatch_event_rule.report_verified.name
  event_bus_name = aws_cloudwatch_event_bus.disaster_bus.name
  target_id      = "verified-to-cloudwatch"
  arn            = aws_cloudwatch_log_group.verified_events_log.arn
}

# ----------------------------------------------------------
# Rule 2: ReportStatusChangedEvent → log to CloudWatch
# (Dashboard / Notification services would subscribe here)
# ----------------------------------------------------------
resource "aws_cloudwatch_event_rule" "status_changed" {
  name           = "${local.prefix}-status-changed"
  event_bus_name = aws_cloudwatch_event_bus.disaster_bus.name
  description    = "Broadcast all report status changes"

  event_pattern = jsonencode({
    source      = ["service.report-verify"]
    detail-type = ["ReportStatusChangedEvent"]
  })
}

resource "aws_cloudwatch_log_group" "status_events_log" {
  name              = "/events/${local.prefix}/status-changed"
  retention_in_days = 7
}

resource "aws_cloudwatch_event_target" "status_to_log" {
  rule           = aws_cloudwatch_event_rule.status_changed.name
  event_bus_name = aws_cloudwatch_event_bus.disaster_bus.name
  target_id      = "status-to-cloudwatch"
  arn            = aws_cloudwatch_log_group.status_events_log.arn
}

# Policy to allow EventBridge to write to CloudWatch Logs
resource "aws_cloudwatch_log_resource_policy" "eventbridge_log_policy" {
  policy_name = "${local.prefix}-eventbridge-logs"

  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EventBridgeToLogs"
        Effect    = "Allow"
        Principal = { Service = "events.amazonaws.com" }
        Action    = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = [
          "${aws_cloudwatch_log_group.verified_events_log.arn}:*",
          "${aws_cloudwatch_log_group.status_events_log.arn}:*",
        ]
      }
    ]
  })
}
