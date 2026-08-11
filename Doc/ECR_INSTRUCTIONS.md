# ECR Setup & GitHub Actions Integration

This document explains how to create an Amazon ECR repository, configure IAM permissions for GitHub Actions (recommended: GitHub OIDC), and add the necessary repository secrets for the `push-to-ecr` job in `.github/workflows/docker-build.yml`.

## 1) Create the ECR repository

Run locally with AWS CLI (or use AWS Console):

```bash
aws ecr create-repository --repository-name sample-app --region us-west-2
```

Replace `sample-app` and `us-west-2` with your repository name and region.

Verify:

```bash
aws ecr describe-repositories --repository-names sample-app --region us-west-2
```

## 2) GitHub Actions authentication options

Preferred: GitHub OIDC (no long-lived AWS keys)
Alternative: Use `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (less secure)

### 2A) GitHub OIDC (recommended)

1. In AWS, create an IAM role for GitHub Actions and allow the OIDC provider `token.actions.githubusercontent.com` to assume it. Example trust policy (replace ACCOUNT_ID and repo path):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/YOUR_REPO:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

2. Attach a policy granting ECR permissions to the role, example minimal actions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories",
        "ecr:CreateRepository"
      ],
      "Resource": "*"
    }
  ]
}
```

3. In GitHub repository secrets (Settings → Secrets and variables → Actions), add:

- `AWS_ACCOUNT_ID` — your AWS account ID
- `AWS_REGION` — e.g. `us-west-2`
- `ECR_REPOSITORY` — e.g. `sample-app`

The workflow uses the role ARN pattern: `arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/GitHubActionsOIDCRole`. If you used a different role name, update the workflow's `role-to-assume` value.

### 2B) Using AWS keys (alternative)

If you cannot use OIDC, store long-lived credentials (not recommended):

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `ECR_REPOSITORY`

Then update the workflow to use these environment variables or the `aws-actions/configure-aws-credentials` action with access keys.

## 3) How the workflow builds and pushes

The `push-to-ecr` job performs these steps:

1. Configures AWS credentials (via OIDC role assumed)
2. Verifies identity with `aws sts get-caller-identity`
3. Ensures the ECR repo exists (creates it if missing)
4. Logs into ECR: `aws ecr get-login-password | docker login ...`
5. Builds Docker image and tags it as `latest` and with commit SHA
6. Pushes both tags to ECR
7. Uploads `image-info.txt` as a workflow artifact containing the pushed image URI

## 4) Typical image URIs

Image URI format:

```
<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/<REPO>:<TAG>
```

Example:

```
123456789012.dkr.ecr.us-west-2.amazonaws.com/sample-app:abcdef12
```

## 5) Troubleshooting tips

- If `docker push` fails with `access denied`, check the assumed role permissions and that the runner can assume the role (OIDC). Run `aws sts get-caller-identity` in a workflow step to validate.
- If `aws ecr describe-repositories` returns `RepositoryNotFoundException`, the repository name may differ; create it or correct the name.
- Check that the runner has Docker installed (`docker --version`) and the runner user can run Docker commands.

---

If you want, I can also add a sample minimal IAM CloudFormation / Terraform snippet to provision the role and policy automatically.