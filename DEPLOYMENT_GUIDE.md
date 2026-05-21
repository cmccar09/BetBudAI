# Lambda Deployment Guide

## ⚠️ IMPORTANT: Read Before Deploying

### BettingPicksAPI Lambda Function

**Source File:** `lambda_api_picks.py`  
**Lambda Handler:** `lambda_function.lambda_handler`  
**Region:** `eu-west-1`

### How to Deploy

**ALWAYS use the deployment script:**

```powershell
.\deploy_api_lambda.ps1
```

**DO NOT manually deploy** - the script handles the required filename conversion.

### Why the Script is Required

The Lambda function is configured with handler `lambda_function.lambda_handler`, which means:
- Lambda looks for a file named `lambda_function.py`
- Our source file is `lambda_api_picks.py` (for clarity)
- The script automatically copies and renames during deployment

### What the Script Does

1. ✅ Validates `lambda_api_picks.py` exists
2. ✅ Copies to `lambda_function.py` (temp file)
3. ✅ Creates deployment package with correct filename
4. ✅ Uploads to AWS Lambda in eu-west-1
5. ✅ Tests the API endpoint
6. ✅ Cleans up temp files

### Manual Deployment (Emergency Only)

If the script fails, you can deploy manually:

```powershell
# Copy source file
Copy-Item lambda_api_picks.py lambda_function.py

# Create package
Compress-Archive -Path lambda_function.py -DestinationPath lambda_deployment.zip -Force

# Deploy
aws lambda update-function-code `
    --function-name BettingPicksAPI `
    --zip-file fileb://lambda_deployment.zip `
    --region eu-west-1

# Clean up
Remove-Item lambda_function.py
```

### Troubleshooting

**Error: "No module named 'lambda_function'"**
- ✅ Solution: Use `deploy_api_lambda.ps1` (it handles the rename)
- ❌ Cause: File was uploaded as `lambda_api_picks.py` instead of `lambda_function.py`

**Error: HTTP 500**
- Check logs: `aws logs tail /aws/lambda/BettingPicksAPI --region eu-west-1 --since 5m`
- Verify deployment time matches recent upload

### API Endpoints

After deployment, test these endpoints:

- `GET https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/today`
- `GET https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/results/today`
- `GET https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/results/yesterday`

### Version Control

**Before deploying:**
1. Commit changes to `lambda_api_picks.py`
2. Run the deployment script
3. Test the live API

**Files to commit:**
- ✅ `lambda_api_picks.py` (source file)
- ❌ `lambda_function.py` (temp file - auto-generated)
- ❌ `lambda_deployment.zip` (build artifact - auto-generated)

### Recent Fixes

**Feb 14, 2026 - Case-Insensitive Outcome Handling**
- Fixed: Win count showing 0 despite winning bets
- Cause: Database had mixed case (`WON`, `win`, `won`)
- Solution: Lambda now handles all case variations
- Commits: `50a192b`, `69ba4b4`, `cc9f956`
2. Create new repository (e.g., "ai-betting-system")
3. Don't initialize with README (you already have one)

**Option B: Via GitHub CLI**
```powershell
gh repo create ai-betting-system --private --source=. --remote=origin --push
```

### 4. Push to GitHub

```powershell
git remote add origin https://github.com/YOUR_USERNAME/ai-betting-system.git
git branch -M main
git push -u origin main
```

## AWS Amplify Deployment

### Option 1: Deploy via AWS Console (Recommended)

1. **Go to AWS Amplify Console**
   - https://console.aws.amazon.com/amplify/

2. **Connect Repository**
   - Click "Host web app"
   - Select "GitHub" as your Git provider
   - Authorize AWS Amplify to access your GitHub
   - Select your repository and branch (main)

3. **Configure Build Settings**
   - Amplify will auto-detect `amplify.yml`
   - Build settings are already configured for React frontend
   - Click "Save and Deploy"

4. **Set Environment Variables** (in Amplify Console)
   ```
   ANTHROPIC_API_KEY = your-key-here
   ```

5. **Deploy**
   - Amplify will build and deploy automatically
   - You'll get a URL like: `https://main.d1234567890abc.amplifyapp.com`

### Option 2: Deploy via Amplify CLI

```powershell
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Configure Amplify
amplify configure

# Initialize Amplify in project
cd C:\Users\charl\OneDrive\futuregenAI\Betting\frontend
amplify init

# Add hosting
amplify add hosting

# Publish
amplify publish
```

## Important Notes

### ⚠️ Backend Services

The Amplify deployment only hosts the **React frontend**. You still need:

1. **DynamoDB Table** - Already exists (SureBetBets)
2. **API Server** - Options:
   - **Option A:** Keep running locally (`api_server.py`)
   - **Option B:** Deploy as Lambda + API Gateway
   - **Option C:** Deploy to EC2/ECS

3. **Scheduled Tasks** - Options:
   - **Option A:** Keep Windows Task Scheduler locally
   - **Option B:** Use AWS EventBridge + Lambda

### Frontend Configuration

Update `frontend/src/App.js` API endpoint for production:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
```

Then set in Amplify Console:
```
REACT_APP_API_URL = https://your-api-gateway-url.com/api
```

## Recommended Production Architecture

```
┌─────────────────┐
│   AWS Amplify   │ ← React Frontend (Static Hosting)
│   (Frontend)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Gateway +  │ ← API Server (Lambda)
│     Lambda      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    DynamoDB     │ ← Data Storage
│  (SureBetBets)  │
└─────────────────┘
         ▲
         │
┌─────────────────┐
│  EventBridge    │ ← Scheduled Workflow
│   + Lambda      │   (Every 2 hours)
└─────────────────┘
```

## Deploy API as Lambda (Optional)

```powershell
# Package API server
cd C:\Users\charl\OneDrive\futuregenAI\Betting
pip install -t lambda-api-package/ flask flask-cors boto3
cp api_server.py lambda-api-package/
cd lambda-api-package
zip -r ../api-lambda.zip .

# Deploy to AWS
aws lambda create-function `
  --function-name BettingAPI `
  --runtime python3.9 `
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role `
  --handler api_server.app `
  --zip-file fileb://../api-lambda.zip
```

## Cost Estimate

- **Amplify Hosting**: $0.01/GB served + $0.15/build minute
- **DynamoDB**: On-demand pricing (~$0.25/million requests)
- **Lambda**: Free tier (1M requests/month)
- **API Gateway**: $3.50/million requests

**Estimated Monthly Cost**: $5-20 depending on usage

## Git Commands Reference

```powershell
# View status
git status

# View commit history
git log --oneline

# Create new branch
git checkout -b feature-name

# Push to GitHub
git push origin main

# Pull latest changes
git pull origin main
```

## Support

Repository: https://github.com/YOUR_USERNAME/ai-betting-system
Documentation: See `README.md` in repository
