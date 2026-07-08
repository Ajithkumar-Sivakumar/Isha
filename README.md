# sample-app — K3s + EKS + ECR + GitHub Actions

Complete end-to-end CI/CD pipeline for deploying a Python Flask application to both K3s (staging on EC2) and Amazon EKS (production), with automated building, testing, and deployment via GitHub Actions.

## 🚀 Quick Start

**New to this setup?** Start here: [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)

## 📚 Documentation

This project includes comprehensive documentation for all aspects of the CI/CD pipeline:

| Document | Purpose |
|----------|---------|
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | 📋 **START HERE** - Complete setup checklist & quick start guide |
| [DEPLOYMENT_SETUP.md](DEPLOYMENT_SETUP.md) | 🔧 Step-by-step K3s & EKS installation + IAM configuration |
| [GITHUB_CI_CONFIGURATION.md](GITHUB_CI_CONFIGURATION.md) | 🔐 Secrets, variables, and GitHub environment setup |
| [KUBERNETES_MANIFESTS_GUIDE.md](KUBERNETES_MANIFESTS_GUIDE.md) | ☸️ Production-grade K8s manifests with Kustomize overlays |
| [TROUBLESHOOTING_MONITORING.md](TROUBLESHOOTING_MONITORING.md) | 🔍 Common issues, debugging commands, and monitoring setup |

## 📁 Project Structure

```
sample-app/
├── app.py                          # Flask application with health checks
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Production-ready container image
├── README.md                       # This file
│
├── .github/
│   └── workflows/
│       └── docker-build.yml        # CI/CD Pipeline (Build → Push → Deploy K3s → Deploy EKS)
│
├── k8s/                            # Kubernetes manifests
│   ├── namespace.yaml              # Namespace & resource quotas
│   ├── deployment.yaml             # Base deployment config
│   ├── service.yaml                # ClusterIP service
│   ├── ingress.yaml                # Ingress configuration
│   ├── configmap.yaml              # Environment variables
│   ├── rbac.yaml                   # Service account & RBAC roles
│   ├── hpa.yaml                    # Horizontal Pod Autoscaler (EKS)
│   ├── pdb.yaml                    # Pod Disruption Budget
│   └── overlays/                   # Kustomize environment overlays
│       ├── staging/                # K3s specific (2 replicas, less resources)
│       └── production/             # EKS specific (3 replicas, HPA, more resources)
│
└── iam/                            # IAM configuration examples
    ├── gha-oidc-trust.json         # GitHub OIDC trust policy
    └── ecr-push-policy.json        # ECR push permissions
```

## 🔄 CI/CD Pipeline Overview

The GitHub Actions workflow runs automatically on push to `main`:

```
1. Build & Test (Self-hosted runner)
   ├─ Verify runner capabilities
   ├─ Build Docker image
   └─ Push to ECR (latest + commit SHA)

2. Deploy to K3s (Staging) - Auto
   ├─ Get kubeconfig from AWS Secrets Manager
   ├─ Update deployment (2 replicas)
   ├─ Wait for rollout (5 min timeout)
   └─ Verify health checks

3. Deploy to EKS (Production) - Requires Approval
   ├─ Update kubeconfig via AWS CLI
   ├─ Deploy 3 replicas + HPA
   ├─ Create ALB LoadBalancer
   ├─ Wait for rollout (10 min timeout)
   └─ Verify pod logs
```

## 🛠️ Local Development

### Build Docker Image Locally
```bash
docker build -t sample-app:local .
```

### Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask app
python app.py
# Visit: http://localhost:8080
# Health: http://localhost:8080/health
```

## 📋 Setup Checklist

### Phase 1: AWS (Week 1)
- [ ] Create EKS cluster
- [ ] Launch K3s on EC2
- [ ] Configure GitHub OIDC provider
- [ ] Store K3s kubeconfig in AWS Secrets Manager

**Guide:** [DEPLOYMENT_SETUP.md](DEPLOYMENT_SETUP.md)

### Phase 2: GitHub Configuration (Week 1)
- [ ] Add repository secrets (AWS_ACCOUNT_ID, AWS_REGION, ECR_REPOSITORY)
- [ ] Create `staging` and `production` environments
- [ ] Add environment-specific secrets
- [ ] Configure deployment protection rules

**Guide:** [GITHUB_CI_CONFIGURATION.md](GITHUB_CI_CONFIGURATION.md)

### Phase 3: Kubernetes Setup (Week 2)
- [ ] Review and update K8s manifests with your account ID/region
- [ ] Test manifests locally with `kubectl kustomize`
- [ ] Deploy to both clusters manually (initial setup)

**Guide:** [KUBERNETES_MANIFESTS_GUIDE.md](KUBERNETES_MANIFESTS_GUIDE.md)

### Phase 4: First Deployment (Week 2)
- [ ] Commit and push to `main` branch
- [ ] Monitor GitHub Actions workflow
- [ ] Verify deployments on both K3s and EKS

### Phase 5: Monitoring (Week 3)
- [ ] Set up CloudWatch logs on EKS
- [ ] Install Prometheus & Grafana (optional)
- [ ] Configure alerting rules

**Guide:** [TROUBLESHOOTING_MONITORING.md](TROUBLESHOOTING_MONITORING.md)

## 🔐 Security Features

✅ **Authentication & Authorization**
- GitHub OIDC for AWS credential exchange
- No hardcoded credentials
- IAM role-based access control (RBAC) in Kubernetes

✅ **Secrets Management**
- K3s kubeconfig in AWS Secrets Manager
- ECR credentials handled via IAM
- Environment-specific secrets in GitHub

✅ **Network Security**
- Network policies for namespace isolation
- Pod security contexts (non-root, read-only fs)
- Resource quotas to prevent exhaustion
- Pod disruption budgets for reliability

✅ **Container Security**
- Security scanning in Dockerfile
- Minimal base image (python:3.11-slim)
- Non-root user (uid: 1000)
- Dropped Linux capabilities

## 📊 Environments

### Staging (K3s on EC2)
- **Use Case**: Testing, CI/CD validation, pre-production
- **Replicas**: 2
- **CPU**: 100m request, 500m limit
- **Memory**: 128Mi request, 256Mi limit
- **Ingress**: nginx-ingress-controller
- **Auto Scaling**: Manual

### Production (EKS)
- **Use Case**: Live traffic, high availability
- **Replicas**: 3-10 (auto-scaling via HPA)
- **CPU**: 200m request, 1000m limit
- **Memory**: 256Mi request, 512Mi limit
- **Ingress**: AWS ALB
- **Auto Scaling**: Horizontal (HPA) + Cluster (Karpenter)
- **Deployments**: Require manual approval

## 🆘 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **ImagePullBackOff** | [View guide](TROUBLESHOOTING_MONITORING.md#issue-1-imagepullbackoff) |
| **CrashLoopBackOff** | [View guide](TROUBLESHOOTING_MONITORING.md#issue-2-crashloopbackoff) |
| **Pending Pods** | [View guide](TROUBLESHOOTING_MONITORING.md#issue-3-pending-pods) |
| **Stuck Rollout** | [View guide](TROUBLESHOOTING_MONITORING.md#issue-5-deployment-stuck-in-rollout) |
| **LoadBalancer Pending** | [View guide](TROUBLESHOOTING_MONITORING.md#issue-4-loadbalancer-stuck-in-pending-eks) |

### Useful Commands

```bash
# Check K3s deployment
kubectl --kubeconfig=k3s-kubeconfig.yaml get pods -n sample-app
kubectl --kubeconfig=k3s-kubeconfig.yaml logs -n sample-app -l app=sample-app

