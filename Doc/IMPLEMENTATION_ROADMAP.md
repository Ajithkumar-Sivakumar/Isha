# CI/CD Pipeline: Implementation Roadmap & Quick Start

## Overview

This document provides a roadmap to implement the complete CI/CD pipeline with both K3s (staging) and EKS (production) deployments.

---

## 📋 Quick Start Checklist

### Phase 1: AWS Setup (Week 1)

- [ ] **Create EKS Cluster**
  ```bash
  eksctl create cluster --name sample-app-prod --version 1.28 --region us-west-2
  ```
  See: [DEPLOYMENT_SETUP.md](DEPLOYMENT_SETUP.md) → Part 2

- [ ] **Set Up OIDC Provider** (auto with eksctl)
  ```bash
  aws iam list-open-id-connect-providers
  ```

- [ ] **Install AWS Load Balancer Controller on EKS**
  ```bash
  helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    -n kube-system --set clusterName=sample-app-prod
  ```

- [ ] **Create K3s EC2 Instance & Install K3s**
  ```bash
  curl -sfL https://get.k3s.io | sh -s - server --write-kubeconfig-mode=644
  ```
  See: [DEPLOYMENT_SETUP.md](DEPLOYMENT_SETUP.md) → Part 1

### Phase 2: Secrets & Variables (Week 1, Day 4)

- [ ] **Store K3s Kubeconfig in AWS Secrets Manager**
  ```bash
  aws secretsmanager create-secret --name k3s-kubeconfig \
    --secret-string file://k3s-kubeconfig.yaml --region us-west-2
  ```

- [ ] **Add GitHub Repository Secrets**
  - `AWS_ACCOUNT_ID` → 123456789012
  - `AWS_REGION` → us-west-2
  - `ECR_REPOSITORY` → sample-app
  
  See: [GITHUB_CI_CONFIGURATION.md](GITHUB_CI_CONFIGURATION.md) → Step 1

- [ ] **Add GitHub Repository Variables**
  - `AWS_ACCOUNT_ID` → 123456789012
  - `AWS_REGION` → us-west-2
  - `ECR_REPOSITORY` → sample-app

- [ ] **Create GitHub Environments**
  - `staging` (with K3s_KUBECONFIG_SECRET_ID)
  - `production` (with EKS_CLUSTER_NAME, require reviewers)
  
  See: [GITHUB_CI_CONFIGURATION.md](GITHUB_CI_CONFIGURATION.md) → Step 3

### Phase 3: Kubernetes Configuration (Week 2)

- [ ] **Review Kubernetes Manifests**
  - Base deployment: `k8s/deployment-base.yaml`
  - K3s overlay: `k8s/overlays/staging/`
  - EKS overlay: `k8s/overlays/production/`
  
  See: [KUBERNETES_MANIFESTS_GUIDE.md](KUBERNETES_MANIFESTS_GUIDE.md)

- [ ] **Update Image URIs**
  Replace `ACCOUNT_ID` and `REGION` in all manifests:
  ```bash
  sed -i 's/ACCOUNT_ID/123456789012/g' k8s/**/*.yaml
  sed -i 's/REGION/us-west-2/g' k8s/**/*.yaml
  ```

- [ ] **Test Local Deployment**
  ```bash
  # Test K3s manifests
  kubectl kustomize k8s/overlays/staging/ | head -50
  
  # Test EKS manifests
  kubectl kustomize k8s/overlays/production/ | head -50
  ```

### Phase 4: Pipeline Execution (Week 2, Day 4)

- [ ] **Push to Main Branch**
  ```bash
  git add .github/workflows/docker-build.yml
  git commit -m "Add K3s and EKS deployment stages"
  git push origin main
  ```

- [ ] **Monitor First Deployment**
  - Go to GitHub → Actions
  - Watch workflow: Build → Push ECR → Deploy K3s → Deploy EKS
  - Each stage should complete successfully

### Phase 5: Verification & Testing (Week 3)

- [ ] **Verify K3s Deployment**
  ```bash
  kubectl --kubeconfig=k3s-kubeconfig.yaml get pods -n sample-app
  kubectl --kubeconfig=k3s-kubeconfig.yaml logs -n sample-app -l app=sample-app
  ```

