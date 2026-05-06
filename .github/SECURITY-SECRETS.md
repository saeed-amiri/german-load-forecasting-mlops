# CI/CD Secrets Policy

All credentials and sensitive configuration used by workflows must be stored in GitHub repository secrets.

## Required repository secrets

- `DISCORD_WEBHOOK_URL`: Deploy notifications webhook URL.
- `DAGSHUB_REPO`: DagsHub repository slug (`owner/repo`) for MLflow tracking.
- `DAGSHUB_USERNAME`: DagsHub username for MLflow authentication.
- `DAGSHUB_TOKEN`: DagsHub access token for MLflow authentication.
- `DVC_REMOTE_USERNAME`: Username for DVC remote authentication.
- `DVC_REMOTE_PASSWORD`: Password or token for DVC remote authentication.

## Optional repository variables

- `CI_ALERT_DURATION_MINUTES`: Duration threshold in minutes for long-run alerts (default: `30`).
- `CI_MONITOR_LOOKBACK_HOURS`: Lookback window for scheduled monitoring job (default: `168`).

## Rules

- Never hardcode tokens, passwords, API keys, or webhooks in workflow YAML.
- Reference secrets only via `${{ secrets.NAME }}`.
- Do not print secret values in logs.
- Keep job and workflow `permissions` minimal (least privilege).
- Rotate secrets periodically and after any suspected exposure.

## Setup path in GitHub

`Repository -> Settings -> Secrets and variables -> Actions -> New repository secret`
