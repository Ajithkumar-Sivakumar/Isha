# Self-hosted GitHub Actions Runner — Troubleshooting & Setup

This guide explains how GitHub Actions runs jobs, how to install and manage a self-hosted runner, and how to diagnose common issues when jobs are queued or failing to run.

## How GitHub selects a runner for a job

- `runs-on: ubuntu-latest` (or `windows-latest`, `macos-latest`) uses GitHub-hosted runners.
- `runs-on: self-hosted` requires a runner you install and register with GitHub (repository or organization level).
- Additional labels like `Linux`, `X64`, or `aws` narrow which self-hosted runner can accept the job.
- If no matching runner is online, jobs remain queued until a matching runner becomes available.

## Quick checks (from your local machine)

1. Confirm GitHub Actions shows the runner as **Online**: Repository Settings → Actions → Runners.
2. If the runner is offline, check the host machine where the runner is installed.
3. Review recent workflow run logs in GitHub Actions — queued jobs indicate no matching runner.

## Install a self-hosted runner (Linux - systemd)

1. On the machine (e.g., EC2), create a folder and download the runner:

```bash
# Replace OWNER and REPO with your GitHub repository
OWNER=your-org-or-user
REPO=your-repo
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64.tar.gz
tar xzf ./actions-runner-linux-x64.tar.gz
```

2. Create a registration token (in the repository: Settings → Actions → Runners → New self-hosted runner)

3. Configure the runner with labels (for example: `self-hosted`, `Linux`, `X64`, `aws`):

```bash
./config.sh --url https://github.com/${OWNER}/${REPO} --token YOUR_TOKEN --labels self-hosted,Linux,X64,aws
```

4. Install and start the runner service (systemd):

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

5. Verify service status:

```bash
sudo systemctl status actions.runner.${REPO}.service
# or check journal logs
sudo journalctl -u actions.runner.${REPO}.service --no-pager -n 200
```

## Common issues & fixes

- Runner says "No matching labels": ensure the job's `runs-on` labels match exactly the runner labels.
- Runner is installed but offline: check `svc.sh status` / `systemctl` logs and ensure network access to `https://api.github.com`.
- Token expired during config: re-run `./config.sh` with a fresh token.
- Permissions errors when running Docker: add the runner user to `docker` group or run Docker-in-Docker carefully.

## How to check which labels a job requires

Open the workflow file and look for the `runs-on` key. Example:

```yaml
runs-on:
  - self-hosted
  - Linux
  - X64
  - aws
```

A runner must have all those labels to pick up the job.

## Debugging queued jobs

1. Go to the Actions run in the repository and look at the job — GitHub will say `waiting for a runner` or similar if it cannot find a runner.
2. Confirm at least one self-hosted runner with the matching labels is `Online` in repository settings.
3. On the runner host, check logs and service status (see above).
4. If necessary, temporarily change `runs-on` to `ubuntu-latest` for debugging to ensure the workflow steps themselves work.

## Logs and diagnostic files

- Runner logs are located in the runner installation directory under `_diag` or available via `journalctl` if installed as a service.
- Use the GitHub Actions UI to see when a job was queued and any messages about runner selection.

## Security notes

- Keep the runner host updated and locked down — actions executed on self-hosted runners run with the permissions of the runner user.
- Use organization-level runner groups if you need shared runner pools with controlled access.

---

If you want, I can also add a small `check-runner.sh` script to the repo to execute from the runner host and validate connectivity and Docker availability.