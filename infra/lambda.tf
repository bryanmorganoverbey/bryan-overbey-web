# ──────────────────────────────────────────────
# ECR Repository
# ──────────────────────────────────────────────
resource "aws_ecr_repository" "fuel_sorter" {
  name                 = "fuel-receipt-sorter"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "fuel_sorter" {
  repository = aws_ecr_repository.fuel_sorter.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ──────────────────────────────────────────────
# S3 Bucket – Lambda temp storage
# ──────────────────────────────────────────────
resource "aws_s3_bucket" "lambda_temp" {
  bucket = "${var.domain_name}-lambda-temp"
}

resource "aws_s3_bucket_public_access_block" "lambda_temp" {
  bucket = aws_s3_bucket.lambda_temp.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "lambda_temp" {
  bucket = aws_s3_bucket.lambda_temp.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "GET"]
    allowed_origins = [
      "https://${var.domain_name}",
      "https://www.${var.domain_name}",
      "http://localhost:3000",
    ]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "lambda_temp" {
  bucket = aws_s3_bucket.lambda_temp.id

  rule {
    id     = "cleanup-temp-files"
    status = "Enabled"

    filter {}

    expiration {
      days = 1
    }
  }
}

# ──────────────────────────────────────────────
# Lambda IAM Role
# ──────────────────────────────────────────────
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "fuel-receipt-sorter-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda_s3" {
  statement {
    sid    = "S3TempBucketAccess"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]

    resources = ["${aws_s3_bucket.lambda_temp.arn}/*"]
  }
}

resource "aws_iam_role_policy" "lambda_s3" {
  name   = "s3-temp-access"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_s3.json
}

# ──────────────────────────────────────────────
# Lambda Function
# ──────────────────────────────────────────────
resource "aws_lambda_function" "fuel_sorter" {
  function_name = "fuel-receipt-sorter"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.fuel_sorter.repository_url}:latest"
  timeout       = 300
  memory_size   = 1024
  architectures = ["arm64"]

  environment {
    variables = {
      TEMP_BUCKET = aws_s3_bucket.lambda_temp.id
    }
  }

  depends_on = [aws_ecr_repository.fuel_sorter]

  lifecycle {
    ignore_changes = [image_uri]
  }
}
