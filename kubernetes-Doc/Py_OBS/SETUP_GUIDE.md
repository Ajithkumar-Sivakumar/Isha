# Logistics API - Setup Guide (Python/Flask)



## Step 2: Clone the Repository

Open a terminal in VS Code (`` Ctrl+` ``) and run:

```bash
git clone https://github.com/YOUR_ORG/observability_python.git
cd observability_python
```

## Step 3: Start the Stack

```bash
docker compose up -d --build
```

This starts everything:

| Service    | URL                    | Purpose                    |
|------------|------------------------|----------------------------|
| Flask API  | http://localhost:5000  | The logistics API          |
| Grafana    | http://localhost:3000  | Dashboards (admin / admin) |
| Prometheus | http://localhost:9090  | Metrics                    |

Behind the scenes, it also starts PostgreSQL, Tempo (traces), Loki (logs), and Promtail (log collection). You don't need to access those directly.

The first build takes a couple of minutes. After that, subsequent starts are fast.

## Step 4: Import the Insomnia Collection

1. Open Insomnia
2. Go to **File > Import**
3. Choose the `insomnia-collection.json` file from the repo
4. All endpoints are pre-configured and ready to use

The collection includes every API endpoint organized into folders: Customers, Shipments, Carriers, Tracking, Routes & Ports, Customs Declarations, and Analytics. You'll use Insomnia for all your API calls throughout the exercises.

## Step 5: Verify It Works

In Insomnia, open the **Health Check** request and click **Send**. You should see:

```json
{"status": "UP"}
```

Then try the **List Customers** request in the Customers folder. You should see 5 customers in the response.

## Stopping and Restarting

To stop everything:

```bash
docker compose down
```

To stop everything and wipe the database (fresh start):

```bash
docker compose down -v
```

To start again:

```bash
docker compose up -d
```

No `--build` needed after the first time unless you see code changes in the repo.

## Troubleshooting

**"Port already in use"** -- Something else is using port 5000, 3000, or 9090. Run `docker compose down` first, then try again. If it persists, check for other running containers with `docker ps`.

**API returns errors after `docker compose down -v`** -- The `-v` flag wipes the database. The seed data is re-created automatically on the next `docker compose up -d`, but you may need to wait a few seconds for the app container to finish starting.

**Can't connect from Windows browser** -- WSL usually forwards ports to Windows automatically. If `localhost:5000` doesn't work in your browser, try `127.0.0.1:5000`. If that doesn't work either, check that the containers are running with `docker compose ps`.
