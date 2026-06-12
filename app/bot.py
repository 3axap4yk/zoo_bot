import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from app.config import Config
from app.database import DatabaseManager
from app.quiz_engine import QuizEngine
from app.handlers import BotHandlers

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
        
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        
        self.application.post_init = self._post_init
        self.application.post_shutdown = self._post_shutdown
        
        self._setup_routes()

    async def _post_init(self, application: Application) -> None:
        """Вызывается после инициализации приложения, до запуска polling."""
        logger.info("🔌 Подключение к базе данных...")
        await self.db.connect()
        logger.info("✅ Бот готов к работе!")

    async def _post_shutdown(self, application: Application) -> None:
        """Вызывается при остановке приложения."""
        logger.info("🔌 Отключение от базы данных...")
        await self.db.disconnect()
        logger.info("✅ Бот остановлен корректно")

    def _setup_routes(self) -> None:
        """Настройка обработчиков команд и кнопок."""
        self.application.add_handler(CommandHandler("start", self.handlers.start))
        self.application.add_handler(CallbackQueryHandler(self.handlers.button_handler))
        self.application.add_error_handler(self._error_handler)

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Логирование и обработка ошибок."""
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
        
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "Произошла техническая ошибка. Пожалуйста, попробуйте еще раз позже."
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

    def run(self) -> None:
        """Запуск бота (синхронный метод, run_polling сам управляет event loop)."""
        logger.info("🤖 Запуск polling...")
        self.application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    bot = ZooBot()
    bot.run()