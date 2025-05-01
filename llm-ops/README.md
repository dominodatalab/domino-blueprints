# Deploying LLM's to Model API Endpoint

This repo demonstrates how you can deploy LLM's to Model Endpoints in Domino via the Model Registry

## Pre-requisites


As a Domino Administrator create two types of users:
1. Data Scientist - For example, `joe-ds`
2. Model Deployer - For example, `jane-ds`

Furthermore, create two datasets
1. Dev Dataset (`domino-models-dev`), which will be used to deploy models for Data Scientist to perform Dev Testing 
2. Prod Dataset (`domino-models-prod`) , which will be used to deploy models by Model Deployers in production


The permissions are as follows:

| Datasets/<br/>User Role | **domino-models-dev** | **domino-models-dev** |
|-------------------------|-----------------------|-----------------------|
| **Data Scientist**      | RW                    | NONE                  |
| **Prod Deployer**       | RW                    | RW                    |
 
This results in,
1. For a prod-deployer, inside a workspace or a job both datasets are mounted
2. For a data-scientist, inside a workspace or a job only the `domino-models-dev` dataset is mounted

## Model Endpoints And User Role

The key feature of this design is the use of [Domsed](https://github.com/dominodatalab/domino-field-solutions-installations/blob/main/domsed/README.md). 

This allows us to deploy a mutation which mutates the model endpoint as follows:
1. If a Data Scientist is creating a model endpoint the folder `llm-models` from the dataset  `domino-models-dev` is mounted as `/llm-models`
2. If a Prod-Deployer is creating a model endpoint the folder `llm-models` from the dataset  `domino-models-prod` is mounted as `/llm-models`

> You can have as many types of datasets, say you want to add a "staging" dataset. You will need to 
> create users with those roles. Note that in this design roles for not overlap. You cannot have
> a prod deployer also be a data-scientist because we do not want both the datasets to be mounted
> in the model endpoint. 
> 
> If you need that, make sure you use Domino service-accounts for higher roles like "staging-deployer" and
> "prod-deployer". And use Domino API endpoints to deploy model endpoints using those service accounts


## Demonstration

We are now ready to demonstrate how the LLM deployment process to Model Endpoints works in this framework.

The steps are broken down into two phases:

1. Data Scientist development phase
2. Prod Deployer production deployment phase

### Development Phase

Login as a `data-scientist` role and start a workspace 
1. Let us pretend we fine tune model. 
2. Next we deploy the model to the dev dataset and register model to Domino Model Registry
3. We locally test the model by downloading model from model registry. We still do not publish the model binaries to the Domino Experiment Manager
4. We deploy the `Registered Model Name` and `Registered Model Version` (from step 3) as a Model Endpoint and verify it works 
5. When are satisfied with the local testing we publish the model binaries to the Domino Experiment Manager and publish the model again to Domino Model Registry
6. Note the `Registered Model Name` and `Registered Model Version`. This is the version the prod-deployer will deploy as a model endpoint 


#### FineTuning The Model

We provide a [notebook](./local_download.ipynb) to locally download a GPT2 model to `/home/ubuntu//gpt2` folder.
In the real world scenario, you will probably fine tune a model and mount it to one of our datasets so that you have more storage. For this demo
we are assuming this downloaded `GPT2` model is adequate. This notebook also shows you how to test this model locally.

#### Dev Testing and Deployment of Domino Model Endpoint

Next follow the steps in the [notebook](./register_and_test_model.ipynb). This has the following steps:
1. Register Model to Domino Model Registry and test model locally
2. Deploy and test this version Domino Model Endpoint
3. Next register model binaries as a model artifacts to Domino Experiment Manager and re-register new version to Model Registry
4. Deploy this final version as Domino Model Endpoint and re-test

These steps are explained in this notebook as you execute it. Note that when running Domino on AWS, you can speed the 
publishing of artifacts to Domino Experiment Manager by setting the environment variable 
```shell
MLFLOW_ENABLE_PROXY_MULTIPART_UPLOAD=true
```

> The key challenge we are addressing here is, when a registered model version is deployed as 
> a Domino Model Endpoint, the build process for Domino Model Endpoints downloads the model artifacts from the
> Domino Experiment Manager. If we registered the model binaries against the `mlflow-run-id` of this model version
> we would end up with a large model image.
> So we address the challenge by using the mlflow trick to use nested runs. The model binaries are registered against
> the `parent-run-id` and the registered model version is passed this `parent-run-id` in the model context. The model binaries
> are loaded in the mounted dataset in the location  `/llm-models/{parent-run-id}` and this way the 
> model version can access the binaries directly without having them be part of the model image

### Production Phase

Next login as the `prod-deployer`. And follow along the [notebook](./deploy_llm_to_prod.ipynb) to deploy this endpoint to prod.

The main challenge here is we want to download artifacts from the Domino Experiment Manager for the `Registerd Model Version` we 
intend to deploy. For LLM these artifacts can be very large in size (order of GB). To speed up the process we use the 
[IAM Role for Service Accounts](https://domino.ai/solutions/professional-services/domino-blueprints/aws-irsa). This enables the 
user in `prod-deployer` role to download artifacts directly from the S3 bucket using multi-part download 

The `prod-deployer` will now do the following steps:

1. Fetch the `mlflow-run-id` for the registered model version
2. Find the associated `parent-run-id` of this registered model version and copy the model binaries to location
   `{DS-ROOT}/domino-models-prod/llm-models/{parent-run-id}`
3. Stop and restart the Model Endpoint started by the dev-user

The act of restarting the Domino Model Endpoint for the registered model version by the prod-deployer changes the
mounted dataset from `domino-models-dev` to `domino-models-prod`. And we are done.


## Takeaways

Using a relatively straight forward design composed of multiple datasets, mlflow nested runs and IRSA
we have enabled LLM deployments in Domino by addressing the following challenges:

1. Our Model Images are no longer massive improving both build and startup times. The process is both operationally and cost efficient.
2. Using nested mlflow runs we solved the problem of auto deployment of artifacts.
3. Using IRSA Readonly Roles for vetted-users we made the process of downloading large binaries from Domino Experiment Manager efficient.
4. While Domino Datasets are used inside the model endpoints, they are not the source of truth. Truth still resides
   in Domino Experiment Manager. We do not have to worry about accidentally deleting the folders in the dataset. In such an event we can simply 
   refresh the folder from the Domino Experiment Manager

In other words, we have enabled LLM Deployments in Domino efficiently without sacrificing on using Domino
as a System of Record which is the central feature of Domino.

## Appendix

This section covers additional details around how the solution works

### How does the Domino mutation work?
