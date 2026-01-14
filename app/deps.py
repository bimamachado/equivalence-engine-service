from fastapi import Request, HTTPException

def get_tenant_id(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return tenant_id

def get_role(request: Request) -> str:
    role = getattr(request.state, "role", None)
    if not role:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return role

def require_role(*allowed_roles: str):
    def _dep(role: str = Depends(get_role)):
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return role
    return _dep