variable region {
  type    = string
  default = "us-east-1"
}

variable profile {
  type    = string
  default = "hsi"
}

variable runtime {
  type    = string
  default = "python3.6"
}

variable project {
  type    = string
  default = "HSI"
}

variable performer {
  type    = string
  default = "Azavea"
}

variable environment {
  type    = string
  default = "Staging"
}

variable aws_administrator_policy_arn {
  default = "arn:aws:iam::aws:policy/AdministratorAccess"
  type    = string
}

variable aws_ecs_task_execution_role_policy_arn {
  default = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  type    = string
}

variable aws_s3_full_access_policy_arn {
  default = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  type    = string
}

variable aws_batch_full_access_policy_arn {
  default = "arn:aws:iam::aws:policy/AWSBatchFullAccess"
  type    = string
}

variable aws_ec2_service_role_policy_arn {
  default = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
  type    = string
}

variable aws_spot_fleet_service_role_policy_arn {
  default = "arn:aws:iam::aws:policy/service-role/AmazonEC2SpotFleetTaggingRole"
  type    = string
}

variable aws_batch_service_role_policy_arn {
  default = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
  type    = string
}

variable batch_cpu_ce_spot_fleet_allocation_strategy {
  default = "SPOT_CAPACITY_OPTIMIZED"
  type    = string
}

variable aws_key_name {
  type    = string
  default = "nasa-hsi-test"
}

variable batch_cpu_ce_spot_fleet_bid_percentage {
  type    = number
  default = 100
}

variable batch_cpu_ce_min_vcpus {
  type    = number
  default = 2
}

variable batch_cpu_ce_max_vcpus {
  type    = number
  default = 16
}

variable batch_cpu_ce_instance_types {
  type    = list(string)
  default = ["c4.large"]
}

variable step_functions_batch_rule_arn {
  type    = string
  default = "arn:aws:events:us-east-1:513167130603:rule/StepFunctionsGetEventsForBatchJobsRule"
}

variable subnet {
  type    = string
  default = "subnet-0bcddfad46c72cb6a"
}

variable vpc {
  type    = string
  default = "vpc-0b653000c8e08fdb1"
}

variable sns_topic {
  type    = string
  default = "processor-topic"
}

variable sns_topic_deadletter {
  type    = string
  default = "processor-topic-deadletter"
}
