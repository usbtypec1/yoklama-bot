from pydantic import BaseModel


class UserWithCredentials(BaseModel):
    id: int
    student_number: str
    encrypted_password: str
