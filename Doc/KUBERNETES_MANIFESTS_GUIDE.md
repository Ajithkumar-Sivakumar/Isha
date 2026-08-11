# Production-Grade Kubernetes Deployment Strategy

## Overview

This document provides production-ready Kubernetes manifests and strategies for deploying sample-app to both K3s (staging) and EKS (production) environments.

---

## File Structure

```
k8s/
├── namespace.yaml              # Kubernetes namespace
├── deployment.yaml             # Base deployment (deprecated - use kustomize)
├── service.yaml                # ClusterIP service
├── ingress.yaml                # Ingress configuration
├── configmap.yaml              # Environment variables
├── secrets.yaml                # Encrypted secrets reference
├── hpa.yaml                    # Horizontal Pod Autoscaler (EKS only)
├── pdb.yaml                    # Pod Disruption Budget
├── networkpolicy.yaml          # Network policies
└── kustomize/
    ├── kustomization.yaml      # Base configuration
    ├── overlays/
    │   ├── staging/            # K3s specific
    │   │   ├── kustomization.yaml
    │   │   ├── replicas.yaml
    │   │   └── resources.yaml
    │   └── production/         # EKS specific
    │       ├── kustomization.yaml
    │       ├── replicas.yaml
    │       ├── resources.yaml
    │       └── affinity.yaml
```

---

## 1. Namespace Configuration

**k8s/namespace.yaml**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sample-app
  labels:
    name: sample-app
    environment: multi-region
    managed-by: github-actions
  annotations:
    description: "Sample application namespace"
    owner: "DevOps Team"

---
# Optional: ResourceQuota to prevent resource exhaustion
apiVersion: v1
kind: ResourceQuota
metadata:
  name: sample-app-quota
  namespace: sample-app
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
    services.loadbalancers: "2"

---
# Optional: NetworkPolicy default deny
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: sample-app
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress

---
# Allow ingress and egress for sample-app pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-sample-app
  namespace: sample-app
spec:
  podSelector:
    matchLabels:
      app: sample-app
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 443
        - protocol: TCP
          port: 53
        - protocol: UDP
          port: 53
```

---

## 2. ConfigMap for Environment Variables

**k8s/configmap.yaml**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sample-app-config
  namespace: sample-app
  labels:
    app: sample-app
data:
  # Application Configuration
  LOG_LEVEL: "INFO"
  APP_PORT: "8080"
  HEALTH_CHECK_PATH: "/health"
  
  # Feature Flags
  ENABLE_METRICS: "true"
  ENABLE_TRACING: "true"
  
  # Performance tuning
  WORKER_THREADS: "4"
  CONNECTION_POOL_SIZE: "10"
  REQUEST_TIMEOUT_MS: "30000"
  
  # Database (if applicable)
  DB_CONNECTION_TIMEOUT: "5000"
  DB_MAX_RETRIES: "3"

---
# Staging-specific ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: sample-app-config-staging
  namespace: sample-app
  labels:
    app: sample-app
    environment: staging
data:
  ENVIRONMENT: "staging"
  LOG_LEVEL: "DEBUG"
  ENABLE_DEBUG_ENDPOINTS: "true"

---
# Production-specific ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: sample-app-config-production
  namespace: sample-app
  labels:
    app: sample-app
    environment: production
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "WARN"
  ENABLE_DEBUG_ENDPOINTS: "false"
  ENABLE_METRICS: "true"
  ENABLE_TRACING: "true"
```

---

## 3. Service Configuration

**k8s/service.yaml**

```yaml
# ClusterIP Service (Internal)
apiVersion: v1
kind: Service
metadata:
  name: sample-app-svc
  namespace: sample-app
  labels:
    app: sample-app
  annotations:
    description: "Internal service for sample-app pods"
spec:
  type: ClusterIP
  selector:
    app: sample-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
      name: http
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800

---
# Headless Service (for StatefulSets if needed in future)
apiVersion: v1
kind: Service
metadata:
  name: sample-app-headless
  namespace: sample-app
  labels:
    app: sample-app
spec:
  type: ClusterIP
  clusterIP: None
  selector:
    app: sample-app
  ports:
    - protocol: TCP
      port: 8080
      targetPort: 8080
```

