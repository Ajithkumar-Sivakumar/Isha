# Deployment Setup Guide: K3s & EKS on EC2

## Overview
This document provides step-by-step instructions to set up K3s (staging) and EKS (production) deployment stages in your GitHub Actions CI/CD pipeline.

---

## Part 1: K3s Installation on EC2 (Staging Environment)

### 1.1 Prerequisites
- EC2 instance with Ubuntu 20.04 LTS or higher
- Minimum specs: 2vCPU, 4GB RAM, 20GB storage
- Security group allowing:
  - Port 22 (SSH) from your IP
  - Port 6443 (K3s API)
  - Port 80, 443 (HTTP/HTTPS)
  - Ports 30000-32767 (NodePorts)

### 1.2 Step-by-Step K3s Installation

#### Step 1: Launch EC2 Instance and SSH
```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y
```

#### Step 2: Install K3s Server
```bash
# Install K3s with required features
curl -sfL https://get.k3s.io | sh -s - server \
  --write-kubeconfig-mode=644 \
  --bind-address=0.0.0.0 \
  --disable=traefik \
  --disable=local-storage

# Verify K3s installation
sudo k3s --version
sudo k3s kubectl get nodes

# Give current user access to kubectl
sudo usermod -a -G k3s $USER
# Re-login or run: newgrp k3s
```

#### Step 3: Copy K3s Kubeconfig
```bash
# On EC2 instance
sudo cat /etc/rancher/k3s/k3s.yaml

# Copy the entire output - you'll need this for GitHub Actions
# The file should look like:
# apiVersion: v1
# clusters:
# - cluster:
#     certificate-authority-data: <base64-cert>
#     server: https://127.0.0.1:6443
#   name: k3s
# ...
```

#### Step 4: Update Kubeconfig for Remote Access
```bash
# On EC2 instance, get the actual IP address
TOKEN=$(sudo cat /var/lib/rancher/k3s/server/node-token)
CERT=$(sudo cat /etc/rancher/k3s/k3s.yaml | grep certificate-authority-data | awk '{print $2}')

# Get your EC2 public IP
EC2_IP=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)

# Create kubeconfig with public IP
cat <<EOF > ~/k3s-kubeconfig.yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: <paste-cert-from-above>
    server: https://${EC2_IP}:6443
  name: k3s
contexts:
- context:
    cluster: k3s
    user: admin@k3s
  name: k3s
current-context: k3s
kind: Config
preferences: {}
users:
- name: admin@k3s
  user:
    client-certificate-data: <copy-from-original-kubeconfig>
    client-key-data: <copy-from-original-kubeconfig>
EOF

# Verify connectivity
kubectl --kubeconfig=~/k3s-kubeconfig.yaml cluster-info
```

#### Step 5: Set Up ECR Credentials on K3s
```bash
# On EC2 instance
# Create a script to update ECR credentials (runs daily)
cat <<'EOF' > ~/update-ecr-creds.sh
#!/bin/bash
set -e

AWS_ACCOUNT_ID="your-account-id"
AWS_REGION="your-region"
ECR_REPOSITORY="your-repository"

# Get ECR login token
ECR_TOKEN=$(aws ecr get-login-password --region $AWS_REGION)

# Update or create secret
kubectl delete secret ecr-credentials -n sample-app --ignore-not-found
kubectl create secret docker-registry ecr-credentials \
  --docker-server=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$ECR_TOKEN \
  --docker-email=aws@example.com \
  -n sample-app

echo "ECR credentials updated successfully"
EOF

chmod +x ~/update-ecr-creds.sh
~/update-ecr-creds.sh

# Set up cron job to refresh credentials daily (tokens expire)
(crontab -l 2>/dev/null; echo "0 0 * * * /home/ec2-user/update-ecr-creds.sh >> /var/log/ecr-creds.log 2>&1") | crontab -
```

#### Step 6: Install Nginx Ingress Controller for K3s
```bash
# K3s doesn't come with Traefik (we disabled it), so install Nginx
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.0/deploy/static/provider/cloud/deploy.yaml

# Wait for ingress controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# Verify
kubectl get svc -n ingress-nginx
```

#### Step 7: Set Up Storage Class (Optional but Recommended)
```bash
# Install local-path-provisioner for persistent storage
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml

# Verify
kubectl get storageclass
```

---

## Part 2: Amazon EKS Setup (Production Environment)

### 2.1 Prerequisites
- AWS Account with appropriate permissions
- eksctl installed locally
- aws-cli configured with credentials
- kubectl installed

### 2.2 Step-by-Step EKS Setup

