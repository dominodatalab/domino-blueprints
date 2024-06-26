## Domino Advanced Credential Propagation based on EKS Pod Identity

[EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html) provide the ability to manage 
credentials for your applications, similar to the way that Amazon EC2 instance profiles provide credentials to 
Amazon EC2 instances. Instead of creating and distributing your AWS credentials to the containers or using the Amazon 
EC2 instance's role, you associate an IAM role with a Kubernetes service account and configure your Pods to use 
the service account.

## Article Topics
 - Security 
 - Identity And Access Management (IAM) 
 - Role Based Access Control (RBAC)
 - Open Authorization (OAuth), Web Identity and Attribute Based Access Control (ABAC) 

## High Level Overiew

Domino Data Lab’s platform is built on top of the Kubernetes framework. Domino Nexus is a comprehensive platform that 
allows you to execute Data Science and Machine Learning workloads across any compute cluster - whether in the cloud, 
a specific region, or on-premises. By unifying data science silos across the enterprise, Domino Nexus provides a 
centralized hub for building, deploying, and monitoring models. 

In a previous [article] (http://ADD_LINK_HERE) we saw how IAM Role for Service Accounts (IRSA) can be utilized within 
Domino Workloads for assuming IAM Roles. There are situations where IRSA can be operationally challenging to use.
AWS provides another mechanism to assume IAM roles within Kubernetes workloads known as EKS Pod Identity to address
these challenges.

In this article we will explore what these operational challenges are and how EKS Pod Identity can be used within 
Domino Workloads. We will look at specific situations where this approach is more suitable than the IRSA approach.

While this document is meant to guide you on configuring AWS IAM Role propagation to Domino Workloads based on 
EKS Pod Identity, please speak with your Domino Professional 
Services contact for additional information, assistance and support.


### Operational Challenges of IRSA

In general if you treat the EKS cluster hosting Domino as a "pet" and not "cattle", IRSA is a better choice. It offers
more flexibility with respect to assigning roles to Domino workloads. It can also be argued that, delegating the mapping
of Kubernetes Service Accounts to IAM Role via a separate IAM team is a good security practice which allows for more
safeguards when assigning roles to Kubernetes workloads.

However, if you use any variant of Blue/Green deployments, where an upgrade to Domino is a brand new EKS cluster,
you will find EKS Pod Identities useful.

In general the EKS administrators or Domino administrators, do not own the AWS Identity and Access Management. For any
AWS role which can be assumed by a Domino workloads, the IAM owner has to update the trust policy of the IAM Role to
explicity point to the OIDC provider associated with the EKS cluster. This OIDC provider is unique for each EKS cluster.

Consequently, in a Blue/Green scenario when you start the Green EKS cluster and install Domino on it, you will need
to modify the trust relationship of each IAM Role assumed by the Domino Workload to include the OIDC provider of the
Green Domino. After the Blue EKS cluster is retired, you will need to remove the references to the OIDC provider of the
Blue EKS cluster. This increases the operational burden on the IAM Team. In most cases, your internal policies won't 
permit you to make these changes without proper approvals in place adding more pressures on the operational process. 

EKS Pod Identities are introduced by AWS to address this operational challenge

### EKS Pod Identities


What makes EKS Pod Identities impervious to the challenge of changing EKS clusters?  The key is understanding who
the underlying Principal is in the trust policy.

In IRSA your trust policy for the IAM Role looks something like this
```json
{
      "Effect": "Allow",
      "Principal": {
        "Federated": "$PROVIDER_ARN"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${ISSUER_HOSTPATH}:sub": "system:serviceaccount:default:my-serviceaccount"
        }
      }
    }
  ]
}
```
In the above the `$PROVIDER_ARN` is the OIDC endpoint associated with the EKS cluster. And the `${ISSUER_HOSTPATH}:sub`
has to include every K8s Service Account that is permitted to assume this role. Change the EKS cluster and the former 
changes. If too many users can assume the role, you run the risk of hitting the (extended) limit of 4096 characters 
for the trust policy.

Compare this with the trust policy for an IAM role when using EKS Pod Identity

```json
"Principal": {
                "Service": "pods.eks.amazonaws.com"
            }
```
There is an additional configuration needed. The `AmazonEKSWorkerNodePolicy` which is attached to the node role 
`<cluster-name>-eks-nodes` must contain the statement below.
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "WorkerNodePermissions",
            "Effect": "Allow",
            "Action": [
                "eks-auth:AssumeRoleForPodIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```
The above policy is too permissive and allows the Node Policy to assume all IAM Roles. Expect yours to be more restrictive
such that it allows Domino Workloads to assume specific AWS IAM Roles.

Notice how there are no references to the OIDC endpoint or the actual K8s accounts mapped to the role. This mapping 
happens in the EKS cluster settings itself
```shell
aws eks create-pod-identity-association --cluster-name my-cluster --role-arn arn:aws:iam::111122223333:role/my-role --namespace default --service-account my-service-account
```

### Bringing it together

Now imagine doing a Blue/Green upgrade in Domino. When you create the new (Green) EKS cluster, you copy these mappings
into the new cluster. No IAM ownership is needed. The owner of the EKS cluster could perform this action.

When you retire the Blue EKS cluster, simply delete the cluster and your mappings get destroyed with the cluster.

### Comparison between EKS Pod Identities and IRSA


The main challenge with Pod Identities is, you cannot switch roles inside a workload. These mappings are static and 
exactly one K8s Service Account to one IAM Role at any given time.  If you  want a workload to assume a new role, 
you need to create a new pod identity mapping and restart your workload.

IRSA allows you to assume multiple roles inside a workspace. Switching a role is as simple as selecting the appropriate
profile from your `AWS_CONFIG_FILE` or setting the environment variable `AWS_ROLE_ARN`.

Removing the Pod Identity mappings between the Pod Service Account and AWS Role, does not remove the permissions of a 
running workload. There is no documented way to do this. One approach to addressing this problem is to have an 
independent service in your EKS  cluster which performs `ListPodIdentityAssociations` and if any changes occur, 
terminates the pod with stale configurations.

When using EKS Pod Identities, it is trivial to find the K8s Service Accounts associated with the IAM roles. Simply run
the `ListPodIdentityAssociations` and you will get your answer. Using this information, you can also determine which 
current workloads are associated with which IAM roles.

The only way to reliably determine this for IRSA is to iterate over *all IAM Roles* and determine which of these roles has 
a trust policy which permits the K8s service account to assume the role. 


### Example usecase where EKS Pod Identity may be preferred

If you plan to allow users to bring their own AWS credentials into Domino via the use of 
[Domino Credentials Propagation](https://docs.dominodatalab.com/en/latest/admin_guide/eb6a88/aws-credential-propagation/)
, but would like to use Domino [service accounts](https://docs.dominodatalab.com/en/latest/admin_guide/6921e5/domino-service-accounts/) 
to run jobs via automation processes, you will find it efficient to use EKS Pod Identities. 

A service account typically would be mapped to a single IAM Role for the specific purpose of performing a task. 
One to one mapping for a service account to an IAM Role makes operational sense. If you wish to run the same Domino Job 
but use different AWS IAM Roles, it would make sense to create two separate Service Accounts in Domino and map these 
separate IAM Roles to each of these service accounts respectively


