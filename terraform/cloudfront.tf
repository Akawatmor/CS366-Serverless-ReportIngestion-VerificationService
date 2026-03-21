# ============================================================
# CloudFront — Single-domain access (Free Tier)
# ============================================================
# Provides a single URL for both the static website and API:
#   /              → S3 Website (Landing page)
#   /dashboard/    → S3 Website (Dashboard)
#   /api/*         → API Gateway (REST API)
#
# CloudFront Free Tier: 1TB transfer + 10M requests/month
# ============================================================

# Toggle CloudFront on/off (disabled by default for Learner Lab)
variable "enable_cloudfront" {
  description = "Enable CloudFront distribution (set to true if your AWS account supports it)"
  type        = bool
  default     = false
}

# Optional: custom domain (CNAME)
variable "cloudfront_domain_aliases" {
  description = "Custom domain aliases for CloudFront (e.g. [\"ingestverify-366-dev.akawatmor.com\"])"
  type        = list(string)
  default     = []
}

# ----------------------------------------------------------
# Origin Access — CloudFront → S3 (OAC not needed for public bucket)
# CloudFront → API Gateway (custom origin)
# ----------------------------------------------------------

resource "aws_cloudfront_distribution" "main" {
  count = var.enable_cloudfront ? 1 : 0

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "${local.prefix} — Single-domain distribution"
  price_class         = "PriceClass_100" # Cheapest — US, Canada, Europe only

  # Optional custom domain
  aliases = var.cloudfront_domain_aliases

  # ----------------------------------------------------------
  # Origin 1: S3 Website (for static frontend)
  # ----------------------------------------------------------
  origin {
    domain_name = aws_s3_bucket_website_configuration.website.website_endpoint
    origin_id   = "s3-website"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only" # S3 website only supports HTTP
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # ----------------------------------------------------------
  # Origin 2: API Gateway (for REST API)
  # ----------------------------------------------------------
  origin {
    domain_name = "${aws_api_gateway_rest_api.api.id}.execute-api.${local.region}.amazonaws.com"
    origin_id   = "api-gateway"
    origin_path = "/${var.environment}" # /dev stage

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # ----------------------------------------------------------
  # Default behavior — S3 website (landing page + dashboard)
  # ----------------------------------------------------------
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-website"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 300  # 5 minutes
    max_ttl     = 3600 # 1 hour
    compress    = true
  }

  # ----------------------------------------------------------
  # /v1/* behavior — API Gateway (pass-through, no caching)
  # ----------------------------------------------------------
  ordered_cache_behavior {
    path_pattern           = "/v1/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "https-only"

    forwarded_values {
      query_string = true
      headers      = ["X-Api-Key", "Content-Type", "Authorization", "Accept"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 0  # No caching for API
    max_ttl     = 0
    compress    = true
  }

  # ----------------------------------------------------------
  # Custom error responses — SPA fallback
  # ----------------------------------------------------------
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  # ----------------------------------------------------------
  # Restrictions — no geo restrictions
  # ----------------------------------------------------------
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # ----------------------------------------------------------
  # SSL Certificate — CloudFront default (*.cloudfront.net)
  # For custom domain, use ACM certificate in us-east-1
  # ----------------------------------------------------------
  viewer_certificate {
    cloudfront_default_certificate = length(var.cloudfront_domain_aliases) == 0
    # If using custom domain, uncomment and configure:
    # acm_certificate_arn      = aws_acm_certificate.cert[0].arn
    # ssl_support_method       = "sni-only"
    # minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name = "${local.prefix}-cdn"
  }
}

# ----------------------------------------------------------
# Outputs
# ----------------------------------------------------------
output "cloudfront_url" {
  description = "CloudFront distribution URL (single domain for everything)"
  value       = var.enable_cloudfront ? "https://${aws_cloudfront_distribution.main[0].domain_name}" : "(CloudFront disabled — set enable_cloudfront=true)"
}

output "cloudfront_api_url" {
  description = "API URL via CloudFront"
  value       = var.enable_cloudfront ? "https://${aws_cloudfront_distribution.main[0].domain_name}/v1" : "(CloudFront disabled)"
}
