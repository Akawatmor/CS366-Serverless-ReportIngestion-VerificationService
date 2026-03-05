# ============================================================
# S3 — Static Website Hosting (Landing Page + Dashboard)
# ============================================================
# Hosts:
#   /            → index.html  (Landing page)
#   /dashboard/  → dashboard/index.html  (API Testing Dashboard)
# ============================================================

resource "aws_s3_bucket" "website" {
  bucket        = "${local.prefix}-website-${local.account_id}"
  force_destroy = true

  tags = {
    Name = "${local.prefix}-website"
  }
}

# Website configuration
resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

# Public access — disable block for website hosting
resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Bucket policy — allow public read
resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id

  # Wait for public access block to be applied first
  depends_on = [aws_s3_bucket_public_access_block.website]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.website.arn}/*"
      }
    ]
  })
}

# CORS — allow dashboard to call API from different origin
resource "aws_s3_bucket_cors_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    max_age_seconds = 3600
  }
}

# ============================================================
# Upload static files
# ============================================================

resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.website.id
  key          = "index.html"
  source       = "${path.module}/../frontend/index.html"
  content_type = "text/html; charset=utf-8"
  etag         = filemd5("${path.module}/../frontend/index.html")
}

resource "aws_s3_object" "dashboard_html" {
  bucket       = aws_s3_bucket.website.id
  key          = "dashboard/index.html"
  source       = "${path.module}/../frontend/dashboard/index.html"
  content_type = "text/html; charset=utf-8"
  etag         = filemd5("${path.module}/../frontend/dashboard/index.html")
}
