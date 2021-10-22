## Local Workflow

![Argo Workflows](https://argoproj.github.io/argo-workflows/assets/argo.png)

### Get Started

* Install [Docker](https://www.docker.com/) of the latest version
* Install [Kubectl](https://kubernetes.io/docs/tasks/tools/) of the latest version
  * (Optionally) Install [K8S Lens](https://k8slens.dev/) to simplify work with K8S cluster
* Install [Argo CLI](https://github.com/argoproj/argo-workflows/releases/tag/v3.2.2) of the latest version
* Install [iam-authenticator](https://docs.aws.amazon.com/eks/latest/userguide/install-aws-iam-authenticator.html)
  * Run `aws eks --region us-east-1 update-kubeconfig --name hsi-spot` to retrieve kubeconfig
* Switch the K8S context to point to the EKS cluster via
  * * `kubectl config use-context eks_hsi-spot`
* Port forward ArgoWorkflows UI:
  * `kubectl -n argo port-forward deployment/argo-server 2746:2746`
  * Page would be accesible by the address [https://localhost:2746/](https://localhost:2746/)
* Run the Argo Submit command: 
  * `argo submit -n argo workflow-aviris-l1-scene-id-gtiff.yaml -p 'activator-input=["aviris_f130329t01p00r06_sc01"]' --watch`
  * watch will attatch the argo cli output to the terminal session

For more details read [INSTALL.md](./INSTALL.md)


### More examples

To run examples below we'd need to have an active EKS K8S context with Argo Workflows installed.

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

# syntax to pass input parameters (optional, can be replaced directly in the yaml file)
$ argo submit -n argo workflow-aviris-l1-scene-id.yaml -p 'activator-input=["aviris_f130329t01p00r06_sc01"]' --watch

$ argo submit -n argo workflow-sentinel-2s-scene-id.yaml -p 'activator-input=["S2B_23XNK_20210819_0_L2A"]' --watch
```

### S3 Credentials configuration

Controlled via IAM roles, see [eks-iam.tf](../../terraform/eks-iam.tf)

### Configure ECR Registry Access

Controlled via default EKS IAM roles
