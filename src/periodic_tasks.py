import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from dishka import AsyncContainer

from formatters import format_lesson_attendance_change
from models.user import User
from services.obis import compute_lesson_skip_opportunities
from services.user import UserService


logger = logging.getLogger(__name__)


class LessonAttendanceCheckTask:

    def __init__(self, container: AsyncContainer):
        self.__container = container

    async def _process_user(
        self,
        user: User,
        user_service: UserService,
        bot: Bot,
    ) -> None:
        logger.info("Checking lesson attendance for user %s", user.id)
        changes = await user_service.get_attendance_changes(user_id=user.id)

        for attendance_change in changes:
            if attendance_change.previous is None:
                await user_service.save_attendance_change(attendance_change)
                logger.info(
                    "Saved first attendance change for user %s", user.id,
                )
                continue
            text = format_lesson_attendance_change(
                old_lesson_attendance=attendance_change.previous,
                new_lesson_attendance=attendance_change.current,
                lesson_skip_opportunity=compute_lesson_skip_opportunities(
                    attendance_change.current,
                ),
            )
            try:
                await bot.send_message(
                    chat_id=user.id,
                    text=text,
                )
            except TelegramAPIError:
                logger.error(
                    "Could not send attendance change to user %s", user.id,
                )
            else:
                await user_service.save_attendance_change(attendance_change)
                logger.info(
                    "Successfully sent attendance change to user %s", user.id,
                )
            finally:
                await asyncio.sleep(0.1)

    async def execute(self) -> None:
        bot = await self.__container.get(Bot)
        async with self.__container() as nested_container:
            user_service = await nested_container.get(UserService)
            users = await user_service.get_users_with_credentials()

            for user in users:
                try:
                    await self._process_user(user, user_service, bot)
                except Exception as e:
                    logger.exception("Error processing user %s: %s", user.id, e)
