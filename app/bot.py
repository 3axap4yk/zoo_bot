import logging
import sys
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from app.config import Config
from app.database import DatabaseManager
from app.quiz_engine import QuizEngine
from app.handlers import BotHandlers

# Настройка логирования (вывод в stdout для Docker)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

class ZooBot:
    """Главный класс приложения."""
    
    def __init__(self):
        logger.info("🚀 Инициализация ZooBot...")
        self.config = Config()
        self.db = DatabaseManager(self.config)
        self.quiz_engine = QuizEngine()
        self.handlers = BotHandlers(self.db, self.quiz_engine, self.config)
        
        # Создаем приложение Telegram
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Настройка обработчиков команд и кнопок."""
        self.application.add_handler(CommandHandler("start", self.handlers.start))
        self.application.add_handler(CallbackQueryHandler(self.handlers.button_handler))
        
        # Глобальный обработчик ошибок
        self.application.add_error_handler(self._error_handler)

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Логирование и обработка ошибок."""
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
        
        # Если есть сообщение, уведомляем пользователя
        from telegram import Update
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "😕 Произошла техническая ошибка. Пожалуйста, попробуйте еще раз позже "
                "или свяжитесь с администратором."
            )

    async def run(self) -> None:
        """Запуск бота."""
        try:
            logger.info("🔌 Подключение к базе данных...")
            await self.db.connect()
            
            logger.info("🤖 Запуск polling...")
            await self.application.run_polling(allowed_updates=["message", "callback_query"])
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при запуске: {e}")
        finally:
            await self.db.disconnect()

if __name__ == "__main__":
    bot = ZooBot()
    # Запускаем асинхронный цикл
    import asyncio
    asyncio.run(bot.run())