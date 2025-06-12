from __future__ import annotations

from argon2 import PasswordHasher

from .structs import *
from .tokens import *

password_hasher = PasswordHasher()
