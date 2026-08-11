# Troubleshooting & Monitoring Guide for K3s and EKS

## Quick Troubleshooting Commands

### Check Cluster Health

```bash
# K3s
export KUBECONFIG=/tmp/k3s-kubeconfig.yaml
kubectl cluster-info
kubectl get nodes -o wide
kubectl describe nodes

# EKS
aws eks describe-cluster --name sample-app-prod --region us-west-2
kubectl cluster-info
kubectl get nodes -o wide
```

---

## Common Issues & Solutions

### Issue 1: ImagePullBackOff

**Symptoms:**
```
kubectl describe pod <pod-name> -n sample-app
# Shows: Failed to pull image ... unauthorized: authentication required
```

**Root Causes:**
- ECR credentials expired (for K3s)
- ImagePullSecret missing (for EKS)
- Incorrect image URI
- ECR repository doesn't exist

**Solutions:**

#### For K3s:
```bash
# 1. Update ECR credentials immediately
export KUBECONFIG=/tmp/k3s-kubeconfig.yaml
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com

# 2. Delete old secret
kubectl delete secret ecr-credentials -n sample-app --ignore-not-found

# 3. Create new secret
kubectl create secret docker-registry ecr-credentials \
  --docker-server=ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password --region us-west-2) \
  --docker-email=noreply@example.com \
  -n sample-app

# 4. Restart deployment to pick up new credentials
kubectl rollout restart deployment/sample-app-deployment -n sample-app
kubectl rollout status deployment/sample-app-deployment -n sample-app --timeout=5m
```

#### For EKS:
```bash
# 1. Check if secret exists
kubectl get secret -n sample-app | grep ecr

# 2. If not, create it
ECR_TOKEN=$(aws ecr get-login-password --region us-west-2)
kubectl create secret docker-registry ecr-credentials \
  --docker-server=ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$ECR_TOKEN \
  --docker-email=noreply@example.com \
  -n sample-app

# 3. Verify deployment uses the secret
kubectl get deployment sample-app-deployment -n sample-app -o yaml | grep imagePullSecrets

# 4. Restart deployment
kubectl rollout restart deployment/sample-app-deployment -n sample-app
```

#### Verify Fix:
```bash
# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=sample-app -n sample-app --timeout=300s

# Check pod status
kubectl get pods -n sample-app -o wide

# View logs to ensure app is running
kubectl logs -n sample-app -l app=sample-app --tail=50
```

---

### Issue 2: CrashLoopBackOff

**Symptoms:**
```
kubectl get pods -n sample-app
# Shows: CrashLoopBackOff (or multiple restarts)
```

**Root Causes:**
- Application startup failure
- Incorrect environment variables
- Missing configuration
- Port already in use
- Insufficient memory

**Solutions:**

```bash
# 1. Check logs
kubectl logs -n sample-app <pod-name>
kubectl logs -n sample-app <pod-name> --previous  # Check previous crash

# 2. Describe pod to see events
kubectl describe pod <pod-name> -n sample-app

# 3. Check resource constraints
kubectl top pod <pod-name> -n sample-app
kubectl describe node <node-name>

# 4. Verify liveness probe is not too aggressive
# Edit deployment and increase initialDelaySeconds
kubectl edit deployment sample-app-deployment -n sample-app

# 5. Increase memory limit if needed
kubectl set resources deployment sample-app-deployment \
  --limits=memory=512Mi \
  --requests=memory=256Mi \
  -n sample-app

# 6. Check configuration is correct
kubectl get configmap sample-app-config -n sample-app -o yaml
```

---

### Issue 3: Pending Pods

**Symptoms:**
```
kubectl get pods -n sample-app
# Shows: Pending
```

**Root Causes:**
- Node resource exhaustion
- Node selector constraints
- PVC waiting for storage
- Cluster too small

**Solutions:**

```bash
# 1. Check pod events
kubectl describe pod <pod-name> -n sample-app

# 2. Check node resources
kubectl top nodes
kubectl describe nodes

# 3. For K3s - check local storage
kubectl get pvc -n sample-app
kubectl get pv

# 4. For EKS - check availability
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=eks-node*" \
  --region us-west-2

# 5. Scale down deployment and try again
kubectl scale deployment sample-app-deployment --replicas=1 -n sample-app

# 6. For EKS - trigger autoscaler
# Check if autoscaler can add nodes:
kubectl logs -n kube-system -l app=cluster-autoscaler --tail=50
```

---

