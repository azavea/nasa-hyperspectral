
data "archive_file" "lambdas" {
  type        = "zip"
  source_dir  = "lambdas"
  output_path = "lambdas.zip"
}

resource "aws_lambda_function" "sfn-trigger" {
  filename         = "lambdas.zip"
  function_name    = "tf-${terraform.workspace}-sfn-trigger"
  role             = aws_iam_role.iam_for_lambda.arn
  handler          = "sfn_trigger.handler"
  source_code_hash = fileexists("lambdas.zip") ? base64sha256(filebase64("lambdas.zip")) : null
  runtime          = var.runtime
  depends_on = [
    data.archive_file.lambdas,
    aws_iam_role_policy_attachment.lambda_logs
  ]
  environment {
    variables = {
      STATE_MACHINE_ARN = aws_sfn_state_machine.pipeline-state-machine.arn
    }
  }
}

resource "aws_lambda_event_source_mapping" "event_sfn_trigger_processor" {
  batch_size       = 1
  event_source_arn = aws_sqs_queue.processor_queue.arn
  enabled          = true
  function_name    = aws_lambda_function.sfn-trigger.arn
}

resource "aws_lambda_event_source_mapping" "event_sfn_trigger_activator" {
  batch_size       = 1
  event_source_arn = aws_sqs_queue.activator_queue.arn
  enabled          = true
  function_name    = aws_lambda_function.sfn-trigger.arn
}
