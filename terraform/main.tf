# ============================================================
# Report Ingestion & Verification Service — Terraform Main
# ============================================================
# Provider: AWS (Learner Lab)
# State: local (no remote backend for Lab environment)
# ============================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Course      = "CS366"
    }
  }
}

# Current AWS account / region data
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Locals used across modules
locals {
  prefix     = "${var.project_name}-${var.environment}"
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}
