
---

## 🚀 Step-by-Step: Deploy as Domino App

### Step 1: Verify Files Are Ready

Make sure these files exist in your project:
- ✅ `app.py` (main application)
- ✅ `app.sh` (deployment script - already configured correctly)
- ✅ `requirements.txt` (dependencies)
- ✅ `config/onboarding_data.py` (data)

### Step 2: Publish the App

1. **In Domino UI**, go to your project: `<domino-user>/<domino-project>`

2. **Click "Publish"** in the top menu

3. **Select "App"**

4. **Configure the app:**
   - **Name:** "FSI Onboarding App"
   - **Environment:** Select a Python 3.8+ environment (e.g., "Domino Standard Environment Py3.9")
   - **Hardware Tier:** Small (this app is lightweight)
   - **File:** Leave blank (app.sh will run automatically)

5. **Click "Publish"**

6. **Wait 2-3 minutes** for the app to start

7. **Click the app URL** when it's ready

### Step 3: Access Your App

The app will be available at:
```
https://<domino-host>/workspace/<app-id>
```