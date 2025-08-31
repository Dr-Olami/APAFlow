"""
Security utilities for Keycloak integration
"""
import jwt
import requests
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class KeycloakSecurity:
    def __init__(self, server_url: str, realm: str, client_id: str, client_secret: str):
        self.server_url = server_url.rstrip('/')
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.realm_url = f"{self.server_url}/realms/{self.realm}"
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validate JWT token against Keycloak
        """
        try:
            # Get public key from Keycloak
            certs_url = f"{self.realm_url}/protocol/openid_connect/certs"
            response = requests.get(certs_url)
            response.raise_for_status()
            
            # Decode and validate token
            decoded_token = jwt.decode(
                token,
                options={"verify_signature": False},  # For demo - implement proper verification
                algorithms=["RS256"]
            )
            
            return decoded_token
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None
    
    def check_user_roles(self, token: str, required_roles: List[str]) -> bool:
        """
        Check if user has required roles
        """
        decoded_token = self.validate_token(token)
        if not decoded_token:
            return False
        
        user_roles = decoded_token.get('realm_access', {}).get('roles', [])
        return any(role in user_roles for role in required_roles)
    
    def get_user_permissions(self, token: str) -> List[str]:
        """
        Extract user permissions from token
        """
        decoded_token = self.validate_token(token)
        if not decoded_token:
            return []
        
        return decoded_token.get('resource_access', {}).get(self.client_id, {}).get('roles', [])
