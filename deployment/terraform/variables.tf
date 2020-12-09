variable "project" {
  default = "NASA Hyperspectral"
  type    = string
}

locals {
  short = replace(var.project, " ", "")
}

variable "environment" {
  default = "Staging"
  type    = string
}

variable "aws_region" {
  default = "us-east-1"
  type    = string
}

variable "aws_availability_zones" {
  default = ["us-east-1a", "us-east-1b"]
  type    = list(string)
}

variable "aws_key_name" {
  type = string
}

variable "r53_private_hosted_zone" {
  type = string
}

variable "r53_public_hosted_zone" {
  type = string
}

variable "vpc_cidr_block" {
  default = "10.0.0.0/16"
  type    = string
}

variable "external_access_cidr_block" {
  type = string
}

variable "vpc_private_subnet_cidr_blocks" {
  default = ["10.0.1.0/24", "10.0.3.0/24"]
  type    = list(string)
}

variable "vpc_public_subnet_cidr_blocks" {
  default = ["10.0.0.0/24", "10.0.2.0/24"]
  type    = list(string)
}

variable "bastion_ami" {
  type = string
}

variable "bastion_instance_type" {
  default = "t3.nano"
  type    = string
}

variable "bastion_ebs_optimized" {
  default = true
  type    = bool
}

variable "rds_allocated_storage" {
  default = 32
  type    = number
}

variable "rds_engine_version" {
  default = 12.4
  type    = number
}

variable "rds_parameter_group_family" {
  default = "postgres12"
  type    = string
}

variable "rds_instance_type" {
  default = "db.t3.micro"
  type    = string
}

variable "rds_storage_type" {
  default = "gp2"
  type    = string
}

variable "rds_database_identifier" {
  type = string
}

variable "rds_database_name" {
  type = string
}

variable "rds_database_username" {
  type = string
}

variable "rds_database_password" {
  type = string
}

variable "rds_backup_retention_period" {
  default = 30
  type    = number
}

variable "rds_backup_window" {
  default = "04:00-04:30"
  type    = string
}

variable "rds_maintenance_window" {
  default = "sun:04:30-sun:05:30"
  type    = string
}

variable "rds_auto_minor_version_upgrade" {
  default = true
  type    = bool
}

variable "rds_final_snapshot_identifier" {
  default = "nasahyperspectral-rds-snapshot"
  type    = string
}

variable "rds_monitoring_interval" {
  default = 60
  type    = number
}

variable "rds_skip_final_snapshot" {
  default = false
  type    = bool
}

variable "rds_copy_tags_to_snapshot" {
  default = true
  type    = bool
}

variable "rds_multi_az" {
  default = false
  type    = bool
}

variable "rds_storage_encrypted" {
  default = false
  type    = bool
}

variable "rds_deletion_protection" {
  default = true
  type    = bool
}

variable "rds_log_min_duration_statement" {
  default = 500
  type    = number
}

variable "rds_log_connections" {
  default = 0
  type    = number
}

variable "rds_log_disconnections" {
  default = 0
  type    = number
}

variable "rds_log_lock_waits" {
  default = 1
  type    = number
}

variable "rds_log_temp_files" {
  default = 500
  type    = number
}

variable "rds_log_autovacuum_min_duration" {
  default = 250
  type    = number
}

variable "rds_cpu_threshold_percent" {
  default = 75
  type    = number
}

variable "rds_disk_queue_threshold" {
  default = 10
  type    = number
}

variable "rds_free_disk_threshold_bytes" {
  default = 5000000000
  type    = number
}

variable "rds_free_memory_threshold_bytes" {
  default = 128000000
  type    = number
}

variable "rds_cpu_credit_balance_threshold" {
  default = 30
  type    = number
}

variable "batch_root_block_device_size" {
  default = 32
  type    = number
}

variable "batch_root_block_device_type" {
  default = "gp3"
  type    = string
}

variable "batch_spot_fleet_allocation_strategy" {
  default = "SPOT_CAPACITY_OPTIMIZED"
  type    = string
}

variable "batch_spot_fleet_bid_percentage" {
  default = 64
  type    = number
}

variable "batch_min_vcpus" {
  default = 0
  type    = number
}

variable "batch_max_vcpus" {
  default = 256
  type    = number
}

variable "batch_instance_types" {
  default = ["c5d", "m5d"]

  type = list(string)
}

variable "fargate_platform_version" {
  default = "1.4.0"
}

variable "franklin_desired_count" {
  type = number
}

variable "franklin_deployment_min_percent" {
  type = number
}

variable "franklin_deployment_max_percent" {
  type = number
}

variable "franklin_image_tag" {
  type = string
}

variable "franklin_cpu" {
  type = number
}

variable "franklin_memory" {
  type = number
}

variable "aws_batch_service_role_policy_arn" {
  default = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
  type    = string
}

variable "aws_spot_fleet_service_role_policy_arn" {
  default = "arn:aws:iam::aws:policy/service-role/AmazonEC2SpotFleetTaggingRole"
  type    = string
}

variable "aws_ec2_service_role_policy_arn" {
  default = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
  type    = string
}

variable "aws_ecs_task_execution_role_policy_arn" {
  default = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  type    = string
}
