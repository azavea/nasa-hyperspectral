resource "aws_cloudwatch_log_group" "pipeline-group" {
  name              = "/aws/lambda/${aws_lambda_function.activator.function_name}"
  retention_in_days = "1"
}

# resource "aws_cloudwatch_event_rule" "pipeline" {
#   name                = "pipeline"
#   schedule_expression = "rate(1 minute)"
# }

resource "aws_iam_policy" "lambda_logging" {
  name        = "lambda_logging"
  path        = "/"
  description = "IAM policy for logging from pipeline lambdas"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*",
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}

# resource "aws_cloudwatch_event_target" "health_monitor_event_target" {
#   rule     = aws_cloudwatch_event_rule.pipeline.id
#   arn      = aws_sfn_state_machine.pipeline-state-machine.id
#   role_arn = aws_iam_role.iam_for_sfn.arn
#   input    = <<EOF
#   { "msg": "test" }
# EOF
# }
