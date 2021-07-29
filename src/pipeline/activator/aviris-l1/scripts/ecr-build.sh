#!/bin/bash

IMAGE_NAME="aviris-l2-${USER}:latest"
ACCOUNT_ID=$(aws sts get-caller-identity --output text --query 'Account')
AWS_REGION="us-east-1"

docker build -t ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME} .
