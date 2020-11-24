data "template_file" "pipeline" {
  template = file("step-functions/pipeline-batch.json.tmpl")

  vars = {
    activator_batch_arn = "arn:aws:states:::batch:submitJob.sync"
    job_definition_arn  = aws_batch_job_definition.activator_test.arn
    queue_arn           = aws_batch_job_queue.test_queue.arn
    processor_arn       = aws_lambda_function.processor.arn
  }
}

resource "aws_sfn_state_machine" "pipeline-state-machine" {
  name     = "tf-${terraform.workspace}-pipeline-state-machine"
  role_arn = aws_iam_role.iam_for_sfn.arn

  definition = data.template_file.pipeline.rendered
}
