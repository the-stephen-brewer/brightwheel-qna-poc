#!/bin/bash

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Ensure required variables are set
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$AWS_REGION" ] || [ -z "$ECR_URI" ]; then
    echo "Error: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, and ECR_URI must be set in .env"
    exit 1
fi

REPO_NAME="brightwheeldemo"

# Login to ECR
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URI"

# 1. Capture the unique Git Hash
COMMIT_HASH=$(git rev-parse --short HEAD)

# 2. Build the image once
docker build -t "$REPO_NAME:$COMMIT_HASH" .

# 3. Create the 'latest' alias
docker tag "$REPO_NAME:$COMMIT_HASH" "$REPO_NAME:latest"

# 4. Push both to ECR
ECR_URL="$ECR_URI/$REPO_NAME"

docker tag "$REPO_NAME:$COMMIT_HASH" "$ECR_URL:$COMMIT_HASH"
docker tag "$REPO_NAME:$COMMIT_HASH" "$ECR_URL:latest"

docker push "$ECR_URL:$COMMIT_HASH"
docker push "$ECR_URL:latest"
