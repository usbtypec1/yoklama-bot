from exceptions.user import (
    UserHasNoCredentialsError,
    UserNotAcceptedTermsError,
)
from models.lesson_grade import LessonGradeChange
from models.obis import (
    LessonExams, LessonAttendance, LessonAttendanceChange,
)
from models.user import User
from repositories.lesson import LessonRepository
from repositories.lesson_attendance import LessonAttendanceRepository
from repositories.lesson_grade import LessonGradeRepository
from repositories.user import UserRepository
from services.crypto import PasswordCryptor
from services.obis import ObisService


class UserService:

    def __init__(
        self,
        user_repository: UserRepository,
        password_cryptor: PasswordCryptor,
        obis_service: ObisService,
        lesson_attendance_repository: LessonAttendanceRepository,
        lesson_repository: LessonRepository,
        lesson_grade_repository: LessonGradeRepository,
    ):
        self.__user_repository = user_repository
        self.__password_cryptor = password_cryptor
        self.__obis_service = obis_service
        self.__lesson_attendance_repository = lesson_attendance_repository
        self.__lesson_repository = lesson_repository
        self.__lesson_grade_repository = lesson_grade_repository

    async def save_user(
        self,
        *,
        user_id: int,
        student_number: str,
        password: str,
    ) -> None:
        encrypted_password = self.__password_cryptor.encrypt(password)
        await self.__user_repository.save_user(
            user_id=user_id,
            student_number=student_number,
            encrypted_password=encrypted_password,
        )

    async def get_exams(self, user_id: int) -> list[LessonExams]:
        user = await self.__user_repository.get_user_by_id(
            user_id=user_id,
        )
        if user is None:
            raise UserHasNoCredentialsError
        if not user.has_accepted_terms:
            raise UserNotAcceptedTermsError
        plain_password = self.__password_cryptor.decrypt(
            user.encrypted_password,
        )
        await self.__obis_service.login(user.student_number, plain_password)
        return await self.__obis_service.get_lesson_exams()

    async def get_attendance(
        self,
        user_id: int,
    ) -> list[LessonAttendance]:
        user = await self.__user_repository.get_user_by_id(
            user_id=user_id,
        )
        if user is None:
            raise UserHasNoCredentialsError
        if not user.has_accepted_terms:
            raise UserNotAcceptedTermsError
        plain_password = self.__password_cryptor.decrypt(
            user.encrypted_password,
        )
        await self.__obis_service.login(user.student_number, plain_password)
        lessons_attendance_parse_result = await self.__obis_service.get_lessons_attendance()
        return [
            LessonAttendance(
                user_id=user_id,
                lesson_name=lesson.lesson_name,
                lesson_code=lesson.lesson_code,
                theory_skips_percentage=lesson.theory_skips_percentage,
                practice_skips_percentage=lesson.practice_skips_percentage,
            )
            for lesson in lessons_attendance_parse_result
        ]

    async def get_users(self) -> list[User]:
        return await self.__user_repository.get_users()

    async def get_attendance_changes(
        self,
        *,
        user_id: int,
    ) -> list[LessonAttendanceChange]:
        lessons_attendance = await self.get_attendance(user_id)
        changed_attendances: list[LessonAttendanceChange] = []
        for lesson_attendance in lessons_attendance:
            last_attendance = await self.__lesson_attendance_repository.get_last_attendance(
                user_id=user_id,
                lesson_code=lesson_attendance.lesson_code,
            )
            no_history = last_attendance is None
            attendance_changed = last_attendance != lesson_attendance
            if no_history or attendance_changed:
                changed_attendances.append(
                    LessonAttendanceChange(
                        previous=last_attendance,
                        current=lesson_attendance,
                    ),
                )
        return changed_attendances

    async def save_attendance_change(
        self,
        attendance_change: LessonAttendanceChange,
    ) -> None:
        current_attendance = attendance_change.current
        await self.__lesson_repository.create_lesson(
            code=current_attendance.lesson_code,
            name=current_attendance.lesson_name,
        )
        await self.__lesson_attendance_repository.create_attendance(
            user_id=current_attendance.user_id,
            lesson_code=current_attendance.lesson_code,
            theory_skips_percentage=current_attendance.theory_skips_percentage,
            practice_skips_percentage=current_attendance.practice_skips_percentage,
        )

    async def accept_terms(self, user_id: int) -> None:
        await self.__user_repository.accept_terms(user_id)

    async def get_lesson_grade_changes(
        self,
        *,
        user_id: int,
    ) -> list[LessonGradeChange]:
        lessons_exams = await self.get_exams(user_id)
        changes: list[LessonGradeChange] = []
        for lesson_exams in lessons_exams:
            for exam in lesson_exams.exams:
                last_grade = await self.__lesson_grade_repository.get_last_grade(
                    lesson_code=lesson_exams.lesson_code,
                    user_id=user_id,
                )
                is_first_grade = last_grade is None
                score_changed = last_grade.score != exam.score
                if is_first_grade or score_changed:
                    change = LessonGradeChange(
                        user_id=user_id,
                        lesson_code=lesson_exams.lesson_code,
                        lesson_name=lesson_exams.lesson_name,
                        exam_name=exam.name,
                        previous_score=last_grade.score if last_grade else None,
                        current_score=exam.score,
                        is_first_grade=is_first_grade,
                    )
                    changes.append(change)
        return changes

    async def save_grade_change(self, grade_change: LessonGradeChange) -> None:
        await self.__lesson_repository.create_lesson(
            code=grade_change.lesson_code,
            name=grade_change.lesson_name,
        )
        await self.__lesson_grade_repository.create_grade(
            user_id=grade_change.user_id,
            lesson_code=grade_change.lesson_code,
            exam_name=grade_change.exam_name,
            score=grade_change.current_score,
        )
