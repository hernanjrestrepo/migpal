"""Identity — application: comandos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterUserCommand:
    email: str
    username: str
    password: str


@dataclass(frozen=True)
class AuthenticateCommand:
    username: str
    password: str


@dataclass(frozen=True)
class VerifyEmailCommand:
    token: str


@dataclass(frozen=True)
class RequestPasswordResetCommand:
    email: str


@dataclass(frozen=True)
class ResetPasswordCommand:
    token: str
    new_password: str
