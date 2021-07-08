### Argo Workflows

![Argo Workflows](https://argoproj.github.io/argo-workflows/assets/argo.png)

In all examples we use Argo Workflows 3.1.1, since we are interested in some of new argo workflows features, see https://blog.argoproj.io/argo-workflows-v3-1-is-coming-1fb1c1091324

## Argo CLI instructions

For details see: https://github.com/argoproj/argo-workflows/releases/tag/v3.1.1

### Mac

```bash
$ curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.1.1/argo-darwin-amd64.gz
$ gunzip argo-darwin-amd64.gz
$ chmod +x argo-darwin-amd64
$ mv ./argo-darwin-amd64 /usr/local/bin/argo
$ argo version
```

### Linux

```bash
$ curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.1.1/argo-darwin-amd64.gz
$ gunzip argo-linux-amd64.gz
$ chmod +x argo-linux-amd64
$ mv ./argo-linux-amd64 /usr/local/bin/argo
$ argo version
```

## K8S Cluster Access

1. ssh to `ubuntu@kube-1.internal.azavea.com` using the special key in LastPass.
2. `cat ~/.kube/config`
3. Add the cluster, context, and user listed there to your local `$HOME/.kube/config` (you can rename things during this process, i.e. into `azavea-dev`)
4. verify things are ok: `kubectl config get-contexts`, you should see the context you created
5. switch to the azavea-dev context: `kubectl config use-context azavea-dev`
6. confirm everything is correct by listing pods: `kubectl get pods -n kubernetes-dashboard`

## Argo Workflows deploy on a local K8S cluster

This is the summary of the official [Argo Workflows Quick Start](https://argoproj.github.io/argo-workflows/quick-start/).

```bash
# you should be in the azavea-dev context
# to list all contexts run kubectl config get-contexts
$ kubectl config use-context azavea-dev
# lunch argo
$ kubectl create ns argo
# install 3.1.1
$ kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo-workflows/v3.1.1/manifests/quick-start-postgres.yaml
# On GKE, you may need to grant your account the ability to create new clusterroles
# kubectl create clusterrolebinding YOURNAME-cluster-admin-binding --clusterrole=cluster-admin --user=YOUREMAIL@gmail.com
# port forwarding for the local development
$ kubectl -n argo port-forward deployment/argo-server 2746:2746

# Hello World submission
$ argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo-workflows/master/examples/hello-world.yaml
$ argo list -n argo
$ argo get -n argo @latest
$ argo logs -n argo @latest
```

WebUI access here: https://127.0.0.1:2746/

<img width="1000" alt="WebUI" src="./img/workflows.png">

#### !Warning
Argo Workflows support https only, so add your local certificate into trusted to make the endpoint work:

<img width="300" alt="MacOS Keychain Access" src="./img/keychain.png">

### Accessing the provided Minio

```bash
# info 
$ kubectl get service minio --namespace=argo
# port forward, it will generate a URI and a tunnel
$ minikube service --url minio --namespace=argo
## AccessKey: kubectl get secret my-minio-cred -o jsonpath='{.data.accesskey}' | base64 --decode
## SecretKey: kubectl get secret my-minio-cred -o jsonpath='{.data.secretkey}' | base64 --decode
```

### Configuring Minio via Helm (this step is not neccesary)

```bash
$ brew install helm # mac, helm 3.x
$ helm repo add minio https://helm.min.io/ # official minio Helm charts
$ helm repo update
$ helm install argo-artifacts minio/minio --set service.type=LoadBalancer --set fullnameOverride=argo-artifacts --namespace=argo
# info 
$ kubectl get service argo-artifacts --namespace=argo
# port forward, it will generate a URI and a tunnel
$ minikube service --url argo-artifacts --namespace=argo
## AccessKey: kubectl get secret argo-artifacts -o jsonpath='{.data.accesskey}' | base64 --decode
## SecretKey: kubectl get secret argo-artifacts -o jsonpath='{.data.secretkey}' | base64 --decode
```
