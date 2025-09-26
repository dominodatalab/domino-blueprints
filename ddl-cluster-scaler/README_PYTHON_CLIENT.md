# Cluster Scaler Client (Python)

A tiny requests-based helper for talking to the **DDL Cluster Scaler** service from Python.  
It wraps common flows like **get cluster**, **scale workers**, and **restart head + verify**.

---

## Requirements

- Python 3.8+
- `requests` (`pip install requests`)
- Network access to the Cluster Scaler service

---

## Environment Variables

These are read by the client at runtime:

- `CLUSTER_SCALER_BASE_URL` (optional)  
  Defaults to `http://ddl-cluster-scaler-svc.domino-field.svc.cluster.local`.

- `DOMINO_API_PROXY` (preferred)  
  Base URL that serves a token at `/access-token`. Used to build `Authorization: Bearer <token>`.

- `DOMINO_TOKEN` (fallback)  
  Bearer token to use if `DOMINO_API_PROXY` is not set.

- `DOMINO_API_KEY` (fallback)  
  Domino API key; sent as `X-Domino-Api-Key` if neither proxy nor token is present.

- `DOMINO_RUN_ID` (**required**)  
  Used to generate a cluster name `<kind-without-"clusters">-<DOMINO_RUN_ID>` (e.g., `ray-abc123`).

- `COMPUTE_NAMESPACE` (optional)  
  Defaults to `domino-compute`. Used when deriving the head pod name behind the scenes.

---

## Endpoints (expected server-side)

The client assumes these routes exist on your scaler:

- `GET    /healthz`
- `GET    /ddl_cluster_scaler/cluster/<kind>/<name>`
- `PATCH  /ddl_cluster_scaler/scale/<kind>/<name>`  
  JSON body: `{"replicas": <int>, "worker_hw_tier_id": "<id>"}` (tier optional; name also accepted via `worker_hw_tier`)
- `PATCH  /ddl_cluster_scaler/restart_head/<kind>/<name>`
  JSON body: `"head_hw_tier_name": "<id>"}` (tier optional; name also accepted via `head_hw_tier_name`)
- `GET    /ddl_cluster_scaler/restart_status/<kind>/<name>/<node_type>?started_at=<ISO-8601>` (node_type is `head` or `worker`)


---

## Quick Start

```python


from client.client.ddl_cluster_scaling_client import (
  is_cluster_auto_scaler_healthy,
  get_cluster_status,
  scale_cluster,
  get_cluster_restart_status,  
  wait_until_scaling_complete,
  restart_head_node,
  wait_until_head_restart_complete
)
from datetime import datetime, timezone

# 1) health
code, body = is_cluster_auto_scaler_healthy()
print("health:", code, body)

# 2) read current cluster
print(get_cluster_status("rayclusters"))

# 3) scale to 2 workers (optionally pass a HW tier id/name)
j = scale_cluster("rayclusters", worker_hw_tier_name="Medium", replicas=2)

# 4) wait until scaled
wait_until_scaling_complete("rayclusters",scale_start_ts=j['restarted_ts'])

# 5) restart the head (returns JSON with the server’s view; often includes started_at)
j = restart_head_node(cluster_kind="rayclusters",head_hw_tier_name="Small")

# 6) or poll until restarted and ready
wait_until_head_restart_complete("rayclusters", restart_ts=j['started_at'])

```
That’s it. Drop this client into your run, set the env vars, and go.
