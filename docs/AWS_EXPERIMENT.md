# TrustRAG — AWS Experiment Report

**Purpose:** Experimental deployment of TrustRAG to AWS for validation purposes.  
**Status:** Torn down (all resources deleted to avoid ongoing charges).  
**Date:** 2026-05-12  
**Account ID:** 832496386138  
**Region:** us-east-1

---

## Resources Used

### 1. Amazon ECR — Elastic Container Registry

**What it is:** Private Docker image registry hosted on AWS.

**How we used it:**
- Created repository `trustrag-dev` manually via CLI before CloudFormation deployment
- Built the TrustRAG Docker image locally and pushed it to ECR
- ECS pulled the image from ECR to run the container

**CLI commands used:**
```bash
aws ecr create-repository --repository-name trustrag-dev --region us-east-1
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 832496386138.dkr.ecr.us-east-1.amazonaws.com
docker build --platform linux/amd64 -t trustrag:latest .
docker tag trustrag:latest 832496386138.dkr.ecr.us-east-1.amazonaws.com/trustrag-dev:latest
docker push 832496386138.dkr.ecr.us-east-1.amazonaws.com/trustrag-dev:latest
```

**Estimated cost:** ~$0.06/month (573MB storage across 2 images)

---

### 2. AWS ECS Fargate — Elastic Container Service

**What it is:** Serverless container runtime — runs Docker containers without managing EC2 instances.

**How we used it:**
- Created an ECS Cluster (`trustrag-dev`) via CloudFormation
- Defined a Task Definition specifying the container image, CPU (0.5 vCPU), memory (1024MB), port (8000), and environment variables (OpenAI/Pinecone keys)
- Created an ECS Service that kept 1 task running at all times
- Task ran: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`

**Estimated cost:** ~$15–18/month (0.5 vCPU + 1GB RAM, 24/7)

---

### 3. Application Load Balancer (ALB)

**What it is:** Managed HTTP load balancer that routes public traffic to ECS tasks.

**How we used it:**
- Created via CloudFormation: `trustrag-alb-dev`
- Listener on port 80 forwarded traffic to the ECS target group
- Health checks hit `GET /health` every 30 seconds to verify the container was alive
- Public DNS: `trustrag-alb-dev-902053372.us-east-1.elb.amazonaws.com`
- Live endpoint confirmed working: `{"status":"ok","service":"TrustRAG API"}`

**Estimated cost:** ~$16–18/month (ALB base + LCU charges)

---

### 4. AWS CloudFormation

**What it is:** Infrastructure-as-code service — provisions and manages AWS resources from a YAML template.

**How we used it:**
- Template: `infra/cloudformation/template.yml`
- Parameters: `infra/cloudformation/parameters.dev.json`
- Stack name: `trustrag-dev`
- Single command to deploy all resources:

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/template.yml \
  --stack-name trustrag-dev \
  --parameter-overrides file://infra/cloudformation/parameters.dev.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

**Resources provisioned by CloudFormation:**
- ECS Cluster, Task Definition, Service
- ALB + Target Group + HTTP Listener
- IAM Execution Role
- CloudWatch Log Group
- Security Groups (ALB + App)

**Estimated cost:** Free (CloudFormation itself has no charge)

---

### 5. IAM — Identity and Access Management

**What it is:** AWS permissions and roles system.

**How we used it:**
- Created IAM user `trustrag-deploy` with programmatic access
- Attached policies: `AmazonEC2ContainerRegistryFullAccess`, `AmazonECS_FullAccess`, `AWSCloudFormationFullAccess`, `IAMFullAccess`, `CloudWatchLogsFullAccess`, `AmazonEC2FullAccess`
- CloudFormation created an ECS Task Execution Role allowing ECS to pull from ECR and write to CloudWatch

**Estimated cost:** Free

---

### 6. Amazon CloudWatch Logs

**What it is:** Centralised log storage and monitoring.

**How we used it:**
- Log group: `/ecs/trustrag-dev` with 30-day retention
- All `uvicorn` and application logs streamed here automatically
- Used to diagnose container failures (exec format error, database errors)

```bash
aws logs tail /ecs/trustrag-dev --follow
```

**Estimated cost:** ~$0.50/month

---

### 7. VPC, Subnets, Security Groups

**What it is:** Virtual network layer for AWS resources.

**How we used it:**
- Used the default VPC (`vpc-0e19f019a91f54c74`) and two public subnets
- ALB Security Group: allowed inbound HTTP (port 80) from anywhere
- App Security Group: allowed port 8000 only from the ALB security group
- ECS tasks ran with `AssignPublicIp: ENABLED` in public subnets

**Estimated cost:** Free (default VPC, no NAT gateway)

---

## Total Cost Estimate

| Resource | Monthly Cost |
|---|---|
| ECS Fargate (0.5 vCPU, 1GB) | ~$16 |
| Application Load Balancer | ~$17 |
| ECR Storage | ~$0.06 |
| CloudWatch Logs | ~$0.50 |
| Everything else | Free |
| **Total** | **~$33–35/month** |

Stack was torn down after validation to avoid all ongoing charges.

---

## Teardown Commands

```bash
# Delete all CloudFormation-managed resources
aws cloudformation delete-stack --stack-name trustrag-dev --region us-east-1

