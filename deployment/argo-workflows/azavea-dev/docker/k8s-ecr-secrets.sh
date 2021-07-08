#!/bin/bash

function amazon_ecr_login() {
    # Retrieves a temporary authorization token that can be used to access
    # Amazon ECR, along with the registry URL.
    read -r AUTHORIZATION_TOKEN ECR_REGISTRY \
        <<<"$(aws ecr get-authorization-token \
            --output "text" \
            --query "authorizationData[0].[authorizationToken, proxyEndpoint]")"

    # The authorization token is base64 encoded, and we need to strip the
    # protocol from the registry URL.
    AUTHORIZATION_TOKEN="$(echo "${AUTHORIZATION_TOKEN}" | base64 -d)"
    ECR_REGISTRY="${ECR_REGISTRY##*://}"

    # Authenticate to the ECR registry. The authorization token is presented in
    # the format user:password.
    echo "${AUTHORIZATION_TOKEN##*:}" |
        docker login \
            --username "${AUTHORIZATION_TOKEN%%:*}" \
            --password-stdin "${ECR_REGISTRY}"
}

# Login to Amazon ECR with the local Docker client.
amazon_ecr_login

kubectl create secret docker-registry regcred \
  --docker-server=${ECR_REGISTRY} \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password) \
  --namespace=argo
