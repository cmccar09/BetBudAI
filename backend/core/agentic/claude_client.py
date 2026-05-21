"""
Claude AI Client for BetBudAI
Secure integration with Anthropic's Claude API using environment variables.
"""
import os
from anthropic import Anthropic


class ClaudeClient:
    """
    Wrapper for Anthropic Claude API with secure credential management.
    """

    def __init__(self):
        """
        Initialize Claude client with API key from environment.
        Raises ValueError if ANTHROPIC_API_KEY is not set.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )

        self.client = Anthropic(api_key=api_key)
        self.default_model = "claude-sonnet-4-6"  # Latest Sonnet model

    def generate_analysis(self, prompt: str, model: str = None, max_tokens: int = 1024) -> str:
        """
        Generate text analysis using Claude.

        Args:
            prompt: The input prompt/question
            model: Claude model to use (defaults to claude-sonnet-4-6)
            max_tokens: Maximum tokens in response

        Returns:
            Generated text response
        """
        response = self.client.messages.create(
            model=model or self.default_model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text

    def analyze_race_data(self, race_data: dict) -> dict:
        """
        Analyze race data using Claude AI.

        Args:
            race_data: Dictionary containing race information

        Returns:
            Analysis results as dictionary
        """
        prompt = f"""
Analyze this horse racing data and provide insights:

{race_data}

Please provide:
1. Key factors affecting the outcome
2. Surprising patterns or anomalies
3. Confidence level in predictions
"""

        analysis = self.generate_analysis(prompt, max_tokens=2048)

        return {
            "raw_analysis": analysis,
            "race_id": race_data.get("race_id"),
            "model_used": self.default_model
        }


# Example usage
if __name__ == "__main__":
    # Load environment variables from .env file (for local development)
    from dotenv import load_dotenv
    load_dotenv()

    try:
        client = ClaudeClient()

        # Test with simple prompt
        result = client.generate_analysis(
            "Explain what factors make a good horse racing bet in 2 sentences."
        )
        print("Claude Response:")
        print(result)

    except ValueError as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Create a .env file (copy from .env.example)")
        print("2. Add your Anthropic API key to ANTHROPIC_API_KEY")
