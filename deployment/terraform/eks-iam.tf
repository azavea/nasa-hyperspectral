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
  name   = "s3EksWorkerPolicy"
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
  name   = "cloudWatchEksWorkerPolicy"
  policy = data.aws_iam_policy_document.worker_cloudwatch_policy_document.json
}
