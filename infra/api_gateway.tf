# ──────────────────────────────────────────────
# API Gateway HTTP API
# ──────────────────────────────────────────────
resource "aws_apigatewayv2_api" "fuel_sorter" {
  name          = "fuel-receipt-sorter-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = [
      "https://${var.domain_name}",
      "https://www.${var.domain_name}",
      "http://localhost:3000",
    ]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 3600
  }
}

# ──────────────────────────────────────────────
# Lambda Integration
# ──────────────────────────────────────────────
resource "aws_apigatewayv2_integration" "fuel_sorter" {
  api_id                 = aws_apigatewayv2_api.fuel_sorter.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.fuel_sorter.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.fuel_sorter.id
  route_key = "GET /api/health"
  target    = "integrations/${aws_apigatewayv2_integration.fuel_sorter.id}"
}

resource "aws_apigatewayv2_route" "upload_url" {
  api_id    = aws_apigatewayv2_api.fuel_sorter.id
  route_key = "GET /api/upload-url"
  target    = "integrations/${aws_apigatewayv2_integration.fuel_sorter.id}"
}

resource "aws_apigatewayv2_route" "process_s3" {
  api_id    = aws_apigatewayv2_api.fuel_sorter.id
  route_key = "POST /api/process-s3"
  target    = "integrations/${aws_apigatewayv2_integration.fuel_sorter.id}"
}

resource "aws_apigatewayv2_route" "process" {
  api_id    = aws_apigatewayv2_api.fuel_sorter.id
  route_key = "POST /api/process"
  target    = "integrations/${aws_apigatewayv2_integration.fuel_sorter.id}"
}

# ──────────────────────────────────────────────
# Stage (auto-deploy)
# ──────────────────────────────────────────────
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.fuel_sorter.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      method         = "$context.httpMethod"
      path           = "$context.path"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      latency        = "$context.integrationLatency"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/fuel-receipt-sorter"
  retention_in_days = 14
}

# ──────────────────────────────────────────────
# Lambda Permission – allow API Gateway to invoke
# ──────────────────────────────────────────────
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fuel_sorter.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.fuel_sorter.execution_arn}/*/*"
}

# ──────────────────────────────────────────────
# Custom Domain – api.bryanoverbey.com
# ──────────────────────────────────────────────
resource "aws_apigatewayv2_domain_name" "api" {
  domain_name = "api.${var.domain_name}"

  domain_name_configuration {
    certificate_arn = aws_acm_certificate_validation.site.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_apigatewayv2_api_mapping" "api" {
  api_id      = aws_apigatewayv2_api.fuel_sorter.id
  domain_name = aws_apigatewayv2_domain_name.api.id
  stage       = aws_apigatewayv2_stage.default.id
}

# ──────────────────────────────────────────────
# Route 53 – api.bryanoverbey.com → API Gateway
# ──────────────────────────────────────────────
resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.site.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}
