# ──────────────────────────────────────────────
# GitHub OIDC Identity Provider
# ──────────────────────────────────────────────
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

# ──────────────────────────────────────────────
# IAM Role for GitHub Actions
# ──────────────────────────────────────────────
data "aws_iam_policy_document" "github_actions_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "github-actions-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume.json
}

# ──────────────────────────────────────────────
# IAM Policy – frontend deploy (S3 + CloudFront)
# ──────────────────────────────────────────────
data "aws_iam_policy_document" "github_actions_deploy" {
  # S3: sync site files
  statement {
    sid    = "S3DeployAccess"
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.site.arn,
      "${aws_s3_bucket.site.arn}/*",
    ]
  }

  # CloudFront: invalidate cache
  statement {
    sid    = "CloudFrontInvalidation"
    effect = "Allow"

    actions = [
      "cloudfront:CreateInvalidation",
      "cloudfront:GetInvalidation",
    ]

    resources = [aws_cloudfront_distribution.site.arn]
  }
}

resource "aws_iam_role_policy" "github_actions_deploy" {
  name   = "deploy-frontend"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_deploy.json
}

# ──────────────────────────────────────────────
# IAM Policy – backend deploy (ECR + Lambda)
# ──────────────────────────────────────────────
data "aws_iam_policy_document" "github_actions_backend" {
  # ECR: push container images
  statement {
    sid    = "ECRAuth"
    effect = "Allow"

    actions = [
      "ecr:GetAuthorizationToken",
    ]

    resources = ["*"]
  }

  statement {
    sid    = "ECRPush"
    effect = "Allow"

    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
    ]

    resources = [aws_ecr_repository.fuel_sorter.arn]
  }

  # Lambda: update function code
  statement {
    sid    = "LambdaUpdate"
    effect = "Allow"

    actions = [
      "lambda:UpdateFunctionCode",
      "lambda:GetFunction",
    ]

    resources = [aws_lambda_function.fuel_sorter.arn]
  }
}

resource "aws_iam_role_policy" "github_actions_backend" {
  name   = "deploy-backend"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_backend.json
}

# ──────────────────────────────────────────────
# IAM Role for GitHub Actions – Terraform
# ──────────────────────────────────────────────
resource "aws_iam_role" "github_actions_terraform" {
  name               = "github-actions-terraform"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume.json
}

data "aws_iam_policy_document" "github_actions_terraform" {
  statement {
    sid    = "TerraformInfraAccess"
    effect = "Allow"

    actions = [
      "s3:*",
      "cloudfront:*",
      "route53:*",
      "acm:*",
      "apigateway:*",
      "lambda:*",
      "ecr:*",
      "iam:*",
      "logs:*",
      "dynamodb:*",
      "sts:GetCallerIdentity",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_actions_terraform" {
  name   = "terraform-infra"
  role   = aws_iam_role.github_actions_terraform.id
  policy = data.aws_iam_policy_document.github_actions_terraform.json
}
