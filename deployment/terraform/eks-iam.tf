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
