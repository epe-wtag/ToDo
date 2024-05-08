from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user_role, get_current_user




def admin_check(user_role: str = Depends(get_current_user_role)):
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to perform this action",
        )
        
        
