# SureBet Mobile App - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Set Up Stripe (30 minutes)

1. **Create Stripe Account**
   - Go to https://stripe.com and sign up
   - Verify your email
   - Complete business profile

2. **Get API Keys**
   ```
   Dashboard > Developers > API keys
   
   Copy these:
   - Publishable key (starts with pk_test_)
   - Secret key (starts with sk_test_)
   ```

3. **Create Products**
   ```
   Dashboard > Products > Add Product
   
   Product 1: SureBet Pro
   - Price: $29.99/month
   - Recurring: Monthly
   - Save and copy Price ID (price_xxx)
   
   Product 2: SureBet VIP
   - Price: $99.99/month
   - Recurring: Monthly
   - Save and copy Price ID (price_xxx)
   ```

4. **Set Up Webhook**
   ```
   Dashboard > Developers > Webhooks > Add endpoint
   
   Endpoint URL: https://your-api-gateway-url/stripe/webhook
   Events to listen for:
   ✓ customer.subscription.created
   ✓ customer.subscription.updated
   ✓ customer.subscription.deleted
   ✓ invoice.payment_succeeded
   ✓ invoice.payment_failed
   
   Copy Signing secret (whsec_xxx)
   ```

---

### Step 2: Deploy Backend (1 hour)

1. **Install Stripe Package**
   ```powershell
   cd C:\Users\charl\OneDrive\futuregenAI\Betting
   .\.venv\Scripts\activate
   pip install stripe
   ```

2. **Create DynamoDB Table**
   ```powershell
   aws dynamodb create-table \
     --table-name SureBetUsers \
     --attribute-definitions \
       AttributeName=user_id,AttributeType=S \
       AttributeName=email,AttributeType=S \
     --key-schema \
       AttributeName=user_id,KeyType=HASH \
     --global-secondary-indexes \
       "[{\"IndexName\":\"EmailIndex\",\"KeySchema\":[{\"AttributeName\":\"email\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}]" \
     --provisioned-throughput \
       ReadCapacityUnits=5,WriteCapacityUnits=5 \
     --region us-east-1
   ```

3. **Set Environment Variables in Lambda**
   ```
   STRIPE_SECRET_KEY=sk_test_your_key_here
   STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
   ```

4. **Deploy Lambda Functions**
   ```powershell
   # Package each Lambda
   .\deploy_stripe_lambdas.ps1
   ```

---

### Step 3: Create Mobile App (1 week)

1. **Install React Native CLI**
   ```powershell
   npm install -g react-native-cli
   npx react-native init SureBetApp
   cd SureBetApp
   ```

2. **Install Dependencies**
   ```powershell
   npm install @stripe/stripe-react-native
   npm install @react-navigation/native
   npm install @react-navigation/stack
   npm install react-native-paper
   npm install redux @reduxjs/toolkit react-redux
   npm install axios
   ```

3. **Configure Stripe**
   ```javascript
   // App.js
   import { StripeProvider } from '@stripe/stripe-react-native';
   
   export default function App() {
     return (
       <StripeProvider publishableKey="pk_test_your_key">
         {/* Your app */}
       </StripeProvider>
     );
   }
   ```

4. **Run App**
   ```powershell
   # iOS
   npx react-native run-ios
   
   # Android
   npx react-native run-android
   ```

---

## 💰 Subscription Tiers

### FREE (Freemium)
- **Price:** $0/month
- **Features:**
  - 1 pick per day (highest rated)
  - Basic "Why Now" reasoning
  - Decision Rating badge
- **Goal:** Hook users, prove value

### PRO ($29.99/month)
- **Price:** $29.99/month
- **Features:**
  - All 5 daily picks
  - Full enhanced analysis
  - Push notifications
  - 7-day performance history
  - Priority email support
- **Goal:** Main revenue driver

### VIP ($99.99/month)
- **Price:** $99.99/month
- **Features:**
  - Everything in Pro
  - Early access (11 AM picks)
  - 30-day performance analytics
  - Monthly strategy call
  - Private Discord channel
  - Beta features
