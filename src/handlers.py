from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from crypto import PasswordCryptor
from db.gateway import create_database_gateway
from exceptions import ObisClientNotLoggedInError
from obis.gateway import create_obis_client
from obis.services import compute_lesson_skip_opportunities


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


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(
        "📲 Главное меню.",
        reply_markup=MAIN_MENU,
    )
    async with create_database_gateway() as database_gateway:
        await database_gateway.create_user(message.from_user.id)


@router.message(F.text == "Экзамены")
async def on_view_exams_command(
    message: Message,
    password_cryptor: PasswordCryptor,
) -> None:
    async with create_database_gateway() as database_gateway:
        user = await database_gateway.get_user_with_credentials_by_id(
            message.from_user.id,
        )

    if user is None:
        await message.answer(
            "❗ Для начала введите ваши данные от OBIS.",
            reply_markup=MAIN_MENU,
        )
        return

    message = await message.answer("⌛ Загрузка ваших экзаменов...")
    async with create_obis_client(
        student_number=user.student_number,
        password=password_cryptor.decrypt(user.encrypted_password),
    ) as obis_client:
        await obis_client.login()
        try:
            lessons_with_exams = await obis_client.get_taken_grades_page()
        except ObisClientNotLoggedInError:
            await message.edit_text(
                "❌ Не удалось войти в OBIS с предоставленными данными. Пожалуйста, проверьте их и попробуйте снова.",
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
async def on_view_yoklama_command(
    message: Message,
    password_cryptor: PasswordCryptor,
) -> None:
    async with create_database_gateway() as database_gateway:
        user = await database_gateway.get_user_with_credentials_by_id(
            user_id=message.from_user.id,
        )

    if user is None:
        await message.answer(
            "❗ Для начала введите ваши данные от OBIS.",
            reply_markup=MAIN_MENU,
        )
        return

    message = await message.answer("⌛ Загрузка вашей йокламы...")
    async with create_obis_client(
        student_number=user.student_number,
        password=password_cryptor.decrypt(user.encrypted_password),
    ) as obis_client:
        await obis_client.login()
        try:
            lessons = await obis_client.get_lessons_attendance_list()
        except ObisClientNotLoggedInError:
            await message.edit_text(
                "❌ Не удалось войти в OBIS с предоставленными данными. Пожалуйста, проверьте их и попробуйте снова.",
            )
            return

        text = ''
        for lesson in lessons:
            skipping = compute_lesson_skip_opportunities(lesson)
            lesson_name = f"<b>{lesson.lesson_name}</b>"

            if skipping.practice <= 1 or skipping.theory <= 1:
                lesson_name = f"⚠️ {lesson_name}"
            elif skipping.practice == 0 or skipping.theory == 0:
                lesson_name = f"❗ {lesson_name}"

            text += (
                f"{lesson_name}\n"
                f"Теория: {lesson.theory_skips_percentage}% (осталось {skipping.theory} пропусков)\n"
                f"Практика: {lesson.practice_skips_percentage}% (осталось {skipping.practice} пропусков)\n\n"
            )

        if not text:
            text = "У вас нет предметов."
        await message.edit_text(text.strip())


@router.message(
    F.text, F.text != "Ввести данные от OBIS",
    StateFilter(CredentialsStates.obis_password),
)
async def on_obis_password_entered(
    message: Message,
    state: FSMContext,
    password_cryptor: PasswordCryptor,
) -> None:
    data = await state.get_data()
    student_number = data.get("student_number")
    obis_password = message.text
    await state.clear()
    message = await message.answer("🔒 Проверка введённых данных...")

    async with create_obis_client(
        student_number=student_number,
        password=obis_password,
    ) as obis_client:
        try:
            await obis_client.login()
        except ObisClientNotLoggedInError:
            await message.edit_text(
                "❌ Не удалось войти в OBIS с предоставленными данными. Пожалуйста, проверьте их и попробуйте снова.",
            )
            return

    async with create_database_gateway() as database_gateway:
        await database_gateway.update_user_credentials(
            user_id=message.from_user.id,
            student_number=student_number,
            encrypted_password=password_cryptor.encrypt(obis_password),
        )

    await message.edit_text(
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
    await state.update_data(student_number=message.text.removesuffix("@manas.edu.kg"))
    await state.set_state(CredentialsStates.obis_password)
    await message.answer("✏️ Введите ваш пароль от OBIS:")


@router.message(F.text == "Ввести данные от OBIS")
async def on_credentials_command(message: Message, state: FSMContext) -> None:
    await state.set_state(CredentialsStates.student_number)
    await message.answer("✏️ Введите ваш студ.номер:")
