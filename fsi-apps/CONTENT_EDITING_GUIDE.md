# Content Editing Guide - FSI Domino Onboarding App

This guide is for non-technical content editors who need to update the onboarding content without modifying the application code.

## 📁 File to Edit

**Location:** `/mnt/config/onboarding_data.py`

This single file contains ALL the content displayed in the app. You don't need to touch `app.py` (the main application) - all your changes happen here.

---

## 🔧 Common Editing Tasks

### 1. Updating Documentation URLs

**Find this section:**
```python
COMMON_DOCS = {
    "Model Governance": {
        "url": "https://bank.sharepoint.com",
        "description": "Enterprise model governance framework and policies",
        "topics": ["Model Risk Management", "SR 11-7 Compliance", "Governance Bundles"]
    },
    ...
}
```

**Change the URL:**
```python
"url": "https://your-actual-sharepoint.com/path/to/governance-docs",
```

**Repeat for:**
- AI Policy
- Compliance Requirements
- Domino Standards

### 2. Updating Organization SharePoint Links

**Find:**
```python
ORGANIZATIONS = {
    "Retail Banking": {
        "domino_org": "Retail Banking",
        "roles": ["Data Scientist", "Business Manager"],
        "use_case_url": "https://bank.retail.sharepoint.com",  # ← Change this
        "description": "Consumer banking, deposits, loans, and retail financial products"
    },
    ...
}
```

**Update the `use_case_url` for each organization.**

---

### 3. Adding a New Learning Module

**Find the role's learning path:**
```python
LEARNING_PATHS = {
    "Data Scientist": {
        "beginner": [
            # Add new module here
        ],
        ...
    }
}
```

**Add a new module (copy and paste this template):**
```python
{
    "title": "Your Module Title",
    "description": "What this module covers",
    "type": "lab",  # or "tutorial"
    "duration": "45 min",  # estimated time
    "topics": ["Topic1", "Topic2", "Topic3"]
},
```

**Important:** Don't forget the comma after the closing `}` if there are more modules after it!

---

### 4. Adding a New Use Case

**Find your organization in FSI_USE_CASES:**
```python
FSI_USE_CASES = {
    "Retail Banking": [
        # Add new use case here
    ],
    ...
}
```

**Add using this template:**
```python
{
    "title": "Use Case Name",
    "description": "Brief description of what this does",
    "relevant_roles": ["Data Scientist", "ML Engineer"],  # Which roles should see this
    "complexity": "Intermediate",  # Beginner, Intermediate, or Advanced
    "governance_required": True  # True if needs governance, False if not
},
```

---

### 5. Adding a New Organization

**Step 1: Add to ORGANIZATIONS**
```python
ORGANIZATIONS = {
    # ... existing orgs ...
    "Wealth Management": {  # ← New organization
        "domino_org": "Wealth Management",
        "roles": ["Data Scientist", "Business Manager"],  # Available roles
        "use_case_url": "https://bank.wealth.sharepoint.com",
        "description": "Wealth and asset management services"
    }
}
```

**Step 2: Add use cases for this org**
```python
FSI_USE_CASES = {
    # ... existing orgs ...
    "Wealth Management": [  # ← New organization use cases
        {
            "title": "Client Portfolio Analysis",
            "description": "Automated portfolio risk analysis and recommendations",
            "relevant_roles": ["Data Scientist"],
            "complexity": "Intermediate",
            "governance_required": False
        }
    ]
}
```

**Done!** The app will automatically show this new organization.

---

### 6. Modifying Role Descriptions

**Find the role:**
```python
ROLE_DEFINITIONS = {
    "Data Scientist": {
        "domino_role": "Practitioner",
        "project_access": "Project Owner",
        "description": "Develops models, runs experiments, and creates data products",  # ← Edit this
        "key_capabilities": [
            "Create and manage projects",  # ← Edit these
            "Launch workspaces (Jupyter, VS Code, RStudio)",
            # Add more capabilities
        ],
        "typical_tools": ["Python", "R", "Jupyter", "Git", "MLflow", "Spark"]  # ← Edit these
    }
}
```

**Just change the text in quotes!**

---

### 7. Updating Best Practices

**Find the category:**
```python
BEST_PRACTICES = {
    "Project Setup": [
        "Use Git-based projects for version control and collaboration",  # ← Edit these
        "Follow naming conventions from Domino Standards documentation",
        # Add more practices
    ],
    ...
}
```

