# Anthropic Claude API Setup Guide

## Security First! 🔒

**NEVER commit API keys to git or share them publicly.**

## Initial Setup

### 1. Rotate Your Exposed API Key

🚨 **CRITICAL**: The API key you shared earlier is exposed and must be rotated immediately:

1. Go to https://console.anthropic.com/settings/keys
2. Delete the exposed key: `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`
3. Create a new API key

### 2. Add Your New Key to .env

```bash
# Edit .env file (already created for you)
# Replace the placeholder with your NEW key:
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-NEW-KEY-HERE
```

The `.env` file is already in `.gitignore`, so it won't be committed to git.

### 3. Install Dependencies

```bash
# Activate your virtual environment
source .venv/Scripts/activate  # Windows Git Bash
# or
.venv\Scripts\activate  # Windows CMD

# Install the Anthropic SDK
pip install -r backend/requirements.txt
```

## Usage

### Python Example

```python
from backend.core.agentic.claude_client import ClaudeClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize client (automatically reads ANTHROPIC_API_KEY from .env)
client = ClaudeClient()

# Generate analysis
result = client.generate_analysis(
    "What factors make a horse likely to win a race?"
)
print(result)
```

### Race Data Analysis

```python
race_data = {
    "race_id": "2026-05-20-R1",
    "horses": [
        {"name": "Thunder", "form": "1-2-1"},
        {"name": "Lightning", "form": "3-1-2"}
    ]
}

analysis = client.analyze_race_data(race_data)
print(analysis["raw_analysis"])
```

## Files Created/Updated

1. ✅ `.env` - Created from template with placeholder for your API key
2. ✅ `.env.example` - Updated with `ANTHROPIC_API_KEY` template
3. ✅ `backend/requirements.txt` - Added `anthropic==0.47.1`
4. ✅ `backend/core/agentic/claude_client.py` - New secure client wrapper
5. ✅ `.gitignore` - Already had `.env` excluded

## Testing Your Setup

Run the test script:

```bash
python backend/core/agentic/claude_client.py
```

Expected output:
```
Claude Response:
A good horse racing bet considers factors like recent form, track conditions, jockey experience...
```

## AWS Lambda Deployment

For production Lambda functions, store the API key in AWS Secrets Manager:

```bash
# Create secret
aws secretsmanager create-secret \
    --name betbudai/anthropic-api-key \
    --secret-string "your-api-key-here" \
    --region eu-west-1

# Reference in Lambda environment or fetch at runtime
```

## Claude Models Available

- `claude-opus-4-7` - Most capable, best for complex analysis
- `claude-sonnet-4-6` - Balanced performance (default in our client)
- `claude-haiku-4-5-20251001` - Fastest, for simple tasks

## Best Practices

1. ✅ **Never hardcode API keys** in source code
2. ✅ **Use environment variables** for local development
3. ✅ **Use Secrets Manager** for production (AWS Lambda)
4. ✅ **Rotate keys regularly** and immediately if exposed
5. ✅ **Use prompt caching** to reduce costs on repeated prompts
6. ✅ **Monitor usage** at https://console.anthropic.com/settings/usage

## Cost Management

- Sonnet 4.6: ~$3 per million input tokens, ~$15 per million output tokens
- Use `max_tokens` parameter to control response length
- Implement prompt caching for repeated race data analysis

## Support

- Anthropic Docs: https://docs.anthropic.com
- API Console: https://console.anthropic.com
- BetBudAI Issues: [your repo issues link]
