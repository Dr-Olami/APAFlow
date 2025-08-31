"""
Cerbos policy integration for fine-grained authorization
"""
import requests
import json
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class CerbosClient:
    def __init__(self, cerbos_url: str = "http://localhost:3593"):
        self.cerbos_url = cerbos_url.rstrip('/')
        self.api_url = f"{self.cerbos_url}/api/check"
    
    def check_permission(
        self, 
        principal_id: str, 
        resource_kind: str, 
        resource_id: str, 
        action: str,
        principal_roles: List[str] = None,
        resource_attributes: Dict = None
    ) -> bool:
        """
        Check if principal has permission to perform action on resource
        """
        payload = {
            "requestId": f"req_{principal_id}_{resource_id}_{action}",
            "principal": {
                "id": principal_id,
                "roles": principal_roles or []
            },
            "resource": {
                "kind": resource_kind,
                "id": resource_id,
                "attributes": resource_attributes or {}
            },
            "actions": [action]
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("results", [{}])[0].get("isAllowed", False)
            
        except Exception as e:
            logger.error(f"Cerbos permission check failed: {e}")
            return False
    
    def bulk_check_permissions(
        self,
        principal_id: str,
        principal_roles: List[str],
        checks: List[Dict]
    ) -> Dict[str, bool]:
        """
        Perform bulk permission checks
        """
        results = {}
        
        for check in checks:
            resource_kind = check.get("resource_kind")
            resource_id = check.get("resource_id")
            action = check.get("action")
            resource_attributes = check.get("resource_attributes", {})
            
            key = f"{resource_kind}:{resource_id}:{action}"
            results[key] = self.check_permission(
                principal_id,
                resource_kind,
                resource_id,
                action,
                principal_roles,
                resource_attributes
            )
        
        return results

# Example policy decorator
def require_permission(resource_kind: str, action: str):
    """
    Decorator to enforce Cerbos permissions
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract user context (implement based on your auth system)
            user_id = kwargs.get('user_id')
            user_roles = kwargs.get('user_roles', [])
            resource_id = kwargs.get('resource_id')
            
            if not user_id or not resource_id:
                raise ValueError("Missing user_id or resource_id")
            
            cerbos = CerbosClient()
            if not cerbos.check_permission(user_id, resource_kind, resource_id, action, user_roles):
                raise PermissionError(f"Access denied for {action} on {resource_kind}:{resource_id}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
