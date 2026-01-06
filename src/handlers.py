from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
)
from dishka import FromDishka

from exceptions.obis import ObisClientNotLoggedInError
from exceptions.user import UserHasNoCredentialsError
from formatters import format_exams_list, format_attendance_list
from repositories.user import UserRepository
from services.obis import ObisService
from services.user import UserService


router = Router(name=__name__)

MAIN_MENU = ReplyKeyboardMarkup(
    resize_keyboard=True,
    is_persistent=True,
    keyboard=[
        [
            KeyboardButton(text="Йоклама"),
            KeyboardButton(text="Экзамены"),
        ],
        [
            KeyboardButton(text="Ввести данные от OBIS"),
        ]
    ],
)


class CredentialsStates(StatesGroup):
    student_number = State()
    obis_password = State()


@router.callback_query(F.data == "accept_terms")
async def on_accept_terms(
    callback_query: CallbackQuery,
    user_repository: FromDishka[UserRepository],
) -> None:
    await user_repository.create_user(callback_query.from_user.id)
    await callback_query.message.edit_text("✅ Вы успешно приняли условия использования бота.")
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
    if user is None or not user.has_accepted_terms:
        await message.answer(
            "Для использования бота необходимо принять условия использования: *<a href=\"https://graph.org/Polzovatelskoe-soglashenie-manas-yoklama-bot-01-06\">ссылка</a>*.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Принять условия",
                            callback_data="accept_terms",
                        )
                    ]
                ],
            ),
        )
        return
    await message.answer(
        "📲 Главное меню.",
        reply_markup=MAIN_MENU,
    )
    await user_repository.create_user(message.from_user.id)


@router.message(F.text == "Экзамены")
async def on_view_exams_command(
    message: Message,
    user_service: FromDishka[UserService],
) -> None:
    sent_message = await message.answer("⌛ Загрузка ваших экзаменов...")

    try:
        exams = await user_service.get_exams(message.from_user.id)
    except UserHasNoCredentialsError:
        await message.answer(
            "❗ Для начала введите ваши данные от OBIS.",
            reply_markup=MAIN_MENU,
        )
        await sent_message.delete()
        return
    except ObisClientNotLoggedInError:
        await sent_message.edit_text(
            "❌ Не удалось войти в OBIS с предоставленными данными. Пожалуйста, проверьте их и попробуйте снова.",
        )
        return

    text = format_exams_list(exams)
    await sent_message.edit_text(text)


@router.message(F.text == "Йоклама")
async def on_view_yoklama_command(
    message: Message,
    user_service: FromDishka[UserService],
) -> None:
    sent_message = await message.answer("⌛ Загрузка вашей йокламы...")
    try:
        attendance = await user_service.get_attendance(message.from_user.id)
    except UserHasNoCredentialsError:
        await sent_message.answer(
            "❗ Для начала введите ваши данные от OBIS.",
            reply_markup=MAIN_MENU,
        )
        await message.delete()
        return
    except ObisClientNotLoggedInError:
        await sent_message.edit_text(
            "❌ Не удалось войти в OBIS с предоставленными данными. Пожалуйста, проверьте их и попробуйте снова.",
        )
        return

    text = format_attendance_list(attendance)
    await sent_message.edit_text(text)


@router.message(
    F.text, F.text != "Ввести данные от OBIS",
    StateFilter(CredentialsStates.obis_password),
)
async def on_obis_password_entered(
    message: Message,
    state: FSMContext,
    obis_service: FromDishka[ObisService],
    user_service: FromDishka[UserService],
) -> None:
    data = await state.get_data()
    student_number = data.get("student_number")
    obis_password = message.text
    await state.clear()
    sent_message = await message.answer("🔒 Проверка введённых данных...")

    try:
        await obis_service.login(student_number, obis_password)
    except ObisClientNotLoggedInError:
        await sent_message.edit_text(
            "❌ Не удалось войти в OBIS с предоставленными данными. Пожалуйста, проверьте их и попробуйте снова.",
        )
        return

    updated = await user_service.update_user_credentials(
        user_id=message.from_user.id,
        student_number=student_number,
        password=obis_password,
    )
    if not updated:
        await sent_message.edit_text(
            "❌ Произошла ошибка при сохранении ваших данных. Пожалуйста, попробуйте снова позже.",
        )
        return

    await sent_message.edit_text(
        "✅ Ваши данные от OBIS успешно сохранены.",
    )


@router.message(
    F.text, F.text != "Ввести данные от OBIS",
    StateFilter(CredentialsStates.student_number),
)
async def on_student_number_entered(
    message: Message,
    state: FSMContext,
) -> None:
    await state.update_data(
        student_number=message.text.removesuffix("@manas.edu.kg"),
    )
    await state.set_state(CredentialsStates.obis_password)
    await message.answer("✏️ Введите ваш пароль от OBIS:")


@router.message(F.text == "Ввести данные от OBIS")
async def on_credentials_command(message: Message, state: FSMContext) -> None:
    await state.set_state(CredentialsStates.student_number)
    await message.answer("✏️ Введите ваш студ.номер:")
