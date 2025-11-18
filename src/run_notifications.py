import asyncio

import httpx

from src.database_gateway import (
    DatabaseGateway, get_database_connection,
    Lesson,
)
from src.obis import (
    create_http_client, ObisClient,
    ObisClientNotLoggedInError, compare_lessons, LessonSkippingOpportunity,
    compute_lesson_skipping_opportunities,
)


def send_message_to_telegram(
    bot_token: str,
    chat_id: int,
    old_lesson: Lesson,
    new_lesson: Lesson,
    lesson_skipping_opportunity: LessonSkippingOpportunity,
):
    text = (
        f"<b>Ваша йоклама по предмету {old_lesson.name} изменилась:\n</b>"
        f"{old_lesson.theory_skipped_classes_percentage} → {new_lesson.theory_skipped_classes_percentage} (осталось {lesson_skipping_opportunity.theory} пропусков)\n"
        f"с {old_lesson.practice_skipped_classes_percentage} → {new_lesson.practice_skipped_classes_percentage} (осталось {lesson_skipping_opportunity.practice} пропусков)"
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response = httpx.post(
        url, json={"chat_id": chat_id, "text": text, "parse_mode": "html"},
    )
    print(response.text)


async def main():
    with get_database_connection() as connection:
        gateway = DatabaseGateway(connection)
        users = gateway.get_users_with_credentials()

    for user in users:
        async with create_http_client() as http_client:
            with get_database_connection() as connection:
                gateway = DatabaseGateway(connection)
                old_lessons = gateway.get_lessons(user.id)

            obis_client = ObisClient(
                student_number=user.student_number, password=user.password,
                http_client=http_client,
            )
            await obis_client.login()
            try:
                new_lessons = await obis_client.get_taken_lessons_page()
            except ObisClientNotLoggedInError:
                print("Failed to log in for user", user.id)
                return
            changed_lessons = compare_lessons(old_lessons, new_lessons)

            for old_lesson, new_lesson in changed_lessons:
                send_message_to_telegram(
                    bot_token="",
                    chat_id=user.id,
                    old_lesson=old_lesson,
                    new_lesson=new_lesson,
                    lesson_skipping_opportunity=compute_lesson_skipping_opportunities(
                        new_lesson,
                    ),
                )
            with get_database_connection() as connection:
                gateway = DatabaseGateway(connection)
                for lesson in new_lessons:
                    gateway.upsert_lesson(user.id, lesson)


if __name__ == '__main__':
    asyncio.run(main())
