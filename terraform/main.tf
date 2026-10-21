# 1. Tell Terraform to download the AWS plugin
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

terraform {
  backend "s3" {
    bucket = "financial-tracker-tfstate-965825500656"
    key    = "prod/terraform.tfstate"
    region = "ap-southeast-1"
  }
}


# 2. Tell AWS which region to build in
provider "aws" {
  region = "ap-southeast-1" # This is the Singapore region
}



resource "aws_dynamodb_table" "financial_tracker" {
  name         = "FinancialTracker"
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

  # Add this TTL block
  ttl {
    attribute_name = "expire_at"
    enabled        = true
  }

  tags = {
    Environment = "Dev"
    Project     = "FinancialTracker"
  }
}

# Create a private container registry to store our Python Docker images
resource "aws_ecr_repository" "backend_api" {
  name                 = "financial-tracker-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true # Automatically scans Docker images for security vulnerabilities
  }

  tags = {
    Environment = "Dev"
    Project     = "FinancialTracker"
  }
}

# 1. Create an IAM Role (Security permissions for Lambda)
resource "aws_iam_role" "lambda_exec_role" {
  name = "financial_tracker_lambda_role"

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

# Attach basic CloudWatch logging permissions so Lambda can write logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Attach DynamoDB permissions so Lambda can read/write data
resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

# 2. Create the AWS Lambda Function using our ECR Docker Image
resource "aws_lambda_function" "api_backend" {
  function_name = "financial-tracker-api"
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
    Environment = "Dev"
    Project     = "FinancialTracker"
  }
}

# 1. Create the HTTP API Gateway
resource "aws_apigatewayv2_api" "http_api" {
  name          = "financial-tracker-api-gateway"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
  }

  tags = {
    Environment = "Dev"
    Project     = "FinancialTracker"
  }
}

# 2. Create the default stage (auto-deploys any changes immediately)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

# 3. Connect API Gateway to your Lambda function
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"

  integration_uri        = aws_lambda_function.api_backend.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# 4. Route all HTTP traffic (ANY path) to the Lambda integration
resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# 5. Grant API Gateway permission to trigger Lambda
resource "aws_lambda_permission" "api_gw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_backend.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# 6. Print out the public web URL when Terraform finishes
output "api_endpoint" {
  value       = aws_apigatewayv2_api.http_api.api_endpoint
  description = "The public URL for your Financial Tracker API"
}

# ==========================================
# AWS COGNITO AUTHENTICATION
# ==========================================

resource "aws_cognito_user_pool" "users" {
  name = "financial-tracker-users"

  # Allow users to sign up and log in with their email
  alias_attributes         = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  # Ensure the email attribute is required
  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
    mutable             = true
  }

  tags = {
    Environment = "Dev"
    Project     = "FinancialTracker"
  }
}

# Create an App Client for the Nuxt 4 Frontend
resource "aws_cognito_user_pool_client" "nuxt_client" {
  name         = "financial-tracker-nuxt-client"
  user_pool_id = aws_cognito_user_pool.users.id

  # Must be false for Single Page Applications (SPAs) like Vue/Nuxt
  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]
}

# Output the IDs so we can copy them into our Nuxt .env file later
output "cognito_user_pool_id" {
  value       = aws_cognito_user_pool.users.id
  description = "The ID of the Cognito User Pool"
}

output "cognito_client_id" {
  value       = aws_cognito_user_pool_client.nuxt_client.id
  description = "The ID of the Cognito App Client"
}

# ==========================================
# AUTOMATED REPORTING (SES & EVENTBRIDGE)
# ==========================================

# 1. Allow Lambda to send emails using SES
resource "aws_iam_role_policy" "lambda_ses_policy" {
  name = "lambda_ses_policy"
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

# 2. EventBridge Rule: Run at 11:59 PM on the last day of every month
resource "aws_cloudwatch_event_rule" "monthly_report_rule" {
  name                = "financial-tracker-monthly-report"
  description         = "Triggers the monthly financial report generation"
  schedule_expression = "cron(59 23 L * ? *)"
}

# 3. Connect EventBridge to your Lambda
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.monthly_report_rule.name
  target_id = "TriggerMonthlyReportLambda"
  arn       = aws_lambda_function.api_backend.arn
}

# 4. Give EventBridge permission to execute the Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_backend.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monthly_report_rule.arn
}
