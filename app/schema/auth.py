
from pydantic import BaseModel

from app.models import Role


class ForgotPasswordRequest(BaseModel):
    email: str

class ForgotPasswordResponse(BaseModel):
    password_reset_token: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str

class ResetPasswordResponse(BaseModel):
    message: str


class ProfileRequest(BaseModel):
    token: str

class ProfileResponse(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: str
    role: str
    face_verified: bool


class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    role: str = Role.STUDENT.value

class SignupResponse(BaseModel):
    access_token: str
    token_type: str


class RegisterFaceResponse(BaseModel):
    message: str
    face_verified: bool