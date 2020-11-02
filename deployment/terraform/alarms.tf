resource "aws_sns_topic" "global" {
  name = "topic${replace(var.project, " ", "")}GlobalNotifications"
}
