## Local Workflow

![Argo Workflows](https://argoproj.github.io/argo-workflows/assets/argo.png)

To run the workflow sample we'd need to have an active EKS k8s context with Argo Workflows installed.

```bash
# build docker images
$ ./docker/build.sh
# tag them, requires correct AWS credentials
$ ./docker/ecr-tag.sh
# cluster has access to ECR, the next step is to push images into ECR
$ ./docker/ecr-push.sh
# check that the yaml file is valid
$ argo submit workflow-one.yaml --dry-run -o yaml
$ argo submit workflow-two.yaml --dry-run -o yaml
# submit the workflow
$ argo submit -n argo workflow-one.yaml --watch 
$ argo submit -n argo workflow-two.yaml --watch 
```

### S3 Credentials configuration

Controlled via IAM roles, see [eks-iam.tf](../../terraform/eks-iam.tf)

### Configure ECR Registry Access

Controlled via default EKS IAM roles
