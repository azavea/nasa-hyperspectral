## Local Workflow

![Argo Workflows](https://argoproj.github.io/argo-workflows/assets/argo.png)

To run the workflow sample we'd need to have a minikube with installed Argo Workflows.

```bash
# build docker images
$ ./docker/build.sh
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

For more details see [k8s docs](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/#registry-secret-existing-credentials).
