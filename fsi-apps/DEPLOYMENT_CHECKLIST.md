# Deployment Checklist - FSI Domino Onboarding App

Use this checklist to ensure successful deployment of the onboarding application to Domino.

---

## Pre-Deployment Tasks

### Content Validation

- [ ] **Update all SharePoint URLs**
  - [ ] Model Governance URL in `config/onboarding_data.py` (line ~52)
  - [ ] AI Policy URL in `config/onboarding_data.py` (line ~57)
  - [ ] Compliance Requirements URL in `config/onboarding_data.py` (line ~62)
  - [ ] Domino Standards URL in `config/onboarding_data.py` (line ~67)

- [ ] **Update Organization-Specific URLs**
  - [ ] Retail Banking SharePoint (line ~17)
  - [ ] Investment Banking SharePoint (line ~23)
  - [ ] Risk Management SharePoint (line ~29)

- [ ] **Review Learning Modules**
  - [ ] All modules have accurate durations
  - [ ] Module descriptions are clear and concise
  - [ ] Topics are relevant to each role
  - [ ] No placeholder or "TODO" content

- [ ] **Review Use Cases**
  - [ ] All use cases are approved for sharing
  - [ ] Governance requirements are correctly marked
  - [ ] Complexity levels are appropriate
  - [ ] Relevant roles are correctly assigned

- [ ] **Review Best Practices**
  - [ ] All practices align with current standards
  - [ ] No outdated information
  - [ ] Links to standards documentation are correct

### Technical Validation

- [ ] **Test Locally (Optional but Recommended)**
  ```bash
  pip install -r requirements.txt
  streamlit run app.py
  ```
  - [ ] App launches without errors
  - [ ] All pages load correctly
  - [ ] Navigation works smoothly
  - [ ] Content displays properly

- [ ] **Check File Permissions**
  ```bash
  chmod +x app.sh

  ```

- [ ] **Verify File Structure**
  ```
  /mnt/
  ├── app.py
  ├── app.sh
  ├── requirements.txt
  └── config/
      └── onboarding_data.py
  ```

---

## Domino Deployment

### Step 1: Environment Setup

- [ ] **Verify Domino Environment has:**
  - [ ] Python 3.8 or higher
  - [ ] Streamlit 1.28.0+ (or will be installed via requirements.txt)
  - [ ] Internet access for pip install (if not pre-installed)

**Recommended Environment:** Domino Standard Environment (DSE) for Python

### Step 2: Upload Files to Domino Project

- [ ] **Create or select Domino Project**
  - Project Name: `FSI-Onboarding-App` (or your preferred name)
  - Organization: (Select appropriate org)

- [ ] **Upload all files:**
  - [ ] `app.py`
  - [ ] `app.sh`
  - [ ] `requirements.txt`
  - [ ] `config/onboarding_data.py` (create `config/` directory first)

- [ ] **Optional: Upload documentation**
  - [ ] `FSI_ONBOARDING_README.md`
  - [ ] `PROJECT_SUMMARY.md`
  - [ ] `CONTENT_EDITING_GUIDE.md`
  - [ ] `DEPLOYMENT_CHECKLIST.md` (this file)

### Step 3: Publish as Domino App

- [ ] **Navigate to project in Domino UI**

- [ ] **Click "Publish" → "App"**

- [ ] **Configure App Settings:**
  - [ ] **App Name:** "FSI Onboarding" (or your preferred name)
  - [ ] **Environment:** Select environment with Python 3.8+
  - [ ] **Hardware Tier:** Small tier is sufficient (app is lightweight)
  - [ ] **Permissions:** Set appropriate access (usually all org members)

- [ ] **Click "Publish"**

- [ ] **Wait for app to start** (usually 1-3 minutes)

### Step 4: Verify Deployment

- [ ] **Access the app URL**
  - Domino will provide a URL like: `https://your-domino.com/workspace/...`

- [ ] **Test all pages:**
  - [ ] Welcome page loads
  - [ ] Can select organization
  - [ ] Can select role
  - [ ] Learning paths display correctly
  - [ ] Resources page shows all links
  - [ ] Use cases filter properly
  - [ ] Best practices display

- [ ] **Test navigation:**
  - [ ] Sidebar navigation works
  - [ ] Page transitions are smooth
  - [ ] Session state persists (org/role selection)