# Check EKS deployment
kubectl get pods -n sample-app -o wide
kubectl logs -n sample-app -l app=sample-app --tail=100
kubectl get svc -n sample-app  # Get LoadBalancer endpoint

# Check resource usage
kubectl top pods -n sample-app
kubectl top nodes

# View recent events
kubectl get events -n sample-app --sort-by='.lastTimestamp'
```

## 📈 Monitoring

### Application Health
- **Liveness Probe**: `/health` (every 20s)
- **Readiness Probe**: `/health` (every 10s)
- **Startup Probe**: `/health` (30 retries, 10s intervals)

### Metrics
- Prometheus endpoint: `/metrics`
- CloudWatch Container Insights on EKS
- Custom application metrics (requests, duration)

### Logging
- Application logs to stdout (JSON format)
- CloudWatch Logs on EKS
- Local logs on K3s (exportable via Fluent Bit)

## 🔗 Important Links

- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [K3s Documentation](https://docs.k3s.io/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS ECR Best Practices](https://docs.aws.amazon.com/AmazonECR/latest/userguide/best-practices.html)

## 📞 Support

For issues or questions:
1. Check [TROUBLESHOOTING_MONITORING.md](TROUBLESHOOTING_MONITORING.md)
2. Review GitHub Actions logs in repository
3. Check Kubernetes events: `kubectl get events -n sample-app`
4. Contact DevOps team on Slack (#devops)

## 📝 Manual Commands (for reference)

### Build & Push to ECR
```bash
# Build image
docker build -t sample-app:local .

# Authenticate with ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-west-2.amazonaws.com

# Tag and push
docker tag sample-app:local \
  123456789012.dkr.ecr.us-west-2.amazonaws.com/sample-app:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/sample-app:latest

# Verify in ECR
aws ecr describe-images --repository-name sample-app --region us-west-2
```

### Deploy Manually to K3s
```bash
export KUBECONFIG=k3s-kubeconfig.yaml
kubectl kustomize k8s/overlays/staging | kubectl apply -f -
kubectl rollout status deployment/sample-app-deployment -n sample-app
```

### Deploy Manually to EKS
```bash
aws eks update-kubeconfig --name sample-app-prod --region us-west-2
kubectl kustomize k8s/overlays/production | kubectl apply -f -
kubectl rollout status deployment/sample-app-deployment -n sample-app
```

---

**Version**: 1.0 | **Last Updated**: 2024-Q3 | **Maintained By**: DevOps Team

Deploy to EKS (requires `kubectl` configured for your cluster):
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
# Optional ingress
kubectl apply -f k8s/ingress.yaml
```

Useful kubectl checks:
```bash
kubectl get pods -n sample-app
kubectl get deploy -n sample-app
kubectl get svc -n sample-app
kubectl rollout status deployment/sample-app-deployment -n sample-app
kubectl describe pod <pod-name> -n sample-app
kubectl logs <pod-name> -n sample-app
```

Image pull / authentication explanation
-------------------------------------
- If your EKS worker nodes (or node IAM role) have permissions to pull from ECR (for example via an instance profile or IRSA with the right permissions), you do NOT need to create Kubernetes `imagePullSecrets`.
- When worker nodes use an IAM role, the kubelet on the node can call ECR to get authorization tokens on behalf of pods, so storing Docker credentials as secrets in Kubernetes is unnecessary and less secure.
- If you run self-managed nodes without proper IAM permissions, you must either configure `imagePullSecrets` with Docker credentials or give the node role ECR pull permissions.
