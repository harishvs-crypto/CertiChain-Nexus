import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

def _resolve_database_uri():
    raw_uri = os.environ.get("DATABASE_URI")
    if not raw_uri:
        db_path = (BASE_DIR / "instance" / "certichain.db").resolve().as_posix()
        return f"sqlite:///{db_path}"
    if raw_uri.startswith("sqlite:///instance/"):
        rel_subpath = raw_uri[len("sqlite:///instance/"):]
        return f"sqlite:///{(BASE_DIR / 'instance' / rel_subpath).resolve().as_posix()}"
    if raw_uri.startswith("sqlite:///") and not raw_uri.startswith("sqlite:////") and ":" not in raw_uri[10:13]:
        rel_name = raw_uri[len("sqlite:///"):]
        return f"sqlite:///{(BASE_DIR / 'instance' / rel_name).resolve().as_posix()}"
    return raw_uri

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-certichain-nexus-secret-key-32bytes-min!")
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Path settings
    INSTANCE_PATH = BASE_DIR / "instance"
    CERTIFICATES_DIR = BASE_DIR / "certificates"
    KEYS_DIR = BASE_DIR / "instance" / "keys"
    
    # Platform signing key secret for Merkle Checkpoint signatures
    PLATFORM_SIGNING_KEY = os.environ.get("PLATFORM_SIGNING_KEY", "platform-master-key-dev-seed-2026")
    
    # Rate Limiting
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "100 per minute")
    
    # Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # Max 2MB upload limit for Proof Capsule JSON
