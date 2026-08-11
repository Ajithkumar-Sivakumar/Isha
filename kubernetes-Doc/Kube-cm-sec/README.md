# Address Book App for Kubernetes Learning

This folder contains a simple Python container application for an address book. It is designed to support learning topics from Kubernetes Day 13 to Day 18.

## What the app includes
- A Flask web app with a simple address-book UI.
- A Dockerfile so the app can run as a container.
- Kubernetes manifests for Deployment, Service, ConfigMap, Secret, and PVC examples.

## Kubernetes topics covered
- Day 13: Kubernetes Overview, Architecture, Control Plane, Worker Nodes, Objects, Cluster Communication, Ecosystem.
- Day 14: Pod Architecture, Pod Lifecycle, Multi-Container Pods, Init Containers, Scheduling, Networking, Troubleshooting.
- Day 15: ReplicaSets, Deployments, Rolling Updates, Rollbacks, Scaling, Deployment Strategies, High Availability.
- Day 16: Service Discovery, ClusterIP, NodePort, LoadBalancer, ExternalName, Traffic Routing, Networking.
- Day 17: Configuration Management, Environment Variables, ConfigMaps, Secrets, Secret Management, Best Practices.
- Day 18: Persistent Volumes, PVCs, Storage Classes, Dynamic Provisioning, Stateful Apps, Data Persistence.

## Build and run locally
```bash
docker build -t address-book:latest .
docker run -p 8080:8080 address-book:latest
```

Open http://localhost:8080 to view the app.
