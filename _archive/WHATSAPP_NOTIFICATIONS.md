# WhatsApp Notifications for Betting Picks
# Uses Twilio (Free trial) or CallMeBot (Free, no signup)

## Option 1: CallMeBot (Easiest - No signup needed)

1. Add the CallMeBot number to WhatsApp contacts
2. Send "I allow callmebot to send me messages" to the bot
3. You'll receive an API key

```python
import requests

def send_whatsapp_pick(phone_number, api_key, message):
    """
    Send WhatsApp message via CallMeBot (Free)
    
    Args:
        phone_number: Your phone with country code (e.g., +353861234567)
        api_key: API key from CallMeBot
        message: Pick details
    """
    url = f"https://api.callmebot.com/whatsapp.php"
    params = {
        'phone': phone_number,
        'text': message,
        'apikey': api_key
    }
    
    response = requests.get(url, params=params)
    return response.status_code == 200

# Example usage:
pick_message = """
🏇 NEW PICK ALERT!

Horse: Koukeo
Venue: Musselburgh
Time: 13:55
Odds: 2.2
Confidence: 52%

Value Score: 7/10
Form: 1-1-8 (Hot!)
"""

send_whatsapp_pick("+353861234567", "YOUR_API_KEY", pick_message)
```

## Option 2: Twilio (More reliable, $15/month)

```python
from twilio.rest import Client

def send_twilio_whatsapp(message):
    account_sid = 'YOUR_TWILIO_SID'
    auth_token = 'YOUR_TWILIO_TOKEN'
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        from_='whatsapp:+14155238886',  # Twilio sandbox
        body=message,
        to='whatsapp:+353861234567'  # Your number
    )
    
    return message.sid
```

## Integration with Betting System

Add to `save_selections_to_dynamodb.py`:

```python
# After saving pick to DB, send WhatsApp notification
if new_picks_saved:
    for pick in new_picks:
        message = format_pick_message(pick)
        send_whatsapp_pick(PHONE, API_KEY, message)
```

## Setup Steps

1. **For CallMeBot (Free):**
   - Save this number: +34 644 21 17 81
   - Send: "I allow callmebot to send me messages"
   - Save your API key
   - Add to code

2. **For Twilio ($15/month):**
   - Sign up at twilio.com
   - Get API credentials
   - Add to code

## Recommendation

Start with **CallMeBot** - it's free and works immediately!

Want me to create the full integration script?
