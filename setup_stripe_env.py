"""
Set Stripe environment variables on the BettingPicksAPI Lambda.
Fill in your actual keys before running.

Usage: python setup_stripe_env.py
"""
import boto3
import json

FUNCTION_NAME = 'BettingPicksAPI'
REGION        = 'eu-west-1'

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  FILL THESE IN with your actual Stripe keys                       ║
# ║  Get them from: https://dashboard.stripe.com/apikeys               ║
# ║  And Products: https://dashboard.stripe.com/products               ║
# ╚══════════════════════════════════════════════════════════════════════╝

STRIPE_SECRET_KEY     = 'sk_test_REPLACE_ME'          # Secret key from Stripe dashboard
STRIPE_WEBHOOK_SECRET = 'whsec_REPLACE_ME'            # Webhook signing secret (set up in Step 6 below)
STRIPE_PRICE_PREMIUM  = 'price_REPLACE_ME'            # Price ID for €19.99/mo Premium
STRIPE_PRICE_VIP      = 'price_REPLACE_ME'            # Price ID for €99/mo VIP


def main():
    if 'REPLACE_ME' in STRIPE_SECRET_KEY:
        print("ERROR: Please fill in your actual Stripe keys before running!")
        print()
        print("Steps:")
        print("  1. Go to https://dashboard.stripe.com/apikeys")
        print("  2. Copy your Secret Key (sk_test_... or sk_live_...)")
        print("  3. Go to https://dashboard.stripe.com/products")
        print("  4. Create two products:")
        print("     - Premium: €19.99/month recurring → copy the Price ID (price_...)")
        print("     - VIP: €99/month recurring → copy the Price ID (price_...)")
        print("  5. Paste all values in this file and run again")
        print("  6. For webhook secret, set up webhook endpoint first (see below)")
        return

    client = boto3.client('lambda', region_name=REGION)

    # Get existing env vars (preserve them)
    config = client.get_function_configuration(FunctionName=FUNCTION_NAME)
    env_vars = config.get('Environment', {}).get('Variables', {})

    # Add Stripe env vars
    env_vars['STRIPE_SECRET_KEY']     = STRIPE_SECRET_KEY
    env_vars['STRIPE_WEBHOOK_SECRET'] = STRIPE_WEBHOOK_SECRET
    env_vars['STRIPE_PRICE_PREMIUM']  = STRIPE_PRICE_PREMIUM
    env_vars['STRIPE_PRICE_VIP']      = STRIPE_PRICE_VIP

    client.update_function_configuration(
        FunctionName=FUNCTION_NAME,
        Environment={'Variables': env_vars}
    )

    print(f"✓ Stripe env vars set on {FUNCTION_NAME}")
    print(f"  STRIPE_SECRET_KEY:     {STRIPE_SECRET_KEY[:12]}...")
    print(f"  STRIPE_WEBHOOK_SECRET: {STRIPE_WEBHOOK_SECRET[:12]}...")
    print(f"  STRIPE_PRICE_PREMIUM:  {STRIPE_PRICE_PREMIUM}")
    print(f"  STRIPE_PRICE_VIP:      {STRIPE_PRICE_VIP}")


if __name__ == '__main__':
    main()
