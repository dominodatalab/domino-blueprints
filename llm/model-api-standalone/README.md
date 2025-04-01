# LLM as Model API Endpoints

## Challenge - Model API disk size limitation

## Challenge - LLM Artifacts Size

### Consequences of large Model Image Size
 - Build Time
 - Deploy Time
 - Cost Implications 

### Addressing LLM Large Artifacts
- Sharing Datasets across Workspaces/Jobs/Model API

## Workflow

1. Test code in workspace to write to datasets
2. Register model in model registry test locally
3. Create service account in Domino
4. Make Service Account collaborator
5. Create deployment dataset and provide Service Account write permissions on it
6. Run a job to write to the dataset. Register model to model registry
7. Create mutation to mount dataset into a model api (Admin function)
8. Start model api from model in model registry and initialize from dataset

## Future Challenges

GPU per model api

Next article will address how to share GPU's for model apis