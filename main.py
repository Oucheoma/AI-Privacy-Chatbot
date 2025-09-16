from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from routes import router
import os
import httpx
import json
from typing import Dict, Any
from middleware.security import SecurityMiddleware
from services.proxy_service import ProxyService

app = FastAPI(title="Secure AI Proxy Gateway")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Include the API routes
app.include_router(router)

# Set up templates for the web interface
templates = Jinja2Templates(directory="templates")

# Initialize proxy service
proxy_service = ProxyService()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Secure AI Proxy Gateway"}

@app.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_request(request: Request, path: str):
    """
    Main proxy endpoint that forwards requests to various AI services
    """
    try:
        # Get the target service from query parameters or headers
        target_service = request.query_params.get("target", "openrouter")
        
        # Forward the request to the appropriate service
        response = await proxy_service.forward_request(request, path, target_service)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

@app.post("/proxy/chat")
async def proxy_chat(request: Request):
    """
    Specialized chat endpoint for AI conversations
    """
    try:
        body = await request.json()
        target_service = body.get("target", "openrouter")
        
        response = await proxy_service.forward_chat_request(request, body, target_service)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat proxy error: {str(e)}")

@app.get("/proxy/status")
async def proxy_status():
    """Get proxy status and available services"""
    return {
        "status": "operational",
        "available_services": proxy_service.get_available_services(),
        "active_connections": proxy_service.get_active_connections(),
        "security_enabled": True
    }