# Delete ECR repository and images (not managed by CloudFormation)
aws ecr delete-repository --repository-name trustrag-dev --force --region us-east-1
```

---

## Bugs Encountered During AWS Deployment

### BUG-AWS-01: ECR Repository Already Exists (ResourceExistenceCheck)

**What happened:** The ECR repository was manually created before running `aws cloudformation deploy`. The CloudFormation template also tried to create the same repository, triggering an `AWS::EarlyValidation::ResourceExistenceCheck` failure and rolling back the entire stack.

**Root cause:** ECR repo created manually in Step 3 of setup, then CloudFormation template tried to create it again.

**Fix:** Removed the `ECRRepository` resource block from `infra/cloudformation/template.yml`. The `ImageUri` parameter already passed the full ECR URI directly — CloudFormation only needs to deploy ECS/ALB/IAM resources, not the registry itself.

---

### BUG-AWS-02: Missing EC2 Permissions — ROLLBACK_FAILED

**What happened:** First CloudFormation deploy failed because `trustrag-deploy` IAM user lacked `ec2:GetSecurityGroupsForVpc` (needed to create the ALB) and `ec2:DeleteSecurityGroup` (needed to roll back). The stack got stuck in `ROLLBACK_FAILED` state and had to be manually deleted.

**Root cause:** Only ECS/ECR/CloudFormation/IAM/CloudWatch policies were attached — `AmazonEC2FullAccess` was missing.

**Fix:**
```bash
aws iam attach-user-policy \
  --user-name trustrag-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

aws cloudformation delete-stack --stack-name trustrag-dev --region us-east-1
```

---

### BUG-AWS-03: ECS Could Not Pull Image — Repository Empty

**What happened:** CloudFormation provisioned the ECS service successfully but the service kept failing with `CannotPullContainerError: trustrag-dev:latest not found`. The ECR repository existed but had no images in it.

**Root cause:** The Docker image was never pushed to ECR before the CloudFormation deploy. ECS tried to pull `latest` but the tag didn't exist.

**Fix:** Built and pushed the image first, then forced a new ECS deployment:
```bash
docker build --platform linux/amd64 -t trustrag:latest .
docker push 832496386138.dkr.ecr.us-east-1.amazonaws.com/trustrag-dev:latest
aws ecs update-service --cluster trustrag-dev --service trustrag-dev --force-new-deployment --region us-east-1
```

---

### BUG-AWS-04: exec format error — Wrong CPU Architecture

**What happened:** ECS task launched but immediately crashed with `exec /usr/local/bin/uvicorn: exec format error`. The container started and even briefly registered with the ALB target group before failing health checks and being drained.

**Root cause:** The Docker image was built on an Apple Silicon Mac (ARM64 architecture). ECS Fargate runs on x86_64 (AMD64). An ARM image cannot execute on an AMD64 host.

**Fix:** Rebuilt the image with `--platform linux/amd64` flag and re-pushed. Also pinned both Dockerfile stages to ensure future builds always produce the correct architecture:

```dockerfile
FROM --platform=linux/amd64 python:3.11-slim AS builder
FROM --platform=linux/amd64 python:3.11-slim
```

```bash
docker build --platform linux/amd64 -t trustrag:latest .
```

---

### BUG-AWS-05: CloudFormation Stack Stuck in CREATE_IN_PROGRESS

**What happened:** Stack remained in `CREATE_IN_PROGRESS` for over an hour without completing or failing. ECS service was the last resource pending.

**Root cause:** ECS service waits for at least one task to become healthy before CloudFormation marks it `CREATE_COMPLETE`. Since the image was missing (BUG-AWS-03) and then wrong architecture (BUG-AWS-04), no task ever passed the health check, so CloudFormation waited indefinitely.

**Fix:** Resolved by fixing the upstream image issues (BUG-AWS-03 and BUG-AWS-04). Once a healthy task registered with the ALB target group and passed the `/health` check, the stack completed automatically.

---

## Lessons Learned

1. **Push the image to ECR before running CloudFormation** — ECS will fail immediately if the image tag doesn't exist.
2. **Always build with `--platform linux/amd64`** on Apple Silicon Macs when targeting AWS Fargate.
3. **Create ECR repos outside CloudFormation** (manually or separately) to avoid the ResourceExistenceCheck conflict on re-runs.
4. **IAM needs EC2 permissions** for any deployment involving ALBs or security groups.
5. **ALB + ECS Fargate costs ~$33/month** — tear down when not actively using it.
