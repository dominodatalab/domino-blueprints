# Domino Advanced Credential Propagation for AWS based on IAM Role for Service Accounts (IRSA)

IAM Role for Service Accounts ([IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)) is a capability which allows Kubernetes Service Accounts attached to a EKS workload to assume IAM Role(s). In much the same way as you can attach and IAM Role to an EC2 instance at startup.

## Article Topics
 - Security 
 - Identity And Access Management (IAM) 
 - Role Based Access Control (RBAC)
 - OpenID Connect (OIDC), Web Identity and Attribute Based Access Control (ABAC) 

## High Level Overiew

Domino Data Lab’s platform is built on top of the Kubernetes framework. Domino Nexus is a comprehensive platform that 
allows you to execute Data Science and Machine Learning workloads across any compute cluster - whether in the cloud, 
a specific region, or on-premises. By unifying data science silos across the enterprise, Domino Nexus provides a 
centralized hub for building, deploying, and monitoring models. 

Such a hybrid architecture enables a wide variety of use-cases. For example, you could perform data-processing in the
AWS cloud and store a training dataset in S3. Next you could trigger a ML Training job on a GPU on an on-premise 
data plane for better cost performance. How should the on-premise data plane authenticate to AWS IAM to read data 
from S3? Can the user assume an IAM role transparently based on policy defined in agreement between the Domino
and the AWS Administration teams?

It is also possible that two teams working on separate Domino data planes hosted on different Cloud Providers in the
same organization may need to consume resources from each other. Data planes hosted in each of these Cloud Providers 
may need to assume identities in the other Cloud Providers.  

Using Web Identities based on an OpenID Connect Provider supports such use-cases. In this article we will start with a 
basic setup where using IAM Role for Service Accounts (IRSA) we can configure Kubernetes Service Accounts attached to 
an EKS workload to assume IAM Role(s). This is similar to attaching an IAM Role to an EC2 instance at startup. 
Note that this mechanism allows EKS workloads to assume roles in any AWS Account and not just the AWS account hosting 
the EKS cluster.

In the subsequent series of articles we will expand on this to demonstrate how a data plane hosted on both on-premise 
or any cloud provider can assume an IAM role in an AWS account.

While this document is meant to guide you on configuring AWS IAM Role propagation to Domino Workloads based on 
well defined policies consistent with your Enterprise Security guidelines, please speak with your Domino Professional 
Services contact for additional information, assistance and support.

### When should you consider using IRSA with Domino

  - Does your Enterprise Policy forbid the use of long lived credentials?
    
  - Would you like to transparently and securely propagate IAM Role to all Domino Workloads including a 
[Domino Scheduled Job](https://docs.dominodatalab.com/en/latest/user_guide/5dce1f/schedule-jobs/) ?
    
  - Would you like to configure a Domino Workload with a set of IAM Roles based on a set of complex custom criteria?


### Why does using IRSA with Domino help achieve the above goals?

  - When using the IRSA support in Domino, any Domino hosted workloads can assume IAM roles in any AWS account configured to
    trust the Domino Platform
    
  - IRSA support in Domino allows configuration of multiple roles for a Domino workload where the boto3 library can 
    switch across the multiple profiles configured in the ~/.aws/config file
    
  - The mapping of a workload to a set of roles can be configured based on custom configurable rules. This allows for 
    complex mappings to be supported

### How does IRSA work with Domino?
 1 . For a Domino Workload (implemented as a K8s Pod) to be able to assume an IAM Role, it must use the 
 `STS:AssumeRoleWithWebIdentity` API which returns temporary security credentials. But first the caller (in this case 
 a pod) needs to be authenticated with a Web Identity Provider that is compatible with the OpenID connect (OIDC) protocol.

 2. Starting [1.12](https://kubernetes.io/docs/concepts/storage/projected-volumes/) Kubernetes allows an OIDC provider
    to be associated with it. An EKS Cluster provides a unique OIDC provider bound to the `KubeAPIServer` server. A JWT 
    created by this OIDC provider can be mounted as a projected volume in the Pod. This JWT is associated with the K8s 
    Service Account associated with the workload. It is distinct from the JWT issued by the `KubeAPIServer`. This JWT 
    acts as a workload identity credential that can be validated by AWS STS in order to pass IAM role credentials to 
    that workload.

3. This provider is configured as an IAM identity Provider within an AWS Account the EKS workloads want to assume an 
   IAM Role. The key point here is that the EKS cluster and the IAM Role being assumed by a workload running on EKS do 
   not need to be in the same AWS Account. 

4. An AWS Admin will configure the IAM Role Trust Policy to enable a specific K8s Service Account (as identified by the
   JWT above) to assume the Role. AWS STS will validate the Workload Identity and return temporary IAM Role Credentials
   to a workload if an IAM Role Trust Policy allows it.

5. Typically the amazon-eks-pod-identity-webhook will apply mutations based on annotations defined on the Service 
   Account of the pod. Domino provides its own mutating webhook framework called 
   [Domsed](https://github.com/dominodatalab/domino-field-solutions-installations/tree/main/domsed) to enable a user 
   to switch roles which does not rely on Service Account annotations as defined in the original IRSA documentation. 
   But more importantly this implementation allows workloads in Domino data planes running on-premise or in other 
   cloud providers like GCP and Azure to assume AWS IAM Roles. We will cover this in subsequent articles.
![IRSA Designs](advanced-credential-propagation/irsa/assets/irsa.svg)
