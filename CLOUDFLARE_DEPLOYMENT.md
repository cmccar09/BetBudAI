# BetBudAI Cloudflare Pages Deployment Guide

## Current Production Setup (May 21, 2026)

**Platform**: Cloudflare Pages  
**Project Name**: betbudai  
**Deployment Date**: May 21, 2026  
**Build Version**: May 11, 2026 (betbudai-production.zip)

### URLs
- **Production**: https://www.betbudai.com/ ✅ LIVE
- **Cloudflare URL**: https://betbudai.pages.dev/
- **Status**: Active with SSL certificate

## DNS Configuration (Wix)

```
CNAME Records:
www.betbudai.com → betbudai.pages.dev (TTL: 30 minutes)
en.betbudai.com → pointing.wixdns.net (TTL: 1 hour)

SSL Verification (for reference):
_168309a52167b6ccc91acd0c10813a66.betbudai.com → _913eb28de112881d3fb4910b4ea072c3.jkddzztszm.acm-validations.aws
```

**Nameservers**: ns10.wixdns.net, ns11.wixdns.net (cannot be changed)

## Deployment Files

**Current Production Build**: `betbudai-production.zip` (409KB)
- Built from: frontend/build directory (May 11, 2026)
- Contents: index.html, static/, favicon.ico, etc.

**Extracted for Cloudflare**: `cloudflare-deploy/`
- This is the unzipped version used for Cloudflare Pages uploads

## How to Deploy Updates

### Method 1: Web Interface (Recommended for Quick Updates)

1. **Build the React app**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Go to Cloudflare Pages**:
   - Login: https://dash.cloudflare.com/
   - Navigate: Compute → Workers & Pages → betbudai
   - Click "Create deployment" (under Deployments tab)

3. **Upload new files**:
   - Upload all files from `frontend/build/` directory
   - Cloudflare will automatically deploy and activate

4. **Verify**:
   - Check https://betbudai.pages.dev first
   - Then verify https://www.betbudai.com

### Method 2: Wrangler CLI (For Automation)

1. **Install Wrangler**:
   ```bash
   npm install -g wrangler
   ```

2. **Login to Cloudflare**:
   ```bash
   wrangler login
   ```

3. **Deploy from build directory**:
   ```bash
   cd frontend/build
   wrangler pages deploy . --project-name=betbudai
   ```

### Method 3: Direct Git Integration (Future)

Cloudflare Pages supports connecting to GitHub for automatic deployments on push.

## Cloudflare Features

- ✅ **Free Plan**: Unlimited bandwidth and requests
- ✅ **Global CDN**: 300+ edge locations worldwide
- ✅ **Automatic SSL**: Free SSL certificates (auto-renews)
- ✅ **Instant Cache Purge**: Changes propagate in ~30 seconds
- ✅ **No Nameserver Change**: Works with CNAME records only
- ✅ **Analytics**: Built-in web analytics
- ✅ **Preview URLs**: Every deployment gets a unique preview URL

## Troubleshooting

### Site Not Updating After Deploy
- Cloudflare cache: Usually clears automatically in 30 seconds
- Browser cache: Hard refresh (Ctrl+F5) or incognito mode
- Check deployment status in Cloudflare dashboard

### Custom Domain Shows Error
- Verify DNS in Wix: www CNAME must point to betbudai.pages.dev
- DNS propagation: Can take 5-10 minutes after changes
- Check status in Cloudflare: Custom domains tab shows "Active"

### Build Issues
- Ensure `npm run build` completes without errors
- Check frontend/build/ directory exists and has files
- Verify index.html is in the root of build directory

## Migration History

### Why We Switched from AWS Amplify to Cloudflare

**Previous Setup**: AWS Amplify Hosting in eu-west-1
- App IDs tried: dhkrb1ol4d58y, d2e2hrb2ei1cao, and many others
- Issue: Persistent CloudFront CNAME alias conflicts
- Error: "One or more aliases specified for the distribution includes an incorrectly configured DNS record that points to another CloudFront distribution"
- Attempts: Deleted multiple apps, cleared Route53 records, retried 10+ times
- Result: Could not resolve - AWS Support ticket recommended

**Migration to Cloudflare** (May 21, 2026):
- Setup time: 5 minutes
- DNS verification: Instant
- SSL provisioning: 2 minutes
- Result: Working production site at www.betbudai.com

### Old AWS Amplify Apps (For Reference)
These have been deleted or are no longer in use:
- dhkrb1ol4d58y (SureBet-Manual) - deleted
- d2e2hrb2ei1cao (BetBudAI) - may still exist but not used
- d2cp2pfnzl7t60 (frontend, us-east-1) - domain removed
- d2hmpykfsdweob - deleted

**Old AWS Amplify URL**: https://main.d2e2hrb2ei1cao.amplifyapp.com/ (may still work)

## Backend Services

The backend Lambda functions remain on AWS:
- API Gateway endpoints unchanged
- Lambda functions: analysis, bpapi, picks-api, etc.
- These are independent of the frontend hosting

## Monitoring

- **Cloudflare Analytics**: Workers & Pages → betbudai → Metrics
- **Uptime**: Can use Cloudflare's uptime monitoring or external service
- **Logs**: Cloudflare Pages logs available in dashboard

## Team Access

Cloudflare account: Charles.mccarthy@gmail.com
- Admin access to betbudai project
- Can add team members in: Account home → Members

## Cost

**Current**: $0/month (Free Plan)
- Unlimited bandwidth
- Unlimited requests  
- Free SSL certificates
- 500 builds/month included

**No charges expected** for current traffic levels.

## Support

- Cloudflare Docs: https://developers.cloudflare.com/pages/
- Community: https://community.cloudflare.com/
- Support: Available via Cloudflare dashboard (Free plan has community support)

---

**Last Updated**: May 21, 2026  
**Status**: ✅ Production Live  
**Next Review**: As needed for updates
