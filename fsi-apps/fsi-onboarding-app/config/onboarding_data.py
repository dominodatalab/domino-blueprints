"""
FSI Domino Onboarding App - Configuration Data
Maps organizations, roles, Domino capabilities, and learning resources
"""

# Organization and Role Mapping
ORGANIZATIONS = {
    "Retail Banking": {
        "domino_org": "Retail Banking",
        "roles": ["Data Scientist", "Business Manager"],
        "use_case_url": "https://bank.retail.sharepoint.com",
        "description": "Consumer banking, deposits, loans, and retail financial products"
    },
    "Investment Banking": {
        "domino_org": "Investment Banking",
        "roles": ["Data Scientist", "Quant Analyst", "Business Manager"],
        "use_case_url": "https://bank.ib.sharepoint.com",
        "description": "Capital markets, trading, M&A, and institutional financial services"
    },
    "Risk Management": {
        "domino_org": "Risk Management",
        "roles": ["Data Scientist", "Model Validator", "ML Engineer", "Business Manager"],
        "use_case_url": "https://bank.risk.sharepoint.com",
        "description": "Credit risk, market risk, operational risk, and model validation"
    }
}

# Role Definitions and Domino Role Mapping
ROLE_DEFINITIONS = {
    "Data Scientist": {
        "domino_role": "Practitioner",
        "project_access": "Project Owner",
        "description": "Develops models, runs experiments, and creates data products",
        "key_capabilities": [
            "Create and manage projects",
            "Launch workspaces (Jupyter, VS Code, RStudio)",
            "Run jobs and scheduled workflows",
            "Deploy models and applications",
            "Track experiments with MLflow",
            "Collaborate with team members"
        ],
        "typical_tools": ["Python", "R", "Jupyter", "Git", "MLflow", "Spark"]
    },
    "Quant Analyst": {
        "domino_role": "Practitioner",
        "project_access": "Project Owner",
        "description": "Quantitative analysis for trading, pricing, and risk modeling",
        "key_capabilities": [
            "Create and manage projects",
            "Launch workspaces (Jupyter, VS Code, RStudio)",
            "Run computational jobs",
            "Deploy pricing and risk models",
            "Track model experiments",
            "Access distributed computing (Spark, Ray)"
        ],
        "typical_tools": ["Python", "R", "MATLAB", "Jupyter", "Git", "Spark"]
    },
    "Model Validator": {
        "domino_role": "Practitioner",
        "project_access": "Project Owner",
        "description": "Independent validation of models for governance and compliance",
        "key_capabilities": [
            "Create validation projects",
            "Review model artifacts and code",
            "Run validation tests and backtests",
            "Document findings in governance bundles",
            "Access experiment tracking and lineage",
            "Generate validation reports"
        ],
        "typical_tools": ["Python", "R", "Jupyter", "Git", "MLflow", "Governance Bundles"]
    },
    "ML Engineer": {
        "domino_role": "Practitioner",
        "project_access": "Project Owner",
        "description": "Productionizes ML models and builds ML infrastructure",
        "key_capabilities": [
            "Create and manage projects",
            "Build custom environments (Docker)",
            "Deploy model APIs and endpoints",
            "Set up CI/CD pipelines",
            "Configure monitoring and alerting",
            "Orchestrate workflows with Domino Flows"
        ],
        "typical_tools": ["Python", "Docker", "Git", "Kubernetes", "MLflow", "Airflow/Flyte"]
    },
    "Business Manager": {
        "domino_role": "Practitioner or Launcher User or Lite User",
        "project_access": "Varies - can be Project Owner, Contributor, or Launcher User",
        "description": "Business stakeholders who consume or interact with data products",
        "key_capabilities": [
            "Practitioner: Full project access",
            "Launcher User: Run pre-configured analyses via Launchers",
            "Lite User: View apps and dashboards only",
            "Access published apps and dashboards",
            "Review model results and reports",
            "Provide business requirements"
        ],
        "typical_tools": ["Domino Apps", "Launchers", "Dashboards", "Reports"]
    }
}