- [ ] **Test functionality:**
  - [ ] Role selection updates capabilities display
  - [ ] Learning modules expand/collapse
  - [ ] Use case filtering works
  - [ ] All external links work (SharePoint, Confluence)

---

## Post-Deployment

### Communication

- [ ] **Share app URL with:**
  - [ ] Onboarding team
  - [ ] HR/People team
  - [ ] Platform administrators
  - [ ] New user cohorts

- [ ] **Create announcement:**
  - [ ] Email template or Slack message
  - [ ] Include app URL
  - [ ] Brief description of purpose
  - [ ] Who should use it

### Monitoring

- [ ] **Monitor app health:**
  - [ ] Check Domino app logs for errors
  - [ ] Verify app stays running
  - [ ] Monitor resource usage

- [ ] **Collect feedback:**
  - [ ] Set up feedback mechanism (email, Slack channel, form)
  - [ ] Track common questions
  - [ ] Note requested features

### Maintenance Plan

- [ ] **Assign content owner:**
  - Name: _________________
  - Responsibility: Keep content updated

- [ ] **Schedule regular reviews:**
  - [ ] Quarterly content review
  - [ ] Update learning modules as platform evolves
  - [ ] Add new use cases as they emerge
  - [ ] Update documentation links

- [ ] **Plan for enhancements:**
  - [ ] Progress tracking (Phase 2)
  - [ ] Interactive labs (Phase 3)
  - [ ] Admin interface (Phase 4)

---

## Troubleshooting

### App Won't Start

**Symptom:** App shows error on launch

**Solutions:**
1. Check Domino app logs for error messages
2. Verify `app.sh` has execute permissions
3. Ensure environment has Python 3.8+
4. Check `requirements.txt` installs successfully
5. Verify no syntax errors in `config/onboarding_data.py`

### Blank Page or 404 Error

**Symptom:** App URL shows blank page

**Solutions:**
1. Verify app is running in Domino
2. Check if proxy settings are correct in `app.sh`
3. Try stopping and restarting the app
4. Clear browser cache and reload

### Content Not Displaying

**Symptom:** Pages load but content is missing

**Solutions:**
1. Check `config/onboarding_data.py` for syntax errors
2. Verify all required data structures are present
3. Check browser console for JavaScript errors
4. Verify Streamlit version is >= 1.28.0

### Navigation Issues

**Symptom:** Clicking navigation doesn't change pages

**Solutions:**
1. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear Streamlit cache (Settings → Clear Cache in app)
3. Restart the Domino app

### External Links Not Working

**Symptom:** Clicking documentation links shows errors

**Solutions:**
1. Verify URLs are accessible from Domino environment
2. Check if SSO/authentication is required
3. Ensure URLs are correctly formatted (https://)
4. Test links from Domino workspace to verify network access

---

## Rollback Plan

If deployment fails or major issues occur:

### Quick Rollback Steps

1. **Stop the Domino App**
   - Go to app in Domino UI
   - Click "Stop"

2. **Revert to previous version** (if applicable)
   - Restore previous version of files from Git
   - Or re-upload known good version

3. **Identify the issue**
   - Check Domino logs
   - Review recent changes
   - Test locally if possible

4. **Fix and redeploy**
   - Make necessary corrections
   - Test locally first
   - Re-publish app

---

## Success Criteria

App is successfully deployed when:

- ✅ App is accessible via Domino URL
- ✅ All 6 pages load without errors
- ✅ Organization and role selection works
- ✅ Content displays correctly for all roles
- ✅ External documentation links work
- ✅ Navigation is smooth and intuitive
- ✅ No errors in Domino logs
- ✅ First users can successfully complete onboarding flow

---

## Contact Information

**Technical Support:**
- Domino Platform Team: _________________
- Email: _________________
- Slack: _________________

**Content Support:**
- Training & Enablement Team: _________________
- Email: _________________

**Escalation:**
- Manager: _________________
- Email: _________________

---

## Sign-Off

**Deployed By:** _________________ **Date:** _________

**Reviewed By:** _________________ **Date:** _________

**Approved By:** _________________ **Date:** _________

---

**Deployment Status:** ☐ Not Started  ☐ In Progress  ☐ Completed  ☐ Verified

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
