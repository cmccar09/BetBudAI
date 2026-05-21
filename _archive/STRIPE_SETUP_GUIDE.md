# Stripe Setup Guide - Step by Step

## ⏱️ Time Required: 30 minutes

---

## Step 1: Create Stripe Account (5 minutes)

1. **Go to Stripe**
   - Visit: https://stripe.com
   - Click **"Sign up"**

2. **Fill Registration**
   ```
   Email: your-email@example.com
   Full name: Your Name
   Country: United Kingdom
   Password: (secure password)
   ```

3. **Verify Email**
   - Check inbox for verification email
   - Click verification link

4. **Complete Business Profile**
   ```
   Business name: SureBet AI
   Business type: Private company
   Industry: Software/Technology
   Website: https://main.d3cqx8p6ckxtkj.amplifyapp.com
   ```

5. **Skip Payment Setup**
   - Click "I'll do this later"
   - We'll use test mode first

---

## Step 2: Get API Keys (2 minutes)

1. **Navigate to Developers**
   - Dashboard → Top right → Developers
   - Click **"API keys"** in left sidebar

2. **Copy Test Keys**
   ```
   Publishable key: pk_test_51...
   Secret key: sk_test_51... (click "Reveal test key")
   ```

3. **Save Keys Securely**
   - Create file: `stripe-keys.txt` (add to .gitignore!)
   - Paste both keys
   - **NEVER commit these to GitHub!**

---

## Step 3: Create Products (15 minutes)

### Product 1: SureBet Pro

1. **Go to Products**
   - Dashboard → Products → "+ Add product"

2. **Fill Details**
   ```
   Name: SureBet Pro
   Description: Full access to all 5 daily AI-powered horse racing picks with push notifications
   
   Pricing:
   - Type: Recurring
   - Price: £29.99 GBP (or $29.99 USD)
   - Billing period: Monthly
   - Payment button text: Subscribe to Pro
   ```

3. **Add Features (Optional)**
   ```
   - 5 picks per day
   - Push notifications
   - Full enhanced analysis
   - 7-day performance history
   - Email support
   ```

4. **Save & Copy Price ID**
   - Click **"Save product"**
   - Copy the Price ID: `price_1ABC...xyz`
   - Save this as `STRIPE_PRICE_PRO` in your notes

---

### Product 2: SureBet VIP

1. **Add Another Product**
   - Products → "+ Add product"

2. **Fill Details**
   ```
   Name: SureBet VIP
   Description: Premium access with early picks, advanced analytics, and monthly strategy calls
   
   Pricing:
   - Type: Recurring
   - Price: £99.99 GBP (or $99.99 USD)
   - Billing period: Monthly
   - Payment button text: Subscribe to VIP
   ```

3. **Add Features**
   ```
   - Everything in Pro
   - Early access (11 AM picks)
   - 30-day performance analytics
   - Monthly strategy call
   - Private Discord channel
   - Beta features
   ```

4. **Save & Copy Price ID**
   - Click **"Save product"**
   - Copy the Price ID: `price_1DEF...xyz`
   - Save this as `STRIPE_PRICE_VIP` in your notes

---

## Step 4: Enable Free Trials (3 minutes)

1. **Go to Product Settings**
   - Click on **SureBet Pro** product
   - Scroll to **"Trial period"**

2. **Configure Trial**
   ```
   Trial period: 14 days
   Trial requires payment method: No (recommended)
   ```

3. **Save Changes**

4. **Repeat for VIP**
   - Same 14-day trial
   - No payment method required

---

## Step 5: Create Webhook (5 minutes)

1. **Go to Webhooks**
   - Dashboard → Developers → Webhooks
   - Click **"+ Add endpoint"**

2. **Endpoint URL**
   ```
   https://your-lambda-function-url.lambda-url.us-east-1.on.aws/stripe/webhook
   ```
   
   *Note: You'll get this URL after deploying lambda_stripe_webhook*
   *For now, use a placeholder: https://placeholder.com/webhook*

3. **Select Events**
   ```
   ✓ customer.subscription.created
   ✓ customer.subscription.updated
   ✓ customer.subscription.deleted
   ✓ invoice.payment_succeeded
   ✓ invoice.payment_failed
   ```

4. **Add Endpoint**
   - Click **"Add endpoint"**

5. **Copy Signing Secret**
   - Click on the new webhook endpoint
   - Reveal **Signing secret**: `whsec_...`
   - Save this as `STRIPE_WEBHOOK_SECRET`

---

## Step 6: Test Mode Configuration (Complete!)

You're now set up in **Test Mode**. This means:

✅ No real money will be charged  
✅ You can test with test cards  
✅ Perfect for development  

### Test Cards

Use these for testing:

