# Deploying LLM's to Model API Endpoint

This repo demonstrates how you can deploy LLM's to Model Endpoints in Domino via the Model Registry

## Pre-requisites

As an admin user create a dataset which will be shared by users for placing the LLM binaries. In my example my
admin user is `integration-test` and my admin project is `deploy_llm` and my dataset name is `llmstore`

Provide users in Domino with Read-Write privileges if they wish to write to this dataset and expect them to mount
this as a shared dataset into their project.

## User Project Pre-requisite for this demo

Create a Hugging Face token and create a user environment variable `HF_TOKEN`. We will be demonstrating using the model
`google/gemma-2b`. Accept the terms and conditions of this model


## User workspace

Next start a workspace.

### Download the model

Enter the notebook [001_download.ipynb](001_download.ipynb).

1. First add the libraries
```shell
!pip install torch transformers accelerate
```
2.  Next Login to Hugging Face

```python
#Login to hugging face
# Replace 'your_huggingface_token' with your actual token
token=os.environ["HF_TOKEN"]
login(token)
```

3. Download and save model to the dataset

```python
model_name = "google/gemma-2b"
ds_name = "llmstore"
save_path = get_download_dataset_folder(ds_name,model_name)
download_model(model_name,save_path)
```
This will add the model binaries to the folder `/mnt/data/llmstore/google/gemma-2b`

4. Test the downloaded model locally

```python
model_name = "google/gemma-2b"
ds_name = "llmstore"
model_path = get_download_dataset_folder(ds_name,model_name)

model = AutoModelForCausalLM.from_pretrained(model_path, 
                                             torch_dtype=torch.float16, 
                                             device_map="cpu")
tokenizer = AutoTokenizer.from_pretrained(model_path)

# Create a text-generation pipeline
text_generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

# Generate text
prompt = "Once upon a time in a distant land,"
output = text_generator(prompt, max_length=50, do_sample=True)
print(output[0]['generated_text'])

```

### (Optionally Finetune and) Register Model

In this example we do not finetune. But you could finetune the model and store the model binaries in a chosen folder. Instea
we will simply register the model to Domino Model Registry. This functionality is in the [002_register_model.ipynb](002_register_model.ipynb)
notebook.

Run through this notebook to see how to register the model to Model Registry as well as download from Model Registry
and test the model.

When the project meets the above pre-requisites, start a workspace in the project. We will assume a Git based project.

### Obtain the resource id for the dataset

We will need this when we creat the mutation. Run the notebook [003_datasets_utils.ipynb](003_datasets_utils.ipynb)

This will return as three attributes which we will need in the next step:
```json
{'MODEL_PROJECT_ID': '67ea9c74a9d2124bb43797a5', 'RESOURCE_ID': 'f70fadf6-cb67-44aa-b525-aba22a7e1cab', 'DATASET_PATH': '/mnt/data/llmstore'}
```

### Install Domsed and apply Mutation to mount the dataset into the Model API

1. Instructions to install Domsed are [here](https://github.com/dominodatalab/domino-field-solutions-installations/tree/main/domsed)
2. Apply the mutation by replacing the placeholders with values from the previous step
```yaml
apiVersion: apps.dominodatalab.com/v1alpha1
kind: Mutation
metadata:
  name: add-dataset-model
  namespace: domino-platform
rules:
  - insertVolumeMounts:
      containerSelector:
      - model
      volumeMounts:
      - mountPath: <DATASET_PATH>
        name: prediction-data-volume
        subPath: filecache/<RESOURCE_ID>
        readOnly: true
    jqSelector:
      query: |
        include "domsed/selectors/common";
        $__kind__ == "Pod" and
        (.metadata.labels."dominodatalab.com/workload-type" | isIn(["ModelAPI"])) and
        (.metadata.labels."dominodatalab.com/project-id" | isIn(["<MODEL_PROJECT_ID>"]))
```

This creates a mount called `/mnt/data



### Deploy the Model API endpoint

Finally deploy the model with the `model_name` and `model_version` to Model API endpoint


### Call the Model API endpoint

Invoke the model api endpoint with the following input payload

```json
{
  "data": {
    "prompt": "Once upon a time in a distant land,"
  }
}
```

And you should see the output as follows:
```json
{
  "model_time_in_ms": 8252,
  "release": {
    "harness_version": "0.1",
    "registered_model_name": "gemma2b",
    "registered_model_version": "19"
  },
  "request_id": "IREU167VFABC3K4T",
  "result": {
    "text_from_llm": [
      {
        "generated_text": "Once upon a time in a distant land, there reigned a cruel king. He was a tyrant who ruled his kingdom with an iron fist. His subjects were oppressed, their rights trampled upon, and their lives lived in fear and oppression.\n\nOne"
      }
    ]
  },
  "timing": 8252.004623413086
}
```

### Improvements

The following improvements are being made on the domsed side

1. Provide a `dataset_id` to mount instead of the entire `{domino-user-name}/{project-name}/{dataset-name}`
2. Respect the grants on the dataset wrt to the `starting_user` for the model api. Only if the starting user has read permissions will the dataset be mounted
3. Support `sub-path` for the mounts. This allows only a specific sub-paths to be mounted instead of the entire dataset
4. Make the mount read-only even if RW dataset is mounted (snapshots are readonly)