# Common Documentation Links
COMMON_DOCS = {
    "Model Governance": {
        "url": "https://bank.sharepoint.com",
        "description": "Enterprise model governance framework and policies",
        "topics": ["Model Risk Management", "SR 11-7 Compliance", "Governance Bundles"]
    },
    "AI Policy": {
        "url": "https://bank.sharepoint.com",
        "description": "Enterprise AI/ML usage policies and ethical guidelines",
        "topics": ["Responsible AI", "Bias Detection", "Explainability", "Data Privacy"]
    },
    "Compliance Requirements": {
        "url": "https://bank.sharepoint.com",
        "description": "Regulatory compliance requirements for model development",
        "topics": ["SR 11-7", "NIST AI RMF", "Model Documentation", "Audit Trail"]
    },
    "Domino Standards": {
        "url": "https://bank.confluence.com",
        "description": "Internal Domino platform standards and best practices",
        "topics": ["Naming Conventions", "Environment Standards", "Project Templates"]
    }
}

# Learning Paths and Labs by Role
LEARNING_PATHS = {
    "Data Scientist": {
        "beginner": [
            {
                "title": "Getting Started with Domino Workspaces",
                "description": "Launch your first Jupyter workspace and understand the Domino interface",
                "type": "lab",
                "duration": "30 min",
                "topics": ["Workspaces", "Jupyter", "Project Navigation"]
            },
            {
                "title": "Running Your First Domino Job",
                "description": "Execute a Python script as a batch job and review outputs",
                "type": "lab",
                "duration": "20 min",
                "topics": ["Jobs", "Batch Execution", "Hardware Tiers"]
            },
            {
                "title": "Introduction to MLflow Experiment Tracking",
                "description": "Track model experiments with parameters, metrics, and artifacts",
                "type": "lab",
                "duration": "45 min",
                "topics": ["MLflow", "Experiment Tracking", "Model Registry"]
            }
        ],
        "intermediate": [
            {
                "title": "Working with Domino Datasets",
                "description": "Create versioned datasets for reproducible data management",
                "type": "lab",
                "duration": "40 min",
                "topics": ["Datasets", "Data Versioning", "Snapshots"]
            },
            {
                "title": "Building a Model API Endpoint",
                "description": "Deploy a trained model as a REST API for real-time predictions",
                "type": "lab",
                "duration": "60 min",
                "topics": ["Model APIs", "Deployment", "Monitoring"]
            },
            {
                "title": "Git Integration and Version Control",
                "description": "Connect Git repositories and manage code versions",
                "type": "lab",
                "duration": "35 min",
                "topics": ["Git", "Version Control", "Collaboration"]
            }
        ],
        "advanced": [
            {
                "title": "Distributed Computing with Spark",
                "description": "Process large datasets using on-demand Spark clusters",
                "type": "lab",
                "duration": "90 min",
                "topics": ["Spark", "Distributed Computing", "PySpark"]
            },
            {
                "title": "Building ML Pipelines with Domino Flows",
                "description": "Orchestrate multi-step workflows with Flyte-based Flows",
                "type": "lab",
                "duration": "75 min",
                "topics": ["Flows", "Orchestration", "DAGs", "Flyte"]
            },
            {
                "title": "Model Governance and Compliance",
                "description": "Create governance bundles and track model lineage for SR 11-7",
                "type": "lab",
                "duration": "60 min",
                "topics": ["Governance", "Compliance", "SR 11-7", "Audit Trail"]
            }
        ]
    },
    "Quant Analyst": {
        "beginner": [
            {
                "title": "Getting Started with Domino Workspaces",
                "description": "Launch your first Jupyter/RStudio workspace for quant analysis",
                "type": "lab",
                "duration": "30 min",
                "topics": ["Workspaces", "Jupyter", "RStudio"]
            },
            {
                "title": "Running Quantitative Models as Jobs",
                "description": "Execute pricing and risk models as scheduled batch jobs",
                "type": "lab",
                "duration": "25 min",
                "topics": ["Jobs", "Scheduling", "Cron"]
            },
            {
                "title": "Financial Data Access in Domino",
                "description": "Connect to market data sources and internal databases",
                "type": "lab",
                "duration": "40 min",
                "topics": ["Data Connectivity", "SQL", "Market Data"]
            }
        ],
        "intermediate": [
            {
                "title": "High-Performance Computing for Quant Models",
                "description": "Leverage GPU and multi-core compute for Monte Carlo simulations",
                "type": "lab",
                "duration": "50 min",
                "topics": ["GPU Computing", "Monte Carlo", "Performance"]
            },
            {
                "title": "Deploying Pricing Models as APIs",
                "description": "Create real-time pricing endpoints for trading systems",
                "type": "lab",
                "duration": "60 min",
                "topics": ["Model APIs", "Pricing", "Low Latency"]
            },
            {
                "title": "Version Control for Quantitative Research",
                "description": "Manage model versions and research code with Git",
                "type": "lab",
                "duration": "30 min",
                "topics": ["Git", "Version Control", "Research"]
            }
        ],
        "advanced": [
            {
                "title": "Distributed Backtesting with Ray",
                "description": "Run parallel backtests across multiple scenarios",
                "type": "lab",
                "duration": "80 min",
                "topics": ["Ray", "Backtesting", "Distributed Computing"]
            },
            {
                "title": "Real-Time Risk Calculation Pipelines",
                "description": "Build streaming risk calculation workflows",
                "type": "lab",
                "duration": "90 min",
                "topics": ["Flows", "Real-time", "Risk Calculations"]
            },
            {
                "title": "Model Validation and Documentation",
                "description": "Document quant models for model risk management review",
                "type": "lab",
                "duration": "50 min",
                "topics": ["Governance", "Documentation", "Model Risk"]
            }
        ]
    },
    "Model Validator": {
        "beginner": [
            {
                "title": "Understanding Domino Projects and Artifacts",
                "description": "Navigate projects, review code, and access model artifacts",
                "type": "lab",
                "duration": "35 min",
                "topics": ["Projects", "Code Review", "Artifacts"]
            },
            {
                "title": "Accessing Model Experiment History",
                "description": "Review MLflow experiment tracking and model lineage",
                "type": "lab",
                "duration": "40 min",
                "topics": ["MLflow", "Lineage", "Reproducibility"]
            },
            {
                "title": "Running Validation Tests as Jobs",
                "description": "Execute validation scripts and generate test reports",
                "type": "lab",
                "duration": "30 min",
                "topics": ["Jobs", "Testing", "Validation"]
            }
        ],
        "intermediate": [
            {
                "title": "Creating Governance Bundles",
                "description": "Document validation findings in Domino governance framework",
                "type": "lab",
                "duration": "50 min",
                "topics": ["Governance Bundles", "Documentation", "SR 11-7"]
            },
            {
                "title": "Independent Model Replication",
                "description": "Reproduce model results and verify reproducibility",
                "type": "lab",
                "duration": "60 min",
                "topics": ["Reproducibility", "Validation", "Environments"]
            },
            {
                "title": "Automated Validation Workflows",
                "description": "Build automated validation test suites",
                "type": "lab",
                "duration": "45 min",
                "topics": ["Automation", "Testing", "CI/CD"]
            }
        ],
        "advanced": [
            {
                "title": "Model Risk Assessment Framework",
                "description": "Comprehensive model risk tiering and assessment",
                "type": "lab",
                "duration": "90 min",
                "topics": ["Model Risk", "SR 11-7", "Risk Tiering"]
            },
            {
                "title": "Ongoing Monitoring and Validation",
                "description": "Set up continuous monitoring for production models",
                "type": "lab",
                "duration": "70 min",
                "topics": ["Monitoring", "Drift Detection", "Alerts"]
            },
            {
                "title": "End-to-End Validation Documentation",
                "description": "Complete validation report with governance evidence",
                "type": "lab",
                "duration": "80 min",
                "topics": ["Documentation", "Governance", "Compliance"]
            }
        ]
    },
    "ML Engineer": {
        "beginner": [
            {
                "title": "Getting Started with Domino Environments",
                "description": "Understand environment configuration and package management",
                "type": "lab",
                "duration": "40 min",
                "topics": ["Environments", "Docker", "Dependencies"]
            },
            {
                "title": "Deploying Your First Model API",
                "description": "Deploy a simple model endpoint and test the API",
                "type": "lab",
                "duration": "45 min",
                "topics": ["Model APIs", "Deployment", "REST APIs"]
            },
            {
                "title": "Job Scheduling and Automation",
                "description": "Set up scheduled jobs for batch predictions and retraining",
                "type": "lab",
                "duration": "30 min",
                "topics": ["Jobs", "Scheduling", "Automation"]
            }
        ],
        "intermediate": [
            {
                "title": "Custom Environment Development",
                "description": "Build custom Docker environments with specific ML frameworks",
                "type": "lab",
                "duration": "60 min",
                "topics": ["Docker", "Custom Environments", "Dockerfile"]
            },
            {
                "title": "Building Production ML Pipelines",
                "description": "Create end-to-end ML pipelines with Domino Flows",
                "type": "lab",
                "duration": "75 min",
                "topics": ["Flows", "Pipelines", "Flyte", "MLOps"]
            },
            {
                "title": "Model Monitoring and Alerting",
                "description": "Set up Grafana dashboards and alerting for production models",
                "type": "lab",
                "duration": "50 min",
                "topics": ["Monitoring", "Grafana", "Alerts", "Observability"]
            }
        ],
        "advanced": [
            {
                "title": "GPU-Accelerated Model Serving with Triton",
                "description": "Deploy high-performance GPU inference endpoints",
                "type": "lab",
                "duration": "90 min",
                "topics": ["Triton", "GPU", "High Performance", "Inference"]
            },
            {
                "title": "CI/CD for ML Models",
                "description": "Implement automated testing and deployment pipelines",
                "type": "lab",
                "duration": "85 min",
                "topics": ["CI/CD", "GitHub Actions", "Automation", "Testing"]
            },
            {
                "title": "Multi-Environment Orchestration",
                "description": "Build Flows with heterogeneous compute environments",
                "type": "lab",
                "duration": "70 min",
                "topics": ["Flows", "Heterogeneous Compute", "Orchestration"]
            }
        ]
    },
    "Business Manager": {
        "beginner": [
            {
                "title": "Navigating Domino Apps and Dashboards",
                "description": "Access and interact with published data products",
                "type": "tutorial",
                "duration": "20 min",
                "topics": ["Apps", "Dashboards", "Navigation"]
            },
            {
                "title": "Using Domino Launchers",
                "description": "Execute pre-configured analyses with simple forms",
                "type": "tutorial",
                "duration": "15 min",
                "topics": ["Launchers", "Self-Service", "Forms"]
            },
            {
                "title": "Understanding Model Results and Reports",
                "description": "Interpret model outputs and generated reports",
                "type": "tutorial",
                "duration": "25 min",
                "topics": ["Reports", "Model Results", "Interpretation"]
            }
        ],
        "intermediate": [
            {
                "title": "Collaborating on Domino Projects",
                "description": "Provide feedback and requirements to technical teams",
                "type": "tutorial",
                "duration": "30 min",
                "topics": ["Collaboration", "Projects", "Feedback"]
            },
            {
                "title": "Requesting New Analyses via Launchers",
                "description": "Parameterize and run business-driven analyses",
                "type": "tutorial",
                "duration": "20 min",
                "topics": ["Launchers", "Parameters", "Business Analysis"]
            },
            {
                "title": "Basic Workspace Usage (Optional)",
                "description": "For Practitioners: Launch and use workspaces for simple tasks",
                "type": "lab",
                "duration": "40 min",
                "topics": ["Workspaces", "Jupyter", "Basic Analysis"]
            }
        ],
        "advanced": [
            {
                "title": "Model Governance for Business Stakeholders",
                "description": "Understand governance requirements and approval workflows",
                "type": "tutorial",
                "duration": "45 min",
                "topics": ["Governance", "Compliance", "Business Approval"]
            },
            {
                "title": "Creating Business Requirements for Models",
                "description": "Document and communicate model requirements effectively",
                "type": "tutorial",
                "duration": "35 min",
                "topics": ["Requirements", "Documentation", "Communication"]
            },
            {
                "title": "Full Project Ownership (For Practitioners)",
                "description": "Manage projects end-to-end as a business-technical hybrid",
                "type": "lab",
                "duration": "60 min",
                "topics": ["Project Management", "Full Stack", "Leadership"]
            }
        ]
    }
}

