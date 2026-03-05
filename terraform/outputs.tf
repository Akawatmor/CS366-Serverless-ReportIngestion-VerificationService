# ============================================================
# Outputs — information displayed after terraform apply
# ============================================================

output "api_url" {
  description = "Base URL for the API"
  value       = "${aws_api_gateway_stage.dev.invoke_url}/v1"
}

output "api_key" {
  description = "API Key for external client authentication (POST /reports)"
  value       = aws_api_gateway_api_key.external_client.value
  sensitive   = true
}

output "reports_table_name" {
  description = "DynamoDB Reports table name"
  value       = aws_dynamodb_table.reports.name
}

output "audit_table_name" {
  description = "DynamoDB Audit Logs table name"
  value       = aws_dynamodb_table.audit_logs.name
}

output "stats_table_name" {
  description = "DynamoDB Stats Counter table name"
  value       = aws_dynamodb_table.stats.name
}

output "sqs_queue_url" {
  description = "SQS Ingestion Queue URL"
  value       = aws_sqs_queue.ingestion_queue.url
}

output "sqs_dlq_url" {
  description = "SQS Dead Letter Queue URL"
  value       = aws_sqs_queue.ingestion_dlq.url
}

output "event_bus_name" {
  description = "EventBridge Custom Event Bus name"
  value       = aws_cloudwatch_event_bus.disaster_bus.name
}

output "website_url" {
  description = "S3 Static Website URL (Landing Page)"
  value       = "http://${aws_s3_bucket_website_configuration.website.website_endpoint}"
}

output "dashboard_url" {
  description = "S3 Static Website Dashboard URL"
  value       = "http://${aws_s3_bucket_website_configuration.website.website_endpoint}/dashboard/"
}

output "website_bucket" {
  description = "S3 Website bucket name"
  value       = aws_s3_bucket.website.id
}

output "endpoints" {
  description = "All available API endpoints"
  value = {
    health      = "GET    ${aws_api_gateway_stage.dev.invoke_url}/v1/health"
    ingest      = "POST   ${aws_api_gateway_stage.dev.invoke_url}/v1/reports"
    list        = "GET    ${aws_api_gateway_stage.dev.invoke_url}/v1/reports?status=PENDING_REVIEW"
    detail      = "GET    ${aws_api_gateway_stage.dev.invoke_url}/v1/reports/{report_id}"
    verify      = "PATCH  ${aws_api_gateway_stage.dev.invoke_url}/v1/reports/{report_id}"
    delete      = "DELETE ${aws_api_gateway_stage.dev.invoke_url}/v1/reports/{report_id}"
    stats       = "GET    ${aws_api_gateway_stage.dev.invoke_url}/v1/reports/stats"
    website     = "http://${aws_s3_bucket_website_configuration.website.website_endpoint}"
    dashboard   = "http://${aws_s3_bucket_website_configuration.website.website_endpoint}/dashboard/"
  }
}
