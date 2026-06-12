import os
from dotenv import load_dotenv
from typing import Optional


class Config:
    """Класс конфигурации приложения"""
    
    def __init__(self):
        load_dotenv()
        
        # Telegram
        self.BOT_TOKEN: str = self._get_required("BOT_TOKEN")
        self.ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "@zoo_manager")
        self.ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "adoption@moscowzoo.ru")
        self.ADOPTION_LINK: str = os.getenv("ADOPTION_LINK", "https://moscowzoo.ru/adoption")
        self.IMAGES_DIR = "images"
        
        # PostgreSQL
        self.POSTGRES_USER: str = os.getenv("POSTGRES_USER", "zoo_bot_user")
        self.POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.POSTGRES_DB: str = os.getenv("POSTGRES_DB", "zoo_bot_db")
        self.POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
        self.POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
        
        # Формируем DATABASE_URL
        self.DATABASE_URL: str = (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    def _get_required(self, key: str) -> str:
        """Получает переменную окружения"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"❌ Переменная {key} не найдена в .env")
        return value
    
    def get_postgres_sync_url(self) -> str:
        """URL для синхронного подключения"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )