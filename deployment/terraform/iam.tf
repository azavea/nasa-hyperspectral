#
# Batch IAM resources
#
data "aws_iam_policy_document" "batch_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["batch.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "batch_service_role" {
  name               = "batchServiceRole"
  assume_role_policy = data.aws_iam_policy_document.batch_assume_role.json
}

resource "aws_iam_role_policy_attachment" "batch_service_role_policy" {
  role       = aws_iam_role.batch_service_role.name
  policy_arn = var.aws_batch_service_role_policy_arn
}

#
# Spot Fleet IAM resources
#
data "aws_iam_policy_document" "spot_fleet_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["spotfleet.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "spot_fleet_service_role" {
  name               = "fleetServiceRole"
  assume_role_policy = data.aws_iam_policy_document.spot_fleet_assume_role.json
}

resource "aws_iam_role_policy_attachment" "spot_fleet_service_role_policy" {
  role       = aws_iam_role.spot_fleet_service_role.name
  policy_arn = var.aws_spot_fleet_service_role_policy_arn
}

#
# EC2 IAM resources
#
data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ecs_instance_role" {
  name               = "ecsInstanceRole"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ec2_service_role_policy" {
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = var.aws_ec2_service_role_policy_arn
}

resource "aws_iam_instance_profile" "ecs_instance_role" {
  name = aws_iam_role.ecs_instance_role.name
  role = aws_iam_role.ecs_instance_role.name
}

data "aws_iam_policy_document" "scoped_read_write" {
  statement {
    effect = "Allow"

    resources = [
      "arn:aws:s3:::aviris-data",
      "arn:aws:s3:::aviris-data/*",
    ]

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
      "s3:PutObject",
      "s3:PutObjectAcl"
    ]
  }
}

resource "aws_iam_role_policy" "scoped_read_write" {
  name   = "s3ScopedReadWritePolicy"
  role   = aws_iam_role.ecs_instance_role.name
  policy = data.aws_iam_policy_document.scoped_read_write.json
}

#
# ECS IAM resources
#
data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = [
      "sts:AssumeRole",
    ]
  }
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name               = "ecsTaskExecutionRole"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role" "ecs_task_role" {
  name               = "ecsTaskRole"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = var.aws_ecs_task_execution_role_policy_arn
}
