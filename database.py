# database.py - Database models and operations
"""
SQLAlchemy модели для хранения пользователей и бросков кубиков
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from typing import Optional, List
import json

from config import DATABASE_URL

# Database setup
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ===================================
# MODELS
# ===================================

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)

    # Relationships
    throws = relationship("DiceThrow", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.telegram_id}>"


class DiceThrow(Base):
    """Модель броска кубиков"""
    __tablename__ = "dice_throws"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Ситуация пользователя
    situation = Column(Text, nullable=False)

    # Результаты броска (6 позиций)
    symbol = Column(String, nullable=False)  # root
    archetype = Column(String, nullable=False)  # outer
    emotion = Column(String, nullable=False)  # inner

    # Дополнительные символы для полного расклада (6 кубиков)
    shadow_symbol = Column(String, nullable=True)  # тень
    gift_symbol = Column(String, nullable=True)  # дар
    step_symbol = Column(String, nullable=True)  # шаг

    # ИИ интерпретация
    interpretation = Column(Text, nullable=True)

    # Выбранный путь
    chosen_path = Column(String, nullable=True)  # change/stay/patience

    # Journaling подсказки
    reflection_prompts = Column(Text, nullable=True)  # JSON array

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="throws")

    def __repr__(self):
        return f"<DiceThrow {self.id} for user {self.user_id}>"

    def get_reflection_prompts(self) -> List[str]:
        """Получить список подсказок для рефлексии"""
        if self.reflection_prompts:
            return json.loads(self.reflection_prompts)
        return []

    def set_reflection_prompts(self, prompts: List[str]):
        """Установить подсказки для рефлексии"""
        self.reflection_prompts = json.dumps(prompts, ensure_ascii=False)


# ===================================
# DATABASE INITIALIZATION
# ===================================

def init_db():
    """Создать все таблицы в базе данных"""
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована")


def get_db() -> Session:
    """Получить сессию базы данных"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Сессию закроет вызывающий код


# ===================================
# CRUD OPERATIONS - USERS
# ===================================

def create_user(telegram_id: str, username: str = None, full_name: str = None) -> User:
    """Создать нового пользователя"""
    db = get_db()
    try:
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def get_user(telegram_id: str) -> Optional[User]:
    """Получить пользователя по Telegram ID"""
    db = get_db()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        return user
    finally:
        db.close()


def get_or_create_user(telegram_id: str, username: str = None, full_name: str = None) -> User:
    """Получить или создать пользователя"""
    user = get_user(telegram_id)
    if not user:
        user = create_user(telegram_id, username, full_name)
    return user


def update_last_interaction(telegram_id: str):
    """Обновить время последнего взаимодействия"""
    db = get_db()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.last_interaction = datetime.utcnow()
            db.commit()
    finally:
        db.close()


# ===================================
# CRUD OPERATIONS - DICE THROWS
# ===================================

def save_throw(
    telegram_id: str,
    situation: str,
    symbol: str,
    archetype: str,
    emotion: str,
    shadow_symbol: str = None,
    gift_symbol: str = None,
    step_symbol: str = None,
    interpretation: str = None
) -> DiceThrow:
    """Сохранить бросок кубиков (6 символов)"""
    db = get_db()
    try:
        user = get_or_create_user(telegram_id)

        throw = DiceThrow(
            user_id=user.id,
            situation=situation,
            symbol=symbol,  # root
            archetype=archetype,  # outer
            emotion=emotion,  # inner
            shadow_symbol=shadow_symbol,  # тень
            gift_symbol=gift_symbol,  # дар
            step_symbol=step_symbol,  # шаг
            interpretation=interpretation
        )
        db.add(throw)
        db.commit()
        db.refresh(throw)
        return throw
    finally:
        db.close()


def update_throw(
    throw_id: int,
    interpretation: str = None,
    chosen_path: str = None,
    reflection_prompts: List[str] = None
):
    """Обновить информацию о броске"""
    db = get_db()
    try:
        throw = db.query(DiceThrow).filter(DiceThrow.id == throw_id).first()
        if throw:
            if interpretation:
                throw.interpretation = interpretation
            if chosen_path:
                throw.chosen_path = chosen_path
            if reflection_prompts:
                throw.set_reflection_prompts(reflection_prompts)
            db.commit()
    finally:
        db.close()


def get_user_throws(telegram_id: str, limit: int = 10) -> List[DiceThrow]:
    """Получить историю бросков пользователя"""
    db = get_db()
    try:
        user = get_user(telegram_id)
        if not user:
            return []

        throws = db.query(DiceThrow)\
            .filter(DiceThrow.user_id == user.id)\
            .order_by(DiceThrow.timestamp.desc())\
            .limit(limit)\
            .all()
        return throws
    finally:
        db.close()


def get_throw_by_id(throw_id: int) -> Optional[DiceThrow]:
    """Получить бросок по ID"""
    db = get_db()
    try:
        throw = db.query(DiceThrow).filter(DiceThrow.id == throw_id).first()
        return throw
    finally:
        db.close()


# ===================================
# STATISTICS
# ===================================

def get_stats() -> dict:
    """Получить статистику бота"""
    db = get_db()
    try:
        users_count = db.query(User).count()
        throws_count = db.query(DiceThrow).count()

        return {
            "users": users_count,
            "throws": throws_count
        }
    finally:
        db.close()


# Инициализация при импорте
if __name__ != "__main__":
    import os
    if not os.path.exists("dice_bot.db"):
        init_db()