---

## 4. Ingress Configuration

**k8s/ingress-k3s.yaml** (K3s specific - uses nginx)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sample-app-ingress
  namespace: sample-app
  labels:
    app: sample-app
    environment: staging
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-staging"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
    - hosts:
        - app-staging.example.com
      secretName: sample-app-tls-staging
  rules:
    - host: app-staging.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: sample-app-svc
                port:
                  number: 80
```

**k8s/ingress-eks.yaml** (EKS specific - uses ALB)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sample-app-ingress
  namespace: sample-app
  labels:
    app: sample-app
    environment: production
  annotations:
    alb.ingress.kubernetes.io/load-balancer-name: "sample-app-alb"
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: "arn:aws:acm:us-west-2:ACCOUNT_ID:certificate/CERT_ID"
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/wafv2-acl-arn: "arn:aws:wafv2:us-west-2:ACCOUNT_ID:regional/webacl/sample-app/ID"
    alb.ingress.kubernetes.io/tags: "Environment=production,Application=sample-app"
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: sample-app-svc
                port:
                  number: 80
```

---

## 5. Base Deployment Configuration

**k8s/deployment-base.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app-deployment
  namespace: sample-app
  labels:
    app: sample-app
    version: v1
spec:
  replicas: 2  # Override in overlays
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      # Pod security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault

      # Service account
      serviceAccountName: sample-app
      
      # Image pull secrets for ECR
      imagePullSecrets:
        - name: ecr-credentials

      # Init containers (optional - for migrations, etc.)
      initContainers:
        - name: migrations
          image: "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/sample-app:latest"
          command: ["python", "migrations.py"]
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: sample-app-secrets
                  key: database-url
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"

      containers:
        - name: sample-app
          image: "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/sample-app:latest"
          imagePullPolicy: Always
          
          # Port configuration
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP

          # Environment variables from ConfigMap
          envFrom:
            - configMapRef:
                name: sample-app-config
          
          # Additional environment variables
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
            - name: POD_IP
              valueFrom:
                fieldRef:
                  fieldPath: status.podIP
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
            - name: AWS_REGION
              value: "us-west-2"  # Inject via overlay

          # Health probes
          livenessProbe:
            httpGet:
              path: /health
              port: http
              scheme: HTTP
            initialDelaySeconds: 10
            periodSeconds: 20
            timeoutSeconds: 3
            failureThreshold: 3

          readinessProbe:
            httpGet:
              path: /health
              port: http
              scheme: HTTP
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3

          # Startup probe (useful for slow-starting apps)
          startupProbe:
            httpGet:
              path: /health
              port: http
            failureThreshold: 30
            periodSeconds: 10

          # Resource requests and limits
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"

          # Volume mounts
          volumeMounts:
            - name: tmp
              mountPath: /tmp
            - name: logs
              mountPath: /var/log/app

          # Security context
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            capabilities:
              drop:
                - ALL
              add:
                - NET_BIND_SERVICE

      # Volumes
      volumes:
        - name: tmp
          emptyDir: {}
        - name: logs
          emptyDir: {}

      # Pod disruption budget
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - sample-app
                topologyKey: kubernetes.io/hostname

      # Termination
      terminationGracePeriodSeconds: 30
      restartPolicy: Always

      # DNS configuration
      dnsPolicy: ClusterFirst
```

---

## 6. Horizontal Pod Autoscaler (EKS only)

**k8s/hpa.yaml**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sample-app-hpa
  namespace: sample-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sample-app-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 30
        - type: Pods
          value: 2
          periodSeconds: 30
      selectPolicy: Max
```

