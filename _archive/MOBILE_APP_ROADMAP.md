# SureBet Mobile App + Subscription Roadmap

## Overview
Convert SureBet into a subscription-based mobile app (iOS + Android) with Stripe payments.

---

## Phase 1: Stripe Backend Setup (Week 1)

### 1.1 Create Stripe Account
```bash
# Sign up at https://stripe.com
# Get API keys from Dashboard > Developers > API keys
# Test mode keys for development
# Live mode keys for production
```

### 1.2 Define Subscription Products

**Free Tier:**
- Price: $0/month
- Features: 1 pick per day, basic analysis
- Stripe Product ID: `prod_free`

**Pro Tier:**
- Price: $29.99/month
- Features: All picks, enhanced analysis, alerts
- Stripe Product ID: `prod_pro`
- Stripe Price ID: `price_pro_monthly`

**VIP Tier:**
- Price: $99.99/month
- Features: Pro + priority support, custom strategies
- Stripe Product ID: `prod_vip`
- Stripe Price ID: `price_vip_monthly`

### 1.3 Install Stripe Package

```bash
cd C:\Users\charl\OneDrive\futuregenAI\Betting
.\.venv\Scripts\activate
pip install stripe
```

### 1.4 Create Stripe Lambda Functions

**Files to create:**
1. `lambda_stripe_create_customer.py` - Create Stripe customer on signup
2. `lambda_stripe_create_subscription.py` - Handle subscription creation
3. `lambda_stripe_webhook.py` - Handle Stripe webhooks
4. `lambda_stripe_portal.py` - Customer portal for managing subscription

---

## Phase 2: Backend API Updates (Week 1-2)

### 2.1 DynamoDB Schema Updates

**New Table: `SureBetUsers`**
```python
{
    'user_id': 'uuid',
    'email': 'string',
    'stripe_customer_id': 'string',
    'stripe_subscription_id': 'string',
    'subscription_tier': 'free|pro|vip',
    'subscription_status': 'active|canceled|past_due',
    'subscription_period_end': 'timestamp',
    'created_at': 'timestamp',
    'device_tokens': ['fcm_token1', 'fcm_token2'],  # For push notifications
}
```

### 2.2 Update Lambda API

**New endpoints needed:**
```
POST /api/auth/register
POST /api/auth/login
GET  /api/user/profile
POST /api/subscription/create
POST /api/subscription/cancel
POST /api/subscription/portal
POST /api/stripe/webhook
```

**Update existing endpoint:**
```
GET /api/picks/today
- Check user subscription tier
- Return picks based on tier (1 for free, 5 for pro/vip)
```

---

## Phase 3: Mobile App Development (Week 2-4)

### 3.1 Technology Stack

**Framework:** React Native (iOS + Android from one codebase)
**State Management:** Redux Toolkit
**Navigation:** React Navigation
**UI Library:** React Native Paper or NativeBase
**Payments:** `@stripe/stripe-react-native`
**Auth:** AWS Amplify or Firebase Auth
**Push Notifications:** Firebase Cloud Messaging (FCM)

### 3.2 Project Structure

```
surebet-mobile/
├── src/
│   ├── screens/
│   │   ├── Auth/
│   │   │   ├── LoginScreen.js
│   │   │   ├── RegisterScreen.js
│   │   │   └── SubscriptionScreen.js
│   │   ├── Home/
│   │   │   ├── TodayPicksScreen.js
│   │   │   ├── PickDetailScreen.js
│   │   │   └── PerformanceScreen.js
│   │   ├── Profile/
│   │   │   ├── ProfileScreen.js
│   │   │   └── SubscriptionManageScreen.js
│   ├── components/
│   │   ├── BetCard.js
│   │   ├── DecisionRatingBadge.js
│   │   ├── SubscriptionTierCard.js
│   ├── services/
│   │   ├── api.js
│   │   ├── stripe.js
│   │   └── notifications.js
│   ├── store/
│   │   ├── userSlice.js
│   │   ├── picksSlice.js
│   │   └── store.js
│   └── navigation/
│       └── AppNavigator.js
├── android/
├── ios/
├── app.json
└── package.json
```

### 3.3 Key Screens Design

