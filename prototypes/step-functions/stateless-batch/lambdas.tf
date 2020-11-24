
data "archive_file" "lambdas" {
  type        = "zip"
  source_dir  = "lambdas"
  output_path = "lambdas.zip"
}

resource "aws_lambda_function" "pre_activator" {
  filename         = "lambdas.zip"
  function_name    = "tf-${terraform.workspace}-pre-activator"
  role             = aws_iam_role.iam_for_lambda.arn
  handler          = "pre_activator.handler"
  source_code_hash = fileexists("lambdas.zip") ? base64sha256(filebase64("lambdas.zip")) : null
  runtime          = var.runtime
  depends_on = [
    data.archive_file.lambdas,
    aws_iam_role_policy_attachment.lambda_logs
  ]
  environment {
    variables = {
      SNS_TOPIC = aws_sns_topic.activator_topic.arn
    }
  }
}

resource "aws_lambda_function" "activator" {
  filename         = "lambdas.zip"
  function_name    = "tf-${terraform.workspace}-activator"
  role             = aws_iam_role.iam_for_lambda.arn
  handler          = "activator.handler"
  source_code_hash = fileexists("lambdas.zip") ? base64sha256(filebase64("lambdas.zip")) : null
  runtime          = var.runtime
  depends_on = [
    data.archive_file.lambdas,
    aws_iam_role_policy_attachment.lambda_logs
  ]
  environment {
    variables = {
      SNS_TOPIC = aws_sns_topic.activator_topic.arn
    }
  }
}

resource "aws_lambda_function" "processor" {
  filename         = "lambdas.zip"
  function_name    = "tf-${terraform.workspace}-processor"
  role             = aws_iam_role.iam_for_lambda.arn
  handler          = "processor.handler"
  source_code_hash = fileexists("lambdas.zip") ? base64sha256(filebase64("lambdas.zip")) : null
  runtime          = var.runtime
  depends_on = [
    data.archive_file.lambdas,
    aws_iam_role_policy_attachment.lambda_logs
  ]
  environment {
    variables = {
      SNS_TOPIC = aws_sns_topic.processor_topic.arn
    }
  }
}

resource "aws_lambda_event_source_mapping" "event_source_processor" {
  batch_size        = 1
  event_source_arn  = aws_sqs_queue.processor_queue.arn
  enabled           = true
  function_name     = aws_lambda_function.processor.arn
}

resource "aws_lambda_event_source_mapping" "event_source_activator" {
  batch_size        = 1
  event_source_arn  = aws_sqs_queue.activator_queue.arn
  enabled           = true
  function_name     = aws_lambda_function.activator.arn
}
