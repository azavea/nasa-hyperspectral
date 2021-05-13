#
# S3 resources
#
resource "aws_s3_bucket" "data" {
  bucket = "${lower(replace(var.project, " ", ""))}-${lower(var.environment)}-data-${var.aws_region}"

  tags = {
    Name        = "${lower(replace(var.project, " ", ""))}-${lower(var.environment)}-data-${var.aws_region}"
    Project     = var.project
    Environment = var.environment
  }
}

#
# ECR resources
#
module "activator_aviris_l2" {
  source = "github.com/azavea/terraform-aws-ecr-repository?ref=1.0.0"

  repository_name         = "activator-aviris-l2"
  attach_lifecycle_policy = true
}

module "cog_clip" {
  source = "github.com/azavea/terraform-aws-ecr-repository?ref=1.0.0"

  repository_name         = "cog-clip"
  attach_lifecycle_policy = true
}
