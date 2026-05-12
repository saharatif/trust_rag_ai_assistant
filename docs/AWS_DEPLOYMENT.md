# TrustRAG — AWS Deployment Guide

## Overview

TrustRAG deploys as a containerized FastAPI application on AWS ECS Fargate, fronted by an Application Load Balancer. All infrastructure is provisioned via CloudFormation — no manual console steps required.

```
GitHub Actions
    │
    ▼
Docker Build
    │
    ▼
Push to AWS ECR
    │
    ▼
CloudFormation Deploy
    │
    ▼
ECS Fargate Service
    │
    ▼
Application Load Balancer  →  GET /health, POST /ingest, POST /chat …
    │
    ▼
CloudWatch Logs
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| AWS account | IAM user with ECR, ECS, CloudFormation, IAM, CloudWatch permissions |
| AWS CLI v2 | `aws --version` |
| Docker | `docker --version` |
| Python 3.11+ | For running tests locally before deploy |

---

## Step 1 — Configure AWS CLI

```bash
aws configure
# AWS Access Key ID:     <your key>
# AWS Secret Access Key: <your secret>
# Default region name:   us-east-1
# Default output format: json
```

Verify:

```bash
aws sts get-caller-identity
```

---

## Step 2 — Look Up Your Default VPC and Subnets

```bash
# Get your default VPC ID
aws ec2 describe-vpcs \
  --filters "Name=isDefault,Values=true" \
  --query "Vpcs[0].VpcId" \
  --output text

# Get two public subnet IDs in that VPC
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=<VPC_ID>" \
  --query "Subnets[0:2].SubnetId" \
  --output text
```

Save the VPC ID and both subnet IDs — you'll need them in Step 4.

---

## Step 3 — Create the ECR Repository and Push the Image

```bash
REGION=us-east-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/trustrag-dev"

# Authenticate Docker with ECR
aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# Build and tag the image
docker build -t trustrag:latest .
docker tag trustrag:latest "${ECR_URI}:latest"

# Create the ECR repo (first time only)
aws ecr create-repository --repository-name trustrag-dev --region $REGION

# Push
docker push "${ECR_URI}:latest"

echo "Image URI: ${ECR_URI}:latest"
```

---

## Step 4 — Fill In Deployment Parameters

Edit `infra/cloudformation/parameters.dev.json` and replace the placeholder values:

| Key | Value |
|---|---|
| `ImageUri` | Output of `echo $ECR_URI`:latest from Step 3 |
| `VpcId` | Default VPC ID from Step 2 |
| `SubnetIds` | Two subnet IDs from Step 2, comma-separated |
| `OpenAIApiKey` | Your OpenAI key |
| `PineconeApiKey` | Your Pinecone key |

Do **not** commit `parameters.dev.json` with real secrets — add it to `.gitignore` or use `REPLACE_WITH_*` placeholders in git and pass real values at deploy time.

---

## Step 5 — Deploy with CloudFormation

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/template.yml \
  --stack-name trustrag-dev \
  --parameter-overrides file://infra/cloudformation/parameters.dev.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

This creates:
- ECR repository
- ECS Fargate cluster, task definition, and service
- Application Load Balancer + target group + listener
- IAM execution role
- CloudWatch log group (`/ecs/trustrag-dev`)
- Security groups

**First deploy takes ~5 minutes.**

---

## Step 6 — Verify the Deployment

```bash
# Get the ALB DNS name
aws cloudformation describe-stacks \
  --stack-name trustrag-dev \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
  --output text
```

Then hit the health endpoint:

```bash
curl http://<ALB_DNS>/health
# {"status": "ok", "service": "TrustRAG API"}
```

---

## Step 7 — View Logs

```bash
# Stream live logs
aws logs tail /ecs/trustrag-dev --follow

# Query recent errors
aws logs filter-log-events \
  --log-group-name /ecs/trustrag-dev \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s000)
```

---

## Updating the Application

```bash
# 1. Build and push a new image
docker build -t trustrag:latest .
docker tag trustrag:latest "${ECR_URI}:latest"
docker push "${ECR_URI}:latest"

# 2. Force ECS to pull the new image
aws ecs update-service \
  --cluster trustrag-dev \
  --service trustrag-dev \
  --force-new-deployment \
  --region us-east-1
```

ECS performs a rolling deploy: new tasks start before old tasks stop, keeping the service live.

---

## Tearing Down

```bash
aws cloudformation delete-stack --stack-name trustrag-dev --region us-east-1
```

This removes all resources except the ECR images. To also clean up ECR:

```bash
aws ecr delete-repository --repository-name trustrag-dev --force --region us-east-1
```

---

## CI/CD via GitHub Actions

The `.github/workflows/ci.yml` pipeline runs automatically on push to `main`:

1. Runs all tests (`pytest`)
2. Builds the Docker image
3. On success, pushes to ECR and triggers a CloudFormation update (optional — requires GitHub Actions secrets)

Required GitHub Actions secrets:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `AWS_REGION` | `us-east-1` |
| `ECR_REPOSITORY` | Full ECR URI (without tag) |

---

## Troubleshooting

### Service stuck in PENDING

Check the ECS events:

```bash
aws ecs describe-services \
  --cluster trustrag-dev \
  --services trustrag-dev \
  --query "services[0].events[0:5]"
```

Common causes: ECR pull auth failure (re-run `aws ecr get-login-password`), or the task ran out of memory (increase `TaskMemory` in parameters).

### Health check failing

```bash
# Check container logs
aws logs tail /ecs/trustrag-dev --follow

# Verify the container starts locally
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e PINECONE_API_KEY=your-key \
  trustrag:latest
curl http://localhost:8000/health
```

### CloudFormation rollback

If a deploy rolls back, check the stack events:

```bash
aws cloudformation describe-stack-events \
  --stack-name trustrag-dev \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='UPDATE_FAILED']"
```
