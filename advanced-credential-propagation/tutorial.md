## Pre-requisites

> Check with your Domino Professional Services before using this capability. This is a different from how Domino manages
> pod identities by default. 

1. Install [Domsed](https://github.com/dominodatalab/domino-field-solutions-installations/tree/main/domsed#readme). 
2. For users needing to assume AWS role identities create service account per user in the `domino-compute` namespace. 
   

# Use Pod Identity with EKS for Domino Workloads based on Domino Service Accounts

[EKS Pod Identities](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html) allows a K8s pod assume an AWS role based on the ServiceAccount associated with the Pod

Domino Workloads have a dynamically generated Service Accounts. To use Pod Identities we need to use Static Service Accounts

Follow these steps:

1. Domino Service Accounts can be created based on the following [docs](https://docs.dominodatalab.com/en/latest/admin_guide/6921e5/domino-service-accounts/). 
   Assume the following service accounts:
    ```commandline
    svc-user-1
    svc-user-2
    svc-user-3
    ```
2. Create a unique K8s account for each of the Domino Service Accounts created above which need to assume an IAM role using Pod Identities for EKS
```shell
kubectl -n domino-compute create sa svc-user-1-sa 
kubectl -n domino-compute create sa svc-user-2-sa
```

3. Configure [EKS Pod Identities](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html) by following the AWS docs
4. 
5. Map the Domino Service Accounts `svc-user-1 ` and `svc-user-2` to custom IAM Roles. For example, 

| K8 Service Account | IAM Role                                                      |
|--------------------|---------------------------------------------------------------|
| svc-user-1-sa      | arn:aws:iam::111111111111:role/example-eks-pod-identity1-role |
| svc-user-2-sa      | arn:aws:iam::111111111111:role/example-eks-pod-identity2-role |

Each of the above roles has the following trust policy attached-
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowEksAuthToAssumeRoleForPodIdentity",
            "Effect": "Allow",
            "Principal": {
                "Service": "pods.eks.amazonaws.com"
            },
            "Action": [
                "sts:AssumeRole",
                "sts:TagSession"
            ]
        }
    ]
}
```
4. Apply the following mutation 

```shell
kubectl apply -f - <<EOF
apiVersion: apps.dominodatalab.com/v1alpha1
kind: Mutation
metadata:
  name: map-domino-user-k8s-sa
  namespace: domino-platform
rules:
- labelSelectors:
  - dominodatalab.com/workload-type in (Workspace,Batch,Scheduled)
  cloudWorkloadIdentity:
    cloud_type: aws
    default_sa: ""
    assume_sa_mapping: false
    user_mappings:
      svc-user-1: svc-user-1-sa
      svc-user-2: svc-user-2-sa
EOF
```

The workloads started by Domino service accounts `svc-user-1` and `svc-user-2` will have 
the dynamically generated K8s Service Account's replaced with the statically created K8s service accounts.

For workloads started by `svc-user-3` the K8s service account will be a dynamic one.


5. For testing purposes we will start two pods with the proper service accounts assuming the mutations have already been applied

```shell
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: run-xyz-1
  namespace: domino-compute  
  labels:
    dominodatalab.com/workload-type: Workspace
    dominodatalab.com/starting-user-username: svc-user-1-sa
spec:
  serviceAccountName:  svc-user-1-sa
  containers:
  - name: main
    image: demisto/boto3py3:1.0.0.81279
    command: ["sleep", "infinity"]
EOF


kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: run-xyz-2
  namespace: domino-compute  
  labels:
    dominodatalab.com/workload-type: Workspace
    dominodatalab.com/starting-user-username: svc-user-2-sa
spec:
  serviceAccountName:  svc-user-1-sa
  containers:
  - name: main
    image: demisto/boto3py3:1.0.0.81279
    command: ["sleep", "infinity"]
EOF
```
6. Exec into pod run-xyz-1 and start a `python` shell

```shell
kubectl -n domino-compute exec -it run-xyz-1 -- python -c "import boto3, logging; boto3.set_stream_logger('botocore.credentials', logging.DEBUG); print(boto3.client('sts').get_caller_identity()['Arn'])"
```

This should return an output like this indicating that the role has been assumed
```text
2024-06-20 19:35:52,116 botocore.credentials [DEBUG] Looking for credentials via: env
2024-06-20 19:35:52,116 botocore.credentials [DEBUG] Looking for credentials via: assume-role
2024-06-20 19:35:52,116 botocore.credentials [DEBUG] Looking for credentials via: assume-role-with-web-identity
2024-06-20 19:35:52,116 botocore.credentials [DEBUG] Looking for credentials via: sso
2024-06-20 19:35:52,116 botocore.credentials [DEBUG] Looking for credentials via: shared-credentials-file
2024-06-20 19:35:52,117 botocore.credentials [DEBUG] Looking for credentials via: custom-process
2024-06-20 19:35:52,117 botocore.credentials [DEBUG] Looking for credentials via: config-file
2024-06-20 19:35:52,117 botocore.credentials [DEBUG] Looking for credentials via: ec2-credentials-file
2024-06-20 19:35:52,117 botocore.credentials [DEBUG] Looking for credentials via: boto-config
2024-06-20 19:35:52,117 botocore.credentials [DEBUG] Looking for credentials via: container-role
arn:aws:sts::946429944765:assumed-role/sameer-eks-pod-identity1-role/eks-secureds45-run-xyz-1-3005627e-60f9-413f-8e79-11f31bd2be9e
```


8. Clean up
```shell
kubectl -n domino-compute delete pod run-xyz-1
kubectl -n domino-compute delete pod run-xyz-2
```



