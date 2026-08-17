Start the Application and Required Observability Services

From the project root:

docker compose up -d app postgres prometheus loki tempo influxdb promtail

This starts the application and the services required for load testing.

Grafana can remain stopped while its provisioning issue is being investigated.

Verify Containers

Run:

docker compose ps

Expected services:

app
postgres
prometheus
loki
tempo
influxdb
promtail

PostgreSQL should eventually show:

Up (healthy)

If a service is not running, check its logs:

docker compose logs <service-name>

Example:

docker compose logs -f app

Verify the Flask Application

The Flask application is exposed on:

http://localhost:5000

Test:

curl http://localhost:5000

If the application provides a health endpoint, you can also use:

curl http://localhost:5000/health

Use the health endpoint actually defined by the application.

Verify Prometheus

Open:

http://localhost:9090

Or run:

curl http://localhost:9090/-/healthy

Prometheus should respond as healthy.

Verify InfluxDB

InfluxDB is used to store JMeter load-test results.

Port:

8086

The configured JMeter database is:

jmeter

Check:

docker compose ps influxdb

You can also inspect logs:

docker compose logs -f influxdb

Run JMeter Load Test

JMeter is configured as a Docker Compose profile named:

load

Run:

docker compose --profile load run --rm jmeter

The JMeter container communicates with the Flask application using:

app:5000

Do NOT use:

localhost:5000

inside the JMeter container.

Docker Compose service discovery allows the JMeter container to resolve:

app

to the Flask application container.