- **Goal:** Premium users, community

---

## 📱 App Store Requirements

### Apple App Store
- [ ] Apple Developer Account ($99/year)
- [ ] Privacy Policy URL
- [ ] Terms of Service URL
- [ ] App icon (1024x1024px)
- [ ] Screenshots (iPhone + iPad)
- [ ] Age rating: 18+ (gambling content)
- [ ] Disclaimer: "For entertainment purposes only"

### Google Play Store
- [ ] Google Play Account ($25 one-time)
- [ ] Privacy Policy URL
- [ ] Content rating: 18+
- [ ] Feature graphic (1024x500px)
- [ ] Screenshots (phone + tablet)

---

## 🎯 Key Metrics to Track

**User Acquisition:**
- Daily signups
- Conversion rate (free → paid)
- CAC (Customer Acquisition Cost)

**Revenue:**
- MRR (Monthly Recurring Revenue)
- ARPU (Average Revenue Per User)
- Churn rate

**Product:**
- DAU/MAU (Daily/Monthly Active Users)
- Retention (D1, D7, D30)
- Feature usage

---

## 📊 Revenue Projections

**Month 1:**
- 100 users (80 free, 15 pro, 5 vip)
- MRR: $949.80
- Stripe fees: $32.89
- **Net: $916.91**

**Month 6:**
- 1,000 users (400 free, 500 pro, 100 vip)
- MRR: $24,994
- Stripe fees: $724
- **Net: $24,270**

**Month 12:**
- 5,000 users (2,000 free, 2,500 pro, 500 vip)
- MRR: $124,970
- Stripe fees: $3,624
- **Net: $121,346**

**Year 2 Goal:**
- 20,000 users (8,000 free, 10,000 pro, 2,000 vip)
- MRR: $499,880
- **Annual Revenue: $5.9M**

---

## 🔧 Development Phases

**Phase 1 (Week 1):** Stripe backend ✓
**Phase 2 (Week 2):** User authentication API
**Phase 3 (Week 3):** Mobile app scaffold
**Phase 4 (Week 4):** Payment integration
**Phase 5 (Week 5):** Push notifications
**Phase 6 (Week 6):** Testing & QA
**Phase 7 (Week 7-8):** App store submission
**Phase 8 (Week 9-10):** Launch! 🚀

---

## 🎁 Free Trial Strategy

**14-Day Free Trial (Pro Tier)**
- Automatic after signup
- No credit card required upfront
- Day 7: Reminder email
- Day 13: "Last day" email
- Day 14: Convert to paid or downgrade to free

**Benefits:**
- Lower friction (no card needed)
- Higher conversion (users see value first)
- Builds trust

---

## 📧 Email Sequences

**Welcome Email (Day 0):**
```
Subject: Welcome to SureBet! Your first pick is ready 🏇

Hey [Name],

Welcome to SureBet! Your AI analyst just generated today's top pick...

[Show pick card]

Want all 5 picks? Upgrade to Pro for full access.

[CTA: Start 14-Day Free Trial]
```

**Conversion Email (Day 13):**
```
Subject: Tomorrow is your last day of Pro access

Hey [Name],

Your 14-day trial ends tomorrow. Here's what you've achieved:

✓ 12 picks analyzed
✓ 7 winners (58% strike rate!)
✓ +£143 profit

Lock in Pro at $29.99/month:
[CTA: Keep Pro Access]

Or continue with 1 free pick per day.
```

---

## 🚀 Ready to Start?

**Next Actions:**
1. ✅ Set up Stripe account (30 mins)
2. ✅ Deploy backend Lambdas (1 hour)
3. ⬜ Initialize React Native project (2 hours)
4. ⬜ Build subscription screen (1 day)
5. ⬜ Submit to App Store (1 week)

**Need help?** Check MOBILE_APP_ROADMAP.md for detailed instructions.

**Let's build this! 🎯**
