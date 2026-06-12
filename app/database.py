import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.config import Config
from app.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер базы данных PostgreSQL."""
    
    def __init__(self, config: Config):
        self.config = config
        self.engine = None
        self.async_session_maker = None
    
    async def connect(self) -> None:
        """Подключение к базе данных."""
        try:
            self.engine = create_async_engine(
                self.config.DATABASE_URL,
                echo=False,  # True для отладки SQL запросов
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Создаем таблицы
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ Подключение к PostgreSQL успешно установлено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Отключение от базы данных."""
        if self.engine:
            await self.engine.dispose()
            logger.info("🔌 Отключение от PostgreSQL")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получение сессии БД."""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def upsert_user(self, telegram_id: int, username: str, 
                          first_name: str, last_name: str = None) -> None:
        """Добавление или обновление пользователя."""
        async for session in self.get_session():
            from sqlalchemy import select
            from app.models import User
            
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
            else:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
            
            await session.commit()
    
    async def save_quiz_result(self, telegram_id: int, animal_key: str,
                               answers: list, scores: dict) -> None:
        """Сохранение результата викторины."""
        async for session in self.get_session():
            from sqlalchemy import select
            from app.models import User, QuizResult
            
            # Получаем user_id по telegram_id
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            
            quiz_result = QuizResult(
                user_id=user.id,
                animal_key=animal_key,
                answers_json=answers,
                scores_json=scores
            )
            session.add(quiz_result)
            await session.commit()
    
    async def add_feedback(self, telegram_id: int, rating: int, 
                           comment: str = None) -> None:
        """Добавление отзыва."""
        async for session in self.get_session():
            from sqlalchemy import select
            from app.models import User, Feedback
            
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            
            feedback = Feedback(
                user_id=user.id,
                rating=rating,
                comment=comment
            )
            session.add(feedback)
            await session.commit()