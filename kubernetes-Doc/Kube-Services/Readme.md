# Kubernetes Services & Networking

## Topics

* Service Discovery
* ClusterIP
* NodePort
* LoadBalancer
* ExternalName
* Traffic Routing
* Kubernetes Networking

---

# What is a Kubernetes Service?

A **Service** provides a fixed IP address and DNS name to access Pods.

Since Pod IPs change whenever Pods are recreated, applications should communicate through a Service instead of directly using Pod IPs.

---

# Why Do We Need a Service?

Without Service:

* Pod IP changes after restart.
* Applications cannot find the Pod.

With Service:

* Service IP remains the same.
* Traffic is automatically sent to healthy Pods.

---

# Service Discovery

Service Discovery means finding an application using its **Service name** instead of its IP address.

Example:

```text
Frontend
    ↓
backend-service
    ↓
Backend Pods
```

Kubernetes automatically resolves the Service name using **CoreDNS**.

---

# ClusterIP

### What is it?

* Default Service type.
* Accessible only inside the Kubernetes cluster.

### Use Case

Communication between internal applications.

Example:

```text
Frontend
    ↓
ClusterIP Service
    ↓
Backend Pods
```

---

# NodePort

### What is it?

* Exposes the application using the Node's IP and a port.
* Default port range: **30000–32767**

Example:

```text
http://NodeIP:30080
```

### Use Case

* Testing
* Small environments

---

# LoadBalancer

### What is it?

Creates a cloud Load Balancer and exposes the application to the internet.

Supported in:

* AWS
* Azure
* Google Cloud

Example:

```text
Users
   ↓
Load Balancer
   ↓
Service
   ↓
Pods
```

### Use Case

Production applications.

---

# ExternalName

### What is it?

Maps a Kubernetes Service to an external DNS name.

Example:

```text
database-service
      ↓
database.company.com
```

### Use Case

Connecting to external databases or APIs.

---

# Traffic Routing

A Service automatically distributes requests to available Pods.

Example:

```text
Service
 │
 ├── Pod 1
 ├── Pod 2
 └── Pod 3
```

If one Pod fails, traffic is sent to the remaining healthy Pods.

---

# Kubernetes Networking

Kubernetes networking allows Pods and Services to communicate with each other.

### Key Points

* Every Pod gets its own IP.
* Pods can communicate with each other.
* Services provide a stable IP.
* CoreDNS resolves Service names.
* kube-proxy forwards traffic to Pods.

---

# Service Comparison

| Service Type | Internal | External | Common Use             |
| ------------ | -------- | -------- | ---------------------- |
| ClusterIP    | ✅        | ❌        | Internal communication |
| NodePort     | ✅        | ✅        | Testing & Learning     |
| LoadBalancer | ✅        | ✅        | Production             |
| ExternalName | DNS Only | DNS Only | External Services      |

---

# Useful Commands

Create Service

```bash
kubectl apply -f service.yaml
```

View Services

```bash
kubectl get svc
```

Describe Service

```bash
kubectl describe svc <service-name>
```

Delete Service

```bash
kubectl delete svc <service-name>
```

View Endpoints

```bash
kubectl get endpoints
```

---

# Summary

* A Service provides a stable way to access Pods.
* Service Discovery uses DNS names instead of Pod IPs.
* ClusterIP is for internal communication.
* NodePort exposes applications using a Node IP and port.
* LoadBalancer exposes applications to the internet.
* ExternalName connects to external DNS services.
* Kubernetes automatically routes traffic to healthy Pods.