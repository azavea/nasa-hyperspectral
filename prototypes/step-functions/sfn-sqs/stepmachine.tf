data "template_file" "pipeline" {
  template = file("step-functions/pipeline-lambda-batch.json.tmpl")

  vars = {
    batch_arn                    = "arn:aws:states:::batch:submitJob.sync"
    activator_job_definition_arn = aws_batch_job_definition.activator_test.arn
    processor_job_definition_arn = aws_batch_job_definition.processor_test.arn
    queue_arn                    = aws_batch_job_queue.test_queue.arn
    activator_queue_arn          = aws_sqs_queue.activator_queue.arn
    processor_queue_arn          = aws_sqs_queue.processor_queue.arn
  }
}

resource "aws_sfn_state_machine" "pipeline-state-machine" {
  name     = "tf-${terraform.workspace}-pipeline-state-machine"
  role_arn = aws_iam_role.iam_for_sfn.arn

  definition = data.template_file.pipeline.rendered
}
