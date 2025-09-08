# DDL Cluster Scaler API (Blueprint)

This document describes the Flask blueprint that exposes cluster-scaling and head‑pod restart
capabilities for **Ray**, **Dask**, and **Spark** cluster CRDs on Kubernetes.

---

## Overview

- **AuthN/AuthZ**
  - Incoming requests must carry either **`X-Domino-Api-Key`** or **`Authorization: Bearer …`**.
  - The service calls Domino Nucleus **`v4/auth/principal`** to identify the caller.
  - A request is **authorized** if the caller is a Domino admin **or** the CR's label
    `dominodatalab.com/starting-user-id` matches the caller’s canonical ID.
- **Kubernetes integration**
  - Reads/writes CRDs via `CustomObjectsApi` (group `distributed-compute.dominodatalab.com`, version `v1alpha1`).
  - Deletes/reads Pods via `CoreV1Api` for head restarts + status checks.
- **Hardware Tier (optional)**
  - When scaling, an optional hardware tier **name** can be provided. The service fetches tier
    details from Domino (`v4/hardwareTier`), validates restrictions, and applies CPU/memory/GPU
    requests/limits and labels/node selectors to the worker spec.

---


## Resource Types (Kinds)

`<kind>` path segments are **plural** CRD names as used by the Kubernetes API:

- `rayclusters`
- `daskclusters`
- `sparkclusters`

---

## Installation and Testing

Follow the instructions in [README_INSTALL_AND_TEST.md](./README_INSTALL_AND_TEST.md) to install the Helm chart for this service.


## Endpoints

### 1) List clusters

```
GET /ddl_cluster_scaler/list/<kind>
```

**Query**: none

**Response (200)**
```json
{
  "kind": "rayclusters",
  "count": 2,
  "clusters": [ { ...k8s object... }, { ... } ]
}
```

**Errors**
- `400 invalid_kind`
- `500 list_failed`

---

### 2) Get a specific cluster

```
GET /ddl_cluster_scaler/cluster/<kind>/<name>
```

**Response (200)**
```json
{ ... full Kubernetes custom object ... }
```

**Errors**
- `400 invalid_kind`
- `403 unauthorized` (caller is neither admin nor owner)
- `500 get_failed`

---

### 3) Scale a cluster (workers)

```
PATCH /ddl_cluster_scaler/scale/<kind>/<name>
Content-Type: application/json
```

**Body**
```json
{
  "replicas": 3,
  "worker_hw_tier_name": "Medium"   // optional: hardware tier by NAME
}
```

**Behavior**
- `replicas` is **capped** to `spec.autoscaling.maxReplicas`. `maxReplicas` is **not** increased.
- Updates `spec.autoscaling.minReplicas` to the effective value and (if present) `spec.worker.replicas`.
- If `worker_hw_tier_name` is present:
  - Fetches Domino HW tier (by **name**) from `v4/hardwareTier`.
  - Validates `computeClusterRestrictions` (e.g., `restrictToRay/Spark/Dask/Mpi`).
  - Applies to `spec.worker`:
    - `labels.dominodatalab.com/hardware-tier-id = <tier.id>`
    - `nodeSelector.dominodatalab.com/node-pool = <tier.nodePool>`
    - CPU requests/limits from `hwtResources.cores`/`coresLimit` (as strings)
    - Memory requests/limits from `hwtResources.memory{value,unit}` (unit truncated to 2 chars, e.g., `Gi`)
    - GPU requests/limits from `gpuConfiguration.numberOfGpus` (if defined)

**Response (200)**
```json
{
  "kind": "rayclusters",
  "name": "ray-12345",
  "requested_replicas": 3,
  "effective_replicas": 3,
  "maxReplicas": 5,
  "capped": false,
  "worker_hw_tier_id": { ...tier object... }  // present only if provided and found
}
```

**Errors**
- `400 invalid_kind`
- `400 bad_request` (invalid `replicas`)
- `400 invalid_hw_tier` (not found or restricted)
- `403 unauthorized`
- `409 not_scalable` or `409 invalid_autoscaling`
- `500 scale_failed`

---

### 4) Update Head Hardware Tier

