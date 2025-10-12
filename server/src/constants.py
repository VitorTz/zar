from pathlib import Path
import os

class Constants:

    TMP_DIR = Path("tmp")
    LOG_DIR = Path("logs")

    MAX_REQUESTS = 200
    WINDOW = 30
    
    IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"
    SENSITIVE_PATHS = ["/api/v1/auth/", "/api/v1/admin/"]

    CONTENT_SECURITY_HEADER = (
        "default-src 'self'; "
        "script-src 'self' https://cdnjs.cloudflare.com; "
        "style-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdnjs.cloudflare.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    PERMISSIONS_POLICY_HEADER = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )    

    SECRET_KEY = os.getenv("SECRET_KEY")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    MAX_BODY_SIZE = 20 * 1024 * 1024
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    MAX_FAILED_ATTEMPTS = 10
    LOCK_TIME_MINUTES = 16
    CACHE_EXPIRE_SECONDS = 60
