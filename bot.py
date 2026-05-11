import asyncio
import base64
import binascii
import json
import logging
import os
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    BufferedInputFile,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8774638976:AAFgGEZNFAV23UvhKFf2IOa8O1N3QNy5Jls")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://web-production-aa83dd.up.railway.app")

dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message, bot: Bot) -> None:
    await bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonWebApp(
            text="Open Mini App",
            web_app=WebAppInfo(url=WEBAPP_URL),
        ),
    )

    await message.answer(
        "Привет! Нажми кнопку Menu, чтобы открыть Mini App."
    )


@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message) -> None:
    raw_data = message.web_app_data.data

    try:
        payload = json.loads(raw_data)
    except json.JSONDecodeError:
        await message.answer("Ошибка: не удалось распознать JSON от Mini App.")
        return

    photos = payload.get("photos")
    if not isinstance(photos, list) or not photos:
        await message.answer("Ошибка: поле 'photos' отсутствует или пустое.")
        return

    sent_count = 0
    for index, photo_base64 in enumerate(photos, start=1):
        if not isinstance(photo_base64, str):
            continue

        cleaned = photo_base64
        if "," in cleaned and cleaned.split(",", 1)[0].startswith("data:"):
            cleaned = cleaned.split(",", 1)[1]

        try:
            photo_bytes = base64.b64decode(cleaned, validate=True)
        except (binascii.Error, ValueError):
            await message.answer(f"Фото #{index}: некорректный base64.")
            continue

        if not photo_bytes:
            await message.answer(f"Фото #{index}: пустые данные.")
            continue

        photo_file = BufferedInputFile(BytesIO(photo_bytes), filename=f"photo_{index}.jpg")
        await message.answer_photo(photo=photo_file)
        sent_count += 1

    if sent_count == 0:
        await message.answer("Не удалось отправить ни одного фото.")


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
