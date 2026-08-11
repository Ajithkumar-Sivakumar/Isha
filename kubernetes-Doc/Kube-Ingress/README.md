# Kube-Ingress

## What is Ingress?
Ingress is a Kubernetes resource that manages external access to services inside a cluster, typically HTTP and HTTPS traffic.

In real-world use, Ingress gives you one place to:
- Route traffic to different services based on URLs or hostnames
- Terminate TLS/HTTPS
- Expose multiple applications through a single IP address or load balancer

## Why use Ingress?
Use Ingress when you need:
- A single entry point for multiple services
- URL-based routing like `/app` or `/api`
- Host-based routing like `app.example.com` and `api.example.com`
- TLS termination for secure traffic

## How Ingress fits with common Kubernetes resources
### 1. Pods
A Pod is the smallest deployable unit in Kubernetes.
- Contains one or more containers
- Runs your application code
- Ingress does not talk to Pods directly; it routes traffic to Services instead

### 2. Deployments
A Deployment manages a group of identical Pods.
- Ensures the right number of replicas are running
- Handles updates and rollbacks
- A Deployment is used for stateless apps where several copies can run in parallel

### 3. StatefulSets
A StatefulSet manages Pods with stable identity and storage.
- Used for stateful applications like databases
- Each Pod gets a stable network identity and stable storage
- Useful when apps need persistent data and ordered start/stop behavior

### 4. Services
A Service provides a stable network endpoint for a set of Pods.
- Usually `ClusterIP`, `NodePort`, or `LoadBalancer`
- Ingress typically points to a Service of type `ClusterIP`
- The Service selects Pods by label and forwards traffic to them

### 5. ConfigMaps and Secrets
ConfigMaps and Secrets store configuration data for your apps.
- ConfigMap stores non-sensitive configuration values
- Secret stores sensitive data like passwords or TLS certificates
- Pods use them as environment variables or mounted files

### 6. PersistentVolume (PV) and PersistentVolumeClaim (PVC)
PV and PVC manage storage for stateful applications.
- PV is a storage volume in the cluster
- PVC is a request for storage from a Pod
- StatefulSets commonly use PVCs to give each Pod its own persistent disk

## Example: Demo app with Ingress
A typical demo setup includes:
1. A `Deployment` for the app Pods
2. A `Service` to expose the app internally
3. An `Ingress` to expose the app externally
4. Optional `ConfigMap` for configuration
5. Optional `Secret` for TLS or sensitive settings
6. Optional `PV` and `PVC` when the app needs persistent data

### Real-time use case
Imagine a website with two parts:
- `frontend` served from `/`
- `api` served from `/api`

Ingress can send:
- requests to `frontend-service` when the browser hits `/`
- requests to `api-service` when the browser hits `/api`

This means one external IP and one TLS certificate can serve both parts of the application.

## Simple Ingress flow
1. User requests `https://example.com`
2. Ingress controller receives the request
3. Ingress rules check host and path
4. Traffic is forwarded to the corresponding Service
5. Service forwards traffic to matching Pods

## Why this matters
Ingress makes applications easier to operate and secure by:
- reducing the number of public IPs needed
- centrally managing routing rules
- allowing certificates to be reused
- keeping service internals hidden from the outside world

## Notes for beginners
- Ingress only works when an Ingress controller is installed in the cluster
- The Ingress resource defines the rules; the controller implements them
- For simple testing, use a minimal Ingress controller like `nginx-ingress` or `traefik`

## Summary
- Use `Deployment` for stateless app Pods
- Use `StatefulSet` for stateful Pods and stable storage
- Use `Service` to expose Pods internally
- Use `Ingress` to expose services externally with routing and TLS
- Use `ConfigMap` and `Secret` for configuration and credentials
- Use `PV` and `PVC` for persistent storage

With these pieces, your Kubernetes apps can be structured, secure, and accessible from outside the cluster using a clean Ingress entry point.