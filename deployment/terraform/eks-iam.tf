data "aws_iam_policy_document" "worker_s3_policy_document" {
  statement {
    effect = "Allow"

    resources = [
      "arn:aws:s3:::*"
    ]

    actions = [
      "s3:*"
    ]
  }
}

resource "aws_iam_policy" "worker_s3_policy" {
  name   = "s3EksWorkerPolicy-migration"
  policy = data.aws_iam_policy_document.worker_s3_policy_document.json
}

data "aws_iam_policy_document" "worker_cloudwatch_policy_document" {
  statement {
    effect = "Allow"

    resources = [ "*" ]

    actions = [
      "cloudwatch:PutMetricData",
      "ec2:DescribeVolumes",
      "ec2:DescribeTags",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
      "logs:DescribeLogGroups",
      "logs:CreateLogStream",
      "logs:CreateLogGroup"
    ]
  }
}

resource "aws_iam_policy" "worker_cloudwatch_policy" {
  name   = "cloudWatchEksWorkerPolicy-migration"
  policy = data.aws_iam_policy_document.worker_cloudwatch_policy_document.json
}

# References to resources that do not exist yet when creating a cluster will cause a plan failure due to https://github.com/hashicorp/terraform/issues/4149
# There are two options users can take
# 1. Create the dependent resources before the cluster => `terraform apply -target <your policy or your security group> and then `terraform apply`
#   Note: this is the route users will have to take for adding additonal security groups to nodes since there isn't a separate "security group attachment" resource
# 2. For addtional IAM policies, users can attach the policies outside of the cluster definition as demonstrated below
resource "aws_iam_role_policy_attachment" "self_managed_node_groups_worker_s3" {
  for_each   = module.eks.self_managed_node_groups

  policy_arn = aws_iam_policy.worker_s3_policy.arn
  role       = each.value.iam_role_name
}

resource "aws_iam_role_policy_attachment" "self_managed_node_groups_worker_cloudwatch" {
  for_each   = module.eks.self_managed_node_groups

  policy_arn = aws_iam_policy.worker_cloudwatch_policy.arn
  role       = each.value.iam_role_name
}

# https://github.com/terraform-aws-modules/terraform-aws-eks/blob/v17.1.0/docs/autoscaling.md
resource "aws_iam_role_policy_attachment" "workers_autoscaling" {
  for_each   = module.eks.self_managed_node_groups

  policy_arn = aws_iam_policy.worker_autoscaling.arn
  role       = each.value.iam_role_name
}

resource "aws_iam_policy" "worker_autoscaling" {
  name_prefix = "eks-worker-autoscaling-${module.eks.cluster_id}"
  description = "EKS worker node autoscaling policy for cluster ${module.eks.cluster_id}"
  policy      = data.aws_iam_policy_document.worker_autoscaling.json
  path        = "/"
  tags = {
    Name        = "EKSAutoScaledWorker"
    Project     = var.project
  }
}

data "aws_iam_policy_document" "worker_autoscaling" {
  statement {
    sid    = "eksWorkerAutoscalingAllmigration"
    effect = "Allow"

    actions = [
      "autoscaling:DescribeAutoScalingGroups",
      "autoscaling:DescribeAutoScalingInstances",
      "autoscaling:DescribeLaunchConfigurations",
      "autoscaling:DescribeTags",
      "ec2:DescribeLaunchTemplateVersions",
    ]

    resources = ["*"]
  }

  statement {
    sid    = "eksWorkerAutoscalingOwnmigration"
    effect = "Allow"

    actions = [
      "autoscaling:SetDesiredCapacity",
      "autoscaling:TerminateInstanceInAutoScalingGroup",
      "autoscaling:UpdateAutoScalingGroup",
    ]

    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "autoscaling:ResourceTag/kubernetes.io/cluster/${module.eks.cluster_id}"
      values   = ["owned"]
    }

    condition {
      test     = "StringEquals"
      variable = "autoscaling:ResourceTag/k8s.io/cluster-autoscaler/enabled"
      values   = ["true"]
    }
  }
}
