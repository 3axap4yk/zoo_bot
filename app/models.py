from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """Модель пользователя Telegram."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    quiz_results = relationship("QuizResult", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")


class QuizResult(Base):
    """Модель результата прохождения викторины."""
    
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    animal_key = Column(String(100), nullable=False)  # ключ животного (lion, elephant...)
    answers_json = Column(JSON, nullable=False)  # массив ответов
    scores_json = Column(JSON, nullable=False)  # {"lion": 5, "elephant": 3...}
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    user = relationship("User", back_populates="quiz_results")


class Feedback(Base):
    """Модель отзыва пользователя."""
    
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    user = relationship("User", back_populates="feedbacks")