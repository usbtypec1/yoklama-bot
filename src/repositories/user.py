from sqlalchemy import select, update, exists
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User as DatabaseUser
from models.user import User


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.__session = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        user = await self.__session.get(DatabaseUser, user_id)
        if user is None:
            return None
        return User(
            id=user.id,
            student_number=user.student_number,
            encrypted_password=user.encrypted_password,
            has_accepted_terms=user.has_accepted_terms,
        )

    async def get_users_with_credentials(self) -> list[User]:
        statement = select(DatabaseUser).where(
            DatabaseUser.student_number.isnot(None),
            DatabaseUser.encrypted_password.isnot(None),
        )
        result = await self.__session.execute(statement)
        return [
            User(
                id=user.id,
                student_number=user.student_number,
                encrypted_password=user.encrypted_password,
                has_accepted_terms=user.has_accepted_terms,
            )
            for user in result.scalars().all()
        ]

    async def get_user_with_credentials_by_id(
        self,
        user_id: int,
    ) -> User | None:
        statement = select(DatabaseUser).where(
            DatabaseUser.id == user_id,
            DatabaseUser.student_number.isnot(None),
            DatabaseUser.encrypted_password.isnot(None),
        )
        result = await self.__session.execute(statement)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return User(
            id=user.id,
            student_number=user.student_number,
            encrypted_password=user.encrypted_password,
            has_accepted_terms=user.has_accepted_terms,
        )

    async def create_user(self, user_id: int) -> None:
        statement = insert(DatabaseUser).values(
            id=user_id,
            has_accepted_terms=True,
        ).on_conflict_do_nothing()
        async with self.__session.begin():
            await self.__session.execute(statement)

    async def update_user_credentials(
        self,
        user_id: int,
        student_number: str,
        encrypted_password: str,
    ) -> bool:
        user = await self.__session.get(DatabaseUser, user_id)
        if user is None:
            return False
        user.student_number = student_number
        user.encrypted_password = encrypted_password
        await self.__session.commit()
        return True