---

## 7. Pod Disruption Budget

**k8s/pdb.yaml**

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: sample-app-pdb
  namespace: sample-app
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: sample-app
  unhealthyPodEvictionPolicy: AlwaysAllow
```

---

## 8. Service Account & RBAC

**k8s/rbac.yaml**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sample-app
  namespace: sample-app

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: sample-app-role
  namespace: sample-app
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: sample-app-rolebinding
  namespace: sample-app
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: sample-app-role
subjects:
  - kind: ServiceAccount
    name: sample-app
    namespace: sample-app
```

---

## 9. Kustomization Structure

**k8s/kustomization.yaml** (Base)

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: sample-app

commonLabels:
  app: sample-app
  managed-by: kustomize

commonAnnotations:
  kustomize.config.k8s.io/version: v5.0.0

resources:
  - namespace.yaml
  - configmap.yaml
  - rbac.yaml
  - service.yaml
  - deployment-base.yaml

generatorOptions:
  disableNameSuffixHash: false

replicas:
  - name: sample-app-deployment
    count: 2

images:
  - name: sample-app
    newTag: latest
```

**k8s/overlays/staging/kustomization.yaml** (K3s)

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../

patchesStrategicMerge:
  - replicas.yaml
  - resources.yaml

configMapGenerator:
  - name: sample-app-config
    behavior: merge
    literals:
      - ENVIRONMENT=staging
      - LOG_LEVEL=DEBUG

vars:
  - name: IMAGE_TAG
    objref:
      kind: Deployment
      name: sample-app-deployment
      apiVersion: apps/v1
    fieldref:
      fieldpath: spec.template.spec.containers[0].image
```

**k8s/overlays/staging/replicas.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app-deployment
spec:
  replicas: 2
```

**k8s/overlays/staging/resources.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app-deployment
spec:
  template:
    spec:
      containers:
        - name: sample-app
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
```

**k8s/overlays/production/kustomization.yaml** (EKS)

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../

patchesStrategicMerge:
  - replicas.yaml
  - resources.yaml
  - affinity.yaml

resources:
  - hpa.yaml
  - pdb.yaml

configMapGenerator:
  - name: sample-app-config
    behavior: merge
    literals:
      - ENVIRONMENT=production
      - LOG_LEVEL=WARN
```

**k8s/overlays/production/replicas.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app-deployment
spec:
  replicas: 3
```

**k8s/overlays/production/resources.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app-deployment
spec:
  template:
    spec:
      containers:
        - name: sample-app
          resources:
            requests:
              cpu: "200m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "512Mi"
```

**k8s/overlays/production/affinity.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app-deployment
spec:
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values:
                      - sample-app
              topologyKey: kubernetes.io/hostname
```

---

## Deployment Commands

### Apply to K3s (Staging)
```bash
kubectl apply -k k8s/overlays/staging/
```

### Apply to EKS (Production)
```bash
kubectl apply -k k8s/overlays/production/
```

### Preview changes
```bash
kubectl kustomize k8s/overlays/staging/ | kubectl diff -f -
```

### Rollback
```bash
kubectl rollout undo deployment/sample-app-deployment -n sample-app
```

---

## Monitoring & Logging

### View logs
```bash
kubectl logs -n sample-app -l app=sample-app --tail=100 -f
```

### Check deployment status
```bash
kubectl get deployments -n sample-app -o wide
kubectl describe deployment sample-app-deployment -n sample-app
```

### View resource usage
```bash
kubectl top pods -n sample-app
kubectl top nodes
```

---

## Security Hardening Checklist

- ✓ Non-root user (runAsUser: 1000)
- ✓ Read-only root filesystem
- ✓ No privileged escalation
- ✓ Resource requests/limits
- ✓ Network policies
- ✓ Pod security context
- ✓ RBAC roles
- ✓ Secret management
- ✓ Image pull secrets
- ✓ Pod disruption budgets
