# An example React app with the Vite framework on Domino

This repository contains the example code and instructions to create a new React project in Domino with the Vite framework. You can write your application using React components in JavaScript. Then use Vite to run a development server and see your changes instantly inside a Domino workspace.  Use Vite to build your final application for production in Domino.
The example app also contains a housing price prediction endpoint based on a Domino Model API endpoint. 

There is a CICD section with an example script to create a Domino project, git credentials, and deploy the app in this repository.

## Prerequisites

- You need to have Domino git credentials set up to create a git based project from https://github.com/ddl-wasanthag/domino-react-app
- If you are running the CICD automation outside of a Domino, you will need to set the environment variable DOMINO_USER_API_KEY
- Domino Service accounts are recommended for automated deployment. https://docs.dominodatalab.com/en/latest/admin_guide/6921e5/manage-domino-service-accounts/#_assign_roles_to_a_dsa
- DOMINO_USER_API_KEY can be the service account token, in case the use of service accounts
- Create a Domino compute environment with NPM. The following is an example config to add to your Domino compute environments Dockerfile instructions

```
# install Node
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash && \. "$HOME/.nvm/nvm.sh" && nvm install 22 && nvm use 22
```

- Deploy the Domino model API endpoint with the instructions in the endpoint folder

- Set MODEL_API_URL(Ex: https://<your domino url>:443/models/6608b3be91229570a972aa95/latest/model and MODEL_API_TOKEN as user environment variables for development project.

### Github configuration

The CI/CD automation in this repository is based on GitHub Actions. Therefore, all the Domino project/App parameters, as well as secrets to clone github repository and connect to Domino via API, must be defined as GitHub variables and secrets.

In this example, we are using GitHub Environments for UAT and Production. 

#### Github Variables

- APP_NAME (Ex: Housing_predictions)

- DOMINO_URL (Ex: cloud-cx.domino.tech)

- DOMINO_USERNAME (Ex: wasantha_gamage)

- ENVIRONMENT_ID (Ex: 68c09e16ff02ad64bfb459d3)

- GIT_PROVIDER_NAME (Ex: github_creds_001)

- HARDWARE_TIER_ID (Ex: small-k8s)

- PROJECT_NAME (Ex: app_cicd_project01)

- REPO_NAME (Ex: Domino_React_App01)

- REPO_URI (EX: https://github.com/ddl-wasanthag/domino-react-app)

- MODEL_API_URL (Ex: https://cloud-cx.domino.tech:443/models/6608b3be91229570a972aa95/latest/model)

- 
#### Github Secrets

- DOMINO_USER_API_KEY

- GH_PAT (Used to automatically clone the repo)

- MODEL_API_TOKEN



## App development and Preview

This is the process to develop and preview your application inside a Domino workspace. The example code used in this example is in the app-code directory inside the repository. Make sure to update the .gitignore file to filter unnecessary files from being checked into the git repository. 

Example:

```
ubuntu@run-68fe45a3c3fd437842b50347-t49m9:/mnt/code$ cat .gitignore 
# Dependencies
my-vite-app/node_modules/

# Build output
my-vite-app/dist/

# Environment variables
.env
.env.local
.env.production

# Editor files
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db
.Trash-12574/
.ipynb_checkpoints/

```

The development workflow uses the dev branch in the repository. You can create a new workspace based on the dev branch during the workspace creation wizard.


The setup_app_preview.sh script will create the Vite app, copy the code from the app-code folder, and start the server. Here is an example:

```
ubuntu@run-690e40f6c3fd437842b51312-xxwzs:/mnt/code$ ./setup_app_preview.sh  https://cloud-cx.domino.tech
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 16631  100 16631    0     0   210k      0 --:--:-- --:--:-- --:--:--  210k
=> nvm is already installed in /home/ubuntu/.nvm, trying to update using git
=> => Compressing and cleaning up git repository

=> nvm source string already in /home/ubuntu/.bashrc
=> bash_completion source string already in /home/ubuntu/.bashrc
=> Close and reopen your terminal to start using nvm or run the following to use it now:

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
v22.21.1 is already installed.
Now using node v22.21.1 (npm v10.9.4)

> npx
> create-vite my-vite-app --template react --force

│
◇  Scaffolding project in /mnt/code/my-vite-app...
│
└  Done. Now run:

  cd my-vite-app
  npm install
  npm run dev

Installing dependencies...

added 152 packages, and audited 153 packages in 10s

32 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities
Copying application code from app-code...
Copying src folder...
Copying public folder...
Merging package.json dependencies...
Installing additional dependencies from app-code...
npm warn deprecated inflight@1.0.6: This module is not supported, and leaks memory. Do not use it. Check out lru-cache if you want a good and tested way to coalesce async requests by a key value, which is much more comprehensive and powerful.
npm warn deprecated @humanwhocodes/config-array@0.13.0: Use @eslint/config-array instead
npm warn deprecated rimraf@3.0.2: Rimraf versions prior to v4 are no longer supported
npm warn deprecated glob@7.2.3: Glob versions prior to v9 are no longer supported
npm warn deprecated @humanwhocodes/object-schema@2.0.3: Use @eslint/object-schema instead
npm warn deprecated eslint@8.57.1: This version is no longer supported. Please see https://eslint.org/version-support for other options.

added 370 packages, removed 12 packages, changed 21 packages, and audited 511 packages in 16s

170 packages are looking for funding
  run `npm fund` for details

4 moderate severity vulnerabilities

To address all issues (including breaking changes), run:
  npm audit fix --force

Run `npm audit` for details.
Building app...

> my-vite-app@0.0.0 build
> vite build

vite v5.4.21 building for production...
✓ 32 modules transformed.
dist/index.html                   0.46 kB │ gzip:  0.29 kB
dist/assets/index-DoTK98C6.css    2.47 kB │ gzip:  0.98 kB
dist/assets/index-ConEUJjS.js   145.37 kB │ gzip: 47.01 kB
✓ built in 1.28s

=========================================
Preview will be available at:
https://cloud-cx.domino.tech/wasantha_gamage/cicd-blueprint-dev/notebookSession/690e40f6c3fd437842b51312/proxy/4173/
=========================================


> my-vite-app@0.0.0 preview
> vite preview --host 0.0.0.0 --port 4173

  ➜  Local:   http://localhost:4173/
  ➜  Network: http://100.64.67.11:4173/
  ➜  press h + enter to show help


```

Note that the Vite app is referencing the Model API endpoint hosted using the environment variable in app-code/App.jsx

```
const callAPI = async (inputData) => {
    try {
      // Debug: Check what environment variables are available
      console.log('=== DEBUG: Environment Variables ===');
      console.log('VITE_MODEL_API_URL:', import.meta.env.VITE_MODEL_API_URL);
      console.log('VITE_MODEL_API_TOKEN:', import.meta.env.VITE_MODEL_API_TOKEN);
      
      // Read from OS environment variables (as set in Domino)
      const modelApiUrl = import.meta.env.VITE_MODEL_API_URL || import.meta.env.MODEL_API_URL;
      const modelApiToken = import.meta.env.VITE_MODEL_API_TOKEN || import.meta.env.MODEL_API_TOKEN;
      

```

## Automatically Publish the app into UAT in Domino

The app.sh file defines the steps for the code inside my-vite-app/src directory to be run as a Domino Web App. The next step is to create a PR into the uat branch from the dev branch used to develop, test, and preview the code.

The GitHub Actions workflow inside .github/workflows/ci-cd.yml will run tests and then start deploying to the UAT. 


## Automatically Publish the app into Production in Domino
The next step is to create a PR into the master branch from the uat branch.