# FSI-Specific Use Cases by Organization
FSI_USE_CASES = {
    "Retail Banking": [
        {
            "title": "Credit Scoring Models",
            "description": "Build and validate credit risk models for consumer lending",
            "relevant_roles": ["Data Scientist", "Model Validator"],
            "complexity": "Intermediate",
            "governance_required": True
        },
        {
            "title": "Fraud Detection System",
            "description": "Real-time fraud detection for card transactions",
            "relevant_roles": ["Data Scientist", "ML Engineer"],
            "complexity": "Advanced",
            "governance_required": True
        },
        {
            "title": "Customer Churn Prediction",
            "description": "Predict and prevent customer attrition",
            "relevant_roles": ["Data Scientist"],
            "complexity": "Beginner",
            "governance_required": False
        },
        {
            "title": "Personalized Product Recommendations",
            "description": "ML-driven product recommendation engine",
            "relevant_roles": ["Data Scientist", "ML Engineer"],
            "complexity": "Intermediate",
            "governance_required": False
        },
        {
            "title": "Loan Default Analysis Dashboard",
            "description": "Interactive dashboard for loan portfolio analysis",
            "relevant_roles": ["Data Scientist", "Business Manager"],
            "complexity": "Beginner",
            "governance_required": False
        }
    ],
    "Investment Banking": [
        {
            "title": "Algorithmic Trading Strategies",
            "description": "Quantitative trading models and backtesting",
            "relevant_roles": ["Quant Analyst"],
            "complexity": "Advanced",
            "governance_required": True
        },
        {
            "title": "Derivatives Pricing Models",
            "description": "Options and exotic derivatives pricing",
            "relevant_roles": ["Quant Analyst"],
            "complexity": "Advanced",
            "governance_required": True
        },
        {
            "title": "Portfolio Optimization",
            "description": "Mean-variance and risk-parity portfolio construction",
            "relevant_roles": ["Quant Analyst", "Data Scientist"],
            "complexity": "Intermediate",
            "governance_required": False
        },
        {
            "title": "Market Risk VaR Calculation",
            "description": "Value at Risk calculation for trading portfolios",
            "relevant_roles": ["Quant Analyst", "Data Scientist"],
            "complexity": "Intermediate",
            "governance_required": True
        },
        {
            "title": "Deal Screening AI Assistant",
            "description": "NLP-based M&A deal screening and analysis",
            "relevant_roles": ["Data Scientist"],
            "complexity": "Advanced",
            "governance_required": False
        }
    ],
    "Risk Management": [
        {
            "title": "Credit Risk Rating Models",
            "description": "PD, LGD, and EAD models for CECL/IFRS 9",
            "relevant_roles": ["Data Scientist", "Model Validator"],
            "complexity": "Advanced",
            "governance_required": True
        },
        {
            "title": "Model Validation Framework",
            "description": "End-to-end model validation and governance",
            "relevant_roles": ["Model Validator"],
            "complexity": "Advanced",
            "governance_required": True
        },
        {
            "title": "Stress Testing Engine",
            "description": "CCAR/DFAST stress testing automation",
            "relevant_roles": ["Data Scientist", "ML Engineer"],
            "complexity": "Advanced",
            "governance_required": True
        },
        {
            "title": "Operational Risk Loss Prediction",
            "description": "Predict and quantify operational risk losses",
            "relevant_roles": ["Data Scientist"],
            "complexity": "Intermediate",
            "governance_required": True
        },
        {
            "title": "Model Monitoring Dashboard",
            "description": "Real-time monitoring for production risk models",
            "relevant_roles": ["ML Engineer", "Model Validator"],
            "complexity": "Intermediate",
            "governance_required": True
        },
        {
            "title": "Anti-Money Laundering (AML) Detection",
            "description": "Transaction monitoring for AML compliance",
            "relevant_roles": ["Data Scientist", "ML Engineer"],
            "complexity": "Advanced",
            "governance_required": True
        }
    ]
}

