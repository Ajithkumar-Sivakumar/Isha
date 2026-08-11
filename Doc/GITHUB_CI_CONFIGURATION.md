# GitHub Actions CI/CD Configuration Guide

## Quick Reference: All Required Secrets & Variables

### 📋 Summary Table

| Type | Name | Environment | Example Value |
|------|------|-------------|----------------|
| Secret | AWS_ACCOUNT_ID | All | 123456789012 |
| Secret | AWS_REGION | All | us-west-2 |
| Secret | ECR_REPOSITORY | All | sample-app |
| Secret | K3S_KUBECONFIG_SECRET_ID | staging | k3s-kubeconfig |
| Secret | EKS_CLUSTER_NAME | production | sample-app-prod |
| Variable | AWS_REGION | All | us-west-2 |
| Variable | AWS_ACCOUNT_ID | All | 123456789012 |
| Variable | ECR_REPOSITORY | All | sample-app |

---

## Step 1: GitHub Organization/Repository Secrets Setup

### Access Location
**GitHub Repository → Settings → Secrets and Variables → Actions**

### 1.1 Create Repository-Level Secrets (Available to all environments)

#### Secret 1: AWS_ACCOUNT_ID
```
Name: AWS_ACCOUNT_ID
Value: 123456789012  (your actual AWS account ID)
```

#### Secret 2: AWS_REGION
```
Name: AWS_REGION
Value: us-west-2  (or your region)
```

#### Secret 3: ECR_REPOSITORY
```
Name: ECR_REPOSITORY
Value: sample-app  (your ECR repo name)
```

### 1.2 Create Environment-Specific Secrets

#### For `staging` environment (K3s)

Navigate to: **Settings → Environments → staging** (create if doesn't exist)

Add these secrets:

```
Secret 1:
Name: K3S_KUBECONFIG_SECRET_ID
Value: k3s-kubeconfig
Description: AWS Secrets Manager secret ID containing K3s kubeconfig
```

To get this value:
1. SSH into your K3s EC2 instance
2. Store kubeconfig in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name k3s-kubeconfig \
  --secret-string file:///etc/rancher/k3s/k3s.yaml \
  --region us-west-2
```

#### For `production` environment (EKS)

Navigate to: **Settings → Environments → production** (create if doesn't exist)

Add these secrets:

```
Secret 1:
Name: EKS_CLUSTER_NAME
Value: sample-app-prod
Description: Name of the EKS cluster
```

```
Secret 2:
Name: EKS_REGION
Value: us-west-2
Description: AWS region where EKS cluster is located
```

---

## Step 2: GitHub Repository Variables Setup

### Access Location
**GitHub Repository → Settings → Secrets and Variables → Variables**

### 2.1 Create Repository-Level Variables

#### Variable 1: AWS_ACCOUNT_ID
```
Name: AWS_ACCOUNT_ID
Value: 123456789012
```

#### Variable 2: AWS_REGION
```
Name: AWS_REGION
Value: us-west-2
```

#### Variable 3: ECR_REPOSITORY
```
Name: ECR_REPOSITORY
Value: sample-app
```

### 2.2 Optional: Create Environment-Specific Variables

#### For `staging` environment:
```
Name: K3S_NAMESPACE
Value: sample-app

Name: K3S_REPLICAS
Value: 2

Name: ENVIRONMENT
Value: staging
```

#### For `production` environment:
```
Name: EKS_NAMESPACE
Value: sample-app

Name: EKS_REPLICAS
Value: 3

Name: ENVIRONMENT
Value: production
```

---

## Step 3: GitHub Environments Configuration

### 3.1 Create `staging` Environment

1. Go to **Settings → Environments**
2. Click **New environment**
3. Name: `staging`
4. Click **Configure environment**

Configure settings:
```
Deployment branches and tags:
  ○ All branches
  ● Protected branches and tags
  Pattern: main

Deployment protection rules:
  □ Require reviewers before deployment (optional)
  □ Restrict deployments to specific environments or refs
```

5. Add Environment Secrets:
```
K3S_KUBECONFIG_SECRET_ID = k3s-kubeconfig
```

### 3.2 Create `production` Environment

1. Click **New environment**
2. Name: `production`
3. Click **Configure environment**

Configure settings:
```
Deployment branches and tags:
  ○ All branches
  ● Protected branches and tags
  Pattern: main

Deployment protection rules:
  ☑ Require reviewers before deployment (RECOMMENDED)
  Custom deployment protection rules: None (optional)
  Restrict deployments to specific environments or refs (optional)
```

4. Add Environment Secrets:
```
EKS_CLUSTER_NAME = sample-app-prod
EKS_REGION = us-west-2
```

---

## Step 4: AWS IAM Configuration for GitHub Actions

### 4.1 Verify OIDC Provider

Your GitHub OIDC provider should already be set up. Verify:

```bash
aws iam list-open-id-connect-providers
```

Expected output includes:
```
arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com
```

### 4.2 Existing GitHubActionsOIDCRole

Ensure your `GitHubActionsOIDCRole` has these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories",
        "ecr:CreateRepository"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:k3s-*"
    }
  ]
}
```

### 4.3 Add to Trust Relationship (if not already present)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/YOUR_REPO:*"
        }
      }
    }
  ]
}
```

---

## Step 5: AWS Secrets Manager Setup

### 5.1 Store K3s Kubeconfig

```bash
# On your local machine with AWS CLI configured
# Get kubeconfig from K3s EC2 instance first

