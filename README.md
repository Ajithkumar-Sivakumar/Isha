# sample-app — EKS + ECR + GitHub Actions example

This folder contains a minimal Flask application and an end-to-end example for building and deploying a Docker image to Amazon ECR and running on Amazon EKS.

Important notes:
- The GitHub Actions workflow uses GitHub OIDC and requires an IAM role with a trust relationship to GitHub's OIDC provider. See `iam/gha-oidc-trust.json` and `iam/ecr-push-policy.json`.
- The workflow reads `AWS_REGION`, `AWS_ACCOUNT_ID` and `ECR_REPOSITORY` from repository secrets.

Project structure

sample-app/
├── app.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .github/
│   └── workflows/
│       └── docker-build.yml
└── k8s/
    ├── namespace.yaml
    ├── deployment.yaml
    ├── service.yaml
    └── ingress.yaml


Commands

Replace the example values with your own AWS account, region and repository name where needed.

Create ECR repository (local):
```bash
aws ecr create-repository --repository-name sample-app --region us-west-2
```

Build locally:
```bash
docker build -t sample-app:local .
```

Authenticate & push manually:
```bash
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
docker tag sample-app:local 123456789012.dkr.ecr.us-west-2.amazonaws.com/sample-app:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/sample-app:latest
```

Verify images in ECR (console or):
```bash
aws ecr describe-images --repository-name sample-app --region us-west-2
```

Deploy to EKS (requires `kubectl` configured for your cluster):
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
# Optional ingress
kubectl apply -f k8s/ingress.yaml
```

Useful kubectl checks:
```bash
kubectl get pods -n sample-app
kubectl get deploy -n sample-app
kubectl get svc -n sample-app
kubectl rollout status deployment/sample-app-deployment -n sample-app
kubectl describe pod <pod-name> -n sample-app
kubectl logs <pod-name> -n sample-app
```

Image pull / authentication explanation
-------------------------------------
- If your EKS worker nodes (or node IAM role) have permissions to pull from ECR (for example via an instance profile or IRSA with the right permissions), you do NOT need to create Kubernetes `imagePullSecrets`.
- When worker nodes use an IAM role, the kubelet on the node can call ECR to get authorization tokens on behalf of pods, so storing Docker credentials as secrets in Kubernetes is unnecessary and less secure.
- If you run self-managed nodes without proper IAM permissions, you must either configure `imagePullSecrets` with Docker credentials or give the node role ECR pull permissions....
