## Pre-requisites

> Check with your Domino Professional Services before using this capability. This is a different from how Domino manages
> pod identities by default. 

1. Install [Domsed](https://github.com/dominodatalab/domino-field-solutions-installations/tree/main/domsed#readme). 
2. For users needing to assume AWS role identities create service account per user in the `domino-compute` namespace. 
   
## The IRSA process with Domino

IAM stands of Identity and Access Management. It is a two step process. The first step is Authentication where
a process has to establish its identity. The next step is Access Management where the authenticated Principal requests
access to a resource, an IAM Role in the IRSA process.

1. We will assume there are two Domino users named `john-doe` and `jane-doe` 

2. We will create two K8s service accounts, one for each user

```shell
kubectl -n domino-compute create sa sa-john-doe
kubectl -n domino-compute create sa sa-jane-doe
```

3. To enable Authentication, apply the [mutation](user-identity-based-irsa.yaml) as follows:

```shell
kubectl -f domino-platform apply -f user-identity-based-irsa.yaml
```

This yaml defines a mutation using the `domsed` which is a Domino aware mutating webhook. It does the following:

a. Update the user to K8s service account mappings (see Pre-requisites)

```yaml
- cloudWorkloadIdentity:
    cloud_type: aws
    default_sa: ""
    user_mappings:
      john-doe: sa-john-doe
      jane-doe: sa-jane-doe      
```

b. Projects a Service Account token volume into the containers of the pod. This 
[feature](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#serviceaccount-token-volume-projection) 
requires that you are using K8s 1.12 and above.

```yaml
  insertVolumes:
  - name: aws-user-token
    projected:
      defaultMode: 422
      sources:
      - serviceAccountToken:
          audience: sts.amazonaws.com
          expirationSeconds: 86400
          path: token
  insertVolumeMounts:
    volumeMounts:
      - mountPath: /var/run/secrets/eks.amazonaws.com/serviceaccount/
        name: aws-user-token
```



The above will mount a Service Account token issued by the OIDC provider associated with the EKS cluster in the path 
`/var/run/secrets/eks.amazonaws.com/serviceaccount/token`. This JWT is unlike the JWT issued by the `KubeAPIServer`. The
token provided by the `KubeApiServer` does not have any expiry date on it and now that the issuer is not an OIDC provider
associated with the EKS cluster.
```json
{
  "iss": "kubernetes/serviceaccount",
  "kubernetes.io/serviceaccount/namespace": "default",
  "kubernetes.io/serviceaccount/secret.name": "default-token-x4sjk",
  "kubernetes.io/serviceaccount/service-account.name": "default",
  "kubernetes.io/serviceaccount/service-account.uid": "488d395f-34b0-4aab-871d-17087fc027f7",
  "sub": "system:serviceaccount:default:default"
}
```

In contrast the JWT stored in the `/var/run/secrets/eks.amazonaws.com/serviceaccount/token` has both the `iss` and 
the `exp` attributes populated. 
```json
{
  "aud": [
    "sts.amazonaws.com"
  ],
  "exp": 1674755267,
  "iat": 1674668867,
  "iss": "https://oidc.eks.<AWS_REGION>.amazonaws.com/id/<OIDC_PROVIDER_ID>",
  "kubernetes.io": {
    "namespace": "domino-compute",
    "pod": {
      "name": "run-63d16b3ebe3729589c5bd9d8-mwlc2",
      "uid": "210cd280-1fe8-41ef-af96-53af291fccea"
    },
    "serviceaccount": {
      "name": "john-doe",
      "uid": "314ffbf4-d847-4680-bbf9-e521aabe86a7"
    }
  },
  "nbf": 1674668867,
  "sub": "system:serviceaccount:domino-compute:john-doe"
}
```

c. Lastly the mutation also sets up the following environment variables
```yaml
  modifyEnv:
    env:
    - name: AWS_WEB_IDENTITY_TOKEN_FILE
      value: /var/run/secrets/eks.amazonaws.com/serviceaccount/token
    - name: AWS_DEFAULT_REGION
      value: us-west-2
    - name: AWS_REGION
      value: us-west-2
    - name: AWS_STS_REGIONAL_ENDPOINTS
      value: regional
```

Strictly this is not necessary to be applied via the mutation. A user code could create these environment variables. 
The most crucial environment variable is `AWS_WEB_IDENTITY_TOKEN_FILE` and is used by the Boto3 library to 
authenticate the identity (of the Service Account of the Pod) with AWS IAM. It does so by passing the OIDC provider
issued JWT in `/var/run/secrets/eks.amazonaws.com/serviceaccount/token` as the Web Identity. In our example Boto3 
implicitly authenticates the Domino workload to AWS IAM as `system:serviceaccount:domino-compute:john-doe`. 

This is the  crux of how the Domino workload authenticates to AWS IAM. Two good blogs that describes this process 
in detail are:

- [IAM Roles of K8s Service Accounts Deep Dive](https://mjarosie.github.io/dev/2021/09/15/iam-roles-for-kubernetes-service-accounts-deep-dive.html)
- [EKS Pod Identity Webhook Deep Dive] (https://blog.mikesir87.io/2020/09/eks-pod-identity-webhook-deep-dive/)

Now that we understand how the Domino workload authenticates itself with AWS IAM, let us move to the access control part. 
Which is, how do we configure AWS IAM to permit the workload to assume IAM roles in an AWS Account.

4. In the AWS Account where the Domino workload needs to assume a IAM role, add the OIDC provider associated with the EKS
   cluster (we will see in the future article that this can be generalized to, an OIDC provider associated wih a K8s cluster)
   as an [Identity Provider](https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/setting-up-enable-IAM.html)
   in AWS IAM service. You should pay attention to the `arn` of the Identity Provider. Note that has the following naming 
   convention - `arn:aws:iam::<TARGET_AWS_ACCOUNT>:oidc-provider/oidc.eks.<AWS_REGION_TARGET_AWS_ACCOUNT>.amazonaws.com/id/<SOURCE_EKS_OIDC_ID>`
   Note the `TARGET` and `SOURCE` names in the above naming convention.
   
5. Update the AWS trust policy for the role the user wants to assume (Ex. AWS Role `my-irsa-test-role`)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::<TARGET_AWS_ACCOUNT>:oidc-provider/oidc.eks.<AWS_REGION_TARGET_AWS_ACCOUNT>.amazonaws.com/id/<SOURCE_EKS_OIDC_ID>"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "oidc.eks.<AWS_REGION_TARGET_AWS_ACCOUNT>.amazonaws.com/id/<SOURCE_EKS_OIDC_ID>:sub": [
                       "system:serviceaccount:domino-compute:john-doe",
                        "system:serviceaccount:domino-compute:jane-doe"
                    ]
                }
            }
        }
    ]
}
```

5. Next as one of the mapped users start a workspace and run the following Python code

```python
import os
## You can change this to any role you (based on the k8s service account) have permission to assume
os.environ['AWS_ROLE_ARN']='arn:aws:iam::<TARGET_AWS_ACCOUNT>:role/my-irsa-test-role'

