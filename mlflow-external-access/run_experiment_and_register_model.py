"""
An example script making MLflow API calls as an external client to a Domino deployment.
"""

import os
import argparse
from datetime import datetime
from typing import Union, Iterable

import mlflow.sklearn
import numpy as np
from domino import Domino
from mlflow import MlflowClient
from mlflow.store.artifact.runs_artifact_repo import RunsArtifactRepository
from mlflow.tracking.request_header.registry import _request_header_provider_registry
from sklearn.ensemble import RandomForestRegressor

from domino_api_key_header_provider import DominoApiKeyRequestHeaderProvider
from domino_execution_header_provider import DominoExecutionRequestHeaderProvider
import domino_utils

import pandas as pd

def set_mlflow_tracking_uri(mlflow_tracking_uri):
    mlflow.set_tracking_uri(mlflow_tracking_uri)


def register_domino_api_key_request_header_provider():
    if not os.getenv("DOMINO_USER_API_KEY"):
        print("DOMINO_USER_API_KEY environment variable must be set.")
        exit(1)
    # Set X-Domino-Api-Key request header
    _request_header_provider_registry.register(DominoApiKeyRequestHeaderProvider)


def register_domino_execution_request_header_provider():

    # Set X-Domino-Execution request header
    _request_header_provider_registry.register(DominoExecutionRequestHeaderProvider)





def start_run_and_register_model(experiment_name,run_name,model_name):
    client = MlflowClient()
    artifact_path = "sklearn-model"
    mlflow.set_experiment(experiment_name)
    params = {"n_estimators": 3, "random_state": 42}
    rfr = RandomForestRegressor(**params).fit([[0, 1]], [1])
    try:
        client.create_registered_model(model_name)
    except:
        print('Model Already exists.')
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(params)
        model_info = mlflow.sklearn.log_model(rfr, artifact_path=artifact_path)
        runs_uri = model_info.model_uri
        model_uri = f"runs:/{run.info.run_id}/{artifact_path}"
        # Create a new model version of the RandomForestRegression model from this run
        desc = "A testing version of the model"
        model_src = RunsArtifactRepository.get_underlying_uri(runs_uri)
        print(f'Model Src {model_src}')
        mv = client.create_model_version(model_name,model_uri)
        print("Name: {}".format(mv.name))
        print("Version: {}".format(mv.version))
        print("Description: {}".format(mv.description))
        print("Status: {}".format(mv.status))
        print("Stage: {}".format(mv.current_stage))
    return run

def download_and_run_logged_model(model_name, model_version,x: Union[pd.DataFrame,np.ndarray, Iterable[Iterable[float]]])-> np.ndarray:

    uri = f"models:/{model_name}/{model_version}"
    model = mlflow.pyfunc.load_model(uri)

    if not isinstance(x, pd.DataFrame):
        x = pd.DataFrame(x)
    y_pred = model.predict(x)
    return np.asarray(y_pred)

def main(mlflow_tracking_uri:str, experiment_name:str,
         run_name:str,model_name:str):


    start_run_and_register_model(mlflow_tracking_uri,experiment_name,run_name,model_name)


def start_stub_job(domino_host,project_owner,project_name,api_key,job_name):
    domino_2 = Domino(host=domino_host,project=f"{project_owner}/{project_name}", api_key=api_key)
    result = domino_2.runs_start([f"echo `{job_name}`"], title="Api key based execution")
    return result


if __name__ == "__main__":
    #Ex. DOMINO_EXTERNAL_HOST = mydomino.cs.domino.tech
    parser = argparse.ArgumentParser(description="External MLflow client for Domino")

    parser.add_argument("--domino_host_name", required=True, help="External Domino host name only.")
    parser.add_argument("--domino_project_owner", required=True, help="Domino project owner.")
    parser.add_argument("--domino_project_name", required=True, help="Domino project name")

    parser.add_argument("--domino_experiment_name", required=True, help="Experiment name to use.")
    parser.add_argument("--domino_model_name", required=True, help="Model name to register.")
    parser.add_argument("--domino_run_name_prefix", required=False, help="Run name to use.")


    # optional arguments
    parser.add_argument("--domino_job_name_prefix",  default="external-exp-manager-access", type=str, help="External Experiment Manager job name prefix.")

    args = parser.parse_args()

    domino_host_name= args.domino_host_name
    domino_tracking_uri = f'https://{domino_host_name}'
    mlflow.set_tracking_uri(domino_tracking_uri)

    project_owner = args.domino_project_owner
    project_name = args.domino_project_name
    job_name_prefix = args.domino_job_name_prefix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_name = f'{job_name_prefix}-{project_owner}-{project_name}-{timestamp}'

    experiment_name = args.domino_experiment_name
    model_name = args.domino_model_name
    run_name_prefix = f"{args.domino_run_name_prefix}-{timestamp}" if args.domino_run_name_prefix else f'ExternalRun-{timestamp}'

    api_key = None
    oauth_token =  None
    if 'DOMINO_USER_API_KEY' in os.environ:
        api_key = os.environ['DOMINO_USER_API_KEY']

    if 'DOMINO_OAUTH_TOKEN' in os.environ:
        oauth_token = os.environ['DOMINO_OAUTH_TOKEN']

    if not api_key and not oauth_token:
        print("One of DOMINO_USER_API_KEY or DOMINO_OAUTH_TOKEN must be set.")
        exit(1)

    if not api_key:
        print("DOMINO_USER_API_KEY not set. We will try to get it using the oauth token.")
        print("Generating api key from oauth token. Do not store it anywhere")
        api_key = domino_utils.get_domino_user_api_key(domino_host_name,oauth_token)
        os.environ['DOMINO_USER_API_KEY'] = api_key
    # Domino Mlflow server enforces access control based on two criteria
    # 1. X-Domino-Api-Key header - this is set by the DominoApiKeyRequestHeaderProvider (Identifies the principal)
    # 2. run-id - this is set by the DominoExecutionRequestHeaderProvider (Identifies the project in which the mlflow call is being made)

    #You need to start a run in the project you want to track the mlflow calls against
    #This will give you a run-id which you can use to make mlflow calls
    #The jobs page will also log the action performed against the project
    #You can use any run-id for this project as long as it belongs to the same user identified by the api key
    #But it is better to start a new run so that you can track the actions performed by this script
    result = start_stub_job(domino_tracking_uri,project_owner,project_name,api_key,job_name)
    print("Job started to get run id")
    print(result)
    run_id=result['runId']
    os.environ['DOMINO_RUN_ID'] = run_id

    # Strictly speaking this is not needed unless you are using it in an endpoint
    # where multiple requests are being handled in the same process with different identities
    _request_header_provider_registry._registry.clear()
    register_domino_api_key_request_header_provider()
    register_domino_execution_request_header_provider()

    start_run_and_register_model(experiment_name,run_name_prefix,model_name)
    result = download_and_run_logged_model(model_name,"latest",[[0,1]])
    print(result)



