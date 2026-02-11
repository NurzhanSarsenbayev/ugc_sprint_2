# Observability (ELK demo)

This project supports an optional local ELK stack (Elasticsearch + Kibana + Logstash + Filebeat)
to demonstrate structured JSON logs and trace-based searching.

## Start ELK

```bash
make elk-up
```

Kibana: [http://localhost:5601](http://localhost:5601)

## Start the service

```bash
make up
make ready
```

## Generate a log entry

Make any request:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/health
```

## Get `trace_id` from API logs

```bash
docker compose -f infra/docker-compose.yml logs -n 50 api
```

Find the latest JSON log line and copy the value of `"trace_id"`.

Example:

```json
{"path":"/health","status":200,"trace_id":"<copy-me>"}
```

## Find the request in Kibana

1. Open Kibana ([http://localhost:5601](http://localhost:5601))
2. Go to **Discover**
3. Select/create a data view `logs-*` (time field: `@timestamp`)
4. Search by trace id (KQL):

```
trace_id:"<your-trace-id>"
```

You should see the exact request log line with the same `trace_id`.

## Notes

This setup ships Docker container logs via Filebeat. Some Docker Desktop setups may differ,
but the goal here is a minimal, reproducible local demo.
