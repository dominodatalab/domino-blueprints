# Deploying LLM's to Model API Endpoint

This repo demonstrates how you can deploy a Model API Endpoint to 

### Workspace

Every workspace has a default dataset attached to it. We will use this dataset to share LLM binaries

Once the workspace starts do the following:

1. Login to Hugging Face using your access token (First cell)
```python
#Login to hugging face
import os
from huggingface_hub import login
# Replace 'your_huggingface_token' with your actual token
token=os.environ["HF_TOKEN"]
login(token)
```
2. Install the libraries needed
```shell
pip install torch transformers accelerate
```
3. Next head over to the `download.ipynb` and run the notebook
4. Lastly test it (last few cells at the end of the notebook)

Now your model should be stored in your mounted dataset

### Install Domsed and apply Mutation

1. Instructions to install Domsed are [here](https://github.com/dominodatalab/domino-field-solutions-installations/tree/main/domsed)
2. Apply the mutation
```yaml
apiVersion: apps.dominodatalab.com/v1alpha1
kind: Mutation
metadata:
  generation: 1
  name: add-dataset-model
  namespace: domino-platform
rules:
- addDatasetToModel:
    dataset_name: wadkars/LLM-ModelAPI-Quickstart/LLM-ModelAPI-Quickstart
    snapshot_number: 0
  labelSelectors:
  - dominodatalab.com/workload-type==ModelAPI
  - dominodatalab.com/project-id==67b73a3f7c835e480e8cd061
  matchBuilds: false
```
Make the following changes:

1. Modify to your `{domino-user-name}/{project-name}/{dataset-name}` for the `dataset_name`
2. Update the `labelSelectors` so that `dominodatalab.com/project-id` refers to your project id.

The mutation ensures that the dataset is mounted on for Model API endpoints that match the selectors. In the above
case it only applies the Model API endpoints for projects with project id `67b73a3f7c835e480e8cd061`

### Register the Model to Model Registry

1. Run the notebook `register_model.ipynb`
2. Note the model name (you provide that) and model version (mlflow provides that)

>>> Note: Make sure you update the `model_path` in the `load_context` function to your dataset

```python
import mlflow
class LLMModel(mlflow.pyfunc.PythonModel):
        import os
        from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
        import pandas
        import torch
        import accelerate
        def load_context(self, context):    
            model_path = "/domino/datasets/local/LLM-ModelAPI-Quickstart/google/gemma-2b"
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            #model_path = save_path  # Change this to your local model directory
            model = AutoModelForCausalLM.from_pretrained(model_path, 
                                                         torch_dtype=torch.float16, 
                                                         device_map=device)
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            # Create a text-generation pipeline
            self.text_generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
    
        def predict(self, context, model_input, params=None):
            prompt = model_input["prompt"]            
            input_string = prompt.iloc[0]
            output = self.text_generator(input_string, max_length=50, do_sample=True)
            return {'text_from_llm': output}
```

Note that the model paths in the workspace and the Model API endpoint match. It is the same mount

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

