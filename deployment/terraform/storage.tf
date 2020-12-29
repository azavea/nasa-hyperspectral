module "activator_aviris_l2" {
  source = "github.com/azavea/terraform-aws-ecr-repository?ref=1.0.0"

  repository_name         = "activator-aviris-l2"
  attach_lifecycle_policy = true
}
