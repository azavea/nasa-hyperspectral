#!/bin/bash

IMAGE_NAME="cog-clip-${USER}:latest"
ACCOUNT_ID=$(aws sts get-caller-identity --output text --query 'Account')
AWS_REGION="us-east-1"

aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "pushing: ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}"

docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}