#### Step 1: Create EKS Cluster
```bash
# Set variables
CLUSTER_NAME="sample-app-prod"
AWS_REGION="us-west-2"
INSTANCE_TYPE="t3.medium"
NODES_MIN=2
NODES_MAX=5

# Create cluster
eksctl create cluster \
  --name $CLUSTER_NAME \
  --version 1.28 \
  --region $AWS_REGION \
  --instance-types $INSTANCE_TYPE \
  --nodes $NODES_MIN \
  --nodes-max $NODES_MAX \
  --with-oidc \
  --enable-ssm

# This takes ~15-20 minutes
```

#### Step 2: Update Kubeconfig
```bash
aws eks update-kubeconfig \
  --region $AWS_REGION \
  --name $CLUSTER_NAME

# Verify
kubectl cluster-info
kubectl get nodes
```

#### Step 3: Set Up IAM OIDC Provider (Already done by eksctl with --with-oidc)
```bash
# Verify OIDC provider exists
aws iam list-open-id-connect-providers
```

#### Step 4: Install AWS Load Balancer Controller
```bash
# This allows Kubernetes Service type LoadBalancer to work on EKS
# Install Helm first if needed
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Add AWS EKS Helm repo
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# Create IAM policy for ALB controller
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.0/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json

# Create service account
eksctl create iamserviceaccount \
  --cluster=$CLUSTER_NAME \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name=AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::ACCOUNT_ID:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve \
  --region=$AWS_REGION

# Install ALB controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

#### Step 5: Set Up EBS CSI Driver (for persistent volumes)
```bash
# Create IAM policy
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-ebs-csi-driver/master/docs/example-iam-policy.json

aws iam create-policy \
  --policy-name AmazonEBSCSIDriverPolicy \
  --policy-document file://example-iam-policy.json

# Create service account
eksctl create iamserviceaccount \
  --cluster=$CLUSTER_NAME \
  --namespace=kube-system \
  --name=ebs-csi-controller-sa \
  --role-name=AmazonEKS_EBS_CSI_DriverRole \
  --attach-policy-arn=arn:aws:iam::ACCOUNT_ID:policy/AmazonEBSCSIDriverPolicy \
  --approve \
  --region=$AWS_REGION

# Add the EBS CSI driver add-on
aws eks create-addon \
  --cluster-name $CLUSTER_NAME \
  --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::ACCOUNT_ID:role/AmazonEKS_EBS_CSI_DriverRole \
  --region=$AWS_REGION
```

#### Step 6: Set Up Auto Scaling
```bash
# Install Cluster Autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Create IAM policy for autoscaler
cat <<EOF > asg-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeAutoScalingInstances",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeScalingActivities",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeLaunchTemplateVersions"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name EKSClusterAutoscalerPolicy \
  --policy-document file://asg-policy.json
```

---

## Part 3: GitHub Actions Configuration

### 3.1 Required Secrets

Add these secrets to your GitHub repository (**Settings > Secrets > Actions**):

#### ECR/Build Secrets (Already configured)
- `AWS_ACCOUNT_ID`: Your AWS Account ID
- `AWS_REGION`: Your AWS region (e.g., us-west-2)
- `ECR_REPOSITORY`: Your ECR repository name

#### K3s Specific Secrets
- `K3S_KUBECONFIG_BASE64`: Base64 encoded K3s kubeconfig file
  ```bash
  # Create on your local machine after getting kubeconfig from EC2
  cat ~/k3s-kubeconfig.yaml | base64 | pbcopy  # macOS
  # Or on Linux: cat ~/k3s-kubeconfig.yaml | base64 | xclip -selection clipboard
  ```

- `K3S_KUBECONFIG_SECRET_ID`: AWS Secrets Manager secret ID containing K3s kubeconfig
  ```bash
  # Store in AWS Secrets Manager
  aws secretsmanager create-secret \
    --name k3s-kubeconfig \
    --secret-string file://~/k3s-kubeconfig.yaml \
    --region us-west-2
  ```

#### EKS Specific Secrets
- `EKS_CLUSTER_NAME`: Name of your EKS cluster (e.g., sample-app-prod)
- `EKS_REGION`: AWS region for EKS (e.g., us-west-2)

### 3.2 Required Repository Variables

Add these variables to your GitHub repository (**Settings > Secrets > Variables**):

```bash
# Build Configuration
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=123456789012
ECR_REPOSITORY=sample-app

# K3s Configuration
K3S_EC2_INSTANCE_ID=i-0123456789abcdef0
K3S_NAMESPACE=sample-app

