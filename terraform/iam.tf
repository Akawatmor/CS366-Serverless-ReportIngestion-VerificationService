# ============================================================
# IAM Roles & Policies for Lambda Functions
# ============================================================

# ----------------------------------------------------------
# Lambda Execution Role — shared by all Lambda functions
# ----------------------------------------------------------
resource "aws_iam_role" "lambda_exec" {
  name = "${local.prefix}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# CloudWatch Logs — all Lambdas can write logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy — DynamoDB + SQS + EventBridge
resource "aws_iam_role_policy" "lambda_service_policy" {
  name = "${local.prefix}-lambda-service"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # DynamoDB — full access to owned tables
      {
        Sid    = "DynamoDBAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:DescribeTable",
        ]
        Resource = [
          aws_dynamodb_table.reports.arn,
          "${aws_dynamodb_table.reports.arn}/index/*",
          aws_dynamodb_table.audit_logs.arn,
          "${aws_dynamodb_table.audit_logs.arn}/index/*",
          aws_dynamodb_table.stats.arn,
        ]
      },
      # SQS — receive/delete from ingestion queue
      {
        Sid    = "SQSAccess"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:SendMessage",
        ]
        Resource = [
          aws_sqs_queue.ingestion_queue.arn,
          aws_sqs_queue.ingestion_dlq.arn,
        ]
      },
      # EventBridge — publish events
      {
        Sid    = "EventBridgePublish"
        Effect = "Allow"
        Action = [
          "events:PutEvents",
          "events:DescribeEventBus",
        ]
        Resource = [
          aws_cloudwatch_event_bus.disaster_bus.arn,
        ]
      },
    ]
  })
}

# ----------------------------------------------------------
# API Gateway Role — for SQS direct integration
# ----------------------------------------------------------
resource "aws_iam_role" "apigw_sqs_role" {
  name = "${local.prefix}-apigw-sqs"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "apigw_sqs_send" {
  name = "${local.prefix}-apigw-sqs-send"
  role = aws_iam_role.apigw_sqs_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSQSSend"
        Effect = "Allow"
        Action = "sqs:SendMessage"
        Resource = aws_sqs_queue.ingestion_queue.arn
      }
    ]
  })
}
