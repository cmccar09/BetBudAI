#!/usr/bin/env python3
"""
WhatsApp notification sender for betting picks
Uses CallMeBot API (free, no signup needed)
"""
import requests
from typing import Dict, Any
import json
from pathlib import Path

# Configuration file
CONFIG_FILE = Path(__file__).parent / 'whatsapp_config.json'

def load_config():
    """Load WhatsApp configuration"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'enabled': False,
        'phone': '',
        'api_key': '',
        'provider': 'callmebot'
    }

def save_config(config):
    """Save WhatsApp configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, indent=2, fp=f)

def setup_whatsapp():
    """Interactive setup for WhatsApp notifications"""
    print("\n" + "="*80)
    print("WHATSAPP NOTIFICATION SETUP")
    print("="*80)
    
    print("\nUsing CallMeBot (Free service)")
    print("\nSetup steps:")
    print("1. Save this number in your contacts: +34 644 21 17 81")
    print("2. Send this message to that contact:")
    print('   "I allow callmebot to send me messages"')
    print("3. You'll receive an API key in response")
    print()
    
    phone = input("Enter your phone number (with country code, e.g., +353861234567): ").strip()
    api_key = input("Enter the API key you received: ").strip()
    
    config = {
        'enabled': True,
        'phone': phone,
        'api_key': api_key,
        'provider': 'callmebot'
    }
    
    save_config(config)
    
    # Test it
    print("\n🧪 Sending test message...")
    if send_whatsapp_notification("✅ WhatsApp notifications setup complete! You'll receive pick alerts here.", config):
        print("✅ Test message sent successfully!")
        print(f"✅ Configuration saved to {CONFIG_FILE}")
        return True
    else:
        print("❌ Test failed. Please check your phone number and API key.")
        return False

def format_pick_message(pick: Dict[str, Any]) -> str:
    """Format a pick as WhatsApp message"""
    horse = pick.get('horse', 'Unknown')
    venue = pick.get('course', 'Unknown')
    race_time = pick.get('race_time', '')[:16]
    odds = pick.get('odds', 'N/A')
    confidence = pick.get('confidence', 'N/A')
    bet_type = pick.get('bet_type', 'WIN')
    
    # Get value/form scores if available
    all_horses = pick.get('all_horses_analyzed', {})
    value_info = ""
    form_info = ""
    
    if all_horses:
        # Find this horse in the analysis
        for expert, horses in all_horses.items():
            if isinstance(horses, list):
                for h in horses:
                    if h.get('runner_name') == horse:
                        if 'value_score' in h:
                            value_info = f"\n💰 Value Score: {h['value_score']}/10"
                        if 'form_score' in h:
                            form_info = f"\n📊 Form Score: {h['form_score']}/10"
                        break
    
    message = f"""🏇 *NEW PICK ALERT!*

🐴 *{horse}*
📍 {venue}
⏰ {race_time}
💵 Odds: {odds}
🎯 Confidence: {confidence}%
📋 Type: {bet_type}{value_info}{form_info}

Good luck! 🍀"""
    
    return message

def send_whatsapp_notification(message: str, config: Dict = None) -> bool:
    """
    Send WhatsApp message via CallMeBot
    
    Args:
        message: Text to send
        config: Optional config override
        
    Returns:
        True if sent successfully
    """
    if config is None:
        config = load_config()
    
    if not config.get('enabled', False):
        return False
    
    phone = config.get('phone', '').replace('+', '')
    api_key = config.get('api_key', '')
    
    if not phone or not api_key:
        return False
    
    try:
        url = "https://api.callmebot.com/whatsapp.php"
        params = {
            'phone': phone,
            'text': message,
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        print(f"WhatsApp notification error: {e}")
        return False

def notify_new_pick(pick: Dict[str, Any]) -> bool:
    """Send notification for a new pick"""
    config = load_config()
    
    if not config.get('enabled', False):
        return False
    
    message = format_pick_message(pick)
    return send_whatsapp_notification(message, config)

def notify_result(pick: Dict[str, Any], outcome: str) -> bool:
    """Send notification for a pick result"""
    config = load_config()
    
    if not config.get('enabled', False):
        return False
    
    horse = pick.get('horse', 'Unknown')
    venue = pick.get('course', 'Unknown')
    odds = pick.get('odds', 'N/A')
    
    emoji = "🎉" if outcome == "WON" else "❌"
    
    message = f"""{emoji} *RESULT*

🐴 {horse}
📍 {venue}
💵 Odds: {odds}
📊 Result: {outcome}"""
    
    return send_whatsapp_notification(message, config)

if __name__ == '__main__':
    # Run setup
    setup_whatsapp()
