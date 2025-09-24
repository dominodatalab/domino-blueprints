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
- **Logging**
  - Configured via `LOG_LEVEL` (default `INFO`). Structured messages at INFO/WARN/ERROR are emitted.

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Log level for the service (e.g., `DEBUG`, `INFO`, `WARNING`) |
| `COMPUTE_NAMESPACE` | `domino-compute` | Kubernetes namespace for the CRDs and head pod |
| `DOMINO_NUCLEUS_URI` | `https://…` | Base URL for Domino Nucleus (used for `v4/auth/principal` & HW tiers) |
| `FLASK_ENV` | *(unset)* | If `development`, enables debug behaviors (not required here) |

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


### 4) Restart the head pod (fire-and-forget)

```
PATCH /ddl_cluster_scaler/restart_head/<kind>/<name>
```

**Behavior**
- Deletes the head pod with a 20s grace period. Does **not** wait for the replacement to be ready.

**Body**
```json
{
  "replicas": 3,
  "head_hw_tier_name": "Medium"   // optional: hardware tier by NAME
}
```


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

### 5) restart status

```
GET /ddl_cluster_scaler/restart_status/<kind>/<name>/<node_type>?started_at=<ISO-8601>
```

**Query Params**
- `started_at` (required): ISO-8601 UTC timestamp used as the reference for “since when”.

**Behavior**
- Depending on the node-type (`head` or `worker`), waits until all replicas restarted

**Response (200)**
```json
{
    "desired_replicas": 1,
    "evaluated_with": "statefulset_pods",
    "namespace": "domino-compute",
    "node_type": "<node-type",
    "ok": true,
    "oldestCreationTimestamp": "2025-09-24T14:10:03+00:00",
    "ready_equals_running": true,
    "ready_pods": 1,
    "restarted": true,
    "running_pods": 1,
    "started_at": "2025-09-24T14:09:56+00:00",
    "statefulset": "ray-68d3e28f58a29b2e16b6a44f-ray-head",
    "status": "restarted_and_ready_counts_ok"
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

