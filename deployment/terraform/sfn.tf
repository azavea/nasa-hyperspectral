# #
# # Step Functions resources
# #
# resource "aws_sfn_state_machine" "pipeline-choice" {
#   name     = "stateMachine${local.short}PipelineChoice"
#   role_arn = aws_iam_role.step_functions_service_role.arn

#   definition = templatefile("${path.module}/step-functions/pipeline-choice.json", {
#     batch_arn      = "arn:aws:states:::batch:submitJob.sync"
#     queue          = aws_batch_job_queue.default.arn
#     activator_name = aws_batch_job_definition.activator_aviris_l2.name
#     cog_clip_name  = aws_batch_job_definition.cog_clip.name
#   })
# }
