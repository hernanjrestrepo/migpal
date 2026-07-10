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
