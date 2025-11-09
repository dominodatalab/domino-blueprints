# How to run
# python script.py <username> <domino_url> <github_pat> <project_name> <app_name> <environment_id> <hardware_tier_id>
# python3 create_project_and_start_app.py wasantha_gamage prod-field.cs.domino.tech ghp_xxxxxxxxx az_idle_wks my_app env_123 small-k8s
# Or with config file:
# python script.py create --config-file my-domino-configs.yaml

import requests
import json
import sys
import os
import argparse
import logging
import time
import yaml

# Set up logging to a file
script_name = os.path.splitext(os.path.basename(__file__))[0]
logging.basicConfig(filename=f'{script_name}.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_config_file(config_path):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            logging.info(f"Configuration loaded from {config_path}")
            return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)

def lookup_user(domino_url, api_key, username):
    """Look up user by username and return user data."""
    url = f"https://{domino_url}/v4/users?userName={username}"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key
    }
    
    print(f"Debug - Looking up user: {username}")
    print(f"Debug - Full URL: {url}")
    print(f"Debug - API Key starts with: {api_key[:10] if api_key and len(api_key) >= 10 else 'TOO_SHORT'}...")
    print(f"Debug - API Key length: {len(api_key) if api_key else 0}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"Debug - Response status: {response.status_code}")
        print(f"Debug - Response headers: {dict(response.headers)}")
        print(f"Debug - Response body: {response.text}")
        
        if response.status_code == 200:
            user_data = response.json()
            if user_data and len(user_data) > 0:
                logging.info(f"User found: {user_data[0]}")
                print(f"Debug - User ID: {user_data[0].get('id')}")
                return user_data[0]
            else:
                logging.error("User not found - empty response.")
                print(f"Error: User '{username}' not found in Domino. API returned empty list.")
                print("Check that the username is spelled correctly and exists in Domino.")
                sys.exit(1)
        elif response.status_code == 401:
            print("Error: Authentication failed (401). The API key is invalid or expired.")
            print("Please check your DOMINO_USER_API_KEY secret in the UAT environment.")
            sys.exit(1)
        elif response.status_code == 403:
            print("Error: Access forbidden (403). The API key doesn't have permission to access user data.")
            sys.exit(1)
        else:
            logging.error(f"Failed to fetch user. Status: {response.status_code}, Response: {response.text}")
            print(f"Error: Failed to fetch user. HTTP Status: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error while looking up user: {str(e)}")
        print(f"Error: Network error while looking up user: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error while looking up user: {str(e)}")
        print(f"Error: Unexpected error: {str(e)}")
        sys.exit(1)

def create_git_provider(domino_url, api_key, user_id, github_pat, git_provider_name):
    """Create a GitHub provider for the user."""
    url = f"https://{domino_url}/v4/accounts/{user_id}/gitcredentials"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "name": git_provider_name,
        "gitServiceProvider": "github",
        "accessType": "token",
        "token": github_pat,
        "type": "TokenGitCredentialDto"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        git_provider = response.json()
        logging.info(f"GitHub provider created successfully: {git_provider}")
        return git_provider
    else:
        logging.error(f"Failed to create GitHub provider. Status: {response.status_code}, Response: {response.text}")
        print("Failed to create GitHub provider.")
        sys.exit(1)

def create_project(domino_url, api_key, user_id, git_provider_id, project_name, repo_uri, repo_name, git_ref_type="branches", git_ref_value="master"):
    """Create a new project with git repository."""
    url = f"https://{domino_url}/v4/projects"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "name": project_name,
        "description": "Created with API for app deployment",
        "visibility": "Private",
        "ownerId": user_id,
        "mainRepository": {
            "uri": repo_uri,
            "defaultRef": {
                "type": git_ref_type,
                "value": git_ref_value
            },
            "name": repo_name,
            "serviceProvider": "github",
            "credentialId": git_provider_id
        },
        "collaborators": [],
        "tags": {"tagNames": []}
    }
    
    print(f"Debug - Creating project with git ref: {git_ref_type}/{git_ref_value}")
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        project = response.json()
        logging.info(f"Project created successfully: {project}")
        return project
    else:
        logging.error(f"Failed to create project. Status: {response.status_code}, Response: {response.text}")
        print(f"Failed to create project. Status: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

def create_app(domino_url, api_key, project_id, app_name, environment_id, hardware_tier_id, git_ref_type="branches", git_ref_value="main", description="App created via API"):
    """Create an app in the specified project using the new beta API."""
    url = f"https://{domino_url}/api/apps/beta/apps"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    data = {
        "name": app_name,
        "description": description,
        "projectId": project_id,
        "entryPoint": "app.sh",
        "renderIFrame": True,
        "visibility": "GRANT_BASED",
        "discoverable": True,
        "mountDatasets": True,
        "version": {
            "hardwareTierId": hardware_tier_id,
            "environmentId": environment_id,
            "externalVolumeMountIds": [],
            "netAppVolumeIds": []
        },
        "gitRef": {
            "type": git_ref_type,
            "value": git_ref_value
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        app = response.json()
        logging.info(f"App created successfully: {app}")
        return app
    else:
        logging.error(f"Failed to create app. Status: {response.status_code}, Response: {response.text}")
        print(f"Failed to create app. Status: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
        
def start_app(domino_url, api_key, app_id, environment_id, hardware_tier_id):
    """Start the created app."""
    url = f"https://{domino_url}/v4/modelProducts/{app_id}/start"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "environmentId": environment_id,
        "hardwareTierId": hardware_tier_id,
        "externalVolumeMountIds": []
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        logging.info("App started successfully.")
        print("App started successfully.")
        return True
    else:
        logging.error(f"Failed to start app. Status: {response.status_code}, Response: {response.text}")
        print("Failed to start app.")
        return False

def stop_app(domino_url, api_key, app_id):
    """Stop the specified app."""
    url = f"https://{domino_url}/v4/modelProducts/{app_id}/stop"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key
    }
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        logging.info("App stopped successfully.")
        print("App stopped successfully.")
        return True
    else:
        logging.error(f"Failed to stop app. Status: {response.status_code}, Response: {response.text}")
        print("Failed to stop app.")
        return False

def find_app_by_name(domino_url, api_key, project_id, app_name):
    """Find an app by name within a project."""
    url = f"https://{domino_url}/v4/modelProducts"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        all_apps = response.json()
        project_apps = [app for app in all_apps if app.get('projectId') == project_id and app.get('name') == app_name]
        if project_apps:
            logging.info(f"Found app: {project_apps[0]}")
            return project_apps[0]
        else:
            logging.error(f"App '{app_name}' not found in project.")
            print(f"App '{app_name}' not found in project.")
            return None
    else:
        logging.error("Failed to fetch apps.")
        print("Failed to fetch apps.")
        return None

def find_project_by_name(domino_url, api_key, project_name, user_id=None):
    """Find a project by name."""
    url = f"https://{domino_url}/v4/projects"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        all_projects = response.json()
        matching_projects = [proj for proj in all_projects if proj.get('name') == project_name]
        
        # If user_id is provided, filter by owner
        if user_id and matching_projects:
            matching_projects = [proj for proj in matching_projects if proj.get('ownerId') == user_id]
        
        if matching_projects:
            logging.info(f"Found project: {matching_projects[0]}")
            return matching_projects[0]
        else:
            logging.error(f"Project '{project_name}' not found.")
            print(f"Project '{project_name}' not found.")
            return None
    else:
        logging.error("Failed to fetch projects.")
        print("Failed to fetch projects.")
        return None

def wait_for_project_ready(domino_url, api_key, project_id, max_wait_time=300):
    """Wait for project to be ready before creating app."""
    url = f"https://{domino_url}/v4/projects/{project_id}"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key
    }
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            project_data = response.json()
            # Check if project is in a ready state
            if project_data.get('status') != 'Creating':
                logging.info("Project is ready.")
                return True
        
        print("Waiting for project to be ready...")
        time.sleep(10)
    
    logging.warning("Project creation timeout reached.")
    print("Warning: Project may still be initializing.")
    return False

def get_available_environments(domino_url, api_key):
    """Get list of available environments."""
    url = f"https://{domino_url}/v4/environments"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        environments = response.json()
        logging.info(f"Available environments: {len(environments)}")
        return environments
    else:
        logging.error("Failed to fetch environments.")
        return []

def get_available_hardware_tiers(domino_url, api_key):
    """Get list of available hardware tiers."""
    url = f"https://{domino_url}/v4/hardwareTiers"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        hardware_tiers = response.json()
        logging.info(f"Available hardware tiers: {len(hardware_tiers)}")
        return hardware_tiers
    else:
        logging.error("Failed to fetch hardware tiers.")
        return []

def main():
    # Check if first argument is an action
    if len(sys.argv) > 1 and sys.argv[1] in ["create", "start", "stop"]:
        # Action-based argument parsing
        action = sys.argv[1]
        remaining_args = sys.argv[2:]  # Remove the action from args
        
        parser = argparse.ArgumentParser(description="Create Git provider, project, and manage apps in Domino.")
        
        # Config file option
        parser.add_argument("--config-file", help="Path to YAML configuration file")
        
        # Make all positional arguments optional when config file might be used
        parser.add_argument("username", nargs='?', help="The username of the user")
        parser.add_argument("user_api_key", nargs='?', help="The API key of the user")
        parser.add_argument("domino_url", nargs='?', help="The URL of the Domino instance")
        parser.add_argument("github_pat", nargs='?', help="The GitHub Personal Access Token")
        parser.add_argument("project_name", nargs='?', help="The name of the project")
        parser.add_argument("app_name", nargs='?', help="The name of the app to create/manage")
        parser.add_argument("environment_id", nargs='?', help="The environment ID for the app (required for create/start)")
        parser.add_argument("hardware_tier_id", nargs='?', help="The hardware tier ID for the app (required for create/start)")
                
        # Optional arguments
        parser.add_argument("--app-description", default="App created via API", help="Description for the app")
        parser.add_argument("--list-resources", action="store_true", help="List available environments and hardware tiers")
        parser.add_argument("--wait-for-project", action="store_true", help="Wait for project to be fully ready before creating app")
        parser.add_argument("--app-id", help="Specific app ID to start/stop (optional, will search by name if not provided)")
        parser.add_argument("--project-id", help="Specific project ID (optional, will search by name if not provided)")
        parser.add_argument("--repo-uri", default="https://github.com/ddl-wasanthag/WineQualityWorkshop", help="Git repository URI")
        parser.add_argument("--repo-name", default="wine_quality", help="Git repository name")
        parser.add_argument("--git-provider-name", default="sa-git-creds-app", help="Git provider name")
        parser.add_argument("--git-ref-type", default="branches", help="Git reference type (branches, tags, commit)")
        parser.add_argument("--git-ref-value", default="main", help="Git reference value (branch name, tag name, or commit hash)")

        args = parser.parse_args(remaining_args)
        args.action = action  # Add the action back
    else:
        # Default parsing (backward compatible)
        parser = argparse.ArgumentParser(description="Create Git provider, project, and manage apps in Domino.")
        
        # Config file option
        parser.add_argument("--config-file", help="Path to YAML configuration file")
        
        # Make all positional arguments optional when config file might be used  
        parser.add_argument("username", nargs='?', help="The username of the user")
        parser.add_argument("user_api_key", nargs='?', help="The api key of the user")
        parser.add_argument("domino_url", nargs='?', help="The URL of the Domino instance")
        parser.add_argument("github_pat", nargs='?', help="The GitHub Personal Access Token")
        parser.add_argument("project_name", nargs='?', help="The name of the project")
        parser.add_argument("app_name", nargs='?', help="The name of the app to create/manage")
        parser.add_argument("environment_id", nargs='?', help="The environment ID for the app (required for create/start)")
        parser.add_argument("hardware_tier_id", nargs='?', help="The hardware tier ID for the app (required for create/start)")
        
        # Action arguments
        parser.add_argument("--action", choices=["create", "start", "stop"], default="create",
                           help="Action to perform: create (default), start, or stop")
        parser.add_argument("--app-description", default="App created via API", help="Description for the app")
        parser.add_argument("--list-resources", action="store_true", help="List available environments and hardware tiers")
        parser.add_argument("--wait-for-project", action="store_true", help="Wait for project to be fully ready before creating app")
        parser.add_argument("--app-id", help="Specific app ID to start/stop (optional, will search by name if not provided)")
        parser.add_argument("--project-id", help="Specific project ID (optional, will search by name if not provided)")
        parser.add_argument("--repo-uri", default="https://github.com/ddl-wasanthag/WineQualityWorkshop", help="Git repository URI")
        parser.add_argument("--repo-name", default="wine_quality", help="Git repository name")
        parser.add_argument("--git-provider-name", default="sa-git-creds-app", help="Git provider name")
        parser.add_argument("--git-ref-type", default="branches", help="Git reference type (branches, tags, commit)")
        parser.add_argument("--git-ref-value", default="main", help="Git reference value (branch name, tag name, or commit hash)")

        args = parser.parse_args()

    # Load configuration from file if provided
    config = {}
    if args.config_file:
        config = load_config_file(args.config_file)
        
    # Override with config file values, but command line args take precedence
    def get_value(key, default=None):
        arg_value = getattr(args, key, None)
        config_value = config.get(key, None)
        
        # Use config value if arg value is None or equals the default
        if arg_value is None:
            return config_value if config_value is not None else default
        elif key in ['repo_uri', 'repo_name', 'git_provider_name']:
            # For these keys, check if we're using the hardcoded defaults
            defaults = {
                'repo_uri': 'https://github.com/ddl-wasanthag/WineQualityWorkshop',
                'repo_name': 'wine_quality', 
                'git_provider_name': 'sa-git-creds-app'
            }
            if arg_value == defaults.get(key) and config_value is not None:
                return config_value
        
        return arg_value if arg_value is not None else default
    
    # Apply configuration values
    args.username = get_value('username', args.username)
    args.user_api_key = get_value('user_api_key', args.user_api_key)
    args.domino_url = get_value('domino_url', args.domino_url)
    args.github_pat = get_value('github_pat', args.github_pat)
    args.project_name = get_value('project_name', args.project_name)
    args.app_name = get_value('app_name', args.app_name)
    args.environment_id = get_value('environment_id', args.environment_id)
    args.hardware_tier_id = get_value('hardware_tier_id', args.hardware_tier_id)
    args.repo_uri = get_value('repo_uri', getattr(args, 'repo_uri', 'https://github.com/ddl-wasanthag/WineQualityWorkshop'))
    args.repo_name = get_value('repo_name', getattr(args, 'repo_name', 'wine_quality'))
    args.git_provider_name = get_value('git_provider_name', getattr(args, 'git_provider_name', 'sa-git-creds-app'))
    args.app_description = get_value('app_description', getattr(args, 'app_description', 'App created via API'))
    args.git_ref_type = get_value('git_ref_type', getattr(args, 'git_ref_type', 'branches'))
    args.git_ref_value = get_value('git_ref_value', getattr(args, 'git_ref_value', 'main'))
    
    # Validate required arguments after config loading
    required_fields = ['username', 'domino_url', 'github_pat', 'project_name', 'app_name']
    missing_fields = [field for field in required_fields if not getattr(args, field)]
    
    if missing_fields:
        print(f"Error: Missing required fields: {', '.join(missing_fields)}")
        if args.config_file:
            print("These must be provided in the config file or via command line arguments.")
        else:
            print("These can be provided via command line arguments or in a config file (use --config-file).")
        sys.exit(1)

    # Get API key
    api_key = args.user_api_key
    
    # Use the provided domino_url directly
    domino_url = args.domino_url
    
    # Debug output to see what's being parsed
    print(f"Debug - Action: {getattr(args, 'action', 'create')}")
    print(f"Debug - Username: {args.username}")
    print(f"Debug - User_api_key: {args.user_api_key}")
    print(f"Debug - Domino URL: {args.domino_url}")
    print(f"Debug - Project: {args.project_name}")
    print(f"Debug - App: {args.app_name}")
    print(f"Debug - Repo URI: {args.repo_uri}")
    print(f"Debug - Repo Name: {args.repo_name}")
    print(f"Debug - Git Provider Name: {args.git_provider_name}")
    print(f"Debug - Config file used: {args.config_file}")
    print(f"Debug - Config loaded: {bool(config)}")
    if config:
        print(f"Debug - Git provider name from config: {config.get('git_provider_name', 'NOT FOUND')}")
    
    # List available resources if requested
    if args.list_resources:
        print("Available Environments:")
        environments = get_available_environments(domino_url, api_key)
        for env in environments:
            print(f"  ID: {env.get('id')}, Name: {env.get('name')}")
        
        print("\nAvailable Hardware Tiers:")
        hardware_tiers = get_available_hardware_tiers(domino_url, api_key)
        for tier in hardware_tiers:
            print(f"  ID: {tier.get('id')}, Name: {tier.get('name')}")
        return

    # Get user information
    user = lookup_user(domino_url, api_key, args.username)
    user_id = user['id']
    logging.info(f"User ID: {user_id}")

    action = getattr(args, 'action', 'create')
    
    if action == "create":
        # Validate required arguments for create action
        if not args.environment_id or not args.hardware_tier_id:
            print("Error: environment_id and hardware_tier_id are required for create action")
            sys.exit(1)

        # Create git provider
        git_provider = create_git_provider(domino_url, api_key, user_id, args.github_pat, args.git_provider_name)
        git_provider_id = git_provider['id']
        logging.info(f"GitHub Provider ID: {git_provider_id}")

        # Create project
        project = create_project(
            domino_url, 
            api_key, 
            user_id, 
            git_provider_id, 
            args.project_name, 
            args.repo_uri, 
            args.repo_name,
            git_ref_type=args.git_ref_type,
            git_ref_value=args.git_ref_value
        )
        project_id = project['id']
        logging.info(f"Project ID: {project_id}")
        print(f"Project created successfully with ID: {project_id}")

        # Wait for project to be ready if requested
        if args.wait_for_project:
            wait_for_project_ready(domino_url, api_key, project_id)

        # Create the app
        app = create_app(
            domino_url, 
            api_key, 
            project_id, 
            args.app_name,
            args.environment_id, 
            args.hardware_tier_id,
            git_ref_type=args.git_ref_type,
            git_ref_value=args.git_ref_value,
            description=args.app_description
        )
        app_id = app['id']
        logging.info(f"App ID: {app_id}")
        print(f"App created successfully with ID: {app_id}")

        # Start the app
        if start_app(domino_url, api_key, app_id, args.environment_id, args.hardware_tier_id):
            print(f"App '{args.app_name}' has been created and started successfully in project '{args.project_name}'!")
        else:
            print("App creation succeeded but failed to start. You may need to start it manually.")

        print(f"\nSummary:")
        print(f"Project: {args.project_name} (ID: {project_id})")
        print(f"App: {args.app_name} (ID: {app_id})")

    elif action == "start":
        # Handle start action for existing app
        if not args.environment_id or not args.hardware_tier_id:
            print("Error: environment_id and hardware_tier_id are required for start action")
            sys.exit(1)

        # Find project and app
        if args.project_id:
            project_id = args.project_id
        else:
            project = find_project_by_name(domino_url, api_key, args.project_name, user_id)
            if not project:
                sys.exit(1)
            project_id = project['id']

        if args.app_id:
            app_id = args.app_id
        else:
            app = find_app_by_name(domino_url, api_key, project_id, args.app_name)
            if not app:
                sys.exit(1)
            app_id = app['id']

        # Start the app
        if start_app(domino_url, api_key, app_id, args.environment_id, args.hardware_tier_id):
            print(f"App '{args.app_name}' has been started successfully!")
        else:
            print("Failed to start the app.")

    elif action == "stop":
        # Handle stop action for existing app
        # Find project and app
        if args.project_id:
            project_id = args.project_id
        else:
            project = find_project_by_name(domino_url, api_key, args.project_name, user_id)
            if not project:
                sys.exit(1)
            project_id = project['id']

        if args.app_id:
            app_id = args.app_id
        else:
            app = find_app_by_name(domino_url, api_key, project_id, args.app_name)
            if not app:
                sys.exit(1)
            app_id = app['id']

        # Stop the app
        if stop_app(domino_url, api_key, app_id):
            print(f"App '{args.app_name}' has been stopped successfully!")
        else:
            print("Failed to stop the app.")

if __name__ == "__main__":
    main()