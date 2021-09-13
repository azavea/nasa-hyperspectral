#!/bin/bash

if [[ -n "${GIT_COMMIT}" ]]; then
    GIT_COMMIT="${GIT_COMMIT:0:7}"
else
    GIT_COMMIT="$(git rev-parse --short HEAD)"
fi

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

# Push the Aviris activator.
docker push "${ECR_REGISTRY}/activator:${GIT_COMMIT}"
docker push "${ECR_REGISTRY}/activator:latest"

# Push the COG Clip module.
docker push "${ECR_REGISTRY}/cog-clip:${GIT_COMMIT}"
docker push "${ECR_REGISTRY}/cog-clip:latest"
