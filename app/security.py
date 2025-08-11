import hashlib
import hmac
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Use env or secrets; in Streamlit, st.secrets is preferred, but for helpers we keep it simple
SESSION_COOKIE_KEY = os.getenv("SESSION_COOKIE_KEY", "please-change-session-cookie-key")


def hash_password(password: str, salt: Optional[str] = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return f"pbkdf2_sha256$200000${salt}${dk.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, iterations_str, salt, digest_hex = password_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), iterations)
        return hmac.compare_digest(dk.hex(), digest_hex)
    except Exception:
        return False