# Update cluster server address to use EC2 public IP
# Create the secret:
aws secretsmanager create-secret \
  --name k3s-kubeconfig \
  --description "K3s cluster kubeconfig for GitHub Actions" \
  --secret-string file://path/to/k3s-kubeconfig.yaml \
  --region us-west-2 \
  --tags Key=Environment,Value=staging Key=Purpose,Value=GitHubActions

# Verify:
aws secretsmanager describe-secret --secret-id k3s-kubeconfig --region us-west-2
```

### 5.2 Store EKS Configuration (Optional - CLI can fetch directly)

If you want to store EKS kubeconfig too:

```bash
# Get EKS kubeconfig
aws eks update-kubeconfig \
  --name sample-app-prod \
  --region us-west-2 \
  --kubeconfig eks-kubeconfig.yaml

# Store in Secrets Manager
aws secretsmanager create-secret \
  --name eks-kubeconfig \
  --description "EKS cluster kubeconfig for GitHub Actions" \
  --secret-string file://eks-kubeconfig.yaml \
  --region us-west-2
```

---

## Step 6: Accessing Secrets in GitHub Actions

### 6.1 Repository Secrets (Used in all jobs)

```yaml
- name: Use Repository Secret
  run: |
    echo "AWS Account: ${{ secrets.AWS_ACCOUNT_ID }}"
    echo "AWS Region: ${{ secrets.AWS_REGION }}"
    echo "ECR Repository: ${{ secrets.ECR_REPOSITORY }}"
```

### 6.2 Environment Secrets (Used only in that environment)

```yaml
jobs:
  deploy-k3s:
    environment: staging
    steps:
      - name: Get K3s Kubeconfig
        run: |
          # This secret is only available in staging environment
          aws secretsmanager get-secret-value \
            --secret-id ${{ secrets.K3S_KUBECONFIG_SECRET_ID }} \
            --query SecretString \
            --output text > kubeconfig.yaml
```

---

## Step 7: Testing Your Configuration

### 7.1 Test Secrets Access

Create a test workflow: `.github/workflows/test-secrets.yml`

```yaml
name: Test Secrets

on: [workflow_dispatch]

jobs:
  test-repo-secrets:
    runs-on: ubuntu-latest
    steps:
      - name: Test Repository Secrets
        run: |
          echo "AWS Account ID: ${{ secrets.AWS_ACCOUNT_ID }}"
          echo "AWS Region: ${{ secrets.AWS_REGION }}"
          echo "ECR Repository: ${{ secrets.ECR_REPOSITORY }}"

  test-staging-secrets:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Test Staging Secrets
        run: |
          echo "K3S Secret ID: ${{ secrets.K3S_KUBECONFIG_SECRET_ID }}"
          
  test-production-secrets:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Test Production Secrets
        run: |
          echo "EKS Cluster Name: ${{ secrets.EKS_CLUSTER_NAME }}"
          echo "EKS Region: ${{ secrets.EKS_REGION }}"
