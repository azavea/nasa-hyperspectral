#
# Batch resources
#
# Pull the image ID for the latest Amazon ECS GPU-optimized AMI
# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html#w520aac22c15c31b5
data "aws_ssm_parameter" batch_cpu_container_instance_image_id {
  name = "/aws/service/ecs/optimized-ami/amazon-linux-2/recommended/image_id"
}

resource "aws_launch_template" "batch_cpu_container_instance" {
  name_prefix = "ltBatchCPUContainerInstance-"
}

data "aws_vpc" "sample" {
  id = var.vpc
}

data "aws_subnet" "sample" {
  id = var.subnet
}

resource "aws_security_group" "sample" {
  name = "aws_batch_compute_environment_security_group"

  vpc_id = data.aws_vpc.sample.id

  egress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_batch_compute_environment" "cpu" {
  depends_on = [aws_iam_role_policy_attachment.batch_policy]

  compute_environment_name_prefix = "batchProcessingCPU"
  type                            = "MANAGED"
  state                           = "ENABLED"
  service_role                    = aws_iam_role.container_instance_batch.arn

  compute_resources {
    type                = "SPOT"
    allocation_strategy = var.batch_cpu_ce_spot_fleet_allocation_strategy
    bid_percentage      = var.batch_cpu_ce_spot_fleet_bid_percentage
    ec2_key_pair        = var.aws_key_name
    image_id            = data.aws_ssm_parameter.batch_cpu_container_instance_image_id.value

    min_vcpus = var.batch_cpu_ce_min_vcpus
    max_vcpus = var.batch_cpu_ce_max_vcpus

    launch_template {
      launch_template_id = aws_launch_template.batch_cpu_container_instance.id
      version            = aws_launch_template.batch_cpu_container_instance.latest_version
    }

    spot_iam_fleet_role = aws_iam_role.container_instance_spot_fleet.arn
    instance_role       = aws_iam_instance_profile.container_instance.arn

    instance_type = var.batch_cpu_ce_instance_types

    security_group_ids = [aws_security_group.sample.id]

    subnets = [data.aws_subnet.sample.id]

    tags = {
      Name      = "BatchCPUWorker"
      Project   = var.project
      Performer = var.performer
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_batch_job_definition" "activator_test" {
  name = "tf_test_activator_batch_job_definition"
  type = "container"

  container_properties = <<CONTAINER_PROPERTIES
{
    "parameters": { 
      "event": "{ 'msg': 'default-test' }" 
    },
    "command": ["python", "./activator.py", "Ref::event"],
    "image": "513167130603.dkr.ecr.us-east-1.amazonaws.com/nasa-hsi-v2-batch:latest",
    "memory": 1024,
    "vcpus": 1,
    "volumes": [
      {
        "host": {
          "sourcePath": "/tmp"
        },
        "name": "tmp"
      },
      {
        "host": {
          "sourcePath": "/home/ec2-user"
        },
        "name": "home"
      }
    ],
    "environment": [
        {
            "name": "SNS_TOPIC", 
            "value": "${aws_sns_topic.processor_topic.arn}"
        }
    ],
    "mountPoints": [
        {
          "sourceVolume": "tmp",
          "containerPath": "/tmp",
          "readOnly": false
        },
        {
          "sourceVolume": "home",
          "containerPath": "/opt/data",
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

resource "aws_batch_job_definition" "processor_test" {
  name = "tf_test_processor_batch_job_definition"
  type = "container"

  container_properties = <<CONTAINER_PROPERTIES
{
    "command": ["python", "./processor.py", "Ref::event"],
    "image": "513167130603.dkr.ecr.us-east-1.amazonaws.com/nasa-hsi-v2-batch:latest",
    "memory": 1024,
    "vcpus": 1,
    "volumes": [
      {
        "host": {
          "sourcePath": "/tmp"
        },
        "name": "tmp"
      },
      {
        "host": {
          "sourcePath": "/home/ec2-user"
        },
        "name": "home"
      }
    ],
    "environment": [
        {
            "name": "SNS_TOPIC",
            "value": "${aws_sns_topic.processor_topic.arn}"
        }
    ],
    "mountPoints": [
        {
          "sourceVolume": "tmp",
          "containerPath": "/tmp",
          "readOnly": false
        },
        {
          "sourceVolume": "home",
          "containerPath": "/opt/data",
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

resource "aws_batch_job_queue" "test_queue" {
  name                 = "tf-test-batch-job-queue"
  state                = "ENABLED"
  priority             = 1
  compute_environments = [aws_batch_compute_environment.cpu.arn]
}
