# FSI Domino Onboarding App - Project Summary

## 📦 Deliverables

This project contains a fully functional Streamlit-based onboarding application for FSI teams using Domino Data Lab.

---

## 🏗️ Architecture

### Data Model ([config/onboarding_data.py](config/onboarding_data.py))

Comprehensive configuration covering:

1. **Organizations (3)**
   - Retail Banking
   - Investment Banking
   - Risk Management

2. **Roles (5)**
   - Data Scientist
   - Quant Analyst
   - Model Validator
   - ML Engineer
   - Business Manager

3. **Learning Paths**
   - 3 difficulty levels per role (Beginner, Intermediate, Advanced)
   - 60+ total learning modules across all roles
   - Customized content for each role type

4. **FSI Use Cases**
   - 17 real-world use cases across organizations
   - Credit scoring, fraud detection, algorithmic trading, model validation, etc.
   - Governance requirements clearly marked

5. **Documentation Links**
   - Model Governance: https://bank.sharepoint.com
   - AI Policy: https://bank.sharepoint.com
   - Compliance: https://bank.sharepoint.com
   - Domino Standards: https://bank.confluence.com
   - BU-specific SharePoint sites

6. **Best Practices**
   - 8 categories (Project Setup, Environment Management, etc.)
   - 30+ specific guidelines
   - Aligned with enterprise standards

---

## 🎨 Application Features ([app.py](app.py))

### Page 1: Welcome
- Platform overview
- Onboarding journey introduction
- Governance highlights
- Quick metrics

### Page 2: Role Selection
- Organization selection (3 organizations)
- Role selection based on organization
- Detailed role capabilities display
- Domino role mapping

### Page 3: Learning Path
- Personalized modules based on selected role
- 3 difficulty levels (Beginner, Intermediate, Advanced)
- Module details with duration and topics
- Progress tracking framework (ready for future enhancement)

### Page 4: Resources
- Enterprise-wide documentation links
- Organization-specific SharePoint links
- Quick links to support and training
- Expandable documentation sections

### Page 5: Use Cases
- FSI-specific examples by organization
- Filtered by selected role
- Governance requirements highlighted
- Complexity badges (Beginner/Intermediate/Advanced)

### Page 6: Best Practices
- Categorized guidelines
- Role-specific recommendations
- Links to detailed standards

---

## 🎨 Domino Theming

Custom CSS implementation matching Domino Design System:

- **Primary Color:** #543FDE (Domino Purple) 
- **Background Color:** #FAFAFA (Domino Light)
- **Secondary Color:** #FFFFFF (Domino White)
- **Text color:** #2E2E38 (Primary text)
- **font** sans serif (Inter loaded via CSS)
- **Styled Components:**
  - Cards with hover effects
  - Custom tabs
  - Badges (difficulty levels, module types)
  - Sidebar styling
  - Buttons with animations

---

## 🚀 Deployment Configuration

### [app.sh](app.sh) - Domino App Launcher

- Port configuration (8888)
- Proxy compatibility settings
- WebSocket configuration
- Streamlit server settings
- Automatic dependency installation

### [requirements.txt](requirements.txt)

- Streamlit >= 1.28.0

---

## 📊 Data Mappings

### Organization → Role Mapping

| Organization | Roles |
|-------------|-------|
| Retail Banking | Data Scientist, Business Manager |
| Investment Banking | Data Scientist, Quant Analyst, Business Manager |
| Risk Management | Data Scientist, Model Validator, ML Engineer, Business Manager |

### Role → Domino Role Mapping

| Internal Role | Domino Role | Project Access |
|--------------|-------------|----------------|
| Data Scientist | Practitioner | Project Owner |
| Quant Analyst | Practitioner | Project Owner |
| Model Validator | Practitioner | Project Owner |
| ML Engineer | Practitioner | Project Owner |
| Business Manager | Practitioner / Launcher User / Lite User | Varies |

---

## 🔧 How to Deploy

1. **In Domino:**
   - Click "Publish" → "App"
   - Select environment with Python 3.8+ and Streamlit
   - App will launch automatically using `app.sh`

---

## 📝 Customization Guide

### Adding a New Organization

1. Edit `config/onboarding_data.py`
2. Add entry to `ORGANIZATIONS` dictionary:
   ```python
   "New Org Name": {
       "domino_org": "New Org Name",
       "roles": ["Role1", "Role2"],
       "use_case_url": "https://sharepoint-url.com",
       "description": "Organization description"
   }
   ```
3. Add use cases to `FSI_USE_CASES` dictionary
4. No code changes needed in `app.py`!

### Adding a New Role

1. Add role to organization in `ORGANIZATIONS`
2. Define role in `ROLE_DEFINITIONS`
3. Create learning path in `LEARNING_PATHS`
4. App automatically picks it up!

### Updating Documentation Links

Simply update URLs in `COMMON_DOCS` and organization `use_case_url` fields.

---

## 🎯 Key Benefits

1. **Personalized Onboarding**
   - Content tailored to organization and role
   - Progressive learning paths
   - Relevant use cases only

2. **FSI-Specific**
   - Banking use cases (credit risk, trading, validation)
   - Governance and compliance emphasis
   - SR 11-7 and NIST AI RMF alignment

3. **Maintainable**
   - All content in single config file
   - No code changes needed for content updates
   - Clear separation of data and presentation

4. **Domino-Native**
   - Matches Domino design system
   - Works behind Domino's reverse proxy
   - Ready for Domino App deployment

---

## 🔮 Future Enhancement Roadmap

### Phase 2 - Progress Tracking
- User authentication integration
- Progress persistence (completed modules)
- Personal dashboard
- Certification tracking

### Phase 3 - Interactive Content
- Embedded code examples
- Live Domino workspace integration
- Sample project templates
- Interactive quizzes

### Phase 4 - Admin Features
- Content management UI
- Analytics dashboard (most used modules, completion rates)
- User feedback collection
- A/B testing for content effectiveness

### Phase 5 - Advanced Personalization
- Auto-detect role from Domino API
- Recommended next steps based on usage
- Peer learning (what similar users are doing)
- Integration with HR onboarding systems

---

## 📊 Application Statistics

- **6 Main Pages**
- **3 Organizations**
- **5 Role Types**
- **60+ Learning Modules**
- **17 Use Cases**
- **30+ Best Practices**
- **8 Documentation Categories**
- **Full Domino Theming**

---

## ✅ Ready for Deployment

The application is **production-ready** and can be deployed immediately to Domino as an App. All placeholder URLs should be replaced with actual internal links before deployment.

**Next Steps:**
1. Replace SharePoint/Confluence URLs with real links
2. Review and customize learning modules
3. Add organization-specific use cases
4. Deploy to Domino
5. Share with onboarding teams
