<table>
  <thead>
    <tr>
      <th>Pattern</th>
      <th>Purpose</th>
      <th>Common Tools</th>
    </tr>
  </thead>
  <tbody>
    <tr><td><b>Sidecar</b></td><td>Extend application functionality</td><td>Fluent Bit, Envoy</td></tr>
    <tr><td><b>Ambassador</b></td><td>Proxy external services</td><td>Nginx, HAProxy, Envoy</td></tr>
    <tr><td><b>Adapter</b></td><td>Transform data formats</td><td>Fluentd, Logstash</td></tr>
    <tr><td><b>Init Container</b></td><td>Perform startup initialization</td><td>BusyBox, Alpine</td></tr>
    <tr><td><b>Helper</b></td><td>Background maintenance tasks</td><td>BusyBox, Cron</td></tr>
    <tr><td><b>Logging</b></td><td>Collect and forward logs</td><td>Fluent Bit, Filebeat</td></tr>
    <tr><td><b>Monitoring</b></td><td>Export metrics</td><td>Prometheus Exporters</td></tr>
    <tr><td><b>Proxy</b></td><td>Control network traffic</td><td>Envoy, Nginx</td></tr>
    <tr><td><b>Security</b></td><td>Security and secrets management</td><td>Vault Agent, Falco</td></tr>
    <tr><td><b>Git Sync</b></td><td>Synchronize Git content</td><td>git-sync</td></tr>
    <tr><td><b>File Processing</b></td><td>Process shared files</td><td>Custom worker containers</td></tr>
    <tr><td><b>Cache</b></td><td>Improve application performance</td><td>Redis, Memcached</td></tr>
  </tbody>
</table>

Connect the K3s or K8s and delpoy the pods in that with below commands.

kubectl apply -f filename.yaml

Since, the namesapce is not menioned in the file the pod will be added in the default namespace

kubectl get pods -- Verify the pods status

Describe the pod and check the events and other details with the below command

kubectl describe pod pod-name

Get the logs for the secondary container

kubectl logs pod-name -c secondary-container

Get in to the app container

kubectl exec -it pod-name -c application-container -- sh  

Get in to the secondary container

kubectl exec -it pod-name -c secondary-container -- sh

Delete the pod

kubectl delete pod pod-name