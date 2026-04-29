# FSI Domino Onboarding Application

A personalized onboarding application for Financial Services Institution teams using Domino Data Lab. This Streamlit-based app provides role-specific learning paths, use cases, and resources tailored to different organizations and job functions.

## 🎯 Purpose

This application helps new Domino users:
- Understand their role-specific capabilities on the platform
- Access curated learning paths based on their organization and role
- Discover relevant use cases from their business unit
- Follow best practices for governance and compliance
- Find essential documentation and resources

## 🏦 Supported Organizations

- **Retail Banking** - Consumer banking, deposits, loans, and retail products
- **Investment Banking** - Capital markets, trading, M&A, and institutional services
- **Risk Management** - Credit risk, market risk, operational risk, and model validation

## 👥 Supported Roles

- **Data Scientist** - Model development and data product creation
- **Quant Analyst** - Quantitative analysis for trading and risk modeling
- **Model Validator** - Independent model validation and governance
- **ML Engineer** - Model productionization and ML infrastructure
- **Business Manager** - Business stakeholders consuming data products

## 📋 Features

### 1. Welcome Page
- Overview of the onboarding journey
- Quick statistics and platform overview
- Governance and compliance highlights

### 2. Role Selection
- Organization and role selection
- Detailed role descriptions and capabilities
- Domino role mapping (Practitioner, Launcher User, Lite User)

### 3. Personalized Learning Path
- Beginner, Intermediate, and Advanced modules
- Role-specific labs and tutorials
- Estimated duration and topic coverage
- Progressive learning tracks

### 4. Documentation Resources
- Enterprise-wide documentation (Governance, AI Policy, Compliance)
- Organization-specific SharePoint resources
- Internal Domino standards and best practices
- Quick links to support and training

### 5. FSI Use Cases
- Real-world examples from each organization
- Filtered by role relevance
- Governance requirements highlighted
- Complexity indicators (Beginner/Intermediate/Advanced)

### 6. Best Practices
- Categorized best practices (Project Setup, Environment Management, etc.)
- Role-specific recommendations
- Alignment with enterprise standards

## 🚀 Deployment on Domino

### Prerequisites
- Domino Data Lab platform access
- Project with Python environment (Python 3.8+)

### Deployment Steps

1. **Create a new Domino Project** or use an existing one

2. **Upload the application files:**
   ```
   /mnt/
   ├── app.py                      # Main Streamlit application
   ├── app.sh                      # Domino app deployment script
   ├── requirements.txt            # Python dependencies
   ├── config/
   │   └── onboarding_data.py     # Configuration and data model
   └── FSI_ONBOARDING_README.md   # This file
   ```

3. **Publish as a Domino App:**
   - Click "Publish" in your Domino project
   - Select "App"
   - Choose the appropriate environment (must have Streamlit installed)
   - The `app.sh` script will automatically run

4. **Access the app:**
   - Once published, access via the provided Domino app URL
   - Share with your team members

## 🛠️ Configuration

### Customizing Organization Data

Edit `config/onboarding_data.py` to customize:

- **Organizations:** Add/modify organizations in `ORGANIZATIONS` dictionary
- **Roles:** Update role definitions in `ROLE_DEFINITIONS`
- **Learning Paths:** Customize modules in `LEARNING_PATHS`
- **Use Cases:** Add organization-specific use cases in `FSI_USE_CASES`
- **Documentation Links:** Update URLs in `COMMON_DOCS`
- **Best Practices:** Modify practices in `BEST_PRACTICES`

### Updating Documentation Links

Replace the placeholder SharePoint and Confluence URLs with your actual internal links:

```python
COMMON_DOCS = {
    "Model Governance": {
        "url": "https://your-actual-sharepoint-url.com",
        # ...
    },
    # ...
}

ORGANIZATIONS = {
    "Retail Banking": {
        "use_case_url": "https://your-retail-banking-sharepoint.com",
        # ...
    },
    # ...
}
```

## 🎨 Domino Theming

The app uses custom CSS to match Domino's design system:
- **Primary Color:** `#FF6B35` (Domino Orange)
- **Secondary Color:** `#004E89` (Domino Blue)
- **Accent Color:** `#1A659E`

Theming is applied via embedded CSS in `app.py`.

## 📊 Data Model

### Organization Structure
```python
{
    "Organization Name": {
        "domino_org": "Matching Domino Org Name",
        "roles": ["Role1", "Role2"],
        "use_case_url": "SharePoint URL",
        "description": "Organization description"
    }
}
```

### Role Mapping
```python
{
    "Role Name": {
        "domino_role": "Practitioner | Launcher User | Lite User",
        "project_access": "Project Owner | Contributor | ...",
        "description": "Role description",
        "key_capabilities": ["capability1", "capability2"],
        "typical_tools": ["tool1", "tool2"]
    }
}
```

## 🔧 Technical Details

### Dependencies
- **Streamlit** >= 1.28.0 - Web application framework

### Domino App Configuration
- **Port:** 8888 (Domino standard)
- **Proxy Compatibility:** Configured for Domino's reverse proxy
- **WebSocket:** Enabled with compression

### File Structure
```
/mnt/
├── app.py                   # Main Streamlit application (800+ lines)
├── app.sh                   # Deployment script
├── requirements.txt         # Python packages
├── config/
│   └── onboarding_data.py  # Data model and configuration (1000+ lines)
└── FSI_ONBOARDING_README.md # Documentation
```

## 🔒 Governance & Compliance

This app highlights governance requirements throughout the onboarding journey:
- **SR 11-7** compliance for model risk management
- **NIST AI RMF** framework alignment
- Enterprise AI policy adherence
- Model documentation and audit trail requirements

## 📝 Future Enhancements

Potential improvements for future versions:

1. **Progress Tracking**
   - User progress persistence (track completed modules)
   - Personalized dashboards
   - Certification tracking

2. **Interactive Labs**
   - Embedded code examples
   - Integration with Domino workspaces
   - Sample project templates

3. **Admin Interface**
   - Content management UI
   - Analytics dashboard
   - User onboarding metrics

4. **Authentication Integration**
   - SSO integration
   - Role auto-detection from Domino
   - Personalized content based on Domino user

5. **Search Functionality**
   - Full-text search across resources
   - Smart recommendations
   - Related content suggestions

## 🆘 Support

For questions or issues:
- **Domino Support:** Submit ticket via internal support portal
- **App Customization:** Contact Domino Platform Team
- **Content Updates:** Contact Training & Enablement Team

## 📄 License

Internal use only - Proprietary to [Your Financial Institution]

---

**Built with:** Streamlit + Domino Data Lab
**Version:** 1.0.0
