import os
import datetime
from typing import List
from functools import lru_cache
import pydantic as pyd
from src.lib.utils import get_path


class Settings(pyd.BaseSettings):
    # Project base setting details
    debug: bool = os.getenv("DEBUG")
    project_name: str = os.getenv("PROJECT_NAME")
    project_version: float = os.getenv("PROJECT_VERSION")
    project_description: str = os.getenv("PROJECT_DESCRIPTION")
    api_prefix: str = os.getenv("API_PREFIX")
    project_url: str = os.getenv("PROJECT_URL")
    environment: str = os.getenv("ENVIRONMENT")
    backend_cors_origins: List[str] = os.getenv("BACKEND_CORS_ORIGINS")
    # admin email settings
    admin_email: str = os.getenv("ADMIN_EMAIL")
    admin_password: str = os.getenv("ADMIN_PASSWORD")
    email_port: int = os.getenv("EMAIL_PORT")
    email_server: str = os.getenv("EMAIL_SERVER")
    # developer contact information
    contact_email: str = os.getenv("CONTACT_EMAIL")
    contact_name: str = os.getenv("CONTACT_NAME")
    # Database settings
    db_name: str = os.getenv("DB_NAME")
    db_user: str = os.getenv("DB_USER")
    db_password: str = os.getenv("DB_PASSWORD")
    db_port: int = os.getenv("DB_PORT")
    db_host: str = os.getenv("DB_HOST")
    db_type: str = os.getenv("DB_TYPE")
    # JSON web token settings
    secret_key: str = os.getenv("SECRET_KEY")
    refresh_secret_key: str = os.getenv("REFRESH_SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    access_token_expire_time: int = os.getenv("ACCESS_TOKEN_EXPIRE_TIME")
    refresh_token_expire_time: int = os.getenv("REFRESH_TOKEN_EXPIRE_TIME")
    # payment service settings
    payment_secret_key: str = os.getenv("PAYMENT_SECRET_KEY")
    payment_public_key: str = os.getenv("PAYMENT_PUBLIC_KEY")
    # project template, static files path settings
    base_dir: pyd.DirectoryPath = get_path.get_base_dir()
    media_url_endpoint_name = "get_media"
    email_template_dir: pyd.DirectoryPath = get_path.get_template_dir()
    static_file_dir: pyd.DirectoryPath = get_path.get_static_file_dir()
    media_file_dir: pyd.DirectoryPath = get_path.get_media_file_dir()
    pdf_media_file_dir: pyd.DirectoryPath = get_path.get_pdf_file_dir()

    def get_access_expires_time(self):
        return datetime.timedelta(seconds=self.access_token_expire_time)

    def get_refresh_expires_time(
        self,
    ):
        return datetime.timedelta(seconds=self.refresh_token_expire_time)

    def get_database_url(self) -> str:
        if self.environment in [
            "production",
            "development",
            "dev",
        ]:
            return f"{self.db_type}://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return "sqlite+aiosqlite:///./testing.sqlite"

    class Config:
        env_file: str = ".env"


@lru_cache
def get_settings():
    return Settings()


config = get_settings()
