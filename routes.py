from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.forwarder import forward_to_ai
from config import USE_SECURE_FILTER

router = APIRouter()

# Define enhanced request model
class ProxyRequest(BaseModel):
    message: str
    filename: str = "user_code.py"
    use_secure_filter: Optional[bool] = None  # Override global setting
    security_level: Optional[str] = "high"  # low, medium, high

@router.post("/chat")
async def secure_proxy(data: ProxyRequest):
    """
    Secure AI Proxy endpoint with comprehensive filtering
    
    - Filters PII, source code, business secrets, and confidential documents
    - Maintains context and accuracy while protecting sensitive information
    - Supports personal chatbot mode when secure filtering is disabled
    """
    try:
        user_code = data.message
        file_name = data.filename
        use_secure_filter = data.use_secure_filter if data.use_secure_filter is not None else USE_SECURE_FILTER
        
        # Log the request for monitoring
        print(f"🔐 Processing request with secure filtering: {use_secure_filter}")
        
        response = forward_to_ai(user_code, file_name, use_secure_filter)
        # Robust: Always return the same structure
        if isinstance(response, dict) and "error" in response:
            return {
                "proxy_response": None,
                "error": response["error"],
                "security_info": {
                    "secure_filtering_enabled": use_secure_filter,
                    "security_level": data.security_level,
                    "message": f"Error: {response['error']}"
                }
            }
        return {
            "proxy_response": response,
            "security_info": {
                "secure_filtering_enabled": use_secure_filter,
                "security_level": data.security_level,
                "message": "Content processed with enhanced security filtering" if use_secure_filter else "Content processed in personal mode"
            }
        }
    except Exception as e:
        return {
            "proxy_response": None,
            "error": str(e),
            "security_info": {
                "secure_filtering_enabled": data.use_secure_filter if data.use_secure_filter is not None else USE_SECURE_FILTER,
                "security_level": data.security_level,
                "message": f"Proxy processing error: {str(e)}"
            }
        }

@router.get("/status")
async def get_status():
    """Get the current security configuration status"""
    return {
        "secure_filtering_enabled": USE_SECURE_FILTER,
        "service_status": "operational",
        "features": [
            "PII Detection and Masking",
            "Source Code Protection", 
            "Business Document Filtering",
            "Confidential Content Redaction",
            "Personal Chatbot Mode Toggle"
        ]
    }