# Support Information
SUPPORT_INFO = {
    "incident_system": {
        "name": "Internal Incident Ticket System",
        "url": "https://bank.servicedesk.com",
        "description": "Submit and track support tickets for Domino platform issues"
    },
    "best_practices": [
        {
            "title": "Creating Effective Support Tickets",
            "guidelines": [
                "Provide a clear, descriptive title summarizing the issue",
                "Include the exact error message (copy-paste, not screenshot)",
                "Specify the project name and Domino organization",
                "List the steps to reproduce the problem",
                "Mention any recent changes (new packages, environment updates, etc.)"
            ]
        },
        {
            "title": "Uploading Evidence",
            "guidelines": [
                "Attach relevant screenshots showing the error or unexpected behavior",
                "Include log files from failed jobs or workspace sessions",
                "Attach relevant code files (if applicable and non-sensitive)",
                "Provide the job ID or workspace session ID",
                "Include environment.yml or requirements.txt if environment-related"
            ]
        },
        {
            "title": "Providing Context",
            "guidelines": [
                "Include the full Domino URL where the issue occurs",
                "Specify the environment name and version being used",
                "Mention the hardware tier selected",
                "Describe the expected behavior vs. actual behavior",
                "Indicate urgency level and business impact"
            ]
        },
        {
            "title": "Best Practices for Faster Resolution",
            "guidelines": [
                "Check Domino documentation and knowledge base first",
                "Search existing tickets to see if issue is already reported",
                "Provide all information upfront to avoid back-and-forth",
                "Be available for follow-up questions from support team",
                "Update the ticket if you discover new information or workarounds"
            ]
        }
    ],
    "contact_channels": [
        {
            "channel": "Service Desk Portal",
            "url": "https://bank.servicedesk.com",
            "use_for": "All technical issues, access requests, and general inquiries",
            "sla": "Response within 4 business hours"
        },
        {
            "channel": "Slack #domino-support",
            "url": "slack://channel?team=TEAMID&id=domino-support",
            "use_for": "Quick questions, community help, and platform updates",
            "sla": "Best effort, community-driven"
        },
        {
            "channel": "Office Hours",
            "url": "https://bank.confluence.com/domino-office-hours",
            "use_for": "Live help sessions, architecture discussions, best practices",
            "sla": "Weekly sessions, Tuesday & Thursday 2-3 PM EST"
        },
        {
            "channel": "Emergency Hotline",
            "url": "tel:+1-555-DOMINO-1",
            "use_for": "Production outages and critical issues only",
            "sla": "Immediate response 24/7"
        }
    ]
}

