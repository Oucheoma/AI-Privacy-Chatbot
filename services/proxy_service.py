import httpx
import json
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse, Response
import time
import hashlib
from masking.smart_masking import smart_mask
from config import USE_SECURE_FILTER, OPENROUTER_API_KEY
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyService:
    def __init__(self):
        self.active_connections = 0
        self.request_count = 0
        self.services = {
            "openrouter": {
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": OPENROUTER_API_KEY,
                "models": ["anthropic/claude-3-haiku", "openai/gpt-4", "meta-llama/llama-3.1-8b-instruct"]
            },
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "api_key": None,  # Will be set from environment
                "models": ["gpt-4", "gpt-3.5-turbo"]
            },
            "anthropic": {
                "base_url": "https://api.anthropic.com/v1",
                "api_key": None,  # Will be set from environment
                "models": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"]
            }
        }
        self.rate_limits = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000
        }
        self.request_history = []

    async def forward_request(self, request: Request, path: str, target_service: str) -> Response:
        """
        Forward a general HTTP request to the target service
        """
        if target_service not in self.services:
            raise HTTPException(status_code=400, detail=f"Unknown service: {target_service}")
        
        service_config = self.services[target_service]
        
        # Check rate limits
        if not self._check_rate_limit():
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Get request body
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
            except:
                body = None
        
        # Get headers (filter out sensitive ones)
        headers = dict(request.headers)
        headers_to_remove = ["host", "content-length", "transfer-encoding"]
        for header in headers_to_remove:
            headers.pop(header, None)
        
        # Add service-specific headers
        if target_service == "openrouter":
            headers.update({
                "Authorization": f"Bearer {service_config['api_key']}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Secure AI Proxy"
            })
        
        # Build target URL
        target_url = f"{service_config['base_url']}/{path}"
        
        # Log the request
        self._log_request(request, target_service, path)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    params=dict(request.query_params)
                )
                
                # Log the response
                self._log_response(response, target_service)
                
                # Return the response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
        except Exception as e:
            logger.error(f"Proxy forwarding error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Forwarding failed: {str(e)}")

    async def forward_chat_request(self, request: Request, body: Dict[str, Any], target_service: str) -> Dict[str, Any]:
        """
        Forward a chat request with security filtering
        """
        if target_service not in self.services:
            raise HTTPException(status_code=400, detail=f"Unknown service: {target_service}")
        
        service_config = self.services[target_service]
        
        # Check rate limits
        if not self._check_rate_limit():
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Extract messages from the request
        messages = body.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Apply security filtering to messages
        filtered_messages = []
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content", "")
                # Apply smart masking
                masked_content, _ = smart_mask(content, "chat_message.txt", USE_SECURE_FILTER)
                filtered_messages.append({
                    "role": message["role"],
                    "content": masked_content
                })
            else:
                filtered_messages.append(message)
        
        # Prepare the request body
        request_body = {
            "model": body.get("model", service_config["models"][0]),
            "messages": filtered_messages,
            "max_tokens": body.get("max_tokens", 1000),
            "temperature": body.get("temperature", 0.7),
            "stream": body.get("stream", False)
        }
        
        # Add optional parameters
        optional_params = ["top_p", "frequency_penalty", "presence_penalty", "stop"]
        for param in optional_params:
            if param in body:
                request_body[param] = body[param]
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {service_config['api_key']}"
        }
        
        if target_service == "openrouter":
            headers.update({
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Secure AI Proxy"
            })
        
        # Build target URL
        target_url = f"{service_config['base_url']}/chat/completions"
        
        # Log the request
        self._log_request(request, target_service, "chat/completions")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url=target_url,
                    headers=headers,
                    json=request_body
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Add security metadata
                result["security_metadata"] = {
                    "secure_filtering_applied": USE_SECURE_FILTER,
                    "original_message_count": len(messages),
                    "filtered_message_count": len(filtered_messages),
                    "proxy_service": target_service
                }
                
                # Log the response
                self._log_response(response, target_service)
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from {target_service}: {e.response.status_code}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Chat forwarding error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Chat forwarding failed: {str(e)}")

    def _check_rate_limit(self) -> bool:
        """
        Check if the request is within rate limits
        """
        current_time = time.time()
        
        # Remove old requests from history
        self.request_history = [req_time for req_time in self.request_history 
                              if current_time - req_time < 3600]  # Keep last hour
        
        # Check hourly limit
        if len(self.request_history) >= self.rate_limits["requests_per_hour"]:
            return False
        
        # Check minute limit (last 60 seconds)
        recent_requests = [req_time for req_time in self.request_history 
                          if current_time - req_time < 60]
        
        if len(recent_requests) >= self.rate_limits["requests_per_minute"]:
            return False
        
        # Add current request to history
        self.request_history.append(current_time)
        return True

    def _log_request(self, request: Request, target_service: str, path: str):
        """
        Log the incoming request
        """
        user_hash = self._get_user_hash(request)
        log_entry = {
            "user_hash": user_hash,
            "method": request.method,
            "path": path,
            "target_service": target_service,
            "timestamp": time.time(),
            "status": "forwarded"
        }
        
        logger.info(f"Request logged: {log_entry}")
        self.request_count += 1

    def _log_response(self, response: httpx.Response, target_service: str):
        """
        Log the response from the target service
        """
        log_entry = {
            "target_service": target_service,
            "status_code": response.status_code,
            "timestamp": time.time(),
            "response_size": len(response.content) if response.content else 0
        }
        
        logger.info(f"Response logged: {log_entry}")

    def _get_user_hash(self, request: Request) -> str:
        """
        Generate a hash for the user based on IP and headers
        """
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Create a hash from IP and user agent
        user_string = f"{client_ip}:{user_agent}"
        return hashlib.md5(user_string.encode()).hexdigest()[:8]

    def get_available_services(self) -> List[str]:
        """
        Get list of available services
        """
        return list(self.services.keys())

    def get_active_connections(self) -> int:
        """
        Get number of active connections
        """
        return self.active_connections

    def get_request_stats(self) -> Dict[str, Any]:
        """
        Get request statistics
        """
        return {
            "total_requests": self.request_count,
            "active_connections": self.active_connections,
            "rate_limits": self.rate_limits,
            "recent_requests": len(self.request_history)
        } 