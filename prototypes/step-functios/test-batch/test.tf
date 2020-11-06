provider "aws" {
  version = "~> 3.13.0"
  profile = "hsi"
  region  = "us-east-1"
}

provider "template" {
  version = "~> 2.2.0"
}

provider "archive" {
  version = "~> 2.0.0"
}

resource "aws_vpc" "selected" {
  cidr_block = "10.1.0.0/16"
}

resource "aws_subnet" "private" {
  vpc_id = aws_vpc.selected.id

  cidr_block = "10.1.1.0/24"

  tags = {
    subnet = "private"
  }
}

resource "aws_security_group" "this" {

  name   = "batch_compute_env"
  vpc_id = aws_vpc.selected.id
  
  # egress only to VPC + S3 buckets for ECR pulling/test bucket
  egress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidr_blocks = [
      aws_vpc.selected.cidr_block,
      "0.0.0.0/0"
    ]
  }
}

# Batch Service Role
resource "aws_iam_role" "aws_batch_service_role" {
  name = "aws_batch_service_role"

  assume_role_policy = <<EOF
{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "batch.amazonaws.com"
            }
        }]
}
EOF
}

resource "aws_iam_role_policy_attachment" "aws_batch_service_role" {
  role       = aws_iam_role.aws_batch_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

# Batch Instance Role
resource "aws_iam_role" "ecs_instance_role" {
  name = "ecs_instance_role"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [{
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
            "Service": "ec2.amazonaws.com"
        }
    }]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ecs_instance_policy" {
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_role_policy_attachment" "ecs_ssm_policy" {
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM"
}

resource "aws_iam_instance_profile" "ecs_instance_role" {
  name = "ecs_instance_role"
  role = aws_iam_role.ecs_instance_role.name
}

data "aws_ssm_parameter" "image_id" {
  name = "/aws/service/ecs/optimized-ami/amazon-linux-2/recommended/image_id"
}

resource "aws_launch_template" "batch_launch_template" {

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = 100
      encrypted   = true
    }
  }

  image_id = data.aws_ssm_parameter.image_id.value
}

resource "aws_batch_compute_environment" "spot" {
  compute_environment_name = "spot-fleet"

  compute_resources {
    allocation_strategy = "SPOT_CAPACITY_OPTIMIZED"

    instance_role = aws_iam_instance_profile.ecs_instance_role.arn
    instance_type = [
      "optimal",
    ]


    max_vcpus     = 16
    min_vcpus     = 2
    desired_vcpus = 4

    security_group_ids = [
      aws_security_group.this.id,
    ]

    subnets = [aws_subnet.private.id]

    type = "SPOT"

    launch_template {
      launch_template_id = aws_launch_template.batch_launch_template.id
      version            = "$Latest"
    }
  }

  service_role = aws_iam_role.aws_batch_service_role.arn
  type         = "MANAGED"
}

resource "aws_batch_job_queue" "this" {
  name     = "queue"
  state    = "ENABLED"
  priority = "1"
  compute_environments = [
    aws_batch_compute_environment.spot.arn,
  ]
}

resource "aws_batch_job_definition" "example" {
  name = "tf_test_batch_job_definition"
  type = "container"

  container_properties = <<CONTAINER_PROPERTIES
{
    "command": ["ls", "-la"],
    "image": "busybox",
    "memory": 1024,
    "vcpus": 1,
    "volumes": [
      {
        "host": {
          "sourcePath": "/tmp"
        },
        "name": "tmp"
      }
    ],
    "environment": [
        {"name": "VARNAME", "value": "VARVAL"}
    ],
    "mountPoints": [
        {
          "sourceVolume": "tmp",
          "containerPath": "/tmp",
          "readOnly": false
        }
    ],
    "ulimits": [
      {
        "hardLimit": 1024,
        "name": "nofile",
        "softLimit": 1024
      }
    ]
}
CONTAINER_PROPERTIES
}