# EKS Configuration
EKS_CLUSTER_NAME=sample-app-prod
EKS_NAMESPACE=sample-app
EKS_ENVIRONMENT=production
```

### 3.3 GitHub Environments Configuration

#### Staging Environment (K3s)
1. Go to **Settings > Environments**
2. Create new environment: `staging`
3. Add deployment branches: `main`
4. Add protection rule: `Require reviewers before deployment` (optional)
5. Add environment-specific secrets:
   - `K3S_KUBECONFIG_SECRET_ID`

#### Production Environment (EKS)
1. Create new environment: `production`
2. Add deployment branches: `main` only
3. Add protection rules:
   - `Require reviewers before deployment`: ✓
   - `Restrict deployments to specified environments or refs`: ✓
4. Add environment-specific secrets:
   - `EKS_CLUSTER_NAME`

---

## Part 4: IAM Configuration for GitHub Actions

### 4.1 Create GitHub OIDC Trust Relationship

#### For K3s EC2 Instance Access
```bash
# K3s instance should have an IAM role with EC2 instance profile
# Attach policy for Systems Manager (to retrieve kubeconfig from Secrets Manager)

cat <<EOF > k3s-ssm-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:k3s-kubeconfig*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name K3sGitHubActionsPolicy \
  --policy-document file://k3s-ssm-policy.json
```

#### For EKS Cluster Access
```bash
# Already configured in Part 1: docker-build.yml
# Uses existing GitHubActionsOIDCRole
# Verify role has EKS permissions:

cat <<EOF > eks-policy-addition.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:UpdateClusterVersion"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Add this to your GitHubActionsOIDCRole policy
```

---

## Part 5: Running the Deployment

### 5.1 Automatic Deployment
Push to `main` branch:
```bash
git add .
git commit -m "Deploy new version"
git push origin main
```

This triggers:
1. Build & Push to ECR
2. Deploy to K3s (staging) 
3. Deploy to EKS (production)

### 5.2 Manual Deployment via GitHub CLI
```bash
# Trigger workflow manually
gh workflow run docker-build.yml --ref main
```

### 5.3 Verify Deployments

#### Check K3s Deployment
```bash
kubectl --kubeconfig=k3s-kubeconfig.yaml get deployments -n sample-app
kubectl --kubeconfig=k3s-kubeconfig.yaml get pods -n sample-app
kubectl --kubeconfig=k3s-kubeconfig.yaml logs -n sample-app -l app=sample-app --tail=100
```

#### Check EKS Deployment
```bash
kubectl get deployments -n sample-app
kubectl get pods -n sample-app
kubectl get svc -n sample-app  # Get LoadBalancer endpoint
curl http://<LoadBalancer-DNS>/health  # Verify app
```

---

## Part 6: Troubleshooting

### K3s Issues

#### Issue: ImagePullBackOff on K3s
```bash
# Fix: Update ECR credentials
~/update-ecr-creds.sh

# Verify secret exists
kubectl get secret ecr-credentials -n sample-app -o yaml
```

#### Issue: Ingress not working on K3s
```bash
# Check nginx-ingress-controller
kubectl get pods -n ingress-nginx
kubectl describe ingress sample-app-ingress -n sample-app
```

### EKS Issues

#### Issue: LoadBalancer pending
```bash
# Check ALB controller
kubectl get pods -n kube-system | grep aws-load-balancer
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller --tail=50
```

#### Issue: ECR pull failing
```bash
# Recreate ECR secret on EKS
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-west-2.amazonaws.com

kubectl create secret docker-registry ecr-credentials \
  --docker-server=<account>.dkr.ecr.us-west-2.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password) \
  --docker-email=aws@example.com \
  -n sample-app --dry-run=client -o yaml | kubectl apply -f -
```

---

## Part 7: Monitoring & Logging

### K3s Monitoring
```bash
# Install Prometheus & Grafana (optional)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

### EKS Monitoring
```bash
# Enable CloudWatch Container Insights
eksctl utils update-cluster-logging \
  --enable-logging api,audit,authenticator,controllerManager,scheduler \
  --cluster=$CLUSTER_NAME \
  --approve

# View logs
kubectl logs -n kube-system -l app=sample-app --all-containers=true
```

---

## Summary Checklist

- [ ] K3s EC2 instance launched and configured
- [ ] K3s kubeconfig stored in AWS Secrets Manager
- [ ] ECR credentials cron job set up on K3s
- [ ] EKS cluster created with OIDC provider
- [ ] AWS Load Balancer Controller installed on EKS
- [ ] All GitHub Secrets configured
- [ ] GitHub repository variables set
- [ ] GitHub Environments (staging/production) configured
- [ ] First deployment tested successfully
- [ ] Monitoring and logging configured
