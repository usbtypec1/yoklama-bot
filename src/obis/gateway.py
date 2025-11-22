import contextlib
import logging
from dataclasses import dataclass
from typing import NewType, AsyncGenerator

import httpx
from bs4 import BeautifulSoup

from exceptions import ObisClientNotLoggedInError
from obis.models import LessonAttendance, LessonExams
from obis.parsers import parse_lessons_attendance_page, parse_taken_grades_page


logger = logging.getLogger(__name__)

ObisHttpClient = NewType("ObisHttpClient", httpx.AsyncClient)


@contextlib.asynccontextmanager
async def create_obis_http_client() -> AsyncGenerator[ObisHttpClient, None]:
    async with httpx.AsyncClient(
        base_url="https://obistest.manas.edu.kg/",
        headers={"User-Agent": "Yoklama parser"},
        timeout=30,
        follow_redirects=True,
    ) as http_client:
        yield ObisHttpClient(http_client)


@dataclass(slots=True, kw_only=True)
class ObisClient:
    student_number: str
    password: str
    http_client: ObisHttpClient

    async def login(self) -> None:
        url = "/site/login"
        response = await self.http_client.get(url)

        soup = BeautifulSoup(response.text, "lxml")

        csrf_input = soup.find("input", {"name": "_csrf"})
        if csrf_input is None:
            logger.error("ObisClient login: CSRF token not found")
            return

        csrf_token = csrf_input.get("value")
        if csrf_token is None:
            logger.error("ObisClient login: CSRF token value not found")
            return

        request_data = {
            "_csrf": csrf_token,
            "LoginForm[username]": self.student_number,
            "LoginForm[password_hash]": self.password,
        }
        response = await self.http_client.post(url, data=request_data)
        if response.is_error:
            logger.error(
                "ObisClient login: login failed for student number %s",
                self.student_number,
            )
            raise ObisClientNotLoggedInError

    async def get_lessons_attendance_list(self) -> list[LessonAttendance]:
        url = "/vs-ders/taken-lessons"
        response = await self.http_client.get(url)
        return parse_lessons_attendance_page(response.text)

    async def get_taken_grades_page(self) -> list[LessonExams]:
        url = "/vs-ders/taken-grades"
        response = await self.http_client.get(url)
        return parse_taken_grades_page(response.text)


@contextlib.asynccontextmanager
async def create_obis_client(
    *,
    student_number: str,
    password: str,
) -> AsyncGenerator[ObisClient, None]:
    async with create_obis_http_client() as http_client:
        yield ObisClient(
            student_number=student_number,
            password=password,
            http_client=http_client,
        )
