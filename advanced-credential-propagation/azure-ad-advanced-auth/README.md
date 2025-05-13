# Advanced authorization with Entra ID

## Pre-requisites

### Azure Entra User tokens

See our [previous guide](https://github.com/dominodatalab/domino-blueprints/tree/main/advanced-credential-propagation/azure-ad-user-tokens)

### Azure Workload Identity

The Azure configuration of this feature is outside the scope of this guide, but you can follow, [[Azure Documentation](https://learn.microsoft.com/en-us/azure/aks/workload-identity-deploy-cluster#update-an-existing-aks-cluster)] to enable this on an existing cluster. 

The end goal should be to have a set of kubernetes service accounts, in the `domino-compute` namespace, which are linked to your target Managed Identities in Azure

In subsequent steps, we will refer to these kubernetes accounts as `aad-id1/2/3..`

### Domino Webhook Operator (Domsed)

This solution depends on a PS-developed service for Domino installations called [Domsed](https://github.com/dominodatalab/domino-field-solutions-installations/tree/main/domsed) . The service is installed via a helm chart and custom image, contact your PS representatives for access to the latest release chart & image. 

We need this service installed and running in the platform namespace before proceeding

## Scenario 1: Users are not allowed access to production data/resources during development

IMG PLACEHOLDER HERE

In this scenario, we want to make sure a particular service account "sa_1" is assigned a managed identity when it creates a scheduled job. The following yaml can be deployed to configure this:

```yaml
apiVersion: apps.dominodatalab.com/v1alpha1
kind: Mutation
metadata:
  name: scenario-1
  namespace: domino-platform
rules:
- labelSelectors:
  - "dominodatalab.com/workload-type==Scheduled" # Targets scheduled jobs only
  cloudWorkloadIdentity:
    cloud_type: azure # Sets the proper annotations for azure WI on the pod
    user_mappings:
      sa_1: aad-id1 # assign domino account "sa_1" the kubernetes service account "aad-id1"
    default_sa: "" # If unmatched, assign nothing
```

The `domino_aad` package (https://mirrors.domino.tech/domino_aad-0.0.4-py3-none-any.whl) contains a `DominoChainCredential` type credential, which allows you to choose whether to use User credentials or WI based on an environment variable `DOMINO_WI_CREDENTIAL`. If this is set to true, a WI token is returned (if available), otherwise a user token is returned. 

This class can be used to write code that can utlize multiple credential types based on the context, allowing users to have a single code base that works under development and production scenarios.

Another option is to use azure's default [chained credentials](https://learn.microsoft.com/en-us/azure/developer/python/sdk/authentication/credential-chains?tabs=dac#chainedtokencredential-overview) method like so:
```
credential = ChainedTokenCredential(
    DominoCredential(),
    WorkloadIdentityCredential()
)
```

## Scenario 2: You want to deploy your application with strong security not linked to an individual

IMG PLACEHOLDER HERE

In this scenario, we want to force all deployed Applications in Domino to use a particular managed identity from Azure

```yaml
apiVersion: apps.dominodatalab.com/v1alpha1
kind: Mutation
metadata:
  name: scenario-2
  namespace: domino-platform
rules:
- labelSelectors:
  - "dominodatalab.com/workload-type==App" # Targets apps only
  cloudWorkloadIdentity:
    cloud_type: azure # Sets the proper annotations for azure WI on the pod
    default_sa: "aad-id2" # Sets kubernetes service account "aad-id2"
```


## Scenario 3: Allow wide scope permissions for development and narrow scope for deployment

IMG PLACEHOLDER HERE

In this scenario, we want to mix and match multiple identities to be used for different use cases

```yaml
apiVersion: apps.dominodatalab.com/v1alpha1
kind: Mutation
metadata:
  name: scenario-3
  namespace: domino-platform
rules:
- labelSelectors:
  - "dominodatalab.com/workload-type==App" # Targets apps only
  cloudWorkloadIdentity:
    cloud_type: azure # Sets the proper annotations for azure WI on the pod
    user_mappings:
      sa_2: aad_id3 
      user_1: aad_id4 # Map domino service accounts and/or users to their respective identities
    default_sa: "" # If unmatched, assign nothing
- labelSelectors:
  - "dominodatalab.com/workload-type==Scheduled" # Targets scheduled jobs only
  cloudWorkloadIdentity:
    cloud_type: azure # Sets the proper annotations for azure WI on the pod
    user_mappings:
      sa_3: aad_id5
      user_2: aad_id6 # Map domino service accounts and/or users to their respective identities
    default_sa: "" # If unmatched, assign nothing
```