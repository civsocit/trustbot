from settings import BotSettings
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from database import Database, Relation
from utils import usage, BadCommandFormat


bot = Bot(token=BotSettings.token())
dp = Dispatcher(bot, storage=MemoryStorage())

db = Database.restore_backup()


@dp.message_handler(commands=["start"])
async def start(message: types.Message, state: FSMContext):
    await message.answer("Приветик")


@dp.message_handler(commands=["inc", "dec"])
@usage("Формат команды: /inc(/dec) @telegram_login комментарий")
async def inc_dec(message: types.Message, state: FSMContext):
    data = message.text.split(" ", maxsplit=3)

    # Command, username must be specified
    if len(data) < 2:
        raise BadCommandFormat()

    command = data[0]
    username = data[1]
    comment = data[2] if len(data) > 2 else None
    # Username must be a dog
    if not username.startswith("@"):
        raise BadCommandFormat()

    if not message.from_user.username:
        await message.answer("У вас должен быть свой username")
        return

    relation = {
        "/inc": Relation.good,
        "/dec": Relation.bad
    }[command]

    db.add_relation("@" + message.from_user.username,
                    username,
                    relation,
                    comment)
    await message.answer("Добавлено")


@dp.message_handler(commands=["info"])
@usage("Формат команды: /info @username")
async def info(message: types.Message, state: FSMContext):
    data = message.text.split(" ", maxsplit=2)

    if len(data) < 2:
        raise BadCommandFormat()

    username = data[1]

    if not message.from_user.username:
        await message.answer("У вас должен быть свой username")
        return

    comments = db.get_trusted_comments("@" + message.from_user.username,
                                       username)

    if not comments:
        await message.answer("Нет информации по этому пользователю")
        return

    text = "Информация:"
    for comment in comments:
        text += f"{comment.relation_s}: {comment.comment}\n"

    await message.answer(text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)