```
PATCH /ddl_cluster_scaler/head-hw-tier/<kind>/<name>
Content-Type: application/json
```

**Kinds**
- `rayclusters`
- `daskclusters`
- `sparkclusters`

**Body**
```json
{
  "head_hw_tier_name": "Medium"   
}
```

**Behavior**
- Validates `kind` is one of `rayclusters|daskclusters|sparkclusters`.
- AuthZ: caller must be **Domino admin** or the **cluster owner** (compared via label `dominodatalab.com/starting-user-id`). Caller identity is obtained from Domino Nucleus (`v4/auth/principal`) using forwarded auth headers (`Authorization` or `X-Domino-Api-Key`).
- Looks up the Domino Hardware Tier **by name** via `v4/hardwareTier`.
- Validates any `computeClusterRestrictions` on the tier:
  - `restrictToRay`, `restrictToSpark`, `restrictToDask`, `restrictToMpi`
  - If any flag is `true`, the requested `kind` must match one of the allowed kinds.
- Applies the tier to the **head** pod spec (key varies by kind):
  - `rayclusters`  → `spec.head`
  - `daskclusters` → `spec.scheduler`
  - `sparkclusters`→ `spec.master`
- Patch sets (when available in the tier):
  - `labels.dominodatalab.com/hardware-tier-id = <tier.id>`
  - `nodeSelector.dominodatalab.com/node-pool = <tier.nodePool>`
  - CPU: `resources.requests.cpu = hwtResources.cores`, `resources.limits.cpu = hwtResources.coresLimit`
  - Memory: `resources.requests.memory = <value><unit[:2]>`, `resources.limits.memory = <value><unit[:2]>` (e.g., `GiB` → `Gi`)
  - GPUs: `resources.requests["nvidia.com/gpu"] = gpuConfiguration.numberOfGpus` (also set in `limits`)
- **Does not** change worker replicas or autoscaling settings; only updates head node labels/resources.
- Returns the patched CR object from Kubernetes.



## Response (200)
```json
{
  "kind": "rayclusters",
  "name": "ray-12345",
  "head_hw_tier_name": "Medium",
  "object": { /* patched CR (truncated) */ }
}
```

## Errors
- `400 invalid_kind` — kind not one of the allowed values
- `400 bad_request` — missing or invalid `head_hw_tier_name`
- `400 invalid_hw_tier` — tier not found or restricted for this kind
- `403 unauthorized` — caller is not the owner/admin
- `409 not_supported` — CRD does not expose a head/scheduler/master spec
- `500 update_head_hw_tier_failed` — unexpected error while patching


---

### 5) Restart the head pod (fire-and-forget)

```
PATCH /ddl_cluster_scaler/restart_head/<kind>/<name>
```

**Behavior**
- Deletes the head pod with a 20s grace period. Does **not** wait for the replacement to be ready.
- The head pod name is computed as:
  - `get_head_pod_name(<name>)` → `f"{name}-{cluster_type}-head-0"` where `cluster_type = name.split("-")[0]`  
    e.g., `ray-12345` → `ray-12345-ray-head-0`

**Response (202)**
```json
{
  "ok": true,
  "namespace": "domino-compute",
  "pod": "ray-12345-ray-head-0",
  "grace_period_seconds": 20,
  "started_at": "2025-09-02T15:40:00Z",
  "k8s_response": { "...sanitized V1Status..." }
}
```

**Errors**
- `404` when head pod is not found
- `500` on other Kubernetes API errors

---

### 6) Head restart status

```
GET /ddl_cluster_scaler/restart_head_status/<kind>/<name>?started_at=<ISO-8601>
```

**Query Params**
- `started_at` (required): ISO-8601 UTC timestamp used as the reference for “since when”.

**Behavior**
- Reads the head pod (derived as above) and compares its `metadata.creationTimestamp` against `started_at`.
- **require_ready is assumed true**: `ok` is true only if the pod was **restarted** and is **Ready** now.

**Response (200)**
```json
{
  "ok": true,
  "restarted": true,
  "ready": true,
  "status": "restarted_and_ready",
  "namespace": "domino-compute",
  "pod": "ray-12345-ray-head-0",
  "creationTimestamp": "2025-09-02T15:40:05Z",
  "started_at": "2025-09-02T15:40:00Z",
  "evaluated_with": "started_at"
}
```