```

### 7.2 Run Test Workflow

1. Push to repository
2. Go to **Actions** tab
3. Select **Test Secrets** workflow
4. Click **Run workflow**
5. Check logs to verify all secrets are accessible

---

## Step 8: Complete Configuration Checklist

### Repository Secrets (Settings → Secrets and Variables → Actions)
- [ ] `AWS_ACCOUNT_ID` = your account ID
- [ ] `AWS_REGION` = us-west-2 (or your region)
- [ ] `ECR_REPOSITORY` = sample-app

### Repository Variables (Settings → Secrets and Variables → Variables)
- [ ] `AWS_ACCOUNT_ID` = your account ID
- [ ] `AWS_REGION` = us-west-2
- [ ] `ECR_REPOSITORY` = sample-app

### Staging Environment (Settings → Environments → staging)
- [ ] Created and configured
- [ ] Deployment branches: main
- [ ] Secret `K3S_KUBECONFIG_SECRET_ID` = k3s-kubeconfig

### Production Environment (Settings → Environments → production)
- [ ] Created and configured
- [ ] Deployment branches: main
- [ ] Deployment protection: Require reviewers ✓
- [ ] Secret `EKS_CLUSTER_NAME` = sample-app-prod
- [ ] Secret `EKS_REGION` = us-west-2

### AWS Configuration
- [ ] OIDC provider configured for GitHub
- [ ] `GitHubActionsOIDCRole` has correct permissions
- [ ] K3s kubeconfig stored in Secrets Manager
- [ ] K3s EC2 instance can access AWS Secrets Manager

### Workflow File
- [ ] `.github/workflows/docker-build.yml` updated with K3s and EKS stages

---

## Troubleshooting Common Issues

### Issue: "Secret not found" in staging environment

**Solution:**
```bash
# Verify secret exists in AWS
aws secretsmanager describe-secret --secret-id k3s-kubeconfig --region us-west-2

# Verify GitHub Actions role has access
# Check IAM role permissions include secretsmanager:GetSecretValue
```

### Issue: "EKS cluster not found"

**Solution:**
```bash
# Verify environment secret is set
# Check secret value matches actual cluster name:
aws eks describe-cluster --name sample-app-prod --region us-west-2
```

### Issue: Deployment not using correct environment

**Solution:**
```yaml
# Ensure job specifies environment:
jobs:
  deploy-k3s:
    environment: staging  # This line is critical
    steps: ...
    
  deploy-eks:
    environment: production  # This line is critical
    steps: ...
```

---

## Environment Variables in Workflow

### Using Both Secrets and Variables Together

```yaml
- name: Example Job
  env:
    AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }}
    AWS_REGION: ${{ vars.AWS_REGION }}
    DEPLOY_ENV: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
  run: |
    echo "Deploying to $DEPLOY_ENV"
    echo "Using account: $AWS_ACCOUNT_ID"
    echo "Region: $AWS_REGION"
```

### Accessing in Shell Scripts

```yaml
- name: Run deployment script
  env:
    K3S_SECRET: ${{ secrets.K3S_KUBECONFIG_SECRET_ID }}
  run: |
    ./deploy.sh "$K3S_SECRET"
```

---

## Security Best Practices

1. **Environment Protection Rules**: 
   - Enable "Require reviewers" for production
   - Limit deployments to `main` branch only

2. **Secret Rotation**:
   - ECR credentials: Rotate monthly
   - Kubeconfigs: Rotate quarterly
   - AWS credentials: Rotate according to AWS guidelines

3. **Audit Trail**:
   - Enable GitHub organization audit logs
   - Review deployment history in GitHub Actions
   - Monitor AWS CloudTrail for IAM assumption events

4. **Least Privilege**:
   - K3s role: Only Secrets Manager access to k3s secret
   - EKS role: Only EKS describe permissions needed
   - ECR: Only push/pull permissions for the repository

---

## Quick Command Reference

```bash
# Create K3s secret
aws secretsmanager create-secret --name k3s-kubeconfig \
  --secret-string file://k3s-kubeconfig.yaml --region us-west-2

# Update K3s secret
aws secretsmanager update-secret --secret-id k3s-kubeconfig \
  --secret-string file://k3s-kubeconfig.yaml --region us-west-2

# List all secrets
aws secretsmanager list-secrets --region us-west-2

# Delete secret (30 day recovery window)
aws secretsmanager delete-secret --secret-id k3s-kubeconfig \
  --recovery-window-in-days 30 --region us-west-2

# Describe EKS cluster
aws eks describe-cluster --name sample-app-prod --region us-west-2

# List OIDC providers
aws iam list-open-id-connect-providers
```