## Now verify you have assumed it successfully
import boto3.session
session = boto3.session.Session()
sts_client = session.client('sts')
sts_client.get_caller_identity()
```

This should produce the output below which indicates that you have successfully assumed the role

```shell
{'UserId': 'AROA5YW464O6XT4444V43:botocore-session-1701963056',
 'Account': '111111111111',
 'Arn': 'arn:aws:sts::111111111111:assumed-role/my-irsa-test-role/botocore-session-1701963056',
 'ResponseMetadata': {'RequestId': '77f078d6-237f-4351-9527-c959d7b409a8',
  'HTTPStatusCode': 200,
  'HTTPHeaders': {'x-amzn-requestid': '77f078d6-237f-4351-9527-c959d7b409a8',
   'content-type': 'text/xml',
   'content-length': '478',
   'date': 'Thu, 07 Dec 2023 15:30:56 GMT'},
  'RetryAttempts': 0}}

```


### Bringing it all together

We shall emulate the entire process in a vanilla EKS cluster (with no `domsed` installed). 

First, add the OIDC provider associated with the EKS cluster into the Target AWS Account as an Identity Provider. Next,
configure the trust policy of a Target AWS role in a Target AWS Account where you are assuming the Role. 

We shall refer to the following variables 
- `<TARGET_AWS_ACCOUNT>`
- `<TARGET_AWS_ROLE>`
- `<REGION_OF_TARGET_AWS_ACCOUNT>`
- `<SOURCE_EKS_ACCOUNT_OIDC_ID>`

1. Create a Service Account below in the EKS cluster 

```shell
kubectl -n domino-compute create sa sa-jane-doe
```

2. Create test pod which emulates a Domino workload by running the following pod specification:
```shell
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: run-test-1
  namespace: domino-compute  
