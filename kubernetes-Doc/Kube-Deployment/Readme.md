## Kubernetes Deployments

<details>
<summary><b>🔹 Deployment 1: Basic Deployment</b></summary>

* [x] **Theory:** Fundamentals of Kubernetes Deployments
* [x] **Architecture:** How Deployment controllers manage ReplicaSets and Pods
* [x] **Complete YAML:** Manifest configuration
* [x] **Line-by-line Explanation:** Detailed breakdown of specs
* [x] **kubectl Commands:** Deployment, updating, and deletion
* [x] **Expected Output:** What terminal responses should look like
* [x] **Validation:** Verifying deployment status
* [x] **Interview Questions:** Top questions & answers
* [x] **Troubleshooting:** Common issues and fixes

</details>

<details>
<summary><b>🔹 Deployment 2: Labels</b></summary>

* [x] **Theory:** Purpose of labels in Kubernetes
* [x] **Complete YAML:** Deployment with labels
* [x] **Why Labels?:** Service discovery and Pod selection
* [x] **Commands:** Filtering and querying by label selectors
* [x] **Validation:** Checking label matching
* [x] **Real-time Example:** Microservices labeling strategy
* [x] **Interview Questions:** Common interview scenarios

</details>

<details>
<summary><b>🔹 Deployment 3: Annotations</b></summary>

* [x] **Complete YAML:** Deployment with non-identifying metadata
* [x] **Commands:** Adding and updating annotations dynamically
* [x] **Validation:** Inspecting metadata via `kubectl describe`
* [x] **Production Example:** Ingress controls, release notes, and tooling integration

</details>

<details>
<summary><b>🔹 Deployment 4: Resources</b></summary>

* [x] **Requests:** Soft guarantees for container scheduling
* [x] **Limits:** Hard caps to prevent resource exhaustion
* [x] **CPU:** Millicores allocation
* [x] **Memory:** MiB/GiB allocation & OOMKilled handling
* [x] **Scheduling:** Impact of resource definitions on node placement
* [x] **Validation:** Monitoring actual usage vs limits

</details>

<details>
<summary><b>🔹 Deployment 5: Environment Variables</b></summary>

* [x] **`env`:** Static key-value pairs
* [x] **`envFrom`:** Bulk injection from external sources
* [x] **ConfigMap Integration:** Decoupling configuration from image builds
* [x] **Validation:** Executing into Pods to inspect runtime environments

</details>

<details>
<summary><b>🔹 Deployment 6: Health Checks</b></summary>

* [x] **Liveness Probe:** Detecting & recovering from deadlocks
* [x] **Readiness Probe:** Controlling traffic routing to ready Pods
* [x] **Startup Probe:** Handling slow-starting legacy applications
* [x] **Commands:** Configuring HTTP, TCP, and Exec probes
* [x] **Validation:** Simulating application failures

</details>

<details>
<summary><b>🔹 Deployment 7: Volumes</b></summary>

* [x] **`emptyDir`:** Temporary scratch space lifecycle
* [x] **`hostPath`:** Mounting host node filesystem
* [x] **PVC Introduction:** PersistentVolumeClaims setup
* [x] **Validation:** Testing data persistence across Pod restarts

</details>

<details>
<summary><b>🔹 Deployment 8: Deployment Strategy</b></summary>

* [x] **Rolling Update:** Zero-downtime updates
* [x] **Recreate:** All-at-once update strategy
* [x] **`maxSurge`:** Controlling extra Pod creation rate
* [x] **`maxUnavailable`:** Controlling dropped capacity during updates
* [x] **Validation:** Observing rollouts and performing rollbacks

</details>

<details>
<summary><b>🔹 Deployment 9: Node Selector</b></summary>

* [x] **Labels:** Assigning attributes to Kubernetes nodes
* [x] **Scheduling:** Simple node constraint rules
* [x] **Commands:** Labeling nodes and binding Pods

</details>

<details>
<summary><b>🔹 Deployment 10: Tolerations</b></summary>

* [x] **Taints:** Repelling Pods from specific nodes
* [x] **Tolerations:** Allowing Pods to schedule on tainted nodes
* [x] **Scheduling Demo:** Practical node dedication scenarios

</details>

<details>
<summary><b>🔹 Deployment 11: Affinity</b></summary>

* [x] **Node Affinity:** Advanced rules for node targeting (required vs preferred)
* [x] **Pod Affinity:** Co-locating Pods on the same topology domain
* [x] **Pod Anti-Affinity:** Spreading Pods across nodes for high availability
* [x] **Validation:** Inspecting Pod distribution across the cluster

</details>

<details>
<summary><b>🔹 Deployment 12: Production Deployment</b></summary>

* [x] **Full Production YAML:** Complete battle-tested template
* [x] **Resources:** Tight requests & limits
* [x] **Health Checks:** Full Liveness, Readiness, & Startup probes
* [x] **Security Context:** Non-root execution & read-only root filesystems
* [x] **Service Account:** Least-privilege RBAC binding
* [x] **Affinity:** High-availability scheduling rules
* [x] **Tolerations:** Edge-case node scheduling
* [x] **Volumes:** Secure config and state mounts
* [x] **Strategy:** Zero-downtime rolling update parameters
* [x] **Image Pull Policy:** Safe image fetch settings (`Always` / `IfNotPresent`)

</details>

---

```bash

kubectl apply -f deployment.yaml