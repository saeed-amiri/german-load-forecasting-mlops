# german-load-forecasting-mlops
### *MLOps Platform for German Electricity Load Forecasting and Grid Anomaly Detection*

# What
**Project Idea**  
> A production-ready MLOPS sytem that forecast short-term electricity load in Germany and detects anomalies in consumpation patterns.

<details>

### Output of the system: 
- Hourly / day-ahead electricity demand forecast for Germany  
- Detection of abnormal consumption patterns (spikes, drops, sensor errors, etc.) → Anomaly detectiin  
- Automated monitoring of model performance and data drift  

### Prediction target:
- Hourly load forecast
- Day-ahead forecast

## Data Sources:
- **ENTSO-E Transparency Platform**: Provides historical and real-time electricity load data for Germany  
- **Open Power System Data**: Offers comprehensive datasets on electricity generation, consumption, and weather data for Germany  
- **Weather Data**: Historical and forecasted weather data from sources like OpenWeatherMap or Meteostat, which can be crucial for load forecasting  

</details>


# Why
**Motivation**
> Accurate load forecasting is essential for grid stability, efficient energy management, and cost optimization. Anomalies in consumption patterns can indicate issues such as equipment failures, cyber-attacks, or unexpected demand surges. By building a robust MLOps pipeline, we can ensure that our forecasting models are reliable, scalable, and maintainable in a production environment.

<details>

### Why anomaly detetection is matters:
Operational systems must detect anomalies like:  
- sensor failures  
- missing telemetry  
- unexpected demand spikes  
- grid disturbances  

</details>

# How
**Approach**
> We will implement a complete MLOps pipeline that includes data ingestion, model training, deployment, and monitoring. The pipeline will be designed to handle the specific challenges of load forecasting and anomaly detection, such as time-series data, seasonality, and the need for real-time predictions.

<details>

```text
Data sources  
     ↓  
Data ingestion pipeline  
     ↓  
Feature engineering  
     ↓  
Training pipeline  
     ↓  
Model registry  
     ↓  
Prediction service (API)  
     ↓  
Monitoring + drift detection  
     ↓  
Automatic retraining  

</details>
```

# Access Links And Curl Cheat Sheet

This section is a quick reference for checking all running services.

## Through Nginx (single entrypoint)

Base URL:
- http://localhost:8080

Links:
- API home: http://localhost:8080/api/
- API health: http://localhost:8080/api/health
- API alert webhook: http://localhost:8080/api/alert
- Auth login: http://localhost:8080/auth/login
- Auth register: http://localhost:8080/auth/register
- Auth protected: http://localhost:8080/auth/protected
- Auth admin-only: http://localhost:8080/auth/admin-only
- Auth user-only: http://localhost:8080/auth/user-only
- Airflow UI: http://localhost:8080/airflow/
- Prometheus: http://localhost:8080/prometheus/
- Alertmanager: http://localhost:8080/alerts/
- Grafana: http://localhost:8080/grafana/
- Node Exporter metrics: http://localhost:8080/node/metrics
- cAdvisor: http://localhost:8080/cadvisor/

## Standalone / Direct Ports (without nginx)

When using debug overrides (docker-compose.debug.yml):
- API: http://127.0.0.1:8000
- Auth: http://127.0.0.1:8002
- Airflow UI: http://127.0.0.1:8082
- Prometheus: http://127.0.0.1:9090
- Alertmanager: http://127.0.0.1:9093
- Node Exporter: http://127.0.0.1:9100/metrics
- cAdvisor: http://127.0.0.1:8081/cadvisor/

## Curl Commands (Nginx)

```bash
# API health
curl -fsS http://localhost:8080/api/health

# API alert webhook
curl -fsS -X POST http://localhost:8080/api/alert \
     -H 'Content-Type: application/json' \
     -d '{"alerts":[]}'

# Register user
curl -fsS -X POST http://localhost:8080/auth/register \
     -H 'Content-Type: application/json' \
     -d '{"username":"demo","password":"demo123","role":"user"}'

# Login
curl -fsS -X POST http://localhost:8080/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"demo","password":"demo123"}'

# Optional: extract token with jq
TOKEN=$(curl -fsS -X POST http://localhost:8080/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"demo","password":"demo123"}' | jq -r '.access_token')

# Protected endpoint
curl -fsS http://localhost:8080/auth/protected \
     -H "Authorization: Bearer $TOKEN"

# RBAC checks
curl -i http://localhost:8080/auth/admin-only \
     -H "Authorization: Bearer $TOKEN"
curl -i http://localhost:8080/auth/user-only \
     -H "Authorization: Bearer $TOKEN"

# Airflow web UI availability
curl -I http://localhost:8080/airflow/
```

## Curl Commands (Direct Auth Port)

