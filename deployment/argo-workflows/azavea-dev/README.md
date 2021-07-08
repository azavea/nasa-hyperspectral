## Local Workflow

![Argo Workflows](https://argoproj.github.io/argo-workflows/assets/argo.png)

To run the workflow sample we'd need to have a minikube with installed Argo Workflows.

All steps require a correctly set K8S context, for more instructions see [INSTALL.md](./INSTALL.md#k8s-cluster-access).

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

You may set it via Lens:

* namespace: **argo**
* secrets name: **s3-secrets**
  * keys:
    * **accessKey**
    * **secretAccessKey**
    * **region**

<img width="800" alt="diag" src="../local/img/s3-secrets.png">

### Configure ECR Registry Access (if unset)

#### TLDR;

Run: `./docker/k8s-ecr-secrets.sh`

#### The long read version

The idea is to set AWS secrets via:

```bash
kubectl create secret docker-registry regcred \
  --docker-server=<aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password) \
  --namespace=argo
```

In manifest that can be specified via (see [workflow-one.yaml](./workflow-one.yaml) or [workflow-two.yaml](./workflow-two.yaml) for more eaxmples):

```yaml
spec:
  containers:
    # ...
  imagePullSecrets:
      - name: regcred
```

For more details, see [https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/#registry-secret-existing-credentials](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/#registry-secret-existing-credentials)

`imagePullSecrets` can be referenced in a workflow spec, which will be carried forward to all pods
of the workflow. Note that imagePullSecrets can also be attached to a service account, see [https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#add-imagepullsecrets-to-a-service-account](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#add-imagepullsecrets-to-a-service-account).

In the dev cluster, workflow pods are launched with the default serviceaccount in the `argo` namespace:
```bash
kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "regcred"}]}' -n argo
# there is also an argo service account which also has ECR credentials set
kubectl patch serviceaccount argo -p '{"imagePullSecrets": [{"name": "regcred"}]}' -n argo
```