**Errors**
- `400 bad_request` (missing/invalid `started_at`)
- `404 head_pod_not_found`
- `500 k8s_error` or `unexpected_error`

---

## Auth Details

- **Forwarded headers** (from incoming request):
  - Prefer `X-Domino-Api-Key`, else `Authorization: Bearer …`.
- **Caller identity** is resolved via:
  - `GET {DOMINO_NUCLEUS_URI}/v4/auth/principal`
- **Authorization rule**:
  - Allowed if **admin**, else the caller’s `canonicalId` must equal the CR label
    `dominodatalab.com/starting-user-id`.

---

## Kubernetes RBAC Requirements

The ServiceAccount used by this service must be able to:

- **Custom Objects (CRDs)**
  - `get`, `list`, `patch` on resources: `rayclusters`, `daskclusters`, `sparkclusters`
  - apiGroup: `distributed-compute.dominodatalab.com`

- **Pods (head restart & status)**
  - `delete`, `get`, `list`, `watch` on `pods` in `COMPUTE_NAMESPACE`

Example snippet:

```yaml
rules:
- apiGroups: ["distributed-compute.dominodatalab.com"]
  resources: ["rayclusters","daskclusters","sparkclusters"]
  verbs: ["get","list","patch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get","list","watch","delete"]
```

---

## Examples

### cURL

List clusters
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$BASE/ddl_cluster_scaler/list/rayclusters"
```

Scale (replicas capped to max, optional HW tier name)
```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"replicas": 3, "worker_hw_tier_name": "Medium"}' \
  "$BASE/ddl_cluster_scaler/scale/rayclusters/ray-12345"
```

Restart head and check status
```bash
# Kick restart
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  "$BASE/ddl_cluster_scaler/restart_head/rayclusters/ray-12345"

# Use the returned started_at value for the status check
curl -H "Authorization: Bearer $TOKEN" \
  "$BASE/ddl_cluster_scaler/restart_head_status/rayclusters/ray-12345?started_at=2025-09-02T15:40:00Z"
```

### Python (requests)

```python
import requests, json
BASE = "https://your-host"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

# Scale
resp = requests.patch(
    f"{BASE}/ddl_cluster_scaler/scale/rayclusters/ray-12345",
    headers=HEADERS,
    json={"replicas": 2, "worker_hw_tier_name": "Medium"},
    timeout=(3.05, 15),
)
print(resp.status_code, resp.json())

# Restart head
r = requests.patch(
    f"{BASE}/ddl_cluster_scaler/restart_head/rayclusters/ray-12345",
    headers=HEADERS,
    timeout=(3.05, 15),
)
data = r.json(); stamp = data["started_at"]

# Check
s = requests.get(
    f"{BASE}/ddl_cluster_scaler/restart_head_status/rayclusters/ray-12345",
    headers=HEADERS, params={"started_at": stamp}, timeout=(3.05, 15)
)
print(json.dumps(s.json(), indent=2))
```

---

## Notes & Assumptions

- **Head pod name** defaults to `f"{name}-{name.split('-')[0]}-head-0"`; adjust `get_head_pod_name()` 
- **Scaling** only updates `minReplicas` and (if present) `worker.replicas`; it **never** increases `maxReplicas`.
- HW tier memory units are normalized to the first **two** characters of the unit (`GiB` → `Gi`).
- If `spec.worker` is absent, HW tier resource patches are skipped.
- The service uses a pooled `requests.Session` with retries for Domino API calls.

---

## Development & Logging

- Set `LOG_LEVEL=DEBUG` for verbose traces.
- Kubernetes config is loaded **in-cluster**; if unavailable, it falls back to local `kubeconfig`.

---

## Health

A `/healthz` route is typically provided by the hosting Flask app. This blueprint does not define it.

## Python Client

Follow this [documentation](./README_PYTHON_CLIENT.md) for how to use a python client to interact with the DDL Cluster Scaler service

The [notebook](./notebooks/ddl_cluster_scaler_client_example.ipynb) provides an example of how to use the python client from your
Domino notebook inside the workspace