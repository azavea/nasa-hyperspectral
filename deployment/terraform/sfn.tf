#
# Step Functions resources
#
resource "aws_sfn_state_machine" "pipeline" {
  name     = "stateMachine${local.short}Pipeline"
  role_arn = aws_iam_role.step_functions_service_role.arn

  definition = templatefile("${path.module}/step-functions/pipeline.json", {
    queue      = aws_batch_job_queue.default.arn
    region     = var.aws_region
    account_id = data.aws_caller_identity.current.account_id
  })
}
