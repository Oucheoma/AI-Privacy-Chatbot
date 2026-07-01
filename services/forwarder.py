import os
import requests
from masking.smart_masking import smart_mask
from config import USE_SECURE_FILTER, OPENROUTER_API_KEY

def forward_to_ai(user_input: str, file_name: str = "user_code.py", use_secure_filter: bool = None):
    """
    Enhanced AI forwarding with comprehensive security filtering
    
    Args:
        user_input: The user's input text
        file_name: Name of the file for context
        use_secure_filter: Whether to apply secure filtering (overrides global setting)
    """
    if use_secure_filter is None:
        use_secure_filter = USE_SECURE_FILTER
    
    masked_text, ai_pre_prompt = smart_mask(user_input, file_name, use_secure_filter)

    final_prompt = ai_pre_prompt + masked_text

    if not OPENROUTER_API_KEY:
        return {"error": "OpenRouter API key not configured"}
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Secure AI Proxy",
        "Content-Type": "application/json"
    }
    url = "https://openrouter.ai/api/v1/chat/completions"

    body = {
        "model": "anthropic/claude-3-haiku",
        "messages": [
            {"role": "user", "content": final_prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.7,
        "stream": False
    }

    # Debug: Print request details (remove sensitive info)
    print(f"Debug: Sending request to {url}")
    print(f"Debug: Model: {body['model']}")
    print(f"Debug: Content length: {len(final_prompt)}")
    print(f"Debug: Headers: {list(headers.keys())}")
    
    print(f"\nPROMPT SENT TO AI:")
    print("=" * 50)
    print(final_prompt)
    print("=" * 50)
    print()

    try:
        response = requests.post(url, headers=headers, json=body)
        print(f"Debug: Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Debug: Response text: {response.text[:200]}...")
        
        response.raise_for_status()

        result = response.json()
        result["security_metadata"] = {
            "secure_filtering_applied": use_secure_filter,
            "original_length": len(user_input),
            "masked_length": len(masked_text),
            "context_preserved": True
        }
        
        return result
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
