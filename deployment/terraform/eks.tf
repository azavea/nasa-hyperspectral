data "aws_availability_zones" "available" {}

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = var.eks_cluster_name
  cluster_version = "1.20"
  subnets         = module.vpc.private_subnet_ids

  tags = {
    Environment = "training"
    GithubRepo  = "terraform-aws-eks"
    GithubOrg   = "terraform-aws-modules"
  }

  vpc_id = module.vpc.id

  workers_group_defaults = {
    root_volume_type = "gp2"
  }

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

  workers_additional_policies   = [aws_iam_policy.worker_s3_policy.arn]
}

data "aws_eks_cluster" "cluster" {
  name = module.eks.cluster_id
}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_id
}
