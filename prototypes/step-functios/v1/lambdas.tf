
data "archive_file" "lambdas" {
  type        = "zip"
  source_dir  = "lambdas"
  output_path = "lambdas.zip"
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
}