### Issue 4: LoadBalancer Stuck in Pending (EKS)

**Symptoms:**
```
kubectl get svc -n sample-app
# Shows: sample-app-svc | LoadBalancer | <pending>
```

**Root Causes:**
- ALB controller not installed
- ALB controller not running properly
- AWS permissions insufficient
- Service doesn't have proper annotations

**Solutions:**

```bash
# 1. Verify ALB controller is running
kubectl get pods -n kube-system | grep aws-load-balancer-controller

# 2. Check ALB controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller --tail=50

# 3. Verify ALB controller has proper IAM permissions
kubectl describe serviceaccount aws-load-balancer-controller -n kube-system

# 4. Check service has proper annotations
kubectl get svc sample-app-svc -n sample-app -o yaml

# 5. If ALB controller is not installed, install it:
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=sample-app-prod \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# 6. Wait for controller to reconcile
sleep 30
kubectl get svc -n sample-app -o wide
```

---

### Issue 5: Deployment Stuck in Rollout

**Symptoms:**
```
kubectl rollout status deployment/sample-app-deployment -n sample-app
# Hangs indefinitely
```

**Root Causes:**
- Liveness probe failing
- Insufficient resources
- New image not pulling
- Pod evictions

**Solutions:**

```bash
# 1. Check rollout history
kubectl rollout history deployment/sample-app-deployment -n sample-app

# 2. Get current rollout status with details
kubectl get deployment sample-app-deployment -n sample-app -o yaml | grep -A 20 "status:"

# 3. Check pod events
kubectl describe deployment sample-app-deployment -n sample-app

# 4. Check recent pod logs
kubectl logs -n sample-app -l app=sample-app --tail=100 --all-containers=true

# 5. Increase rollout timeout
kubectl rollout status deployment/sample-app-deployment \
  -n sample-app --timeout=10m

# 6. Force rollback if stuck too long
kubectl rollout undo deployment/sample-app-deployment -n sample-app
kubectl rollout status deployment/sample-app-deployment -n sample-app --timeout=5m

# 7. Check and adjust liveness probe
kubectl get deployment sample-app-deployment -n sample-app -o yaml | \
  grep -A 10 "livenessProbe:"
```

---

### Issue 6: Connection Refused Errors

**Symptoms:**
```
curl: (7) Failed to connect to app.example.com
# Or in logs: Connection refused
```

**Root Causes:**
- Ingress not configured
- Service selector mismatch
- Pod not ready
- Network policies blocking traffic

**Solutions:**

```bash
# 1. Verify ingress exists and is configured
kubectl get ingress -n sample-app
kubectl describe ingress sample-app-ingress -n sample-app

# 2. Verify service exists
kubectl get svc -n sample-app
kubectl describe svc sample-app-svc -n sample-app

# 3. Verify service has endpoints
kubectl get endpoints -n sample-app

# 4. Verify pod labels match service selector
kubectl get pods -n sample-app --show-labels
kubectl get svc sample-app-svc -n sample-app -o yaml | grep selector -A 5

# 5. Test pod directly
POD_NAME=$(kubectl get pods -n sample-app -l app=sample-app -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward pod/$POD_NAME 8080:8080 -n sample-app
# In another terminal: curl http://localhost:8080/health

# 6. Check network policies
kubectl get networkpolicy -n sample-app
kubectl describe networkpolicy <policy-name> -n sample-app

# 7. For K3s - verify nginx-ingress-controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=50
```

---

## Monitoring Setup

### 1. Basic Monitoring with kubectl

```bash
# Watch deployment changes
kubectl get deployment -n sample-app -w

# Watch pod status
kubectl get pods -n sample-app -w

# Check resource usage in real-time
kubectl top pods -n sample-app --containers
kubectl top nodes

# Get events
kubectl get events -n sample-app --sort-by='.lastTimestamp'
```

### 2. Prometheus & Grafana Setup (Optional - Recommended for Production)

#### For EKS:

```bash
# 1. Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=admin123 \
  --set grafana.persistence.enabled=true \
  --set grafana.persistence.storageClassName=ebs \
  --set grafana.persistence.size=10Gi

# 2. Wait for all components to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=prometheus \
  -n monitoring --timeout=300s

# 3. Access Grafana
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# Open: http://localhost:3000
# Login: admin / admin123
```

#### For K3s:

```bash
# 1. Install lightweight monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=7d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.accessModes='{ReadWriteOnce}' \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=20Gi \
  --set grafana.adminPassword=admin123
```

