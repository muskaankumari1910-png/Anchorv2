"""
Sprint 8: Workspace context management for multi-tenancy.

Provides utilities to:
1. Extract workspace_id from request headers
2. Validate workspace access
3. Default to "default" workspace for backward compatibility
"""
from fastapi import Header, HTTPException
from typing import Optional

DEFAULT_WORKSPACE_ID = "default"

def get_workspace_id(
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> str:
    """
    Extract workspace_id from request header.
    
    Usage in route:
        @app.get("/api/requirements")
        def get_requirements(workspace_id: str = Depends(get_workspace_id)):
            # workspace_id is now available
    
    Header: X-Workspace-ID
    Default: "default" (for backward compatibility)
    """
    return x_workspace_id or DEFAULT_WORKSPACE_ID


def get_workspace_id_required(
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> str:
    """
    Extract workspace_id from request header (REQUIRED).
    
    Raises 400 if no workspace_id provided.
    Use this for new V2-only endpoints.
    """
    if not x_workspace_id:
        raise HTTPException(
            status_code=400,
            detail="X-Workspace-ID header is required"
        )
    return x_workspace_id


class WorkspaceContext:
    """
    Context manager for workspace operations.
    Ensures all queries are scoped to the correct workspace.
    """
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
    
    def validate_access(self, resource_workspace_id: str) -> bool:
        """
        Verify that a resource belongs to the current workspace.
        
        Returns True if access allowed, False otherwise.
        Prevents cross-workspace data leakage.
        """
        return resource_workspace_id == self.workspace_id
    
    def ensure_access(self, resource_workspace_id: str):
        """
        Ensure access to a resource, raise 403 if denied.
        """
        if not self.validate_access(resource_workspace_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Resource belongs to different workspace"
            )


# Workspace scoping helpers for queries
def scope_query_to_workspace(query, model, workspace_id: str):
    """
    Add workspace filter to a SQLAlchemy query.
    
    Usage:
        query = db.query(Requirement)
        query = scope_query_to_workspace(query, Requirement, workspace_id)
    """
    return query.filter(model.workspace_id == workspace_id)
