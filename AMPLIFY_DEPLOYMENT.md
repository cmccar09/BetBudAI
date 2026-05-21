# BetBudAI Amplify Deployment Guide

## Current Production Setup

**Amplify App ID**: `dhkrb1ol4d58y`  
**App Name**: SureBet-Manual  
**Platform**: WEB (Manual Deployment)  
**Deployment Date**: May 21, 2026  
**Build Version**: May 11, 2026 (frontend_build_flat.zip)

### URLs
- **Production**: https://www.betbudai.com/ (once DNS/SSL complete)
- **Amplify URL**: https://main.dhkrb1ol4d58y.amplifyapp.com/
- **CloudFront**: d2m6952efl50lp.cloudfront.net

## DNS Configuration (Wix)

```
www.betbudai.com → d2m6952efl50lp.cloudfront.net (CNAME)
_168309a52167b6ccc91acd0c10813a66.betbudai.com → _913eb28de112881d3fb4910b4ea072c3.jkddzztszm.acm-validations.aws (CNAME for SSL cert)
```

## Deployment Files

**Current Production Build**: `betbudai-production.zip` (400KB)
- This is the currently deployed and working version
- Built from frontend/build directory on May 11, 2026
- Uses forward slashes (not backslashes) for proper S3/CloudFront serving

## How to Deploy Updates

### Prerequisites
- AWS CLI configured
- Access to Amplify app `dhkrb1ol4d58y`

### Deployment Steps

1. **Build the React app**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Create deployment zip** (IMPORTANT: Must use forward slashes):
   ```bash
   # On Linux/Mac:
   cd build
   zip -r ../../betbudai-deploy.zip .
   
   # On Windows (use WSL or Git Bash):
   cd build
   tar -czf ../../betbudai-deploy.tar.gz *
   # Then convert to zip with forward slashes
   ```

3. **Create Amplify deployment**:
   ```bash
   aws amplify create-deployment --app-id dhkrb1ol4d58y --branch-name main --region eu-west-1
   ```
   This returns a `jobId` and `zipUploadUrl`

4. **Upload the zip**:
   ```bash
   curl -X PUT "<zipUploadUrl>" --data-binary "@betbudai-deploy.zip" -H "Content-Type: application/zip"
   ```

5. **Start deployment**:
   ```bash
   aws amplify start-deployment --app-id dhkrb1ol4d58y --branch-name main --job-id <jobId> --region eu-west-1
   ```

6. **Check status**:
   ```bash
   aws amplify get-job --app-id dhkrb1ol4d58y --branch-name main --job-id <jobId> --region eu-west-1 --query 'job.summary.status'
   ```

## Known Issues

### Windows PowerShell Zip Problem
PowerShell's `Compress-Archive` creates zips with backslashes (`static\css\file.css`) instead of forward slashes (`static/css/file.css`). This causes 404 errors when CloudFront tries to serve the files.

**Solution**: Use WSL, Git Bash, or Linux to create the deployment zip with proper forward slashes.

### SSL Certificate Provisioning
When adding/changing custom domains, AWS Certificate Manager takes 20-30 minutes to provision SSL certificates. During this time, the site will show SSL errors.

## Cleanup Notes (May 21, 2026)

- Deleted old Git-based Amplify app (d2hmpykfsdweob)
- Removed all old deployment zip files
- Kept only backend Lambda deployment zips:
  - _analysis_lambda.zip
  - _bpapi_lambda.zip
  - backend-core-layer.zip
  - betbudai-picks-api.zip
  - enhanced_lambda.zip
  - lambda_*.zip files
  - python-dependencies-layer.zip
  - sl-results-handler.zip

## Current Status

✅ React app deployed and working at https://main.dhkrb1ol4d58y.amplifyapp.com/  
⏳ SSL certificate provisioning for www.betbudai.com (20-30 min wait)  
✅ DNS configured correctly in Wix  
✅ Manual deployment working with May 11 build  

## Future Improvements

1. Set up proper Git-based deployment with corrected amplify.yml
2. Automate deployment with GitHub Actions
3. Configure staging environment
4. Set up CloudFront cache invalidation on deploy