```
Success:
4242 4242 4242 4242

Decline:
4000 0000 0000 0002

Requires 3D Secure:
4000 0025 0000 3155

Expiry: Any future date (e.g., 12/28)
CVC: Any 3 digits (e.g., 123)
ZIP: Any 5 digits (e.g., 12345)
```

---

## Step 7: Save Configuration

Create file: `stripe-config.json` (add to .gitignore!)

```json
{
  "mode": "test",
  "publishable_key": "pk_test_your_key_here",
  "secret_key": "sk_test_your_key_here",
  "webhook_secret": "whsec_your_secret_here",
  "products": {
    "pro": {
      "price_id": "price_1ABC...xyz",
      "name": "SureBet Pro",
      "amount": 2999,
      "currency": "gbp",
      "interval": "month"
    },
    "vip": {
      "price_id": "price_1DEF...xyz",
      "name": "SureBet VIP",
      "amount": 9999,
      "currency": "gbp",
      "interval": "month"
    }
  }
}
```

---

## Step 8: Update Lambda Environment Variables

1. **Go to AWS Lambda Console**
   - https://console.aws.amazon.com/lambda/

2. **For EACH of the 3 Lambda functions:**
   - Configuration → Environment variables → Edit

3. **Add Variables:**
   ```
   STRIPE_SECRET_KEY = sk_test_your_actual_key_here
   ```

4. **For webhook Lambda only, also add:**
   ```
   STRIPE_WEBHOOK_SECRET = whsec_your_actual_secret_here
   ```

5. **Save Changes**

---

## Step 9: Update Webhook URL (After Lambda Deployment)

1. **Get Lambda Function URL**
   - Deploy `lambda_stripe_webhook.py` to AWS Lambda
   - Configuration → Function URL → Create function URL
   - Copy the URL: `https://abc123.lambda-url.us-east-1.on.aws`

2. **Update Stripe Webhook**
   - Stripe Dashboard → Developers → Webhooks
   - Click your webhook endpoint
   - Update URL to: `https://abc123.lambda-url.us-east-1.on.aws`
   - Save

---

## Step 10: Test the Integration (Optional)

### Test User Registration

```powershell
curl -X POST https://your-customer-lambda-url.lambda-url.us-east-1.on.aws `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","name":"Test User"}'
```

Expected response:
```json
{
  "user_id": "uuid-here",
  "email": "test@example.com",
  "stripe_customer_id": "cus_abc123",
  "subscription_tier": "free"
}
```

### Test Subscription Creation

```powershell
curl -X POST https://your-subscription-lambda-url.lambda-url.us-east-1.on.aws `
  -H "Content-Type: application/json" `
  -d '{
    "user_id":"uuid-from-above",
    "price_id":"price_1ABC...xyz"
  }'
```

Expected response:
```json
{
  "subscription_id": "sub_xyz789",
  "client_secret": "pi_abc_secret_def",
  "status": "incomplete",
  "tier": "pro"
}
```

---

## ✅ Checklist

Before going live, verify:

- [ ] Test mode API keys saved securely
- [ ] Both products created (Pro & VIP)
- [ ] Price IDs copied and saved
- [ ] Webhook endpoint created
- [ ] Webhook secret saved
- [ ] Lambda functions have environment variables
- [ ] Test cards work in Stripe dashboard
- [ ] DynamoDB SureBetUsers table created
- [ ] User registration endpoint tested
- [ ] Subscription creation endpoint tested

---

## 🚀 Going Live (Later)

When ready for production:

1. **Activate Account**
   - Stripe Dashboard → Complete account setup
   - Add bank account details
   - Verify identity

2. **Switch to Live Mode**
   - Toggle "Test mode" to OFF
   - Get new live API keys: `pk_live_...` and `sk_live_...`
   - Update Lambda environment variables

3. **Update Mobile App**
   - Replace test publishable key with live key
   - Test with real card (charge yourself £0.50)
   - Refund test charge

4. **Monitor Payments**
   - Dashboard → Payments
   - Set up email alerts for failed payments

---

## 🆘 Troubleshooting

### "Invalid API key provided"
- Double-check you copied the full key
- Make sure no extra spaces
- Verify you're using test key in test mode

### "No such price"
- Price ID must match exactly
- Check you're in correct mode (test vs. live)

### "Webhook signature verification failed"
- Webhook secret must match
- Check Lambda environment variable

### "Customer already exists"
- Email must be unique in Stripe
- Use different email for testing

---

## 📚 Resources

- Stripe Dashboard: https://dashboard.stripe.com
- Stripe API Docs: https://stripe.com/docs/api
- Test Cards: https://stripe.com/docs/testing
- Webhooks Guide: https://stripe.com/docs/webhooks

---

**Next Steps:** Deploy Lambda functions with `deploy_stripe_lambdas.ps1`

**Questions?** Check Stripe docs or ask in setup channel.

---

*Setup time: ~30 minutes | Last updated: January 4, 2026*