# Role-Specific Programming Tools and Languages
ROLE_TECH_STACK = {
    "Data Scientist": {
        "primary_languages": [
            {
                "name": "Python",
                "version": "3.8+",
                "use_cases": "General ML, data analysis, deep learning",
                "key_libraries": ["pandas", "scikit-learn", "TensorFlow", "PyTorch", "XGBoost"],
                "learning_resources": [
                    "Python for Data Science (Domino Academy)",
                    "Scikit-learn official documentation",
                    "Internal Python style guide"
                ]
            },
            {
                "name": "R",
                "version": "4.0+",
                "use_cases": "Statistical analysis, econometrics, visualization",
                "key_libraries": ["tidyverse", "caret", "data.table", "ggplot2", "shiny"],
                "learning_resources": [
                    "R for Financial Services (Domino Academy)",
                    "Tidyverse documentation",
                    "Internal R coding standards"
                ]
            }
        ],
        "key_tools": [
            "Jupyter Notebook/Lab - Interactive development and prototyping",
            "RStudio - R development and Shiny apps",
            "VS Code - General-purpose coding and debugging",
            "Git - Version control and collaboration",
            "MLflow - Experiment tracking and model registry",
            "DVC - Data version control"
        ],
        "domino_specific": [
            "Domino Workspaces - Launch Jupyter, RStudio, or VS Code",
            "Domino Jobs - Run batch training jobs with scheduling",
            "Domino Datasets - Store and version training data",
            "Experiment Manager - Track model experiments with MLflow",
            "Model APIs - Deploy models as REST endpoints"
        ]
    },
    "Quant Analyst": {
        "primary_languages": [
            {
                "name": "Python",
                "version": "3.8+",
                "use_cases": "Quantitative modeling, backtesting, optimization",
                "key_libraries": ["NumPy", "SciPy", "pandas", "QuantLib", "PyMC", "statsmodels"],
                "learning_resources": [
                    "Python for Quantitative Finance",
                    "QuantLib documentation",
                    "Internal quant library documentation"
                ]
            },
            {
                "name": "R",
                "version": "4.0+",
                "use_cases": "Time series analysis, econometrics, risk modeling",
                "key_libraries": ["quantmod", "PerformanceAnalytics", "rugarch", "forecast", "zoo"],
                "learning_resources": [
                    "R for Quantitative Finance",
                    "Time Series Analysis in R",
                    "Internal risk modeling guides"
                ]
            },
            {
                "name": "MATLAB",
                "version": "R2020a+",
                "use_cases": "Derivatives pricing, optimization, numerical methods",
                "key_libraries": ["Financial Toolbox", "Optimization Toolbox", "Statistics Toolbox"],
                "learning_resources": [
                    "MATLAB Financial Toolbox documentation",
                    "Internal MATLAB best practices"
                ]
            }
        ],
        "key_tools": [
            "Jupyter Notebook - Prototyping and analysis",
            "RStudio - Statistical modeling and visualization",
            "Git - Version control for models and research",
            "Spark - Large-scale data processing",
            "Ray - Distributed backtesting and optimization"
        ],
        "domino_specific": [
            "High-Performance Compute - GPU and multi-core instances",
            "Distributed Computing - Spark and Ray clusters",
            "Scheduled Jobs - Automated model runs and reports",
            "Model APIs - Real-time pricing endpoints",
            "Domino Flows - Multi-stage backtesting pipelines"
        ]
    },
    "Model Validator": {
        "primary_languages": [
            {
                "name": "Python",
                "version": "3.8+",
                "use_cases": "Model replication, validation testing, analysis",
                "key_libraries": ["pandas", "scikit-learn", "NumPy", "pytest", "hypothesis"],
                "learning_resources": [
                    "Python testing best practices",
                    "Model validation guidelines",
                    "Internal validation framework docs"
                ]
            },
            {
                "name": "R",
                "version": "4.0+",
                "use_cases": "Statistical validation, backtesting, reporting",
                "key_libraries": ["testthat", "validate", "data.table", "rmarkdown"],
                "learning_resources": [
                    "R testing frameworks",
                    "RMarkdown for validation reports"
                ]
            }
        ],
        "key_tools": [
            "Jupyter Notebook - Validation analysis and documentation",
            "RStudio - Statistical tests and reports",
            "Git - Code review and version control",
            "MLflow - Model lineage and artifact review",
            "Governance Bundles - Documentation and evidence management"
        ],
        "domino_specific": [
            "Governance Bundles - Centralized validation documentation",
            "Experiment Tracking - Review model development history",
            "Domino Jobs - Automated validation test suites",
            "Project Collaboration - Independent validation workspace",
            "Model Artifacts - Access training data, code, and results"
        ]
    },
    "ML Engineer": {
        "primary_languages": [
            {
                "name": "Python",
                "version": "3.8+",
                "use_cases": "MLOps, deployment, pipeline orchestration",
                "key_libraries": ["Flask/FastAPI", "Docker", "Kubernetes", "Airflow", "pytest"],
                "learning_resources": [
                    "MLOps best practices",
                    "Docker and Kubernetes documentation",
                    "Internal deployment guidelines"
                ]
            },
            {
                "name": "Bash/Shell",
                "version": "N/A",
                "use_cases": "Automation, scripting, CI/CD",
                "key_libraries": ["N/A"],
                "learning_resources": [
                    "Shell scripting guide",
                    "Internal automation standards"
                ]
            }
        ],
        "key_tools": [
            "Docker - Container development and custom environments",
            "Git - Source control and CI/CD integration",
            "VS Code - Development and debugging",
            "Kubernetes - Container orchestration (if applicable)",
            "Jenkins/GitHub Actions - CI/CD pipelines",
            "Grafana - Monitoring and observability"
        ],
        "domino_specific": [
            "Domino Environments - Custom Docker environment creation",
            "Model APIs - Deploy and monitor production endpoints",
            "Domino Flows - Orchestrate multi-step ML pipelines",
            "CI/CD Integration - GitHub Actions with Domino API",
            "Monitoring - Grafana dashboards for model health",
            "NVIDIA Triton - GPU-accelerated model serving"
        ]
    },
    "Business Manager": {
        "primary_languages": [
            {
                "name": "SQL",
                "version": "N/A",
                "use_cases": "Data queries and basic analysis (for Practitioners)",
                "key_libraries": ["N/A"],
                "learning_resources": [
                    "SQL fundamentals",
                    "Internal data catalog"
                ]
            },
            {
                "name": "Python (Optional)",
                "version": "3.8+",
                "use_cases": "Basic scripting and automation (for Practitioners)",
                "key_libraries": ["pandas", "matplotlib"],
                "learning_resources": [
                    "Python for Business Users",
                    "Data analysis with pandas"
                ]
            }
        ],
        "key_tools": [
            "Domino Apps - Access interactive dashboards and reports",
            "Launchers - Run parameterized analyses with web forms",
            "Jupyter Notebook (Optional) - For Practitioners doing analysis",
            "Web Browser - Primary interface for Lite Users"
        ],
        "domino_specific": [
            "Domino Apps - Published Streamlit, Dash, or Shiny applications",
            "Launchers - Self-service analytics with pre-configured parameters",
            "Project Access - View results and reports from technical teams",
            "Workspaces (Practitioners) - Launch Jupyter for ad-hoc analysis"
        ]
    }
}