**Onboarding Flow:**
1. Splash Screen (logo + loading)
2. Welcome Screen (features overview)
3. Register/Login Screen
4. Subscription Selection Screen
5. Payment Screen (Stripe)
6. Home Screen

**Main App Flow:**
1. Today's Picks (main screen)
2. Pick Detail (expanded view)
3. Performance Dashboard
4. Profile & Settings
5. Subscription Management

---

## Phase 4: Stripe Integration (Week 3)

### 4.1 Mobile Payment Flow

```javascript
// In SubscriptionScreen.js
import { useStripe } from '@stripe/stripe-react-native';

const handleSubscribe = async (priceId) => {
  // 1. Create customer on backend
  const customer = await api.post('/subscription/create-customer', {
    email: user.email
  });
  
  // 2. Create subscription
  const subscription = await api.post('/subscription/create', {
    customerId: customer.id,
    priceId: priceId
  });
  
  // 3. Confirm payment (if required)
  if (subscription.status === 'requires_payment_method') {
    const { error } = await confirmPayment(subscription.client_secret);
    if (error) {
      // Handle error
    }
  }
  
  // 4. Update local user state
  dispatch(updateSubscription(subscription));
};
```

### 4.2 Webhook Handling

**Events to handle:**
- `customer.subscription.created` - New subscription
- `customer.subscription.updated` - Subscription changed
- `customer.subscription.deleted` - Subscription canceled
- `invoice.payment_succeeded` - Payment successful
- `invoice.payment_failed` - Payment failed

---

## Phase 5: App Store Submission (Week 4-5)

### 5.1 Apple App Store

