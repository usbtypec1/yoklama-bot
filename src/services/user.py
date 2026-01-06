from exceptions.user import UserHasNoCredentialsError
from models.obis import LessonExams, LessonAttendance
from repositories.user import UserRepository
from services.crypto import PasswordCryptor
from services.obis import ObisService


class UserService:

    def __init__(
        self,
        user_repository: UserRepository,
        password_cryptor: PasswordCryptor,
        obis_service: ObisService,
    ):
        self.__user_repository = user_repository
        self.__password_cryptor = password_cryptor
        self.__obis_service = obis_service

    async def update_user_credentials(
        self,
        *,
        user_id: int,
        student_number: str,
        password: str,
    ) -> bool:
        encrypted_password = self.__password_cryptor.encrypt(password)
        return await self.__user_repository.update_user_credentials(
            user_id=user_id,
            student_number=student_number,
            encrypted_password=encrypted_password,
        )

    async def get_exams(self, user_id: int) -> list[LessonExams]:
        user = await self.__user_repository.get_user_with_credentials_by_id(
            user_id=user_id,
        )
        if user is None:
            raise UserHasNoCredentialsError
        plain_password = self.__password_cryptor.decrypt(
            user.encrypted_password,
        )
        await self.__obis_service.login(user.student_number, plain_password)
        return await self.__obis_service.get_lesson_exams()

    async def get_attendance(self, user_id: int) -> list[LessonAttendance]:
        user = await self.__user_repository.get_user_with_credentials_by_id(
            user_id=user_id,
        )
        if user is None:
            raise UserHasNoCredentialsError
        plain_password = self.__password_cryptor.decrypt(
            user.encrypted_password,
        )
        await self.__obis_service.login(user.student_number, plain_password)
        return await self.__obis_service.get_lessons_attendance()