```bash
# Register user directly against auth service
curl -fsS -X POST http://127.0.0.1:8002/auth/register \
     -H 'Content-Type: application/json' \
     -d '{"username":"direct","password":"direct123","role":"user"}'

# Login directly
curl -fsS -X POST http://127.0.0.1:8002/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"direct","password":"direct123"}'

# Airflow UI directly (debug profile)
curl -I http://127.0.0.1:8082
```

## Useful Startup Commands

```bash
# Full stack behind nginx
docker compose up

# With direct debug ports exposed
docker compose -f docker-compose.yml -f docker-compose.debug.yml up
```

## Airflow Admin Credentials Recovery

If Airflow is reachable but login fails, reset the admin user from values in .env.

Required .env keys:
- AIRFLOW_ADMIN_USERNAME
- AIRFLOW_ADMIN_PASSWORD
- AIRFLOW_ADMIN_EMAIL
- AIRFLOW_ADMIN_FIRSTNAME
- AIRFLOW_ADMIN_LASTNAME
- AIRFLOW_ADMIN_ROLE

Reset/recreate the admin user:

```bash
make airflow-reset-admin
```

Expected result:
- Admin user is recreated with the configured username and password.
- You can sign in at http://localhost:8080/airflow/login/

If your browser still rejects login after reset:
1. Open an incognito/private window.
2. Retry with your .env credentials.

Rotate credentials safely:
1. Update AIRFLOW_ADMIN_PASSWORD (and optional username/email fields) in .env.
2. Run `make airflow-reset-admin`.
3. Sign in again with the new credentials.

Validate key Prometheus targets after startup:

```bash
make prometheus-targets-check
```

This check verifies the critical targets fixed in this stack:
- cadvisor
- grafana

Prometheus Targets tab note:
- Endpoint values shown there (for example `http://alertmanager:9093/metrics`) are internal Docker-network scrape URLs used by Prometheus.
- They are not nginx redirect URLs and are not intended to be host-browser-friendly.
- `up` in the Targets table means scraping is working correctly.

Browser-friendly metrics URLs (via nginx):
- http://localhost:8080/alerts/metrics
- http://localhost:8080/cadvisor/metrics
- http://localhost:8080/grafana/metrics
- http://localhost:8080/node/metrics

# How To Use Auth Step By Step

This is the practical flow to use auth without confusion.

## Step 1: Start the stack

```bash
docker compose up
```

If you only want direct ports for testing:

```bash
docker compose -f docker-compose.yml -f docker-compose.debug.yml up
```

## Step 2: Register a user (create account)

Use register once per username.

```bash
curl -sS -X POST http://localhost:8080/auth/register \
     -H 'Content-Type: application/json' \
     -d '{"username":"alice","password":"alice123","role":"user"}'
```

Expected result:
- You get `access_token` in response.
- You also get `username`, `role`, and `token_type`.

Important:
- You cannot get the raw password back later.
- Passwords are stored as hashes for security.

## Step 3: Login with username and password

Login is how you get a fresh token any time.

```bash
curl -sS -X POST http://localhost:8080/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"alice","password":"alice123"}'
```

Expected result:
- Response includes `access_token`.

If password is wrong:
- You get `401 Invalid username or password`.

## Step 4: Save token to shell variable

```bash
TOKEN=$(curl -sS -X POST http://localhost:8080/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"alice","password":"alice123"}' | jq -r '.access_token')

echo "$TOKEN"
```

If `jq` is not installed, copy token manually from login response.

## Step 5: Call protected endpoint with Bearer token

```bash
curl -sS http://localhost:8080/auth/protected \
     -H "Authorization: Bearer $TOKEN"
```

Expected result:
- Access granted and token payload in response.

If token missing or invalid:
- You get `401 Invalid or expired token`.

## Step 6: Test role-based routes (RBAC)

User token:

```bash
curl -i http://localhost:8080/auth/user-only \
     -H "Authorization: Bearer $TOKEN"
```

Admin route with same user token:

```bash
curl -i http://localhost:8080/auth/admin-only \
     -H "Authorization: Bearer $TOKEN"
```

Expected result:
- `user-only` succeeds for role `user`.
- `admin-only` returns `403 Insufficient permissions` for role `user`.

## Step 7: Common mistakes and fixes

1. `401` on protected route:
- Check you sent header exactly as `Authorization: Bearer <token>`.

2. `401` right after login:
- Ensure auth secret config is stable and services were restarted cleanly.

3. `400 User already exists` on register:
- Choose a new username, or login with existing credentials.

4. `403` on admin route:
- Use a token created for a user with role `admin`.

## One-command quick demo

```bash
curl -sS -X POST http://localhost:8080/auth/register \
     -H 'Content-Type: application/json' \
     -d '{"username":"demo-user","password":"demo123","role":"user"}' >/dev/null

TOKEN=$(curl -sS -X POST http://localhost:8080/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"demo-user","password":"demo123"}' | jq -r '.access_token')

curl -sS http://localhost:8080/auth/protected \
     -H "Authorization: Bearer $TOKEN"
```