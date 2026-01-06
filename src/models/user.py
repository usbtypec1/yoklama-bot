from pydantic import BaseModel


class User(BaseModel):
    id: int
    student_number: str | None
    encrypted_password: str | None
