# Phone Demo App for Ingress

This demo app shows a simple phone catalog service that can be exposed through an Ingress controller.

## What it includes
- `app.py`: Flask app with a phone catalog and inventory endpoint
- `Dockerfile`: Container image build
- `deployment.yaml`: Deployment with 2 replicas and a PVC mount
- `service.yaml`: ClusterIP service for internal routing
- `ingress.yaml`: exposes the Service outside the cluster through host-based routing
- `pv.yaml` / `pvc.yaml`: Persistent storage for the app's inventory file
- `configmap.yaml` / `secret.yaml`: configuration and environment values
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

## Deploy this on Minikube

### 1. Start Minikube
```bash
minikube start
```

### 2. Enable the Ingress controller
```bash
minikube addons enable ingress
```

### 3. Create the namespace
```bash
kubectl apply -f namespace.yaml
```

### 4. Build the application image
```bash
docker build -t phone-demo:latest .
```

### 5. Load the image into Minikube
```bash
minikube image load phone-demo:latest
```

### 6. Apply the application resources
```bash
kubectl apply -f pv.yaml
kubectl apply -f pvc.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

### 7. Check the status
```bash
kubectl get pods -n phone-demo
kubectl get svc -n phone-demo
kubectl get ingress -n phone-demo
```

### 8. Access the app from your browser
Because `phone-demo.local` is not a real public DNS name, we map the Minikube IP to that hostname on the local machine:

```bash
echo "$(minikube ip) phone-demo.local" | sudo tee -a /etc/hosts
```

Then open:
```text
http://phone-demo.local/
```

Or test it from the terminal without editing the hosts file:
```bash
curl --resolve phone-demo.local:80:$(minikube ip) http://phone-demo.local/
```

## How ingress works in this demo

This is the easiest way to explain it to a student:

1. The student types `http://phone-demo.local/` in the browser.
2. The browser sends a request to the Minikube IP.
3. The NGINX Ingress controller running inside Minikube receives the request on port 80.
4. The Ingress rule checks the host and path.
5. The rule matches `phone-demo.local` and `/`.
6. The controller forwards the request to the Service named `phone-demo-service`.
7. The Service selects the matching Pods and forwards traffic to them.
8. The Pods run the Flask app on port 5000 and return the HTML or JSON response.

In short:

Browser -> Ingress -> Service -> Pod

## Why we need all these objects
- `Deployment`: creates the app Pods
- `Service`: gives the app a stable internal name and IP
- `Ingress`: exposes that Service outside the cluster using a host and path
- `PVC`: keeps the app data on persistent storage
- `Namespace`: keeps this app isolated from other workloads

## Student-friendly summary
"Ingress is the front door of the application. A Service is the internal door inside the cluster, and the Pod is the actual app running the code. Ingress decides where traffic should go based on the hostname and URL path."

This example keeps all app resources inside the `phone-demo` namespace so you can explain how namespaces separate different applications in the same cluster.