### 3. CloudWatch Monitoring (EKS)

```bash
# 1. Install CloudWatch Container Insights
eksctl utils update-cluster-logging \
  --enable-logging api,audit,authenticator,controllerManager,scheduler \
  --cluster=sample-app-prod \
  --approve \
  --region us-west-2

# 2. Deploy CloudWatch Agent
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml

# 3. View logs in CloudWatch
aws logs tail /aws/eks/sample-app-prod/cluster --follow --region us-west-2
```

### 4. Application Metrics

Add metrics endpoint to your Flask app:

```python
# app.py
from prometheus_client import Counter, Histogram, generate_latest
import time

request_count = Counter('app_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('app_request_duration_seconds', 'Request duration')

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    request_count.labels(method=request.method, endpoint=request.path).inc()
    request_duration.observe(duration)
    return response

@app.route('/metrics')
def metrics():
    return generate_latest()
```

---

## Performance Tuning

### K3s Optimization

```bash
# 1. Adjust K3s kubelet settings
cat <<EOF | sudo tee /etc/rancher/k3s/kubelet.config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
maxPods: 110
podsPerCore: 0
systemReserved:
  cpu: 100m
  memory: 100Mi
  ephemeral-storage: 1Gi
kubeReserved:
  cpu: 100m
  memory: 100Mi
  ephemeral-storage: 1Gi
EOF

sudo systemctl restart k3s

# 2. Increase log verbosity for debugging
sudo k3s server --log-level debug
```

### EKS Optimization

```bash
# 1. Enable cluster autoscaling
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# 2. Set up pod autoscaling
kubectl autoscale deployment sample-app-deployment \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n sample-app

# 3. Adjust cluster autoscaler scale-down
kubectl patch deployment cluster-autoscaler -n kube-system --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/command", "value":["./cluster-autoscaler","--cloud-provider=aws","--expander=least-waste","--node-group-auto-discovery=asg:tag:k8s.io/cluster-autoscaler/sample-app-prod,k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/node-template/label/karpenter.sh/provisioner=default"]}]'
```

---

## Logging Best Practices

### Structured Logging in Application

```python
# app.py
import logging
import json
from logging import Formatter

class JsonFormatter(Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
        }
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@app.route('/')
def index():
    logger.info('Root endpoint accessed', extra={'request_id': request.id})
    return "Hello"
```

### Configure Log Aggregation

```bash
# For EKS - use CloudWatch Logs
# For K3s - use local file logging, then export to central system

# Example: FluentBit for K3s
helm install fluent-bit fluent/fluent-bit \
  -n logging \
  --create-namespace \
  -f - <<EOF
config:
  outputs: |
    [OUTPUT]
        name s3
        match *
        bucket my-bucket
        s3_key_format /logs/%Y/%m/%d/%H_%M_%S
EOF
```

---

## Security Monitoring

### Audit Logging

#### EKS:
```bash
# Enable audit logging
eksctl utils update-cluster-logging \
  --enable-logging audit \
  --cluster=sample-app-prod \
  --approve \
  --region us-west-2

# View audit logs
aws logs tail /aws/eks/sample-app-prod/cluster --follow
```

#### K3s:
```bash
# K3s has audit logging enabled by default
sudo tail -f /var/lib/rancher/k3s/server/logs/audit.log
```

### RBAC Audit

```bash
# Check RBAC permissions
kubectl auth can-i get pods --as=system:serviceaccount:sample-app:sample-app -n sample-app

# List roles in namespace
kubectl get roles -n sample-app
kubectl describe role sample-app-role -n sample-app
```

---

## Quick Debugging Checklist

- [ ] Check pod status: `kubectl get pods -n sample-app`
- [ ] Check pod logs: `kubectl logs <pod> -n sample-app`
- [ ] Check events: `kubectl get events -n sample-app --sort-by='.lastTimestamp'`
- [ ] Check resource usage: `kubectl top pods -n sample-app`
- [ ] Check service endpoints: `kubectl get endpoints -n sample-app`
- [ ] Check ingress: `kubectl describe ingress -n sample-app`
- [ ] Test pod directly: `kubectl exec <pod> -n sample-app -- curl localhost:8080/health`
- [ ] Check node health: `kubectl get nodes -o wide`
- [ ] Verify configuration: `kubectl get configmap -n sample-app`
- [ ] Check secrets exist: `kubectl get secrets -n sample-app`