spec:
  volumes:
  - name: aws-user-token
    projected:
      defaultMode: 422
      sources:
      - serviceAccountToken:
          audience: sts.amazonaws.com
          expirationSeconds: 86400
          path: token
  serviceAccountName: sa-jane-doe
  containers:
  - name: run
    image: demisto/boto3py3:1.0.0.81279
    command: ["sleep", "infinity"]
    volumeMounts:
      - mountPath: /var/run/secrets/eks.amazonaws.com/serviceaccount/
        name: aws-user-token
    
EOF
```

3. Open a shell in the `run` container of this pod

```shell
kubectl -n domino-compute exec -it run-test-1 -- sh
```

4. Run the following commands in the shell (values will differ based on the AWS Account, Region and Role being assumed).
   Note, earlier we mentioned these environment variables were configured via the mutation. That was a convinience step.
   These can be set at runtime by the user. 

```shell
AWS_ACCOUNT=<TARGET_AWS_ACCOUNT>
AWS_ROLE=<TARGET_AWS_ROLE>
REGION=<REGION_OF_TARGET_AWS_ACCOUNT>
## Earler was set in the mutation where AWS_ROLE_ARN is empty and set by the user at runtime
AWS_ROLE_ARN=arn:aws:iam::${AWS_ACCOUNT}:role/${AWS_ROLE}
AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token
AWS_STS_REGIONAL_ENDPOINTS=regional
AWS_DEFAULT_REGION=${REGION}
AWS_REGION=${REGION}
```
If you `cat` the file 
`/var/run/secrets/eks.amazonaws.com/serviceaccount/token` can copy paste the contents into [www.jwt.io](www.jwt.io) 
you will see that it is issued by  the OIDC provider associated with the EKS cluster and it represents the 
service account `jane-doe` in the `domino-compute` namespace. 

5. Run the following Python code inside the pod

```python
import os
import boto3
import boto3.session
session = boto3.session.Session()
sts_client = session.client('sts')
sts_client.get_caller_identity()
```

This should result in the following output

```shell
{'UserId': 'AROA5YW464O6XT4444V43:botocore-session-1702067469', 'Account': '<TARGET_AWS_ACCOUNT>', 
 'Arn': 'arn:aws:sts::<TARGET_AWS_ACCOUNT>:assumed-role/<TARGET_AWS_ROLE>/botocore-session-1702067469', 
 'ResponseMetadata': {'RequestId': '4bd490d2-74c7-4605-ae9e-9023d46dd979', 'HTTPStatusCode': 200,
                      'HTTPHeaders': {'x-amzn-requestid': '4bd490d2-74c7-4605-ae9e-9023d46dd979', 
                       'content-type': 'text/xml', 'content-length': '478', 'date': 'Fri, 08 Dec 2023 20:31:10 GMT'}, 
                       'RetryAttempts': 0}}
```

You have successfully assumed the AWS Role `<TARGET_AWS_ROLE>` in the AWS ACCOUNT `<TARGET_AWS_ACCOUNT>`


## Appendix - Inner workings of AWS IRSA Webhook

This is an optional section which delves into the inner workings of the AWS IRSA Webhook. Understanding it will help
you understand why we made the various decisions illustrated above 

### A brief tour of how AWS handles the Service Account annotations for roles for IRSA

To understand how AWS handles IRSA using annotations create a K8s service account in the `domino-compute` namespace 
exactly as below
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sa-test-user
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::111122223333:role/my-role
```
Note that the annotation value for `eks.amazonaws.com/role-arn` above is a non-existent account, as well as IAM role

Now create a pod as follows using the above service account:
```shell
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: run-test-1
  namespace: domino-compute  
spec:
  serviceAccountName:  sa-test-user
  containers:
  - name: run
    image: demisto/boto3py3:1.0.0.81279
    command: ["sleep", "infinity"]
EOF
```

