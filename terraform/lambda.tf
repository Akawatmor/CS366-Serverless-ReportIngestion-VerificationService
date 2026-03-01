# ============================================================
# Lambda Functions + Layer
# ============================================================

# ----------------------------------------------------------
# Lambda Layer — shared Python dependencies
# ----------------------------------------------------------
resource "aws_lambda_layer_version" "dependencies" {
  filename            = "${path.module}/../build/lambda_layer.zip"
  layer_name          = "${local.prefix}-dependencies"
  compatible_runtimes = [var.lambda_runtime]
  description         = "Shared dependencies: boto3, google-generativeai, etc."
  source_code_hash    = filebase64sha256("${path.module}/../build/lambda_layer.zip")
}

# ----------------------------------------------------------
# 1) Ingestion Worker — SQS consumer
# ----------------------------------------------------------
data "archive_file" "lambda_src" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/../build/lambda_src.zip"
}

resource "aws_lambda_function" "ingestion_worker" {
  function_name    = "${local.prefix}-ingestion-worker"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.ingestion_worker.handler"
  runtime          = var.lambda_runtime
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout_worker
  filename         = data.archive_file.lambda_src.output_path
  source_code_hash = data.archive_file.lambda_src.output_base64sha256
  layers           = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      REPORTS_TABLE   = aws_dynamodb_table.reports.name
      AUDIT_TABLE     = aws_dynamodb_table.audit_logs.name
      STATS_TABLE     = aws_dynamodb_table.stats.name
      SQS_QUEUE_URL   = aws_sqs_queue.ingestion_queue.url
      EVENT_BUS_NAME  = aws_cloudwatch_event_bus.disaster_bus.name
      GEMINI_API_KEY  = var.gemini_api_key
      GEMINI_MODEL    = var.gemini_model
      TRUST_AUTO_REJECT   = tostring(var.trust_auto_reject)
      TRUST_HIGH_PRIORITY = tostring(var.trust_high_priority)
      LOG_LEVEL       = "INFO"
      PYTHONPATH       = "/var/task"
    }
  }

  tags = {
    Name = "${local.prefix}-ingestion-worker"
  }
}

# SQS → Lambda trigger
resource "aws_lambda_event_source_mapping" "sqs_to_worker" {
  event_source_arn                   = aws_sqs_queue.ingestion_queue.arn
  function_name                      = aws_lambda_function.ingestion_worker.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  enabled                            = true

  function_response_types = ["ReportBatchItemFailures"]
}

# CloudWatch Log Group for worker
resource "aws_cloudwatch_log_group" "worker_logs" {
  name              = "/aws/lambda/${aws_lambda_function.ingestion_worker.function_name}"
  retention_in_days = 7
}

# ----------------------------------------------------------
# 2) API Handler — REST API for officers
# ----------------------------------------------------------
resource "aws_lambda_function" "api_handler" {
  function_name    = "${local.prefix}-api-handler"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.api_handler.handler"
  runtime          = var.lambda_runtime
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout_api
  filename         = data.archive_file.lambda_src.output_path
  source_code_hash = data.archive_file.lambda_src.output_base64sha256
  layers           = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      REPORTS_TABLE  = aws_dynamodb_table.reports.name
      AUDIT_TABLE    = aws_dynamodb_table.audit_logs.name
      STATS_TABLE    = aws_dynamodb_table.stats.name
      EVENT_BUS_NAME = aws_cloudwatch_event_bus.disaster_bus.name
      GEMINI_API_KEY = var.gemini_api_key
      LOG_LEVEL      = "INFO"
      PYTHONPATH      = "/var/task"
    }
  }

  tags = {
    Name = "${local.prefix}-api-handler"
  }
}

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api_handler.function_name}"
  retention_in_days = 7
}

# ----------------------------------------------------------
# 3) Ingest Handler — POST /reports (Lambda fallback)
# ----------------------------------------------------------
resource "aws_lambda_function" "ingest_handler" {
  function_name    = "${local.prefix}-ingest-handler"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.ingest_handler.handler"
  runtime          = var.lambda_runtime
  memory_size      = 128
  timeout          = 10
  filename         = data.archive_file.lambda_src.output_path
  source_code_hash = data.archive_file.lambda_src.output_base64sha256
  layers           = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      SQS_QUEUE_URL = aws_sqs_queue.ingestion_queue.url
      LOG_LEVEL     = "INFO"
      PYTHONPATH     = "/var/task"
    }
  }

  tags = {
    Name = "${local.prefix}-ingest-handler"
  }
}

resource "aws_cloudwatch_log_group" "ingest_logs" {
  name              = "/aws/lambda/${aws_lambda_function.ingest_handler.function_name}"
  retention_in_days = 7
}

# ----------------------------------------------------------
# 4) Health Handler — GET /health
# ----------------------------------------------------------
resource "aws_lambda_function" "health_handler" {
  function_name    = "${local.prefix}-health-handler"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.health_handler.handler"
  runtime          = var.lambda_runtime
  memory_size      = 128
  timeout          = 15
  filename         = data.archive_file.lambda_src.output_path
  source_code_hash = data.archive_file.lambda_src.output_base64sha256
  layers           = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      REPORTS_TABLE  = aws_dynamodb_table.reports.name
      SQS_QUEUE_URL  = aws_sqs_queue.ingestion_queue.url
      EVENT_BUS_NAME = aws_cloudwatch_event_bus.disaster_bus.name
      GEMINI_API_KEY = var.gemini_api_key
      GEMINI_MODEL   = var.gemini_model
      LOG_LEVEL      = "INFO"
      PYTHONPATH      = "/var/task"
    }
  }

  tags = {
    Name = "${local.prefix}-health-handler"
  }
}

resource "aws_cloudwatch_log_group" "health_logs" {
  name              = "/aws/lambda/${aws_lambda_function.health_handler.function_name}"
  retention_in_days = 7
}
