resource "aws_sns_topic" "processor_topic" {
  name = var.sns_topic_processor
}

resource "aws_sqs_queue" "processor_queue" {
  name                      = "processor-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.processor_queue_deadletter.arn
    maxReceiveCount     = 4
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "processor_queue_deadletter" {
  name = var.sns_topic_processor_deadletter
}

# SQS subscription to receive messages from SNS
resource "aws_sns_topic_subscription" "processor_sqs_target" {
  topic_arn = aws_sns_topic.processor_topic.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.processor_queue.arn
}

# policy to allow sqs to receive sns messages
resource "aws_sqs_queue_policy" "processor_queue_policy" {
  queue_url = aws_sqs_queue.processor_queue.id

  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Id": "sqspolicy",
  "Statement": [
    {
      "Sid": "First",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.processor_queue.arn}",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "${aws_sns_topic.processor_topic.arn}"
        }
      }
    }
  ]
}
POLICY
}

resource "aws_sns_topic" "activator_topic" {
  name = var.sns_topic_activator
}

resource "aws_sqs_queue" "activator_queue" {
  name                      = "activator-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.activator_queue_deadletter.arn
    maxReceiveCount     = 4
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "activator_queue_deadletter" {
  name = var.sns_topic_activator_deadletter
}

# SQS subscription to receive messages from SNS
resource "aws_sns_topic_subscription" "activator_sqs_target" {
  topic_arn = aws_sns_topic.activator_topic.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.activator_queue.arn
}

# policy to allow sqs to receive sns messages
resource "aws_sqs_queue_policy" "activator_queue_policy" {
  queue_url = aws_sqs_queue.activator_queue.id

  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Id": "sqspolicy",
  "Statement": [
    {
      "Sid": "First",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.activator_queue.arn}",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "${aws_sns_topic.activator_topic.arn}"
        }
      }
    }
  ]
}
POLICY
}
