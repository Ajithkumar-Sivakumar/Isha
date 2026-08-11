# Deployment vs StatefulSet vs DaemonSet

| Feature | Deployment | StatefulSet | DaemonSet |
|----------|------------|-------------|-----------|
| **Purpose** | Deploy stateless applications | Deploy stateful applications | Run one Pod on every node |
| **Best For** | Web Apps, APIs, Microservices | Databases, Kafka, Redis, Elasticsearch | Monitoring, Logging, Networking, Security |
| **Pod Identity** | Random pod names | Stable and unique pod names | One pod per node |
| **Pod Name** | Changes when recreated | Never changes (e.g., mysql-0) | Changes only if the node changes |
| **Hostname** | Dynamic | Stable | Based on the node |
| **Persistent Storage** | Optional / Shared | Dedicated storage for each Pod | Usually uses host storage (`hostPath`) |
| **Scaling** | Manual or Auto (HPA) | Manual or Auto (Ordered) | Automatic (one Pod per node) |
| **Pod Creation Order** | Parallel | Sequential (0 → 1 → 2) | One Pod created on each node |
| **Pod Deletion Order** | Any order | Reverse order (2 → 1 → 0) | Removed when the node is removed |
| **Load Balancing** | Supported through Service | Usually Headless Service | Not applicable |
| **Rolling Updates** | Supported | Supported (Ordered) | Supported |
| **High Availability** | Multiple replicas | Multiple replicas with stable identity | One replica per node |
| **Storage Requirement** | Not mandatory | Mandatory for most workloads | Usually not required |
| **Typical Kubernetes Object** | Deployment | StatefulSet | DaemonSet |
| **Real-World Examples** | Nginx, React, Spring Boot, Node.js APIs | MySQL, PostgreSQL, MongoDB, Kafka, Redis Cluster | Fluentd, Prometheus Node Exporter, Calico, Falco, Filebeat |
| **When a Pod Crashes** | New Pod with a new identity is created | Same Pod name and storage are restored | Pod is recreated only on the same node if available |
| **When a New Node is Added** | No new Pod unless scaled | No new Pod unless scaled | Automatically creates one Pod on the new node |
| **Example Replica Behavior** | `replicas: 3` creates any 3 Pods | `replicas: 3` creates `app-0`, `app-1`, `app-2` | Ignores replicas; one Pod runs on every node |

## Summary

| Workload Type | Recommended Controller |
|---------------|------------------------|
| Stateless Applications | ✅ Deployment |
| Databases & Stateful Applications | ✅ StatefulSet |
| Monitoring Agents | ✅ DaemonSet |
| Logging Agents | ✅ DaemonSet |
| Network Plugins (CNI) | ✅ DaemonSet |
| Security Agents | ✅ DaemonSet |
| Web Applications | ✅ Deployment |
| Message Brokers (Kafka, RabbitMQ) | ✅ StatefulSet |