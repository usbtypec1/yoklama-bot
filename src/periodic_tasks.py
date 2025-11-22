import asyncio

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from db.gateway import create_database_gateway
from formatters import format_lesson_attendance_change
from obis.gateway import create_obis_client
from obis.models import LessonAttendance
from obis.services import compute_lesson_skip_opportunities


class LessonAttendanceCheckTask:

    def __init__(self, bot: Bot):
        self.__bot = bot

    async def execute(self) -> None:
        async with create_database_gateway() as database_gateway:
            users = await database_gateway.get_users_with_credentials()

        for user in users:
            async with create_obis_client(
                student_number=user.student_number,
                password=user.encrypted_password,
            ) as obis_client:
                await obis_client.login()
                attendance_list = await obis_client.get_lessons_attendance_list()

            old_and_new_attendance_list: list[
                tuple[LessonAttendance, LessonAttendance]] = []
            async with create_database_gateway() as database_gateway:

                for lesson_attendance in attendance_list:
                    previous_attendance = await database_gateway.get_last_lessons_attendance(
                        user_id=user.id,
                        lesson_code=lesson_attendance.lesson_code,
                    )
                    if previous_attendance != lesson_attendance:
                        await database_gateway.create_lesson_attendance(
                            user_id=user.id,
                            lesson_attendance=lesson_attendance,
                        )
                        old_and_new_attendance_list.append(
                            (previous_attendance, lesson_attendance),
                        )

            if old_and_new_attendance_list:
                for old_attendance, new_attendance in old_and_new_attendance_list:
                    lesson_skip_opportunity = compute_lesson_skip_opportunities(
                        new_attendance,
                    )
                    text = format_lesson_attendance_change(
                        old_lesson_attendance=old_attendance,
                        new_lesson_attendance=new_attendance,
                        lesson_skip_opportunity=lesson_skip_opportunity,
                    )
                    try:
                        await self.__bot.send_message(
                            chat_id=user.id,
                            text=text,
                            parse_mode=ParseMode.HTML,
                        )
                    except TelegramAPIError:
                        pass
                    finally:
                        await asyncio.sleep(0.5)
