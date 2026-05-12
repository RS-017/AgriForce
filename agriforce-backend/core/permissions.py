from fastapi import Depends, HTTPException, status
from core.auth import get_current_user
from models.users import User, UserRole


def _require_role(role: UserRole):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to {role.value} role",
            )
        return current_user
    return checker


require_farmer = _require_role(UserRole.FARMER)
require_worker = _require_role(UserRole.WORKER)
require_equipment_provider = _require_role(UserRole.EQUIPMENT_PROVIDER)
require_admin = _require_role(UserRole.ADMIN)