- [ ] **Verify EKS Deployment**
  ```bash
  kubectl get pods -n sample-app
  kubectl get svc -n sample-app  # Get LoadBalancer DNS
  ```

- [ ] **Test Application**
  ```bash
  # Test K3s endpoint
  curl http://k3s-endpoint:80/health
  
  # Test EKS endpoint
  curl http://elb-dns/health
  ```

### Phase 6: Monitoring Setup (Week 3, Day 4)

- [ ] **Set Up CloudWatch Monitoring (EKS)**
  ```bash
  eksctl utils update-cluster-logging --enable-logging api,audit \
    --cluster=sample-app-prod --approve
  ```

- [ ] **Install Prometheus & Grafana (Optional)**
  ```bash
  helm install monitoring prometheus-community/kube-prometheus-stack \
    -n monitoring --create-namespace
  ```

See: [TROUBLESHOOTING_MONITORING.md](TROUBLESHOOTING_MONITORING.md) → Monitoring Setup

---

## 📁 Documentation Structure

| Document | Purpose | Audience |
|----------|---------|----------|
| [DEPLOYMENT_SETUP.md](DEPLOYMENT_SETUP.md) | Complete setup guide for K3s & EKS | DevOps, SRE |
| [GITHUB_CI_CONFIGURATION.md](GITHUB_CI_CONFIGURATION.md) | Secrets, variables, and GitHub setup | DevOps, Release Manager |
| [KUBERNETES_MANIFESTS_GUIDE.md](KUBERNETES_MANIFESTS_GUIDE.md) | K8s manifests and Kustomize structure | Platform Engineer, DevOps |
| [TROUBLESHOOTING_MONITORING.md](TROUBLESHOOTING_MONITORING.md) | Common issues and debugging | DevOps, SRE, Support |

---

## 🔄 Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Developer Push to Main                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  GitHub Actions       │
         │  Runner (Self-hosted) │
         └─────────┬─────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    ┌────────┐ ┌───────┐ ┌──────────┐
    │Verify  │ │Build  │ │Push      │
    │Runner  │ │Docker │ │to ECR    │
    └────┬───┘ └───┬───┘ └────┬─────┘
         │         │          │
         └─────────┴──────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    ┌────────────────────────────┐
    │   Deploy to K3s (Staging)  │
    │   - Update deployment      │
    │   - Rollout wait 5min      │
    │   - Verify health          │
    └────────────┬───────────────┘
                 │ (depends on build success)
    ┌────────────┴──────────────┐
    │                           │
    ▼                           ▼
┌──────────────────┐  ┌──────────────────┐
│  GitHub Review   │  │  Deploy to EKS   │
│  (Production)    │  │  (Production)    │
│  - Require +1    │  │  - Update image  │
└──────────────────┘  │  - Rolling update│
                      │  - Health checks │
                      │  - Verify logs   │
                      └──────────────────┘
```

---

## 🚀 Deployment Flow Details

### 1. Build Stage (~ 5-10 minutes)
- Tests self-hosted runner
- Checks Docker, AWS, Python
- Builds Docker image
- Tags with `latest` and commit SHA
- Pushes to ECR

### 2. K3s Deployment Stage (~ 10 minutes)
- Gets kubeconfig from AWS Secrets Manager
- Creates namespace & ECR pull secret
- Updates deployment image
- Waits for rollout (5 min timeout)
- Verifies pods are running

### 3. EKS Deployment Stage (~ 15 minutes, requires approval)
- Updates EKS kubeconfig
- Creates ECR pull secret
- Deploys 3 replicas (vs 2 for K3s)
- Applies HPA & PDB
- Creates ALB LoadBalancer
- Waits for rollout (10 min timeout)

---

## 🔐 Security Considerations

### Secrets Management
- ✅ K3s kubeconfig stored in AWS Secrets Manager
- ✅ ECR credentials handled by IAM/OIDC
- ✅ GitHub OIDC for AWS authentication
- ✅ No credentials in code or logs

### Access Control
- ✅ Production environment requires reviewer approval
- ✅ Main branch protection enabled (recommended)
- ✅ Role-based access control (RBAC) in Kubernetes
- ✅ Pod security context (non-root, read-only fs)

### Network Security
- ✅ Network policies for namespace isolation
- ✅ SecurityContext with capability dropping
- ✅ Resource quotas to prevent exhaustion
- ✅ Pod disruption budgets for reliability

---

## 📊 Monitoring & Observability

### Health Checks
```
K3s & EKS:
  Liveness: /health (every 20s)
  Readiness: /health (every 10s)
  Startup: /health (30 attempts, 10s interval)
