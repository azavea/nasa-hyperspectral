#
# Security Group resources
#
resource "aws_security_group" "batch" {
  name   = "sgBatchContainerInstance"
  vpc_id = module.vpc.id

  tags = {
    Name        = "sgBatchContainerInstance"
    Project     = var.project
    Environment = var.environment
  }
}

# Pull the image ID for the latest Amazon ECS optimized AMI
# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html
data "aws_ssm_parameter" "batch_ami_id" {
  name = "/aws/service/ecs/optimized-ami/amazon-linux-2/recommended/image_id"
}

#
# Batch resources
#
resource "aws_launch_template" "default" {
  name_prefix = "ltBatchContainerInstance-"

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = var.batch_root_block_device_size
      volume_type = var.batch_root_block_device_type
    }
  }

  user_data = base64encode(file("cloud-config/batch-container-instance"))
}

resource "aws_batch_compute_environment" "default" {
  compute_environment_name_prefix = "batch${local.short}"
  type                            = "MANAGED"
  state                           = "ENABLED"
  service_role                    = aws_iam_role.batch_service_role.arn

  compute_resources {
    type                = "SPOT"
    allocation_strategy = var.batch_spot_fleet_allocation_strategy
    bid_percentage      = var.batch_spot_fleet_bid_percentage
    ec2_key_pair        = var.aws_key_name
    image_id            = data.aws_ssm_parameter.batch_ami_id.value

    min_vcpus = var.batch_min_vcpus
    max_vcpus = var.batch_max_vcpus

    launch_template {
      launch_template_id = aws_launch_template.default.id
      version            = aws_launch_template.default.latest_version
    }

    spot_iam_fleet_role = aws_iam_role.spot_fleet_service_role.arn
    instance_role       = aws_iam_instance_profile.ecs_instance_role.arn

    instance_type = var.batch_instance_types

    security_group_ids = [aws_security_group.batch.id]
    subnets            = module.vpc.private_subnet_ids

    tags = {
      Name        = "BatchWorker"
      Project     = var.project
      Environment = var.environment
    }
  }

  depends_on = [aws_iam_role_policy_attachment.batch_service_role_policy]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_batch_job_queue" "default" {
  name                 = "queue${local.short}"
  priority             = 1
  state                = "ENABLED"
  compute_environments = [aws_batch_compute_environment.default.arn]
}

resource "aws_batch_job_definition" "activator_aviris_l2" {
  name = "jobActivatorAvirisL2"
  type = "container"

  container_properties = templatefile("${path.module}/job-definitions/module.json.tmpl", {
    # image  = "${module.activator_aviris_l2.repository_url}:${var.image_tag}"
    image  = "513167130603.dkr.ecr.us-east-1.amazonaws.com/aviris-l2-daunnc:latest"
    vcpus  = 8
    memory = 8192

    stac_api_uri = "https://${aws_route53_record.franklin.name}"
  })
}

resource "aws_batch_job_definition" "cog_clip" {
  name = "jobCogClip"
  type = "container"

  container_properties = templatefile("${path.module}/job-definitions/module.json.tmpl", {
    # image  = "${module.cog_clip.repository_url}:${var.image_tag}"
    image  = "513167130603.dkr.ecr.us-east-1.amazonaws.com/cog-clip-daunnc:latest"
    vcpus  = 8
    memory = 8192

    stac_api_uri = "https://${aws_route53_record.franklin.name}"
  })
}
