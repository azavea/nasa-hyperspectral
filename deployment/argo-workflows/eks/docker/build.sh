#!/bin/bash

if [[ -n "${GIT_COMMIT}" ]]; then
    GIT_COMMIT="${GIT_COMMIT:0:7}"
else
    GIT_COMMIT="$(git rev-parse --short HEAD)"
fi

# Build the COG Clip module fat assembly jar
pushd ../../../src/pipeline/activator/cog-clip
./sbt assembly
popd

pushd ../../../
# Build tagged container images
GIT_COMMIT="${GIT_COMMIT}" docker compose \
  -f docker-compose.yml \
  -f docker-compose.ci.yml \
  build activator-aviris-l2 cog-clip
popd

# Tag the Aviris L2 activator.
docker tag "activator-aviris-l2:${GIT_COMMIT}" "activator-aviris-l2:latest"

# Tag the COG Clip module.
docker tag "cog-clip:${GIT_COMMIT}" "cog-clip:latest"
