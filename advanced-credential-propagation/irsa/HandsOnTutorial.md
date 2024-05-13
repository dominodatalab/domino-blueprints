## Pre-requisites

> Check with your Domino CSM before using this capability. It is a departure from how Domino manages
> pod identities and may not be suitable for your requirements. 

1. Install [Domsed](https://github.com/dominodatalab/domino-field-solutions-installations/tree/main/domsed#readme). 
2. For users needing to assume AWS role identities create service account per user in the `domino-compute` namespace. 
   The name of the service account should match the user-name

When we switch to domino_user_name based service account as opposed to run_id based service accounts, there are restrictions on how we define our domino user name. It must now conform to the constraint-

> A lowercase RFC 1123 subdomain must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character (e.g. 'Example Domain ', regex used for validation is 'a-z0-9?(\.a-z0-9?)*')

For example a user name test_user is allowed by Keycloak/Domino. However a K8s service account cannot be named test_user . It can only be named test-user or test.user

For new customers this is not a problem. Retrofitting it for existing customers may need require us to map invalid characters (invalid for K8s SA) with a - or a .

## Installation

1. Update the [mutation](user-identity-based-irsa.yaml) as follows:

Update the environment variable mutation as appropriate to your environment

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
Next update the user to K8s service account mappings (see Pre-requisites)

```yaml
- cloudWorkloadIdentity:
    cloud_type: aws
    default_sa: ""
    user_mappings:
      domino-john-doe: john-doe
      domino-jane-doe: jane-doe      
```

And lastly it projects a Service Account token volume into the containers of the pod. This 
[feature](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#serviceaccount-token-volume-projection) 
is requires that you are using K8s 1.12 and above.

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

2. Apply the mutations

```shell
export platform_namespace=domino-platform
kubectl -n ${platform_namespace} apply -f ./user-identity-based-irsa.yaml
```

And let us take a pause here before we discuss the updates that will be made on the AWS side. The most important part
of the above mutation is the service account token volume projection. The JWT will have the file path 
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
The mutation also sets up the environment variable `AWS_WEB_IDENTITY_TOKEN_FILE` 
to `/var/run/secrets/eks.amazonaws.com/serviceaccount/token`. Boto3 uses this environment variable to implicitly
pass the web identity to IAM. And this is how the pod authenticates to IAM as `system:serviceaccount:domino-compute:john-doe`
in the above example. The precondition is that the OIDC Provider associated with the EKS cluster is added to IAM of the 
target AWS Account in which the Domino workload wants to assume an IAM role in as an Identity Provider. This is the 
crux of how the Domino workload authenticates to AWS IAM. Two good blogs that describes this process in detail are-

1. [IAM Roles of K8s Service Accounts Deep Dive](https://mjarosie.github.io/dev/2021/09/15/iam-roles-for-kubernetes-service-accounts-deep-dive.html)
2. [EKS Pod Identity Webhook Deep Dive] (https://blog.mikesir87.io/2020/09/eks-pod-identity-webhook-deep-dive/)

Now that we understand how the Domino workload authenticates itself with AWS IAM, let us move to the access control part 
of the process where we configure AWS IAM to permit the workload to assume IAM roles.

3. Update your AWS trust policy for the role the user wants to assume (Ex. AWS Role `my-irsa-test-role`)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::111111111111:oidc-provider/oidc.eks.<AWS_REGION>.amazonaws.com/id/<OIDC_ID>"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "oidc.eks.<AWS_REGION>.amazonaws.com/id/<OIDC_ID>:sub": [
                       "system:serviceaccount:domino-compute:john-doe",
                        "system:serviceaccount:domino-compute:jane-doe"
                    ]
                }
            }
        }
    ]
}
```

4. Next as one of the mapped users start a workspace and run the following Python code

```python
import os
## You can change this to any role you (based on the k8s service account) have permission to assume
os.environ['AWS_ROLE_ARN']='arn:aws:iam::111111111111:role/my-irsa-test-role'

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

## Appendix - Inner workings of AWS IRSA Webhook


## A brief tour of how AWS handles the Service Account annotations for roles for IRSA

To understand how AWS handles IRSA using annotations create a K8s service account in the `domino-compute` namespace 
exactly as below
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: test-user
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
  name: run-xyz-1
  namespace: domino-compute  
spec:
  serviceAccountName:  test-user
  containers:
  - name: main
    image: demisto/boto3py3:1.0.0.81279
    command: ["sleep", "infinity"]
EOF
```

Now let us shell into this pod

```shell
kubectl -n domino-compute exec -it run-xyz-1 -- sh
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

Note the above output. How did those environment variables appear. Also how did the mount appear. If you `cat` the file 
`/var/run/secrets/eks.amazonaws.com/serviceaccount/token` you will notice that it refers to a projected service account
token. Who injected these environment variables and the mount

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

You will see that the you cannot assume this role because it does not exist. Now consider this role 
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