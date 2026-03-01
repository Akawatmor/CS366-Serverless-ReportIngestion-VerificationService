# ============================================================
# Input Variables
# ============================================================

variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "report-verify"
}

variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

# --- Gemini AI ---
variable "gemini_api_key" {
  description = "Google Gemini API key for trust scoring"
  type        = string
  sensitive   = true
  default     = ""
}

variable "gemini_model" {
  description = "Gemini model name"
  type        = string
  default     = "gemini-2.0-flash"
}

# --- Lambda ---
variable "lambda_memory_size" {
  description = "Lambda memory in MB"
  type        = number
  default     = 256
}

variable "lambda_timeout_api" {
  description = "Timeout for API handler Lambda (seconds)"
  type        = number
  default     = 30
}

variable "lambda_timeout_worker" {
  description = "Timeout for ingestion worker Lambda (seconds)"
  type        = number
  default     = 60
}

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

# --- Trust Score ---
variable "trust_auto_reject" {
  description = "Trust score threshold for auto-rejection (0-100)"
  type        = number
  default     = 30
}

variable "trust_high_priority" {
  description = "Trust score threshold for high priority (0-100)"
  type        = number
  default     = 80
}

# --- SQS ---
variable "sqs_visibility_timeout" {
  description = "SQS visibility timeout in seconds"
  type        = number
  default     = 90
}

variable "sqs_max_receive_count" {
  description = "Max receive count before sending to DLQ"
  type        = number
  default     = 3
}
