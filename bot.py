from aiogram.filters.command import Command
from aiogram import Router
from aiogram.types import Message

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.handlers.callback_query import CallbackQuery
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode
from aiogram import F
from aiogram.fsm.state import State, StatesGroup
import os
from os import walk
from dotenv import dotenv_values
from typing import Optional

from bot_init import sd_bot
from utils import process_document


config = {
    **dotenv_values(".env"),
    **os.environ,
}


dp = sd_bot.dispatcher
bot = sd_bot.bot
form_router = Router()
dp.include_router(form_router)


class AnswerCallback(CallbackData, prefix='new-user'):
    answer: str
    val: Optional[str]


class AddDocument(StatesGroup):
    add_document = State()


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await bot.send_message(chat_id=message.chat.id,
                           text='Загрузите документ, который необходимо разбить на предложения.'
                                'Нажмите на скрепку и выберите пункт Файл.')

    await state.set_state(AddDocument.add_document)


@form_router.message(AddDocument.add_document, F.content_type.in_({'document'}))
async def add_document(message: Message, state: FSMContext) -> None:
    if message.document:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        ind = file_path.rfind('/')
        file_name = file_path[ind + 1:]

        await bot.download_file(file_path, f"documents/{file_name}")

        process_document(file_path, "documents/output.doc")
        out_doc = FSInputFile("documents/output.doc")
        await bot.send_document(chat_id=message.chat.id, document=out_doc)

        # remove all files from directory
        layer = 1
        w = walk('documents')
        for (_, _, filenames) in w:
            for file_name in filenames:
                os.remove(f"documents/{file_name}")
            layer += 1

        await state.clear()
        await cmd_start(message, state)
    else:
        await bot.send_message(chat_id=message.chat.id,
                               text="Добавьте документ!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
