import os
import logging
from typing import Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from app.database import DatabaseManager
from app.quiz_engine import QuizEngine
from app.config import Config

logger = logging.getLogger(__name__)


class BotHandlers:
    """Обработчики событий Telegram бота."""
    
    def __init__(self, db: DatabaseManager, quiz_engine: QuizEngine, config: Config):
        self.db = db
        self.quiz_engine = quiz_engine
        self.config = config

    def _init_user_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Инициализирует данные сессии пользователя."""
        context.user_data["quiz_state"] = "active"
        context.user_data["current_question"] = 0
        context.user_data["scores"] = {animal: 0 for animal in self.quiz_engine.animals.keys()}
        context.user_data["answers"] = []

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start."""
        user = update.effective_user
        
        # Сохраняем пользователя в БД
        await self.db.upsert_user(
            telegram_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or ""
        )
        
        text = (
            f"🦁 *Привет, {user.first_name or 'друг зоопарка'}!*\n\n"
            f"Добро пожаловать в Московский зоопарк!\n"
            f"Узнай, какое из наших 500+ животных похоже на тебя по характеру.\n\n"
            f"📝 *Как это работает:*\n"
            f"• Ответь на 10 вопросов\n"
            f"• Узнай своё тотемное животное\n"
            f"• Получи возможность стать его опекуном!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 Начать викторину", callback_data="start_quiz")],
            [InlineKeyboardButton("ℹ️ О программе опеки", callback_data="about_adoption")],
            [InlineKeyboardButton("📞 Контакты зоопарка", callback_data="contact_zoo")]
        ]
        
        # Используем effective_message вместо message
        await update.effective_message.reply_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="Markdown"
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Центральный маршрутизатор callback-запросов."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "start_quiz":
            self._init_user_data(context)
            await self._show_question(update, context)
        elif data == "about_adoption":
            await self._show_adoption_info(update, context)
        elif data == "contact_zoo":
            await self._show_contact_info(update, context)
        elif data == "restart_quiz":
            self._init_user_data(context)
            await self._show_question(update, context)
        elif data.startswith("answer_"):
            await self._handle_answer(update, context)
        elif data == "back_to_main":
            await self.start(update, context)
        elif data == "feedback_ask":
            await self._show_feedback_menu(update, context)
        elif data.startswith("feedback_"):
            await self._handle_feedback(update, context)

    async def _show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отображает текущий вопрос."""
        q_index = context.user_data["current_question"]
        question = self.quiz_engine.get_question(q_index)
        
        if not question:
            await self._show_result(update, context)
            return
        
        keyboard = [
            [InlineKeyboardButton(opt["text"], callback_data=f"answer_{q_index}_{i}")]
            for i, opt in enumerate(question["options"])
        ]
        
        text = (
            f"📝 *Вопрос {q_index + 1} из {self.quiz_engine.get_total_questions()}*\n\n"
            f"{question['text']}"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
        else:
            await update.effective_message.reply_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )

    async def _handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает выбор ответа."""
        query = update.callback_query
        _, q_idx, opt_idx = query.data.split("_")
        q_idx, opt_idx = int(q_idx), int(opt_idx)
        
        question = self.quiz_engine.get_question(q_idx)
        option = question["options"][opt_idx]
        
        # Сохраняем ответ И список животных, которым начислены баллы (для разрешения ничьей)
        context.user_data["answers"].append({
            "question": question["text"],
            "answer": option["text"],
            "scored_animals": list(option["scores"].keys())
        })
        
        for animal, score in option["scores"].items():
            if animal in context.user_data["scores"]:
                context.user_data["scores"][animal] += score
        
        context.user_data["current_question"] += 1
        await self._show_question(update, context)

    async def _show_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает результат и сохраняет его в БД."""
        user_id = update.effective_user.id
        scores = context.user_data["scores"]
        answers = context.user_data["answers"]
        
        # Передаем историю ответов для разрешения ничьей
        animal_key = self.quiz_engine.calculate_result(scores, answers)
        animal = self.quiz_engine.get_animal_data(animal_key)
        
        # Сохраняем в БД
        await self.db.save_quiz_result(
            telegram_id=user_id,
            animal_key=animal_key,
            answers=answers,
            scores=scores
        )
        
        text = (
            f"🎉 *Поздравляем!*\n\n"
            f"*Твоё тотемное животное — {animal['name_ru']}!*\n\n"
            f"{animal['description']}\n\n"
            f"📌 *Интересные факты:*\n"
        )
        for fact in animal["fun_facts"]:
            text += f"• {fact}\n"
            
        text += (
            f"\n💰 *Стоимость опеки:* {animal['adoption_cost']}\n\n"
            f"Хочешь стать опекуном и получать новости о своём подопечном?"
        )
        
        keyboard = [
            [InlineKeyboardButton("🤝 Стать опекуном", url=self.config.ADOPTION_LINK)],
            [
                InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_quiz"),
                InlineKeyboardButton("💬 Оставить отзыв", callback_data="feedback_ask")
            ],
            [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]
        ]
        
        await update.callback_query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="Markdown"
        )
        
        # Отправка локального фото
        image_filename = animal.get("image_filename")
        if image_filename:
            image_path = os.path.join(self.config.IMAGES_DIR, image_filename)
            if os.path.exists(image_path):
                try:
                    with open(image_path, "rb") as photo_file:
                        await context.bot.send_photo(
                            chat_id=user_id,
                            photo=photo_file,
                            caption=f"📸 Это {animal['name_ru']} — твоё тотемное животное!"
                        )
                except Exception as e:
                    logger.error(f"Ошибка отправки фото {image_filename}: {e}")

    async def _show_adoption_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Информация о программе опеки."""
        text = (
            "🤝 *Программа «Возьми животное под опеку»*\n\n"
            "Ежемесячное пожертвование от 200 ₽ идет на корм, уход и лечение.\n\n"
            "*Что ты получаешь:*\n"
            "✅ Именной сертификат опекуна\n"
            "✅ Регулярные фото и видео твоего подопечного\n"
            "✅ Приоритетное посещение в зоопарке\n"
            "✅ Благодарность от команды зоопарка\n\n"
            "💚 В Московском зоопарке живёт около 6000 животных 1100 видов!"
        )
        keyboard = [
            [InlineKeyboardButton("🔗 Перейти на сайт", url=self.config.ADOPTION_LINK)],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
        else:
            await update.effective_message.reply_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )

async def _show_contact_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Контактная информация."""
    text = (
        "📞 Свяжитесь с отделом опеки!\n\n"
        f"📧 Email: {self.config.ADMIN_EMAIL}\n"
        f"💬 Telegram: {self.config.ADMIN_USERNAME}\n\n"
        "🏢 Адрес: Москва, ул. Большая Грузинская, 1\n"
        "⏰ Режим работы: Пн-Вс 10:00 - 19:00"
    )
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.effective_message.reply_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _show_feedback_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает меню с оценками."""
        keyboard = [
            [InlineKeyboardButton("⭐⭐⭐⭐⭐ Отлично!", callback_data="feedback_5")],
            [InlineKeyboardButton("⭐⭐⭐⭐ Хорошо", callback_data="feedback_4")],
            [InlineKeyboardButton("⭐⭐⭐ Нормально", callback_data="feedback_3")],
            [InlineKeyboardButton("⭐⭐ Можно лучше", callback_data="feedback_2")],
            [InlineKeyboardButton("⭐ Не понравилось", callback_data="feedback_1")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
        ]
        
        text = (
            "💬 *Нам важно твоё мнение!*\n\n"
            "Поставь оценку боту:"
        )
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def _handle_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка отзыва."""
        query = update.callback_query
        rating = int(query.data.split("_")[1])
        
        await self.db.add_feedback(
            telegram_id=update.effective_user.id,
            rating=rating,
            comment=f"Rating: {rating}/5"
        )
        
        messages = {
            5: "🎉 Спасибо за отличную оценку! Мы рады, что тебе понравилось!",
            4: "👍 Спасибо! Мы стараемся стать ещё лучше!",
            3: "🤔 Спасибо за честность! Мы работаем над улучшениями!",
            2: "😔 Нам жаль! Мы обязательно учтём это.",
            1: "😞 Прости нас! Мы постараемся исправить ошибки."
        }
        
        keyboard = [[InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]]
        
        await query.edit_message_text(
            messages.get(rating, "Спасибо за отзыв!"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )