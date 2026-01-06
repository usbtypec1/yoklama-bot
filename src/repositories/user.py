from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.__session = session

    async def get_user_ids(self) -> list[int]:
        statement = select(User.id).distinct()
        result = await self.__session.execute(statement)
        return [row[0] for row in result.fetchall()]

    async def get_users_with_credentials(self) -> list:
        statement = select(User).where(User.student_number.isnot(None), User.encrypted_password.isnot(None))
        result = await self.__session.execute(statement)
        return result.scalars().all()