**Requirements:**
1. Apple Developer Account ($99/year)
2. App Store Connect setup
3. App privacy policy URL
4. Terms of service URL
5. Screenshots (6.5", 5.5", 12.9" iPad)
6. App icon (1024x1024px)
7. App description & keywords

**Gambling Disclaimer:**
```
This app provides AI-generated horse racing tips and analysis for 
educational and entertainment purposes only. Users must be 18+ and 
responsible for their own betting decisions. We do not process 
gambling transactions.
```

**Privacy Policy Must Include:**
- Data collection (email, device info)
- Stripe payment processing
- AWS data storage
- User rights (access, deletion)

### 5.2 Google Play Store

**Requirements:**
1. Google Play Developer Account ($25 one-time)
2. Content rating questionnaire
3. Privacy policy URL
4. Feature graphic (1024x500px)
5. Screenshots (phone + tablet)
6. App description

**Age Rating:** 18+ (gambling-related content)

---

## Phase 6: Push Notifications (Week 5)

### 6.1 Firebase Setup

```bash
# Install Firebase
npm install @react-native-firebase/app
npm install @react-native-firebase/messaging

# Setup Firebase project
# Add iOS app (Bundle ID)
# Add Android app (Package name)
# Download google-services.json (Android)
# Download GoogleService-Info.plist (iOS)
```

### 6.2 Notification Types

**Daily Picks Ready:**
```
Title: "Today's Picks Are Ready! 🏇"
Body: "5 new selections analyzed. Best pick: Krissy (DO IT)"
Action: Open app → Today's Picks
Time: 11:30 AM (30 mins before first race)
```

**High-Confidence Alert:**
```
Title: "DO IT Pick Alert! 🎯"
Body: "Timely Affair at Southwell (Score: 77.3, ROI: 32%)"
Action: Open pick detail
Time: Real-time when pick added
```

**Results Update:**
```
Title: "Your Picks Results 📊"
Body: "3 wins, 2 places today. Profit: +€47.50"
Action: Open performance dashboard
Time: 9:00 PM (after racing)
```

---

## Phase 7: Testing & QA (Week 6)

### 7.1 Test Cases

**Authentication:**
- [ ] Register new user
- [ ] Login existing user
- [ ] Logout
- [ ] Password reset

**Subscriptions:**
- [ ] Subscribe to Pro (test card)
- [ ] Subscribe to VIP (test card)
- [ ] View subscription status
- [ ] Cancel subscription
- [ ] Resubscribe after cancel
- [ ] Handle failed payment

**Content Access:**
- [ ] Free tier: 1 pick visible
- [ ] Pro tier: All picks visible
- [ ] VIP tier: All picks + extra features
- [ ] Tier enforcement on API

**Payments:**
- [ ] Successful payment
- [ ] Failed payment (declined card)
- [ ] 3D Secure flow
- [ ] Refund handling

### 7.2 Test Cards (Stripe)

```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
3D Secure: 4000 0027 6000 3184
```

---

## Cost Breakdown

### Development Costs

**One-Time:**
- Apple Developer Account: $99/year
- Google Play Account: $25 one-time
- App icon/design: $200-500 (Fiverr)
- Privacy policy: $50 (TermsFeed)

**Monthly (Projected 1,000 users):**
- Stripe fees: 2.9% + $0.30/transaction
  - 500 Pro subs ($29.99) = $434.25/month
  - 100 VIP subs ($99.99) = $289.97/month
  - Total Stripe fees: ~$724/month
- AWS costs: $50-100/month (Lambda, API Gateway, DynamoDB)
- Firebase (free tier): $0
- Total: ~$800/month

**Revenue (1,000 users):**
- 400 Free users: $0
- 500 Pro users: $14,995
- 100 VIP users: $9,999
- **Total: $24,994/month**
- **Profit: $24,194/month** (after fees)

---

## Timeline

**Week 1:** Stripe setup, create products, test payments
**Week 2:** Backend API updates, user auth, subscription endpoints
**Week 3:** Mobile app scaffolding, basic UI, navigation
**Week 4:** Stripe integration in app, payment flows
**Week 5:** Push notifications, app store prep
**Week 6:** Testing, bug fixes
**Week 7:** App store submission (Apple)
**Week 8:** App store submission (Google)
**Week 9-10:** Review process, launch! 🚀

---

## Subscription Tiers Detail

### FREE TIER
**Price:** $0/month
**Features:**
- ✅ 1 pick per day (highest rated)
- ✅ Basic analysis (Why Now)
- ✅ Decision Rating visible
- ❌ No historical performance
- ❌ No push notifications
- ❌ No detailed stats

**Goal:** Acquisition (prove value)

### PRO TIER
**Price:** $29.99/month
**Features:**
- ✅ All 5 daily picks
- ✅ Enhanced AI analysis (4-pass reasoning)
- ✅ Decision Rating + confidence breakdown
- ✅ Push notifications (picks + results)
- ✅ Performance dashboard (7 days)
- ✅ Historical insights
- ✅ Email support

**Goal:** Primary revenue stream

### VIP TIER
**Price:** $99.99/month
**Features:**
- ✅ Everything in Pro
- ✅ Early access (picks at 11:00 AM)
- ✅ Custom bet parameters
- ✅ Priority email support (24hr response)
- ✅ Monthly strategy call (15 mins)
- ✅ Advanced analytics (30 days history)
- ✅ Exclusive Discord channel
- ✅ Beta feature access

**Goal:** High-value users, community building

---

## Key Implementation Files Needed

### Backend (Python)
1. `lambda_stripe_create_customer.py`
2. `lambda_stripe_create_subscription.py`
3. `lambda_stripe_webhook.py`
4. `lambda_stripe_cancel_subscription.py`
5. `lambda_user_auth.py` (register/login)
6. `lambda_api_picks_tiered.py` (updated with tier checking)

### Mobile App (React Native)
1. `src/screens/Auth/LoginScreen.js`
2. `src/screens/Auth/RegisterScreen.js`
3. `src/screens/Subscription/SubscriptionScreen.js`
4. `src/screens/Home/TodayPicksScreen.js`
5. `src/screens/Profile/ProfileScreen.js`
6. `src/services/stripe.js`
7. `src/services/api.js`

### Infrastructure
1. `stripe-webhook-lambda.yaml` (CloudFormation)
2. `api-gateway-auth.yaml` (JWT authorizer)
3. `dynamodb-users-table.yaml`

---

## Next Steps

1. **Now:** Set up Stripe account and create products
2. **This week:** Build Lambda functions for Stripe
3. **Next week:** Initialize React Native project
4. **Following week:** Integrate Stripe in mobile app

Ready to start? Let me know which phase you want to tackle first!
