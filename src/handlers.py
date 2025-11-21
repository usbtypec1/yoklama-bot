from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from database_gateway import get_database_connection, DatabaseGateway
from obis import (
    create_http_client,
    ObisClient,
    ObisClientNotLoggedInError,
    compute_lesson_skipping_opportunities,
)


router = Router(name=__name__)

MAIN_MENU = ReplyKeyboardMarkup(
    resize_keyboard=True,
    is_persistent=True,
    keyboard=[
        [
            KeyboardButton(text="Моя йоклама"),
            KeyboardButton(text="Экзамены"),
        ],
        [
            KeyboardButton(text="Ввести данные от OBIS"),
        ],
    ],
)


class CredentialsStates(StatesGroup):
    student_number = State()
    obis_password = State()


@router.message(F.text == "Экзамены")
async def on_view_exams_command(message: Message) -> None:
    with get_database_connection() as connection:
        gateway = DatabaseGateway(connection)
        user = gateway.get_user_by_id(message.from_user.id)

    if user is None:
        await message.answer(
            "Пожалуйста, для начала введите ваши данные от OBIS.",
            reply_markup=MAIN_MENU,
        )
        return

    message = await message.answer("Загрузка ваших экзаменов...")
    async with create_http_client() as http_client:
        obis_client = ObisClient(
            student_number=user.student_number,
            password=user.password,
            http_client=http_client,
        )
        await obis_client.login()
        try:
            lessons_with_exams = await obis_client.get_exams_page()
        except ObisClientNotLoggedInError:
            await message.edit_text(
                "Не удалось войти в OBIS с предоставленными данными. Пожалуйста, проверьте их и попробуйте снова.",
            )
            return

        text = ""
        for lesson in lessons_with_exams:
            text += f"<b>{lesson.lesson_name} ({lesson.lesson_code})</b>\n"
            for exam in lesson.exams:
                text += f" - {exam.name}: {exam.score or ''}\n"
            text += "\n"

        if not text:
            text = "У вас нет оценок за экзамены."
        await message.edit_text(text.strip())


@router.message(F.text == "Йоклама")
async def on_view_yoklama_command(message: Message) -> None:
    with get_database_connection() as connection:
        gateway = DatabaseGateway(connection)
        user = gateway.get_user_by_id(message.from_user.id)

    if user is None:
        await message.answer(
            "Пожалуйста, для начала введите ваши данные от OBIS.",
            reply_markup=MAIN_MENU,
        )
        return

    message = await message.answer("Загрузка вашей йокламы...")
    async with create_http_client() as http_client:
        obis_client = ObisClient(
            student_number=user.student_number,
            password=user.password,
            http_client=http_client,
        )
        await obis_client.login()
        try:
            lessons = await obis_client.get_taken_lessons_page()
        except ObisClientNotLoggedInError:
            await message.edit_text(
                "Не удалось войти в OBIS с предоставленными данными. Пожалуйста, проверьте их и попробуйте снова.",
            )
            return

        text = ""
        for lesson in lessons:
            skipping = compute_lesson_skipping_opportunities(lesson)
            text += (
                f"<b>{lesson.name}</b>\n"
                f"Теория: {lesson.theory_skipped_classes_percentage}% пропущено (осталось {skipping.theory} пропусков)\n"
                f"Практика: {lesson.practice_skipped_classes_percentage}% пропущено (осталось {skipping.practice} пропусков)\n\n"
            )

        if not text:
            text = "У вас нет предметов."
        await message.edit_text(text.strip())


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
            student_number=student_number,
            password=obis_password,
            http_client=http_client,
        )
        await obis_client.login()
        try:
            await obis_client.get_taken_lessons_page()
        except ObisClientNotLoggedInError:
            await message.answer(
                "Не удалось войти в OBIS с предоставленными данными. Пожалуйста, проверьте их и попробуйте снова.",
                reply_markup=MAIN_MENU,
            )
            return

    with get_database_connection() as connection:
        gateway = DatabaseGateway(connection)
        gateway.update_user_credentials(
            user_id=message.from_user.id,
            student_number=student_number,
            password=obis_password,
        )

    await message.answer(
        "Ваши данные от OBIS успешно сохранены.",
        reply_markup=MAIN_MENU,
    )


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
    await message.answer(
        "Введите ваш студ.номер:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(
        "Добро пожаловать! Пожалуйста, введите ваши данные от OBIS, чтобы начать получать уведомления о вашей йокламе.",
        reply_markup=MAIN_MENU,
    )
    with get_database_connection() as connection:
        gateway = DatabaseGateway(connection)
        gateway.init_tables()
        gateway.insert_user(message.from_user.id)
