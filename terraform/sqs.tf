# ============================================================
# SQS Queues — Ingestion Buffer + Dead Letter Queue
# ============================================================

# ----------------------------------------------------------
# Dead Letter Queue (DLQ) — catches failed messages
# ----------------------------------------------------------
resource "aws_sqs_queue" "ingestion_dlq" {
  name                      = "${local.prefix}-ingestion-dlq"
  message_retention_seconds = 1209600 # 14 days
  receive_wait_time_seconds = 0

  tags = {
    Name = "${local.prefix}-ingestion-dlq"
  }
}

# ----------------------------------------------------------
# Main Ingestion Queue — buffer for raw reports
# ----------------------------------------------------------
resource "aws_sqs_queue" "ingestion_queue" {
  name                       = "${local.prefix}-ingestion-queue"
  visibility_timeout_seconds = var.sqs_visibility_timeout
  message_retention_seconds  = 1209600 # 14 days
  receive_wait_time_seconds  = 5       # Long polling
  max_message_size           = 262144  # 256 KB

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingestion_dlq.arn
    maxReceiveCount     = var.sqs_max_receive_count
  })

  tags = {
    Name = "${local.prefix}-ingestion-queue"
  }
}

# SQS Queue Policy — allow API Gateway to send messages
resource "aws_sqs_queue_policy" "ingestion_queue_policy" {
  queue_url = aws_sqs_queue.ingestion_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowAPIGatewaySend"
        Effect    = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.ingestion_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = "${aws_api_gateway_rest_api.api.execution_arn}/*"
          }
        }
      }
    ]
  })
}
