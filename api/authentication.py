from __future__ import annotations

from rest_framework_simplejwt.authentication import JWTAuthentication


class BankJWTAuthentication(JWTAuthentication):
    """Custom JWT auth class placeholder.

    We keep it here to make it easy to extend later (e.g., role checks).
    """

    pass

