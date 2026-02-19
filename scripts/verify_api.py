"""Verify OpenRouter API key and model access."""
import sys
import os
import httpx
from loguru import logger

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import settings

def verify_api():
    api_key = settings.openrouter_api_key
    base_url = settings.openrouter_api_base
    model = settings.openrouter_metadata_model

    print(f"Checking API Configuration:")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")

    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY is not set or empty.")
        print("  Check your .env file or environment variables.")
        return False

    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
    print(f"  API Key: {masked_key}")

    print("\nTesting connection...")
    try:
        client = httpx.Client(timeout=10.0)

        # Test 1: Simple chat completion
        print(f"  Sending test request to {model}...")
        response = client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://pedirbot.local",
                "X-Title": "PedIRBot API Verification",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": "Hello, simply reply with 'API Working'."}
                ],
                "max_tokens": 10,
            },
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"  ✅ Success! Response: {content}")
            return True
        else:
            print(f"  ❌ Failed with status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"  ❌ Exception occurred: {e}")
        return False

if __name__ == "__main__":
    success = verify_api()
    if not success:
        sys.exit(1)
