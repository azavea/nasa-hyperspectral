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
  source           = "terraform-aws-modules/eks/aws"
  cluster_name     = var.eks_cluster_name
  cluster_version  = "1.21"
  subnets          = module.vpc.private_subnet_ids
  write_kubeconfig = false

  tags = {
    Environment = "Hyperspectral"
    GithubRepo  = "nasa-hyperspectral"
    GithubOrg   = "azavea"
  }

  vpc_id = module.vpc.id

  workers_group_defaults = {
    root_volume_type = "gp2"
  }

  # https://aws.amazon.com/premiumsupport/knowledge-center/amazon-eks-cluster-access/
  map_users = local.eks_map_users

  worker_groups = [
    {
      name                          = "worker-group-spot"
      spot_price                    = var.eks_workers_spot_price
      instance_type                 = var.eks_workers_instance_type
      additional_userdata           = "workers group"
      asg_desired_capacity          = var.eks_workers_desired_capacity
      asg_max_size                  = var.eks_workers_max_size
      kubelet_extra_args            = "--node-labels=node.kubernetes.io/lifecycle=spot"
      suspended_processes           = ["AZRebalance"]
      additional_security_group_ids = [aws_security_group.worker_group_management.id]
    }
  ]

  workers_additional_policies = [
    aws_iam_policy.worker_s3_policy.arn,
    aws_iam_policy.worker_cloudwatch_policy.arn
  ]
  # https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html
  # cluster_enabled_log_types = ["api", "controllerManager", "scheduler"]
}