**Add a new category:**
```python
BEST_PRACTICES = {
    # ... existing categories ...
    "Security": [  # ← New category
        "Never commit credentials to Git",
        "Use Domino Secrets for API keys",
        "Follow least-privilege access principles"
    ]
}
```

---

## ⚠️ Important Python Syntax Rules

### 1. Strings Must Be Quoted
```python
# ✅ Correct
"This is a string"

# ❌ Wrong
This is a string  # Will cause an error!
```

### 2. Commas Between Items
```python
# ✅ Correct
["Item 1", "Item 2", "Item 3"]

# ❌ Wrong
["Item 1" "Item 2" "Item 3"]  # Missing commas!
```

### 3. Don't Forget Closing Brackets
Every opening bracket needs a closing one:
- `{` needs `}`
- `[` needs `]`
- `(` needs `)`

```python
# ✅ Correct
{
    "title": "Module",
    "topics": ["Topic1", "Topic2"]
}

# ❌ Wrong - missing closing bracket
{
    "title": "Module",
    "topics": ["Topic1", "Topic2"
```

### 4. Indentation Matters in Python
```python
# ✅ Correct
ORGANIZATIONS = {
    "Retail Banking": {
        "roles": ["Data Scientist"],
        "description": "Banking services"
    }
}

# ❌ Wrong - inconsistent indentation
ORGANIZATIONS = {
"Retail Banking": {
    "roles": ["Data Scientist"],
        "description": "Banking services"
    }
}
```

**Tip:** Use 4 spaces for each indentation level (most editors do this automatically with Tab key).

---

## 🧪 Testing Your Changes

### Option 1: Test Locally
If you have Python installed:
```bash
cd /mnt
pip install streamlit
streamlit run app.py
```

### Option 2: Test in Domino
1. Save your changes to `config/onboarding_data.py`
2. Re-publish the Domino App
3. Check if it loads without errors

### Common Errors

**Error:** `SyntaxError: invalid syntax`
- **Cause:** Missing quote, comma, or bracket
- **Fix:** Check the line number in the error and look for missing punctuation

**Error:** `KeyError: 'SomeRole'`
- **Cause:** You referenced a role that doesn't exist in ROLE_DEFINITIONS
- **Fix:** Make sure role names match exactly (case-sensitive!)

**Error:** `IndentationError: unexpected indent`
- **Cause:** Inconsistent spacing
- **Fix:** Make sure you use 4 spaces for each indentation level

---

## 📋 Content Update Checklist

Before publishing changes:

- [ ] All SharePoint/Confluence URLs updated
- [ ] All organization use case links updated
- [ ] New learning modules added for all relevant roles
- [ ] Use cases marked correctly for governance requirements
- [ ] Best practices reviewed and updated
- [ ] No placeholder URLs (like `https://bank.sharepoint.com`)
- [ ] Tested the app locally or in Domino
- [ ] No syntax errors

---

## 🆘 Getting Help

If you run into issues:

1. **Check the error message** - it usually tells you the line number
2. **Compare with existing entries** - copy the structure of something that works
3. **Ask for help** - Share the error message and line number with technical team

---

## 💡 Tips for Content Editors

### Keep It Concise
- Module descriptions: 1-2 sentences
- Use case descriptions: 1 sentence
- Topics: 2-5 keywords

### Be Consistent
- Use the same terminology throughout
- Match role names exactly (case-sensitive)
- Use consistent duration formats ("30 min", "1 hour")

### Test Incrementally
- Make small changes
- Test after each change
- Don't change multiple sections at once

### Use Comments
Add notes to yourself (start line with `#`):
```python
# TODO: Update this URL after SharePoint migration
"url": "https://temp-url.com",

# REMINDER: Get governance URL from compliance team
```

---

## 🎯 Quick Reference

| Task | Section | Line Range (approx) |
|------|---------|-------------------|
| Update doc URLs | COMMON_DOCS | ~50-90 |
| Update org URLs | ORGANIZATIONS | ~10-50 |
| Add learning modules | LEARNING_PATHS | ~100-400 |
| Add use cases | FSI_USE_CASES | ~450-600 |
| Update best practices | BEST_PRACTICES | ~600-658 |
| Modify role descriptions | ROLE_DEFINITIONS | ~50-100 |

---

**Remember:** You can't break the app by editing content! Worst case, you'll get a syntax error and can revert your changes. Always keep a backup of the working version before making major changes.