```

### Metrics Endpoints
```
Prometheus metrics: /metrics
Prometheus scrape job: http://<pod>:8080/metrics
Interval: Every 30 seconds
```

### Log Aggregation
- **K3s**: Local files in `/var/log/app`
- **EKS**: CloudWatch Logs (via Container Insights)
- **App**: Structured JSON logging to stdout

---

## 🔧 Scaling & Performance

### K3s (Staging)
- Replicas: 2
- CPU Request: 100m, Limit: 500m
- Memory Request: 128Mi, Limit: 256Mi
- No HPA (manual scaling)

### EKS (Production)
- Replicas: 3 (minimum)
- CPU Request: 200m, Limit: 1000m
- Memory Request: 256Mi, Limit: 512Mi
- HPA: Scale 3-10 replicas based on CPU (70%) & Memory (80%)
- Cluster Autoscaler: Auto-adds nodes as needed

---

## 🐛 Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| ImagePullBackOff | [TROUBLESHOOTING_MONITORING.md](TROUBLESHOOTING_MONITORING.md#issue-1-imagepullbackoff) |
| CrashLoopBackOff | [TROUBLESHOOTING_MONITORING.md](TROUBLESHOOTING_MONITORING.md#issue-2-crashloopbackoff) |
| Pending Pods | [TROUBLESHOOTING_MONITORING.md](TROUBLESHOOTING_MONITORING.md#issue-3-pending-pods) |
| LoadBalancer Pending | [TROUBLESHOOTING_MONITORING.md](TROUBLESHOOTING_MONITORING.md#issue-4-loadbalancer-stuck-in-pending-eks) |
| Rollout Stuck | [TROUBLESHOOTING_MONITORING.md](TROUBLESHOOTING_MONITORING.md#issue-5-deployment-stuck-in-rollout) |

---

## 📞 Support & Escalation

### Common Commands for Daily Operations

```bash
# Check all deployments across both clusters
echo "=== K3s Status ===" && \
kubectl --kubeconfig=k3s-kubeconfig.yaml get all -n sample-app

echo "=== EKS Status ===" && \
kubectl get all -n sample-app

# View recent logs
kubectl -n sample-app logs -l app=sample-app --tail=100 -f

# Check resource usage
kubectl top nodes
kubectl top pods -n sample-app

# Rollback if needed
kubectl rollout undo deployment/sample-app-deployment -n sample-app
kubectl rollout status deployment/sample-app-deployment -n sample-app
```

---

## 📈 Next Steps (Post-MVP)

- [ ] Add canary deployments with Flagger
- [ ] Implement ServiceMesh (Istio) for better observability
- [ ] Set up cost optimization (Karpenter for spot instances)
- [ ] Add disaster recovery & cross-region failover
- [ ] Implement GitOps (ArgoCD) for declarative deployments
- [ ] Add advanced security scanning (Falco, OPA/Gatekeeper)
- [ ] Set up multi-region failover

---

## 📚 Additional Resources

### Kubernetes
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [K3s Documentation](https://docs.k3s.io/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)

### AWS
- [AWS EKS Workshop](https://www.eksworkshop.com/)
- [ECR Best Practices](https://docs.aws.amazon.com/AmazonECR/latest/userguide/best-practices.html)

### GitHub Actions
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)

---

## Version Control & Updates

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-Q3 | Initial setup for K3s & EKS |
| 1.1 | TBD | Add canary deployments |
| 1.2 | TBD | Add multi-region setup |

---

**Last Updated**: 2024-Q3
**Maintained By**: DevOps Team
**Slack Channel**: #devops-deployment
