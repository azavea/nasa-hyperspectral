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

## K8S Cluster provisioning

EKS is provisioned via terraform, for more details see [deployment/terraform/eks-*.tf](../../terraform) files.

## K8S Cluster Access

1. Install [iam-authenticator](https://docs.aws.amazon.com/eks/latest/userguide/install-aws-iam-authenticator.html) via `brew install aws-iam-authenticator`
2. Run `aws eks --region us-east-1 update-kubeconfig --name hsi-spot` to retrieve kubeconfig

## Argo Workflows deploy on EKS

This is the summary of the official [Argo Workflows Quick Start](https://argoproj.github.io/argo-workflows/quick-start/).

```bash
# retrieve kubeconfig 
$ aws eks --region us-east-1 update-kubeconfig --name hsi-spot
# to list all contexts run kubectl config get-contexts
$ kubectl config use-context eks_hsi-spot
# lunch argo
$ kubectl create ns argo
# install 3.1.1
$ kubectl apply -n argo -f install-argo.yaml
# port forwarding for the local development
$ kubectl -n argo port-forward deployment/argo-server 2746:2746

# Hello World submission
$ argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo-workflows/master/examples/hello-world.yaml
$ argo list -n argo
$ argo get -n argo @latest
$ argo logs -n argo @latest
```

WebUI access here: https://127.0.0.1:2746/

<img width="1000" alt="WebUI" src="https://github.com/azavea/pipeline-playground/raw/main/argo-workflows/img/workflows.png">

#### !Warning
Argo Workflows support https only, so add your local certificate into trusted to make the endpoint work:

<img width="300" alt="MacOS Keychain Access" src="https://github.com/azavea/pipeline-playground/raw/main/argo-workflows/img/keychain.png">

## CloudWatch Conatiner Insight

For more details check out AWS [Container Insights setup metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-setup-metrics.html) doc page.

EKS Quick start is [here](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-setup-EKS-quickstart.html):

0.x Current EKS CloudWatch Conatiner Insight Deployment

```bash
cat install-cw-container-insight.yaml | sed "s/{{cluster_name}}/hsi-spot/;s/{{region_name}}/us-east-1/" | kubectl apply -f -
```

0.1.x Quick Start with the CloudWatch agent and Fluentd (in case you want to skip all steps below)

curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml | sed "s/{{cluster_name}}/hsi-spot/;s/{{region_name}}/us-east-1/" | kubectl apply -f -

1. Create CloudWatch namespace

```bash
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cloudwatch-namespace.yaml
```

2. Create CloudWatch Service Account

```bash
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-serviceaccount.yaml
```

3. Create CloudWatch agent config map

```bash
curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-configmap.yaml | sed "s/{{cluster_name}}/hsi-spot/;s/{{region_name}}/us-east-1/" | kubectl apply -f -
```

4. Deploy the CloudWatch agent as a DaemonSet

```bash
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-daemonset.yaml
```