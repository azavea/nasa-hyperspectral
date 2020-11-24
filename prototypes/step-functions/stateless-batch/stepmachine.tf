data "template_file" "pipeline" {
  template = file("step-functions/pipeline-lambda.json.tmpl")

  vars = {
    pre_activator_lambda_arn = aws_lambda_function.pre_activator.arn
  }
}

resource "aws_sfn_state_machine" "pipeline-state-machine" {
  name     = "tf-${terraform.workspace}-pipeline-state-machine"
  role_arn = aws_iam_role.iam_for_sfn.arn

  definition = data.template_file.pipeline.rendered
}
