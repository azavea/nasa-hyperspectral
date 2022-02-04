data "aws_availability_zones" "available" { }

locals {
  eks_aws_iam_users = concat(data.aws_iam_group.engineers.users, data.aws_iam_group.operations.users)

  eks_map_users = [for u in local.eks_aws_iam_users : {
     userarn  = u.arn
     username = u.user_name
     groups   = ["system:masters"]
   }
  ]
}

module "eks" {
  version          = "18.2.6"
  source           = "terraform-aws-modules/eks/aws"
  cluster_name     = var.eks_cluster_name
  cluster_version  = "1.21"
  subnet_ids       = module.vpc.private_subnet_ids

  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true

  tags = {
    Environment = "Hyperspectral"
    GithubRepo  = "nasa-hyperspectral"
    GithubOrg   = "azavea"
  }

  vpc_id = module.vpc.id

  # enable_irsa = true

  # workers_group_defaults = {
  #   root_volume_type = "gp2"
  # }

  # self_managed_node_group_defaults = {
  #   root_volume_type = "gp2"
  # }

  # https://aws.amazon.com/premiumsupport/knowledge-center/amazon-eks-cluster-access/
  # map_users = local.eks_map_users

  self_managed_node_groups = {
    single-pool = {
      name                   = "worker-small-group-spot"
      max_price              = "0.0068"
      instance_type          = "t3.small"
      additional_userdata    = "workers group"
      desired_capacity       = "1"
      min_size               = "1"
      max_size               = "1"
      bootstrap_extra_args   = "--kubelet-extra-args '--node-labels=node.kubernetes.io/lifecycle=spot'"
      suspended_processes    = ["AZRebalance"]
      vpc_security_group_ids = [aws_security_group.worker_group_management.id]
      block_device_mappings  = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            delete_on_termination = true
            encrypted             = false
            volume_size           = 100
            volume_type           = "gp2"
          }

        }
      }
    }

    workers-pool = {
      name                   = "worker-group-spot"
      max_price              = var.eks_workers_spot_price
      instance_type          = var.eks_workers_instance_type
      additional_userdata    = "workers group"
      desired_capacity       = var.eks_workers_desired_capacity
      min_size               = var.eks_workers_min_size
      max_size               = var.eks_workers_max_size
      bootstrap_extra_args   = "--kubelet-extra-args '--node-labels=node.kubernetes.io/lifecycle=spot'"
      suspended_processes    = ["AZRebalance"]
      vpc_security_group_ids = [aws_security_group.worker_group_management.id]
      propogate_tags         = [
        {
          "key"                 = "k8s.io/cluster-autoscaler/enabled"
          "propagate_at_launch" = "false"
          "value"               = "true"
        },
        {
          "key"                 = "k8s.io/cluster-autoscaler/${var.eks_cluster_name}"
          "propagate_at_launch" = "false"
          "value"               = "owned"
        }
      ]
      block_device_mappings  = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            delete_on_termination = true
            encrypted             = false
            volume_size           = 100
            volume_type           = "gp2"
          }
        }
      }
    }
  }

  self_managed_node_group_defaults = {
    iam_role_additional_policies = [
      "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
    ]
  }
  # self_managed_node_group_defaults = {
  #   iam_role_additional_policies = [
  #     aws_iam_policy.worker_s3_policy.arn,
  #     aws_iam_policy.worker_cloudwatch_policy.arn
  #   ]
  # }

  # workers_additional_policies = [
  #   aws_iam_policy.worker_s3_policy.arn,
  #   aws_iam_policy.worker_cloudwatch_policy.arn
  # ]
  # https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html
  # cluster_enabled_log_types = ["api", "controllerManager", "scheduler"]
}
