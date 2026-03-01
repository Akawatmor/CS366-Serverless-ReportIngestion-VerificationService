# ============================================================
# API Gateway — REST API (v1)
# ============================================================

resource "aws_api_gateway_rest_api" "api" {
  name        = "${local.prefix}-api"
  description = "Report Ingestion & Verification Service API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${local.prefix}-api"
  }
}

# ==========================
# /v1 base path
# ==========================
resource "aws_api_gateway_resource" "v1" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "v1"
}

# ==========================
# /v1/reports
# ==========================
resource "aws_api_gateway_resource" "reports" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "reports"
}

# --- POST /v1/reports → Ingest Handler Lambda ---
resource "aws_api_gateway_method" "post_reports" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.reports.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "post_reports" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.reports.id
  http_method             = aws_api_gateway_method.post_reports.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ingest_handler.invoke_arn
}

# --- GET /v1/reports → API Handler Lambda ---
resource "aws_api_gateway_method" "get_reports" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.reports.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_reports" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.reports.id
  http_method             = aws_api_gateway_method.get_reports.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

# ==========================
# /v1/reports/stats
# ==========================
resource "aws_api_gateway_resource" "reports_stats" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.reports.id
  path_part   = "stats"
}

resource "aws_api_gateway_method" "get_stats" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.reports_stats.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_stats" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.reports_stats.id
  http_method             = aws_api_gateway_method.get_stats.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

# ==========================
# /v1/reports/{report_id}
# ==========================
resource "aws_api_gateway_resource" "report_by_id" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.reports.id
  path_part   = "{report_id}"
}

# --- GET /v1/reports/{report_id} → API Handler ---
resource "aws_api_gateway_method" "get_report_detail" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.report_by_id.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_report_detail" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.report_by_id.id
  http_method             = aws_api_gateway_method.get_report_detail.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

# --- PATCH /v1/reports/{report_id} → API Handler ---
resource "aws_api_gateway_method" "patch_report" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.report_by_id.id
  http_method   = "PATCH"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "patch_report" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.report_by_id.id
  http_method             = aws_api_gateway_method.patch_report.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

# --- DELETE /v1/reports/{report_id} → API Handler ---
resource "aws_api_gateway_method" "delete_report" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.report_by_id.id
  http_method   = "DELETE"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "delete_report" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.report_by_id.id
  http_method             = aws_api_gateway_method.delete_report.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

# ==========================
# /v1/health
# ==========================
resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "health"
}

resource "aws_api_gateway_method" "get_health" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.health.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_health" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.health.id
  http_method             = aws_api_gateway_method.get_health.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.health_handler.invoke_arn
}

# ==========================
# CORS — OPTIONS methods
# ==========================
module "cors_reports" {
  source  = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.reports.id
}

module "cors_report_by_id" {
  source  = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.report_by_id.id
}

module "cors_stats" {
  source  = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.reports_stats.id
}

module "cors_health" {
  source  = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.health.id
}

# ==========================
# Deployment + Stage
# ==========================
resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.reports.id,
      aws_api_gateway_resource.reports_stats.id,
      aws_api_gateway_resource.report_by_id.id,
      aws_api_gateway_resource.health.id,
      aws_api_gateway_method.post_reports.id,
      aws_api_gateway_method.get_reports.id,
      aws_api_gateway_method.get_stats.id,
      aws_api_gateway_method.get_report_detail.id,
      aws_api_gateway_method.patch_report.id,
      aws_api_gateway_method.delete_report.id,
      aws_api_gateway_method.get_health.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "dev" {
  deployment_id = aws_api_gateway_deployment.api.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.environment

  tags = {
    Name = "${local.prefix}-stage"
  }
}

# ==========================
# API Key + Usage Plan
# ==========================
resource "aws_api_gateway_api_key" "external_client" {
  name    = "${local.prefix}-external-key"
  enabled = true
}

resource "aws_api_gateway_usage_plan" "default" {
  name = "${local.prefix}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.api.id
    stage  = aws_api_gateway_stage.dev.stage_name
  }

  throttle_settings {
    burst_limit = 100
    rate_limit  = 50
  }
}

resource "aws_api_gateway_usage_plan_key" "external_client" {
  key_id        = aws_api_gateway_api_key.external_client.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.default.id
}

# ==========================
# Lambda Permissions for API Gateway
# ==========================
resource "aws_lambda_permission" "apigw_ingest" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_api" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_health" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}
