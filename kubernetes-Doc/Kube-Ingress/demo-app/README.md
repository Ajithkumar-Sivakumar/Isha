# Phone Demo App for Ingress

This demo app shows a simple phone catalog service that can be exposed through an Ingress controller.

## What it includes
- `app.py`: Flask app with a phone catalog and inventory endpoint
- `Dockerfile`: Container image build
- `deployment.yaml`: Deployment with 2 replicas and a PVC mount
- `service.yaml`: ClusterIP service for internal routing
- `pv.yaml` / `pvc.yaml`: Persistent storage for the app's inventory file
- `requirements.txt`: Python dependency

## App behavior
- `/` returns an HTML page with a sample phone list
- `/api/phones` returns JSON phone data
- `/inventory` reads a file from mounted storage
- `/health` returns a health check response

## How Ingress would use this app
1. Ingress receives external traffic
2. It routes requests to `phone-demo-service`
3. `phone-demo-service` forwards traffic to the `phone-demo` Pods
4. The Pods serve the Flask app on port 5000

## Example Ingress paths
- `/` -> phone app homepage
- `/api/phones` -> phone list API
- `/inventory` -> persistent data endpoint

## Deployment notes
- The Deployment uses a `ConfigMap` and `Secret` for environment values
- The pod mounts a PVC at `/data`
- The app writes inventory data to `/data/inventory.txt`

## Build and run
1. Build the image: `docker build -t phone-demo:latest .`
2. Apply storage: `kubectl apply -f pv.yaml -f pvc.yaml`
3. Apply config and secret if available
4. Apply deployment and service: `kubectl apply -f deployment.yaml -f service.yaml`
5. Add an Ingress rule to point to `phone-demo-service`
