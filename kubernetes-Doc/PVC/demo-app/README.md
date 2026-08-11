# Demo Phonebook App

This is a simple phonebook demo app that stores contact entries in a file inside a Kubernetes PersistentVolume (PV) using a PersistentVolumeClaim (PVC).

## What this demo shows

- A Flask app that saves phonebook data to `/data/phonebook.json`
- A `PersistentVolume` (`pv.yaml`) that represents actual storage in the cluster
- A `PersistentVolumeClaim` (`pvc.yaml`) that requests storage from the cluster
- A `Deployment` (`deployment.yaml`) that mounts the PVC at `/data`
- A `Service` (`service.yaml`) to expose the app inside the cluster

## Why PV and PVC matter

- `PersistentVolume` (PV): a storage resource in Kubernetes. It is the actual volume.
- `PersistentVolumeClaim` (PVC): a request for storage by a pod. The pod does not care about the backend details.
- The app writes to `/data/phonebook.json`, and Kubernetes keeps that file on the volume even if the pod restarts.

## How the app stores data

1. The Flask app receives a request to add a phonebook entry.
2. It loads the JSON file from `/data/phonebook.json`.
3. It appends the new entry and writes the file back to the same path.
4. Because `/data` is backed by a PVC, the data persists across pod restarts.

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then use HTTP requests:

```bash
curl http://localhost:5000/entries
curl -X POST http://localhost:5000/entries -H 'Content-Type: application/json' -d '{"name":"Alice","phone":"555-1234"}'
curl -X DELETE http://localhost:5000/entries
```

## Build Docker image

```bash
docker build -t demo-phonebook:latest .
```

## Deploy to Kubernetes

Apply the manifest files in order:

```bash
kubectl apply -f pv.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Connect to the app in Kubernetes

If you use port-forwarding:

```bash
kubectl port-forward svc/demo-phonebook 5000:5000
```

Then use the same `curl` commands against `http://localhost:5000`.

## Files

- `app.py` - simple Flask phonebook service
- `Dockerfile` - builds the runtime image
- `pv.yaml` - PersistentVolume definition
- `pvc.yaml` - PersistentVolumeClaim definition
- `deployment.yaml` - Deployment with volume mount
- `service.yaml` - Service for app access
