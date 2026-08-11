# Kubernetes Storage Study Guide: PersistentVolume (PV) and PersistentVolumeClaim (PVC)

This study guide explains Kubernetes persistent storage concepts in depth. It is designed for students who need a strong foundation in `PersistentVolume` and `PersistentVolumeClaim` behavior, usage, and real-world importance.

## 1. What is a PersistentVolume (PV)?

A `PersistentVolume` is a cluster-level storage resource in Kubernetes. It represents a piece of physical or virtual storage available to the cluster.

### Key characteristics of a PV
- **Cluster resource**: PVs exist independently from pods and deployments.
- **Storage backend**: The volume can be backed by a local host path, NFS server, cloud disk (AWS EBS, GCE PD, Azure Disk), iSCSI, Ceph, and more.
- **Capacity**: Defines how much space is available, for example `1Gi`, `5Gi`, or `20Gi`.
- **Access modes**: Defines how pods can mount the volume:
  - `ReadWriteOnce` (RWO): mounted as read-write by a single node.
  - `ReadOnlyMany` (ROX): mounted read-only by many nodes.
  - `ReadWriteMany` (RWX): mounted as read-write by many nodes.
- **Reclaim policy**: Controls what happens to the data after the claim is released:
  - `Retain`: keep data after release.
  - `Recycle`: delete contents (deprecated in newer Kubernetes versions).
  - `Delete`: delete the volume and underlying storage.

### Example `pv.yaml`
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: demo-phonebook-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /tmp/demo-phonebook-pv
    type: DirectoryOrCreate
```

## 2. What is a PersistentVolumeClaim (PVC)?

A `PersistentVolumeClaim` is a request for storage by a pod or application. It is similar to a pod requesting CPU or memory.

### Key characteristics of a PVC
- **User-facing request**: The developer or application author defines the required size and access mode.
- **Decoupled from storage details**: The app does not need to know the storage backend.
- **Binding**: Kubernetes matches the PVC to an available PV.
- **Lifecycle**: The PVC exists while the pod needs the storage and is released when the pod is deleted.

### Example `pvc.yaml`
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: demo-phonebook-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: manual
```

## 3. How PV and PVC work together

### Static provisioning
1. An administrator creates a `PersistentVolume` definition.
2. The PV becomes available in the cluster.
3. An application creates a `PersistentVolumeClaim`.
4. Kubernetes finds a matching PV and binds them together.
5. The pod mounts the PVC as a volume inside the container.

### Dynamic provisioning
- A `StorageClass` defines how to create PVs automatically.
- When a PVC is created with a `storageClassName`, Kubernetes can provision a PV dynamically.
- This removes the need for administrators to create PVs manually.

## 4. Why persistent storage is important

Containers and pods are ephemeral by design. When a pod restarts, the container filesystem is recreated and all data inside the container is lost unless it is stored on a shared volume.

PV/PVC solves this problem by:
- preserving data across pod restarts and reschedules
- letting storage outlive individual pods
- separating application logic from storage management
- enabling data durability for stateful workloads

This is important for:
- databases (MySQL, PostgreSQL, MongoDB)
- message queues
- file servers
- logs and audit data
- application state and configuration files

## 5. Real-time usage example: phonebook demo

In the phonebook demo app, the Flask code writes data to `/data/phonebook.json`. The Kubernetes manifest mounts the PVC at `/data`.

### Why this is explainable
- The app only writes to a file path.
- Kubernetes attaches actual storage behind that path.
- When the pod restarts, the file still exists because it is stored on the PV.

### Deployment flow
1. Apply `pv.yaml`: create the storage volume.
2. Apply `pvc.yaml`: request the storage.
3. Apply `deployment.yaml`: start the pod and mount the PVC.
4. Apply `service.yaml`: expose the app.

### Accessing the demo app
```bash
kubectl port-forward svc/demo-phonebook 5000:5000
curl http://localhost:5000/entries
curl -X POST http://localhost:5000/entries \
  -H 'Content-Type: application/json' \
  -d '{"name":"Alice","phone":"555-1234"}'
```

### Verify persistence
1. Add an entry through the API.
2. Delete the pod with `kubectl delete pod -l app=demo-phonebook`.
3. Wait for the pod to restart.
4. Query the entries again.

If persistence is working, the entry is still present.

## 6. Common PV/PVC terms

- **Volume**: generic storage abstraction in Kubernetes.
- **PersistentVolume (PV)**: cluster resource representing storage.
- **PersistentVolumeClaim (PVC)**: request for storage by a pod.
- **StorageClass**: defines provisioning and parameters for PV creation.
- **AccessMode**: read/write rules for how pods can mount storage.
- **ReclaimPolicy**: what happens to storage after release.
- **Bound**: the state when a PVC is attached to a PV.

## 7. Binding states and lifecycle

A PVC can be in one of these states:
- `Pending`: waiting for a matching PV.
- `Bound`: successfully matched to a PV.
- `Lost`: the PV is no longer available.

A PV can be in these states:
- `Available`: not yet claimed.
- `Bound`: attached to a PVC.
- `Released`: the claim was deleted but the PV is not yet reclaimed.
- `Failed`: the volume is unusable.

## 8. Storage class and dynamic provisioning (extended learning)

A `StorageClass` is useful when you want storage to be created automatically. It contains a provisioner and optional parameters.

Example:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-storage
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
reclaimPolicy: Delete
volumeBindingMode: Immediate
```

If a PVC requests `storageClassName: fast-storage`, Kubernetes creates a PV automatically.

## 9. Practical notes for students

- Always choose the right access mode for your app.
- Use `ReadWriteOnce` for most single-writer workloads.
- Use `ReadWriteMany` only when the underlying storage supports it.
- Use `Retain` for data you cannot afford to delete accidentally.
- Use `Delete` for temporary storage that should clean up automatically.
- Understand that a PVC is not a volume by itself; it is a claim.
- The pod always consumes the PVC, not the PV directly.

## 10. Debugging PV/PVC issues

### Check PVC status
```bash
kubectl get pvc
kubectl describe pvc demo-phonebook-pvc
```

### Check PV status
```bash
kubectl get pv
kubectl describe pv demo-phonebook-pv
```

### Common problems
- PVC stays `Pending`: no matching PV exists.
- PV is `Available` but not bound: the access mode or storage class does not match.
- Pod cannot mount volume: check pod events and the claim name.
- Data disappears after pod restart: volume may not be mounted or the PV/PVC is misconfigured.

## 11. Summary

- `PV` is the actual storage resource managed by Kubernetes.
- `PVC` is a request from a pod for storage.
- PV and PVC let pods use durable storage that outlives the pod lifecycle.
- This is essential for any stateful application running in Kubernetes.

Use this guide alongside the `demo-app` to see the concept in action and to explain persistent storage clearly to students.
