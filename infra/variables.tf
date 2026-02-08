variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Name of the S3 bucket for the static site"
  type        = string
  default     = "bryanoverbey-com-website"
}

variable "domain_name" {
  description = "Root domain name for the site"
  type        = string
  default     = "bryanoverbey.com"
}

variable "github_repo" {
  description = "GitHub repository in owner/repo format"
  type        = string
  default     = "bryanmorganoverbey/bryan-overbey-web"
}