Now let us shell into this pod

```shell
kubectl -n domino-compute exec -it run-test-1 -- sh
```

Now run the following commands inside the pod shell

```shell
 # env | grep AWS
AWS_ROLE_ARN=arn:aws:iam::111122223333:role/my-role
AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token
AWS_STS_REGIONAL_ENDPOINTS=regional
AWS_DEFAULT_REGION=us-west-2
AWS_REGION=us-west-2
```

Note the above output. How did those environment variables appear?  If you `cat` the file 
`/var/run/secrets/eks.amazonaws.com/serviceaccount/token` you will notice that it refers to a projected service account
token. How did this file appear? Who injected these environment variables and the file?

This was injected by an AWS webhook called the `pod-identity-webhook`

```shell
kubectl -n kube-system get mutatingwebhookconfigurations

pod-identity-webhook                          1          30d
vpc-resource-mutating-webhook                 1          30d

```

This webhook is watching pods as they come up. And if the service account attached to this pod has the annotation  
`eks.amazonaws.com/role-arn` attached to it, it applies mutations which adds the projected service token mount and
the corresponding environment variables. Note that the actual role arn mentioned in the annotations does not even need
to exist. Next inside the shell open a `python3` shell and run the following

```shell
# python3
Python 3.10.13 (main, Oct 19 2023, 06:08:04) [GCC 12.2.1 20220924] on linux
Type "help", "copyright", "credits" or "license" for more information.
---
import os
import boto3
import boto3.session
session = boto3.session.Session()
sts_client = session.client('sts')
sts_client.get_caller_identity()

...
botocore.errorfactory.InvalidIdentityTokenException: An error occurred (InvalidIdentityToken) when calling the AssumeRoleWithWebIdentity operation: No OpenIDConnect provider found in your account for https://oidc.eks.us-west-2.amazonaws.com/id/C7F107CAE94B194C9AF67A09A84B878B
```

Notice that you cannot assume this role because it does not exist. Now consider this role 
`arn:aws:iam::<AWS_ACCOUNT_NO>:role/<AWS_IAM_ROLE>` which actually exists and add a trust policy as follows:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::<AWS_ACCOUNT_NO>:oidc-provider/oidc.eks.us-west-2.amazonaws.com/id/<OIDC_ID>"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "oidc.eks.us-west-2.amazonaws.com/id/<OIDC_ID>:sub": [
                        "system:serviceaccount:domino-compute:john-doe",
                        "system:serviceaccount:domino-compute:jane-doe",
                        "system:serviceaccount:domino-compute:test-user"
                    ]
                }
            }
        }
    ]
}
```

In the python shell now run the following
```python
import os
import boto3
aws_account='<AWS_ACCOUNT_NO>'
aws_role='<AWS_IAM_ROLE>'
os.environ['AWS_ROLE_ARN']=f'arn:aws:iam::{aws_account}:role/{aws_role}'
import boto3.session
session = boto3.session.Session()
sts_client = session.client('sts')
sts_client.get_caller_identity()

{'UserId': 'AROA5YW464O6XT4444V43:botocore-session-1702067469', 'Account': '<AWS_ACCOUNT_NO>', 
 'Arn': 'arn:aws:sts::<AWS_ACCOUNT_NO>:assumed-role/<AWS_IAM_ROLE>/botocore-session-1702067469', 
 'ResponseMetadata': {'RequestId': '4bd490d2-74c7-4605-ae9e-9023d46dd979', 'HTTPStatusCode': 200,
                      'HTTPHeaders': {'x-amzn-requestid': '4bd490d2-74c7-4605-ae9e-9023d46dd979', 
                       'content-type': 'text/xml', 'content-length': '478', 'date': 'Fri, 08 Dec 2023 20:31:10 GMT'}, 
                       'RetryAttempts': 0}}
```
Now we have successfully assumed an existing role with the trust policy configured to allow assuming it by the K8s 
service account

> The annotation on the service account is only a hint for the webhook to apply the proper mutations. It does not
> change the trust policies on any roles. That process is external to EKS. The webhook only prepares the pod to assume
> AWS role by adding the projected service token (establish identity) and configure the environment variables to enable
> boto3 library to make connections
> 