# Domino Best Practices by Topic
BEST_PRACTICES = {
    "Project Setup": [
        "Use Git-based projects for version control and collaboration",
        "Follow naming conventions from Domino Standards documentation",
        "Set up proper project permissions based on team roles",
        "Document project purpose and data sources in README"
    ],
    "Environment Management": [
        "Start with Domino Standard Environments (DSE) when possible",
        "Document custom environment changes in Dockerfile",
        "Pin package versions for reproducibility",
        "Test environments with sample workload before using in production"
    ],
    "Data Management": [
        "Use Domino Datasets for shared data across projects",
        "Create dataset snapshots before major changes",
        "Document data lineage and sources",
        "Follow data access policies and security requirements"
    ],
    "Experiment Tracking": [
        "Enable MLflow autologging for supported frameworks",
        "Log all relevant parameters, metrics, and artifacts",
        "Use meaningful experiment and run names",
        "Register models in MLflow Model Registry for deployment"
    ],
    "Model Deployment": [
        "Test model APIs locally before deployment",
        "Set appropriate resource limits for endpoints",
        "Enable monitoring and alerting for production endpoints",
        "Version model APIs and maintain backwards compatibility"
    ],
    "Governance & Compliance": [
        "Create governance bundles for regulated models",
        "Attach all evidence (code, data, results) to bundles",
        "Document model assumptions and limitations",
        "Follow SR 11-7 and internal governance requirements",
        "Maintain audit trail for all model changes"
    ],
    "Collaboration": [
        "Use Git for code collaboration and version control",
        "Document code with clear comments and docstrings",
        "Share results via Apps and Launchers for business users",
        "Follow code review process for production models"
    ],
    "Performance Optimization": [
        "Right-size hardware tiers for workload requirements",
        "Use distributed computing (Spark/Ray) for large datasets",
        "Optimize data loading and preprocessing",
        "Profile code to identify bottlenecks"
    ]
}
