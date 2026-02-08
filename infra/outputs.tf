output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.site.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.site.arn
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.site.id
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.site.domain_name
}

output "website_url" {
  description = "URL of the deployed website"
  value       = "https://${var.domain_name}"
}

output "route53_zone_id" {
  description = "Route 53 hosted zone ID"
  value       = aws_route53_zone.site.zone_id
}

output "route53_nameservers" {
  description = "Nameservers to configure at your domain registrar"
  value       = aws_route53_zone.site.name_servers
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions to assume"
  value       = aws_iam_role.github_actions.arn
}

output "github_actions_terraform_role_arn" {
  description = "IAM role ARN for GitHub Actions to run Terraform"
  value       = aws_iam_role.github_actions_terraform.arn
}

output "ecr_repository_url" {
  description = "ECR repository URL for the Lambda container image"
  value       = aws_ecr_repository.fuel_sorter.repository_url
}

output "api_url" {
  description = "API Gateway URL"
  value       = "https://api.${var.domain_name}"
}

output "lambda_temp_bucket" {
  description = "S3 bucket for Lambda temp file storage"
  value       = aws_s3_bucket.lambda_temp.id
}
