import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, FSInputFile, Message

from price_bot.common.config import Settings
from price_bot.common.exceptions import BotError
from price_bot.llm.client import LLMClient
from price_bot.mcp.client import McpClient
from price_bot.quotes.renderer import Renderer
from price_bot.quotes.service import QuoteService
from price_bot.storage.db import get_connection, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def _build_service(settings: Settings, mcp_client: McpClient) -> tuple:
    conn = await get_connection(settings)
    await init_db(conn)
    llm_client = LLMClient(settings)
    renderer = Renderer(settings)
    service = QuoteService(conn, llm_client, mcp_client, renderer, settings)
    return conn, service


async def main() -> None:
    settings = Settings()

    mcp_client = McpClient(settings)
    await mcp_client.start()

    conn, service = await _build_service(settings, mcp_client)

    bot = Bot(token=settings.telegram_token)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: Message) -> None:
        await message.answer(
            "Привет! Я помогаю составить коммерческое предложение по продуктам 1С.\n\n"
            "Просто напишите, что нужно посчитать:\n"
            "  «1С:ERP, 10 лицензий, клиент ООО Ромашка»\n\n"
            "Команды:\n"
            "  /refresh_prices — обновить базу цен"
        )

    @dp.message(Command("refresh_prices"))
    async def cmd_refresh_prices(message: Message) -> None:
        assert message.from_user
        try:
            result = await service.handle_refresh_prices(
                telegram_chat_id=message.chat.id,
                telegram_user_id=message.from_user.id,
            )
        except Exception as exc:
            logger.exception("refresh_prices error: %s", exc)
            result = "Что-то пошло не так, попробуйте ещё раз."
        await message.answer(result)

    @dp.message(F.text)
    async def handle_text(message: Message) -> None:
        assert message.from_user
        try:
            result = await service.handle_message(
                telegram_chat_id=message.chat.id,
                telegram_user_id=message.from_user.id,
                telegram_message_id=message.message_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                text=message.text or "",
            )
        except Exception as exc:
            logger.exception("handle_message error: %s", exc)
            await message.answer("Что-то пошло не так, попробуйте ещё раз.")
            return

        if result and os.path.isfile(result) and result.endswith(".md"):
            try:
                await message.answer_document(
                    FSInputFile(result),
                    caption="Ваше коммерческое предложение готово.",
                )
            except Exception as exc:
                logger.exception("send_document error: %s", exc)
                await message.answer(f"КП сформировано, но не удалось отправить файл: {result}")
        else:
            await message.answer(result or "Готово.")

    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    finally:
        await mcp_client.stop()
        await conn.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
