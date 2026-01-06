# Azure Blob Storage Mount-Based Access in Domino

## Table of Contents

- [Overview](#overview)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Configuration Steps](#configuration-steps)
  - [Step 1: Identify the AKS kubelet managed identity](#step-1-identify-the-aks-kubelet-managed-identity)
  - [Step 2: Verify storage account configuration](#step-2-verify-storage-account-configuration)
  - [Step 3: Verify container exists](#step-3-verify-container-exists)
  - [Step 4: Assign RBAC roles to the kubelet identity](#step-4-assign-rbac-roles-to-the-kubelet-identity)
  - [Step 5: Verify Azure Blob CSI driver is enabled](#step-5-verify-azure-blob-csi-driver-is-enabled)
  - [Step 6: Create a StorageClass](#step-6-create-a-storageclass)
  - [Step 7: Create PersistentVolume and PersistentVolumeClaim](#step-7-create-persistentvolume-and-persistentvolumeclaim)
  - [Step 8: Verify PVC binding](#step-8-verify-pvc-binding)
  - [Step 9: Register the External Data Volume in Domino](#step-9-register-the-external-data-volume-in-domino)
- [Validation](#validation)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Limitations](#limitations)

---

## Overview

This guide describes how to expose **Azure Blob Storage (ADLS Gen2)** to **Domino** as a **mounted External Data Volume (EDV)** using Kubernetes CSI-based integration on **Azure Kubernetes Service (AKS)**.

The goal is to allow data science teams to work with large datasets stored in Azure Blob Storage through **familiar filesystem paths** inside Domino workspaces, jobs, and apps—without copying or synchronizing data into Domino-managed storage.

By mounting object storage in place, this approach enables:

- Direct access to up-to-date data in Azure Blob Storage
- Separation of compute and storage
- Scalable access to large, shared datasets
- Alignment with Azure-native identity and access control models

This guide focuses on **platform-level configuration** using the **Azure Blob CSI driver with BlobFuse2**, and exposes mounted storage to users through Domino External Data Volumes.

## Architecture overview

The architecture below illustrates how Azure Blob Storage is exposed to Domino workloads through platform-managed mounting.

![Overview](images/aks-architecture.png)

At a high level:

- **Azure Blob Storage / ADLS Gen2** remains the system of record
- The **Azure Blob CSI driver (BlobFuse2)** mounts storage at the Kubernetes node level
- Authentication is handled using the **AKS kubelet managed identity**
- The mounted path is registered in Domino as an **External Data Volume (EDV)**
- Data is accessible inside Domino workspaces, jobs, and apps as a standard filesystem path (for example, `/mnt/adls/<container>`)

Key components include:

- **Azure Storage Account (Blob / ADLS Gen2)**: Stores data externally in Azure
- **AKS cluster**: Hosts Domino and manages node-level mounts
- **Kubelet managed identity**: Authenticates storage access for all nodes
- **Azure Blob CSI driver**: Performs filesystem translation outside user workloads
- **Domino External Data Volume (EDV)**: Controls how mounted storage is exposed to users

This architecture keeps user workloads unprivileged while enabling filesystem-style access to Azure object storage.

---

## Prerequisites

To expose Azure Blob Storage to Domino as a mounted EDV, the following prerequisites must be met.

You will need:

- Access to the **Azure subscription**
- Access to the **AKS cluster** where Domino is deployed
- **Azure CLI** authenticated with sufficient permissions
- **kubectl** configured for the AKS cluster
- **Domino administrator privileges**

Before proceeding, ensure that:

- An **Azure Storage Account** exists with **ADLS Gen2 (Hierarchical Namespace)** enabled
- The target **blob container** exists
- The **Azure Blob CSI driver** is enabled on the AKS cluster (default for AKS ≥ 1.21)
- You can assign RBAC roles to the AKS kubelet managed identity

## Configuration Steps

### Step 1: Identify the AKS kubelet managed identity

Retrieve the kubelet identity:

```bash
az aks show \
  --resource-group <AKS_RESOURCE_GROUP> \
  --name <AKS_CLUSTER_NAME> \
  --query identityProfile.kubeletidentity \
  --output json
```
Expected output:

```json
{
  "clientId": "<KUBELET_CLIENT_ID>",
  "objectId": "<KUBELET_OBJECT_ID>",
  "resourceId": "<KUBELET_RESOURCE_ID>"
}
```

Save the Object ID, which is used for RBAC role assignments.

### Step 2: Verify Storage Account Configuration

Confirm that Hierarchical Namespace (HNS) is enabled:
```bash
# Check if Hierarchical Namespace is enabled
az storage account show \
  --name edvstoragetest \
  --resource-group <resource_group_name> \
  --query "{Name:name, HnsEnabled:isHnsEnabled, Sku:sku.name, Location:location}" \
  --output table

# Expected output:
# Name             HnsEnabled    Sku            Location
# ---------------  ------------  -------------  ----------
# edvstoragetest   True          Premium_LRS    westus2
```
If HnsEnabled is `false` or `null`, the storage account must be migrated to ADLS Gen2 before continuing.

---

### Step 3: Verify Container Exists
```bash
# List all containers in the storage account
az storage container list \
  --account-name edvstoragetest \
  --auth-mode login \
  --query "[].name" \
  --output table

# Check if specific container exists
az storage container show \
  --name adls-container-test2 \
  --account-name edvstoragetest \
  --auth-mode login
```

**If container doesn't exist**, create it following the steps [here](https://learn.microsoft.com/en-us/cli/azure/storage/container?view=azure-cli-latest)

---

### Step 4: Assign RBAC Roles to Kubelet Identity

The kubelet identity requires **the specific roles** to mount and access blob storage:

#### Reader (Resource Group Scope)

Allows discovery of the storage account within the resource group.
```bash
az role assignment create \
  --role "Reader" \
  --assignee <KUBELET_OBJECT_ID> \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<STORAGE_RESOURCE_GROUP>"
```

#### Storage Blob Data Contributor (Storage Account Scope)

Allows read/write access to blob data.
```bash
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee <KUBELET_OBJECT_ID> \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<STORAGE_RESOURCE_GROUP>/providers/Microsoft.Storage/storageAccounts/<STORAGE_ACCOUNT_NAME>"
```

#### Storage Account Key Operator Service Role (Storage Account Scope)

**CRITICAL:** This role allows the CSI driver to retrieve storage account keys for mounting.
```bash
az role assignment create \
  --role "Storage Account Key Operator Service Role" \
  --assignee <KUBELET_OBJECT_ID> \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<STORAGE_RESOURCE_GROUP>/providers/Microsoft.Storage/storageAccounts/<STORAGE_ACCOUNT_NAME>"
```

#### Verify Role Assignments
```bash
# List all roles assigned to kubelet identity
az role assignment list \
  --assignee <KUBELET_OBJECT_ID> \
  --all \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  --output table

# Expected output should include:
# Reader                                    .../resourceGroups/metlife96619
# Storage Blob Data Contributor             .../storageAccounts/edvstoragetest
# Storage Account Key Operator Service Role .../storageAccounts/edvstoragetest
```

---

### Step 5: Verify Azure Blob CSI Driver is Enabled

Check that the CSI driver is installed:
```bash
# Check if CSI driver is installed
kubectl get csidriver blob.csi.azure.com

# Expected output:
# NAME                   ATTACHREQUIRED   PODINFOONMOUNT   STORAGECAPACITY
# blob.csi.azure.com     false            false            false

# Check CSI driver pods are running
kubectl get pods -n kube-system -l app=csi-blob-node

# Expected output (multiple pods, one per node):
# NAME                  READY   STATUS    RESTARTS   AGE
# csi-blob-node-xxxxx   4/4     Running   0          10d
# csi-blob-node-yyyyy   4/4     Running   0          10d
```

**If CSI driver is not enabled:**
```bash
az aks update \
  --resource-group <AKS_RESOURCE_GROUP> \
  --name <AKS_CLUSTER_NAME> \
  --enable-blob-driver
```

---

### Step 6: Create StorageClass

Create a StorageClass for blob storage with BlobFuse2 protocol:
```bash
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azureblob-fuse-premium
provisioner: blob.csi.azure.com
parameters:
  skuName: Premium_LRS
  protocol: fuse2
reclaimPolicy: Retain
volumeBindingMode: Immediate
allowVolumeExpansion: true
mountOptions:
  - -o allow_other
  - --use-adls=true
  - --file-cache-timeout-in-seconds=120
EOF
```

**Verify StorageClass:**
```bash
kubectl get storageclass azureblob-fuse-premium
```

---

### Step 7: Create PersistentVolume and PersistentVolumeClaim

#### Create PersistentVolume
```bash
 kubectl apply -f azure-pv.yml
```
```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: edvstorage-pv-blob-azure
  annotations:
    pv.kubernetes.io/provisioned-by: blob.csi.azure.com
  labels:
    dominodatalab.com/external-data-volume: Generic
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: azureblob-fuse-premium
  mountOptions:
    - -o allow_other
    - --file-cache-timeout-in-seconds=120
    # If this is ADLS Gen2 / HNS, uncomment:
    # - --use-adls=true
  csi:
    driver: blob.csi.azure.com
    volumeHandle: edv-<STORAGE_ACCOUNT_NAME>-<CONTAINER_NAME>-<ENV>
    volumeAttributes:
      containerName: <CONTAINER_NAME>
      resourceGroup: <STORAGE_RESOURCE_GROUP>
      storageAccount: <STORAGE_ACCOUNT_NAME>
  claimRef:
    name: edvstoragetest-azure-blob
    namespace: domino-compute
```
#### Create PersistentVolumeClaim
```bash
 kubectl apply -f azure-pvc.yml
```
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: edvstoragetest-azure-blob
  namespace: domino-compute
  labels:
    dominodatalab.com/external-data-volume: Generic
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  volumeName: edvstorage-pv-blob-azure
  storageClassName: azureblob-fuse-premium
```

### Step 8: Verify PVC Binding
```bash
# Check PersistentVolume status
kubectl get pv edvstorage-pv-blob-azure -n domino-compute

# Expected output:
# NAME                 CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM
# edvstorage-pv-blob-azure    100Gi      RWX            Retain           Bound    domino-compute/adls-pvc-blob-fuse

# Check PersistentVolumeClaim status
kubectl get pvc edvstoragetest-azure-blob -n domino-compute

# Expected output:
# NAME                 STATUS   VOLUME              CAPACITY   ACCESS MODES
# edvstoragetest-azure-blob   Bound    adls-pv-blob-fuse   100Gi      RWX
```

**If PVC is stuck in "Pending" status, see [Troubleshooting](#troubleshooting) section.**

---

### Step 9: Register External Data Volume in Domino
The above PV should appear as a generic EDV in the EDV section of the admin panel. Configure the EDV per the documentation: https://docs.dominodatalab.com/en/latest/user_guide/f12554/external-data-volumes-edvs/\

![Register-EDV](images/edv-azure-blob.png)
---

## Validation

### Attach the EDV to a Domino Project
1. Follow the steps in this [documentation](https://docs.dominodatalab.com/en/cloud/user_guide/ee8d01/add-edvs-to-projects/) to attach the EDV to a Domino Project

![Attach-EDV](images/attach-edv-project.png)

2. Browse the EDV and access the Azure Blob Storage

![Browse the EDV](images/edv-azure-blob.png)

## Troubleshooting

### PVC Stuck in "Pending" Status

```bash
kubectl describe pvc <AZURE_BLOB_PVC_NAME> -n domino-compute
kubectl get pv <AZURE_BLOB_PV_NAME> -o yaml
kubectl get sc azureblob-fuse-premium -o yaml
```

Check CSI driver logs:
```bash
kubectl logs -n kube-system -l app=csi-blob-node --tail=200
```

**Common Causes:**

1. `resourceGroup` missing in PV `volumeAttributes`
2. Missing `resourceGroup` in the PV
3. Missing `Storage Account Key Operator Service Role` on the kubelet identity

---

### Mount Succeeded but No Files Visible
**Common Causes:**

1. **Missing `resourceGroup` parameter** in PV `volumeAttributes` (most common)
2. **Wrong storage account name** in PV configuration
3. **Wrong container name** in PV configuration
4. **Missing Storage Account Key Operator role** on kubelet identity


### Permission Denied Errors
- Confirm Storage Blob Data Contributor role
- Confirm Storage Account Key Operator Service Role
- Validate kubelet identity object ID
```
az role assignment list \
  --assignee <KUBELET_OBJECT_ID> \
  --all \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  --output table
```

## Security Considerations

### Shared Identity Model

- Access uses a shared kubelet managed identity
- Azure audit logs will show storage access under the kubelet identity
- Use Domino controls and project-level EDV assignment to limit access

### Limitations

- Access uses a shared kubelet identity
- No per-user Azure identity or auditing
- POSIX semantics are limited by BlobFuse2
- Not recommended for high-frequency small file workloads