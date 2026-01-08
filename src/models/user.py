from pydantic import BaseModel


class User(BaseModel):
    id: int
    student_number: str
    encrypted_password: str
    has_accepted_terms: bool
