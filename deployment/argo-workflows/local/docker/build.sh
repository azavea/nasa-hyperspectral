#!/bin/bash

if [[ -n "${GIT_COMMIT}" ]]; then
    GIT_COMMIT="${GIT_COMMIT:0:7}"
else
    GIT_COMMIT="$(git rev-parse --short HEAD)"
fi

# Use minikube env to build containers
eval $(minikube docker-env)

# Build the COG Clip module fat assembly jar
pushd ../../../src/pipeline/cog-clip
./sbt assembly
popd

pushd ../../../
# Build tagged container images
GIT_COMMIT="${GIT_COMMIT}" docker compose \
  -f docker-compose.yml \
  -f docker-compose.ci.yml \
  build activator cog-clip
popd

# Tag the Aviris activator.
docker tag "activator:${GIT_COMMIT}" "activator:latest"

# Tag the COG Clip module.
docker tag "cog-clip:${GIT_COMMIT}" "cog-clip:latest"
