from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import hashlib
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    def __init__(self):
        self.api_keys = {}  # Store valid API keys
        self.blocked_ips = set()  # Store blocked IP addresses
        self.request_logs = []  # Store request logs for analysis
        
    async def __call__(self, request: Request, call_next):
        """
        Process the request through security checks
        """
        start_time = time.time()
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied", "reason": "IP address blocked"}
            )
        
        # Validate API key if required
        api_key = self._extract_api_key(request)
        if not self._validate_api_key(api_key):
            # Allow health check and status endpoints without API key
            if request.url.path in ["/health", "/proxy/status", "/"]:
                pass
            else:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid or missing API key"}
                )
        
        # Check for suspicious patterns
        if self._detect_suspicious_activity(request):
            self.blocked_ips.add(client_ip)
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied", "reason": "Suspicious activity detected"}
            )
        
        # Log the request
        self._log_request(request, client_ip, user_agent, api_key)
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Security-Proxy"] = "enabled"
            response.headers["X-Request-ID"] = self._generate_request_id(request)
            
            # Log response time
            process_time = time.time() - start_time
            self._log_response(request, response, process_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Request processing error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """
        Extract API key from request headers or query parameters
        """
        # Check Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        # Check X-API-Key header
        api_key = request.headers.get("x-api-key")
        if api_key:
            return api_key
        
        # Check query parameter
        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key
        
        return None
    
    def _validate_api_key(self, api_key: Optional[str]) -> bool:
        """
        Validate the API key
        """
        if not api_key:
            return False
        
        # For now, accept any non-empty API key
        # In production, you would validate against a database or external service
        return len(api_key) > 0
    
    def _detect_suspicious_activity(self, request: Request) -> bool:
        """
        Detect suspicious patterns in requests
        """
        # Check for rapid requests from same IP
        client_ip = request.client.host if request.client else "unknown"
        recent_requests = [log for log in self.request_logs 
                          if log["ip"] == client_ip and 
                          time.time() - log["timestamp"] < 60]
        
        if len(recent_requests) > 100:  # More than 100 requests per minute
            return True
        
        # Check for suspicious user agents
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ["bot", "crawler", "spider", "scraper"]
        if any(agent in user_agent for agent in suspicious_agents):
            return True
        
        # Check for suspicious paths
        suspicious_paths = ["/admin", "/config", "/.env", "/wp-admin"]
        if any(path in request.url.path for path in suspicious_paths):
            return True
        
        return False
    
    def _log_request(self, request: Request, client_ip: str, user_agent: str, api_key: Optional[str]):
        """
        Log request details for security analysis
        """
        log_entry = {
            "timestamp": time.time(),
            "ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "user_agent": user_agent,
            "has_api_key": bool(api_key),
            "query_params": dict(request.query_params)
        }
        
        self.request_logs.append(log_entry)
        
        # Keep only last 1000 requests
        if len(self.request_logs) > 1000:
            self.request_logs = self.request_logs[-1000:]
    
    def _log_response(self, request: Request, response, process_time: float):
        """
        Log response details
        """
        log_entry = {
            "timestamp": time.time(),
            "ip": request.client.host if request.client else "unknown",
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": process_time
        }
        
        # You could store this in a database for analysis
        logger.info(f"Response logged: {log_entry}")
    
    def _generate_request_id(self, request: Request) -> str:
        """
        Generate a unique request ID
        """
        client_ip = request.client.host if request.client else "unknown"
        timestamp = str(time.time())
        user_agent = request.headers.get("user-agent", "")
        
        # Create a hash from request details
        request_string = f"{client_ip}:{timestamp}:{user_agent}"
        return hashlib.md5(request_string.encode()).hexdigest()[:16]
    
    def add_api_key(self, key: str, permissions: Dict[str, Any] = None):
        """
        Add a valid API key
        """
        self.api_keys[key] = {
            "permissions": permissions or {},
            "created_at": time.time()
        }
    
    def remove_api_key(self, key: str):
        """
        Remove an API key
        """
        self.api_keys.pop(key, None)
    
    def block_ip(self, ip: str):
        """
        Block an IP address
        """
        self.blocked_ips.add(ip)
    
    def unblock_ip(self, ip: str):
        """
        Unblock an IP address
        """
        self.blocked_ips.discard(ip)
    
    def get_security_stats(self) -> Dict[str, Any]:
        """
        Get security statistics
        """
        return {
            "total_api_keys": len(self.api_keys),
            "blocked_ips": len(self.blocked_ips),
            "recent_requests": len(self.request_logs),
            "blocked_ips_list": list(self.blocked_ips)
        }
