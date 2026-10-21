# 1. Terraform & Provider Configuration
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "financial-tracker-tfstate-965825500656"
    key    = "state/terraform.tfstate"
    region = "ap-southeast-1"
  }
}

provider "aws" {
  region = "ap-southeast-1"
}

# Variable to distinguish dev vs prod
variable "environment" {
  type        = string
  default     = "dev"
  description = "Target deployment environment (dev or prod)"
}

# ==========================================
# DYNAMODB TABLE
# ==========================================

resource "aws_dynamodb_table" "financial_tracker" {
  name         = "FinancialTracker-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "PK"
  range_key = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  ttl {
    attribute_name = "expire_at"
    enabled        = true
  }

  tags = {
    Environment = var.environment
    Project     = "FinancialTracker"
  }
}

# ==========================================
# ECR REPOSITORY & BACKEND LAMBDA
# ==========================================

resource "aws_ecr_repository" "backend_api" {
  name                 = "financial-tracker-backend-${var.environment}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # Allow destroying repo if images exist

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = var.environment
    Project     = "FinancialTracker"
  }
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "financial_tracker_lambda_role_${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

# Auto-cleanup CloudWatch Logs after 14 days
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api_backend.function_name}"
  retention_in_days = 14

  tags = {
    Environment = var.environment
    Project     = "FinancialTracker"
  }
}

resource "aws_lambda_function" "api_backend" {
  function_name = "financial-tracker-api-${var.environment}"
  role          = aws_iam_role.lambda_exec_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.backend_api.repository_url}:latest"

  timeout     = 10
  memory_size = 128

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.financial_tracker.name
    }
  }

  tags = {
    Environment = var.environment
    Project     = "FinancialTracker"
  }
}

# ==========================================
# API GATEWAY
# ==========================================

resource "aws_apigatewayv2_api" "http_api" {
  name          = "financial-tracker-api-gateway-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["content-type", "authorization", "x-guest-session"]
  }

  tags = {
    Environment = var.environment
    Project     = "FinancialTracker"
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"

  integration_uri        = aws_lambda_function.api_backend.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_lambda_permission" "api_gw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_backend.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# ==========================================
# AWS COGNITO AUTHENTICATION
# ==========================================

resource "aws_cognito_user_pool" "users" {
  name = "financial-tracker-users-${var.environment}"

  alias_attributes         = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
    mutable             = true
  }

  tags = {
    Environment = var.environment
    Project     = "FinancialTracker"
  }
}

resource "aws_cognito_user_pool_client" "nuxt_client" {
  name         = "financial-tracker-nuxt-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.users.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]
}

# ==========================================
# AUTOMATED REPORTING (SES & EVENTBRIDGE)
# ==========================================

resource "aws_iam_role_policy" "lambda_ses_policy" {
  name = "lambda_ses_policy_${var.environment}"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_cloudwatch_event_rule" "monthly_report_rule" {
  name                = "financial-tracker-monthly-report-${var.environment}"
  description         = "Triggers the monthly financial report generation"
  schedule_expression = "cron(59 23 L * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.monthly_report_rule.name
  target_id = "TriggerMonthlyReportLambda"
  arn       = aws_lambda_function.api_backend.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_backend.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monthly_report_rule.arn
}

# ==========================================
# FRONTEND HOSTING (S3 + CLOUDFRONT)
# ==========================================

resource "aws_s3_bucket" "frontend_bucket" {
  bucket        = "haikal-financial-tracker-frontend-${var.environment}"
  force_destroy = true # Allow destroying bucket if objects exist

  tags = {
    Environment = var.environment
    Project     = "FinancialTracker"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend_block" {
  bucket = aws_s3_bucket.frontend_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "frontend_oac" {
  name                              = "financial-tracker-oac-${var.environment}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend_cdn" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  aliases = ["finance.haikalahnaf.my.id"]

  origin {
    domain_name              = aws_s3_bucket.frontend_bucket.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.frontend_bucket.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend_oac.id
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.frontend_bucket.id}"

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  # SPA Routing Rule: Direct deep links back to index.html for Vue Router
  custom_error_response {
    error_caching_min_ttl = 300
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
  }

  custom_error_response {
    error_caching_min_ttl = 300
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    # REPLACE THE DEFAULT CERTIFICATE WITH YOUR ACM CERTIFICATE
    cloudfront_default_certificate = false
    acm_certificate_arn            = "arn:aws:acm:us-east-1:965825500656:certificate/110711f7-e812-4bb9-ad03-7e63198aeaa2" # Paste the ARN from your ACM console
    ssl_support_method             = "sni-only"
    minimum_protocol_version       = "TLSv1.2_2021"
  }
}

resource "aws_s3_bucket_policy" "frontend_bucket_policy" {
  bucket = aws_s3_bucket.frontend_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontServicePrincipalReadOnly"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend_bucket.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend_cdn.arn
          }
        }
      }
    ]
  })
}

# ==========================================
# OUTPUTS
# ==========================================

output "api_endpoint" {
  value       = aws_apigatewayv2_api.http_api.api_endpoint
  description = "The public API Gateway URL"
}

output "cognito_user_pool_id" {
  value       = aws_cognito_user_pool.users.id
  description = "The Cognito User Pool ID"
}

output "cognito_client_id" {
  value       = aws_cognito_user_pool_client.nuxt_client.id
  description = "The Cognito Client ID"
}

output "cloudfront_url" {
  value       = aws_cloudfront_distribution.frontend_cdn.domain_name
  description = "The CloudFront CDN domain name"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.frontend_bucket.id
  description = "The S3 bucket name for frontend deployments"
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.frontend_cdn.id
  description = "The CloudFront Distribution ID for cache invalidation"
}
