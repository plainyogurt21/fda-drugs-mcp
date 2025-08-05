"""
Configuration settings for FDA Drugs MCP Server
"""

import os
from typing import Dict, Any, Optional

class Config:
    """Configuration class for FDA Drugs MCP Server."""
    
    # FDA API Configuration
    FDA_API_BASE_URL = "https://api.fda.gov"
    FDA_API_ENDPOINTS = {
        'label': f"{FDA_API_BASE_URL}/drug/label.json",
        'ndc': f"{FDA_API_BASE_URL}/drug/ndc.json", 
        'drugsfda': f"{FDA_API_BASE_URL}/drug/drugsfda.json"
    }
    
    # API Key Configuration
    FDA_API_KEY = os.getenv('FDA_API_KEY', 'mpORfvSB8yDvTm1hD4Ud1snpNSsDwCY6u2W7qpdl')
    
    # API key can also be passed at runtime
    _runtime_api_key: Optional[str] = None
    
    # Rate limiting
    API_RATE_LIMIT_DELAY = 0.1  # 100ms between requests
    API_TIMEOUT = 30  # seconds
    
    # Default query limits
    DEFAULT_SEARCH_LIMIT = 50
    MAX_SEARCH_LIMIT = 100
    
    # Application type filters
    APPROVED_APP_TYPES = ['BLA', 'NDA']  # Exclude ANDA by default
    ALL_APP_TYPES = ['BLA', 'NDA', 'ANDA']
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Server configuration
    SERVER_NAME = "FDA Drugs MCP Server"
    SERVER_VERSION = "1.0.0"
    
    @classmethod
    def get_api_config(cls) -> Dict[str, Any]:
        """Get API configuration settings."""
        return {
            'base_url': cls.FDA_API_BASE_URL,
            'endpoints': cls.FDA_API_ENDPOINTS,
            'api_key': cls.get_api_key(),
            'rate_limit_delay': cls.API_RATE_LIMIT_DELAY,
            'timeout': cls.API_TIMEOUT,
            'default_limit': cls.DEFAULT_SEARCH_LIMIT,
            'max_limit': cls.MAX_SEARCH_LIMIT
        }
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get the FDA API key."""
        return cls._runtime_api_key or cls.FDA_API_KEY
    
    @classmethod
    def set_api_key(cls, api_key: str) -> None:
        """Set the API key at runtime."""
        cls._runtime_api_key = api_key
    
    @classmethod
    def get_server_info(cls) -> Dict[str, Any]:
        """Get server information."""
        return {
            'name': cls.SERVER_NAME,
            'version': cls.SERVER_VERSION
        }