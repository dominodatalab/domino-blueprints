# Domino mount-based access for Azure Blob Storage and Google Cloud Storage

This repository provides a practical, cloud-native approach for exposing **Azure Blob Storage** and **Google Cloud Storage** to **Domino** workspaces and jobs using **mount-based access surfaced as External Data Volumes (EDVs)**.

The goal is to enable data science teams to work with large, shared datasets through **familiar filesystem paths** inside Domino, while keeping cloud object storage as the system of record and avoiding data duplication.

At a high level, cloud object storage is:
- Authenticated using **cloud-native identity** (Azure Managed Identity or GCP Workload Identity),
- Mounted at the **platform / Kubernetes layer** (not inside user workloads),
- And exposed to Domino users as **EDVs**, preserving Domino’s security and isolation model.

## Architecture overview

The diagram below illustrates the conceptual flow for mount-based access in Domino:

![High-Level Architecture: Mounted Object Storage in Domino](images/azure_gcp_architecture_diagram-2.png)

- Cloud object storage remains external to Domino
- Mounting occurs outside user workspaces
- Access is governed by cloud IAM
- Data is consumed inside Domino via EDVs as standard filesystem paths

> The diagram is intentionally cloud-agnostic and focuses on *where the mount lives* rather than provider-specific implementation details.

## Repository contents

- `azure/`  
  High-level steps for mounting Azure Blob Storage via Kubernetes CSI drivers and exposing it as a Domino EDV.

- `gcp/`  
  High-level steps for mounting Google Cloud Storage via the Cloud Storage FUSE CSI driver and exposing it as a Domino EDV.

## Scope and intent

This repository focuses on **architecture patterns and integration flow**, not full production hardening. Detailed implementation guidance, configuration options, and operational limitations are documented in the official Azure and Google Cloud CSI driver documentation linked throughout the repository.
