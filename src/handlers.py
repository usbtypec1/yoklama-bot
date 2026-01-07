from typing import Annotated

from aiogram import Router, F
from aiogram.filters import CommandStart, ExceptionTypeFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    CallbackQuery, WebAppInfo, ErrorEvent,
)
from dishka import FromDishka
from pydantic import BaseModel, Field

from exceptions.obis import ObisClientNotLoggedInError
from exceptions.user import UserHasNoCredentialsError
from formatters import format_exams_list, format_attendance_list
from repositories.user import UserRepository
from services.user import UserService


router = Router(name=__name__)

WEB_APP_BUTTON = KeyboardButton(
    text="Ввести данные от OBIS", web_app=WebAppInfo(
        url="https://yoklama-bot-mini-app.vercel.app/enter-credentials",
    ),
)

MAIN_MENU = ReplyKeyboardMarkup(
    resize_keyboard=True,
    is_persistent=True,
    keyboard=[
        [
            KeyboardButton(text="Йоклама"),
            KeyboardButton(text="Экзамены"),
        ],
        [
            WEB_APP_BUTTON
        ]
    ],
)

UNAUTHORIZED_MENU = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            WEB_APP_BUTTON,
        ]
    ],
)


class CredentialsStates(StatesGroup):
    student_number = State()
    obis_password = State()


@router.error(ExceptionTypeFilter(
    UserHasNoCredentialsError,
    ObisClientNotLoggedInError,
))
async def on_user_has_no_credentials_error(
    event: ErrorEvent,
) -> None:
    await event.update.message.answer(
        "📲 Чтобы использовать бота, введите ваши данные от OBIS.",
        reply_markup=UNAUTHORIZED_MENU,
    )


@router.callback_query(F.data == "accept_terms")
async def on_accept_terms(
    callback_query: CallbackQuery,
    user_repository: FromDishka[UserRepository],
) -> None:
    await user_repository.create_user(callback_query.from_user.id)
    await callback_query.message.edit_text(
        "✅ Вы успешно приняли условия использования бота.",
    )
    await callback_query.message.answer(
        "📲 Главное меню.",
        reply_markup=MAIN_MENU,
    )


@router.message(CommandStart())
async def on_start(
    message: Message,
    user_repository: FromDishka[UserRepository],
) -> None:
    user = await user_repository.get_user_by_id(message.from_user.id)
    if user is None:
        await message.answer(
            "📲 Чтобы использовать бота, введите ваши данные от OBIS.",
            reply_markup=UNAUTHORIZED_MENU,
        )
        return
    await message.answer(
        "📲 Главное меню.",
        reply_markup=MAIN_MENU,
    )


@router.message(F.text == "Экзамены")
async def on_view_exams_command(
    message: Message,
    user_service: FromDishka[UserService],
) -> None:
    sent_message = await message.answer("⌛ Загрузка ваших экзаменов...")
    exams = await user_service.get_exams(message.from_user.id)
    text = format_exams_list(exams)
    await sent_message.edit_text(text)


@router.message(F.text == "Йоклама")
async def on_view_yoklama_command(
    message: Message,
    user_service: FromDishka[UserService],
) -> None:
    sent_message = await message.answer("⌛ Загрузка вашей йокламы...")
    attendance = await user_service.get_attendance(message.from_user.id)
    text = format_attendance_list(attendance)
    await sent_message.edit_text(text)


class Credentials(BaseModel):
    student_number: Annotated[str, Field(validation_alias="studentNumber")]
    password: str


@router.message(
    F.web_app_data.button_text == "Ввести данные от OBIS",
)
async def on_obis_password_entered(
    message: Message,
    user_service: FromDishka[UserService],
) -> None:
    credentials = Credentials.model_validate_json(message.web_app_data.data)
    await user_service.save_user(
        user_id=message.from_user.id,
        student_number=credentials.student_number,
        password=credentials.password,
    )
    await message.answer(
        "✅ Ваши данные от OBIS успешно сохранены.",
    )
    await message.answer(
        "📲 Главное меню.",
        reply_markup=MAIN_MENU,
    )
