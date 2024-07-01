from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.crud_base import CRUDBase
from app.model.base_model import User
from app.schema.auth_schema import UserCreate, UserUpdate
from app.util.hash import async_hash_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_by_username(
        self, db: AsyncSession, *, username: str
    ) -> Optional[User]:
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        create_data = dict(obj_in)
        create_data.pop("password")
        db_obj = User(**create_data)
        db_obj.password = async_hash_password(obj_in.password)
        
        created_user = await super().create(db, obj_in=db_obj)
        return created_user

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]],
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = dict(obj_in)

        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        email: Optional[str] = None,
        username: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        base_query = select(User)
        if email:
            base_query = base_query.filter(User.email.ilike(f"%{email}%"))
        if username:
            base_query = base_query.filter(User.username.ilike(f"%{username}%"))

        users = await self.get_multi(db, skip=skip, limit=limit, query=base_query)
        return users


user_crud = CRUDUser(User)
