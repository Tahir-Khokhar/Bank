from __future__ import annotations  # Enables postponed evaluation of type annotations.

from rest_framework_simplejwt.authentication import JWTAuthentication  # Imports JWT authentication for securing API requests.


class BankJWTAuthentication(JWTAuthentication):  # Custom JWT authentication class for the banking application.
    
    pass
