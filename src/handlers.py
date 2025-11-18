from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from src.database_gateway import get_database_connection, DatabaseGateway
from src.obis import create_http_client, ObisClient, ObisClientNotLoggedInError


router = Router(name=__name__)


class CredentialsStates(StatesGroup):
    student_number = State()
    obis_password = State()


@router.message(F.text, StateFilter(CredentialsStates.obis_password))
async def on_obis_password_entered(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    student_number = data.get("student_number")
    obis_password = message.text
    await state.clear()

    async with create_http_client() as http_client:
        obis_client = ObisClient(
            student_number=student_number, password=obis_password,
            http_client=http_client,
        )
        await obis_client.login()
        try:
            await obis_client.get_taken_lessons_page()
        except ObisClientNotLoggedInError:
            await message.answer(
                "Не удалось войти в OBIS с предоставленными данными. Пожалуйста, проверьте их и попробуйте снова.",
            )
            return

    with get_database_connection() as connection:
        gateway = DatabaseGateway(connection)
        gateway.update_user_credentials(
            user_id=message.from_user.id,
            student_number=student_number,
            password=obis_password,
        )

    await message.answer("Ваши данные от OBIS успешно сохранены.")


@router.message(F.text, StateFilter(CredentialsStates.student_number))
async def on_student_number_entered(
    message: Message,
    state: FSMContext,
) -> None:
    await state.update_data(student_number=message.text)
    await state.set_state(CredentialsStates.obis_password)
    await message.answer("Введите ваш пароль от OBIS:")


@router.message(F.text == "Ввести данные от OBIS")
async def on_credentials_command(message: Message, state: FSMContext) -> None:
    await state.set_state(CredentialsStates.student_number)
    await message.answer("Введите ваш студ.номер:")


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        is_persistent=True,
        keyboard=[
            [
                KeyboardButton(text="Ввести данные от OBIS"),
            ]
        ],
    )
    await message.answer(
        "Добро пожаловать! Пожалуйста, введите ваши данные от OBIS, чтобы начать получать уведомления о вашей йокламе.",
        reply_markup=markup,
    )
    with get_database_connection() as connection:
        gateway = DatabaseGateway(connection)
        gateway.init_tables()
        gateway.insert_user(message.from_user.id)
