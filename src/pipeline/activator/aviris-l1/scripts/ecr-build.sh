#!/bin/bash

IMAGE_NAME="aviris-l2-${USER}:latest"
ACCOUNT_ID=$(aws sts get-caller-identity --output text --query 'Account')
AWS_REGION="us-east-1"

# Temporarily copy the activator_utils module into the current directory, to 
# handle the fact that activator_utils is in a parent directory which isn't 
# available in the Docker context.
cp -R ../activator_utils/ ./activator_utils/
docker build -t ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME} .
rm -R ./activator_utils/