# https://github.com/hashicorp/terraform-provider-aws/blob/v3.49.0/website/docs/d/eks_cluster_auth.html.markdown
# provider "kubernetes" {
#   host                   = data.aws_eks_cluster.cluster.endpoint
#   token                  = data.aws_eks_cluster_auth.cluster.token
#   cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority.0.data)
# }

data "aws_eks_cluster" "cluster" {
  name = module.eks.cluster_id
}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_id
}

# https://github.com/terraform-aws-modules/terraform-aws-eks/blob/v18.2.6/examples/irsa_autoscale_refresh/main.tf#L119
################################################################################
# aws-auth configmap
# Only EKS managed node groups automatically add roles to aws-auth configmap
# so we need to ensure fargate profiles and self-managed node roles are added
################################################################################
data "aws_eks_cluster_auth" "this" {
  name = module.eks.cluster_id
}

locals {
  kubeconfig = yamlencode({
    apiVersion      = "v1"
    kind            = "Config"
    current-context = "terraform"
    clusters = [{
      name = module.eks.cluster_id
      cluster = {
        certificate-authority-data = module.eks.cluster_certificate_authority_data
        server                     = module.eks.cluster_endpoint
      }
    }]
    contexts = [{
      name = "terraform"
      context = {
        cluster = module.eks.cluster_id
        user    = "terraform"
      }
    }]
    users = [{
      name = "terraform"
      user = {
        token = data.aws_eks_cluster_auth.this.token
      }
    }]
  })

  current_auth_configmap = yamldecode(module.eks.aws_auth_configmap_yaml)

  updated_auth_configmap_data = {
    data = {
      # mapRoles = yamlencode(
      #   distinct(concat(
      #   yamldecode(local.current_auth_configmap.data.mapRoles), local.map_roles)
      # ))
      mapUsers = yamlencode(local.eks_map_users)
    }
  }
}

# resource "null_resource" "apply" {
#   triggers = {
#     kubeconfig = base64encode(local.kubeconfig)
#     cmd_patch  = <<-EOT
#       kubectl create configmap aws-auth -n kube-system --kubeconfig <(echo $KUBECONFIG | base64 --decode)
#       kubectl patch configmap/aws-auth --patch "${module.eks.aws_auth_configmap_yaml}" -n kube-system --kubeconfig <(echo $KUBECONFIG | base64 --decode)
#     EOT
#   }

#   provisioner "local-exec" {
#     interpreter = ["/bin/bash", "-c"]
#     environment = {
#       KUBECONFIG = self.triggers.kubeconfig
#     }
#     command = self.triggers.cmd_patch
#   }
# }

resource "null_resource" "apply" {
  triggers = {
    kubeconfig = base64encode(local.kubeconfig)
    cmd_patch  = <<-EOT
      kubectl create configmap aws-auth -n kube-system --kubeconfig <(echo $KUBECONFIG | base64 --decode)
      kubectl patch configmap/aws-auth --patch "${module.eks.aws_auth_configmap_yaml}" -n kube-system --kubeconfig <(echo $KUBECONFIG | base64 --decode)
    EOT
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    environment = {
      KUBECONFIG = self.triggers.kubeconfig
    }
    command = self.triggers.cmd_patch
  }
}