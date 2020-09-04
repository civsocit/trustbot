from settings import BotSettings
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from asyncio import sleep

from database import Database, Relation
from utils import usage, BadCommandFormat


bot = Bot(token=BotSettings.token())
dp = Dispatcher(bot, storage=MemoryStorage())

db = Database.restore_backup()


@dp.message_handler(commands=["start"])
async def start(message: types.Message, state: FSMContext):
    await message.answer("Приветик")


@dp.message_handler(regexp=r"^(/inc|/dec|\+|-)\s")
@usage("Формат команды: /inc(/dec) @telegram_login комментарий")
async def inc_dec(message: types.Message, state: FSMContext):
    """
    Command example
    /inc @user Good guy!
    /dec @user2 Bad guy!
    + @dog Nice dog
    - @cat Bad cat
    :param message:
    :param state:
    :return:
    """
    data = message.text.split(" ", maxsplit=2)

    # Command, username must be specified
    if len(data) < 2:
        raise BadCommandFormat()

    command = data[0]
    username_to = data[1]
    comment = data[2] if len(data) > 2 else None

    # Username must be a dog
    if not username_to.startswith("@"):
        raise BadCommandFormat()

    username_from = message.from_user.username

    if not message.from_user.username:
        await message.answer("У вас должен быть свой username")
        return

    username_from = "@" + username_from

    if username_from == username_to:
        await message.answer("Нельзя комментировать себя")
        return

    relation = {
        "/inc": Relation.good,
        "+": Relation.good,
        "/dec": Relation.bad,
        "-": Relation.bad
    }[command]

    db.add_relation("@" + username_from,
                    username_to,
                    relation,
                    comment)
    await message.answer("Добавлено")


@dp.message_handler(regexp=r"^(@\S+|/info)")
@usage("Формат команды: /info @username")
async def info(message: types.Message, state: FSMContext):
    data = message.text.split(" ", maxsplit=2)

    if len(data) < 2 and data[0] == "/info":
        raise BadCommandFormat()

    username_to = data[0] if data[0].startswith("@") else data[1]

    # Username must be a dog
    if not username_to.startswith("@"):
        raise BadCommandFormat()

    username_from = message.from_user.username

    if not message.from_user.username:
        await message.answer("У вас должен быть свой username")
        return

    username_from = "@" + username_from

    comments = db.get_trusted_comments(username_from, username_to)

    if not comments:
        await message.answer(f"Нет информации по пользователю {username_to}")
        return

    text = f"Информация по {username_to} для {username_from}:\n"
    for comment in comments:
        text += f"{comment.user_from} {comment.relation_s}: {comment.comment}\n"

    await message.answer(text)


@dp.message_handler(commands=["help"])
async def command_help(message: types.Message, state: FSMContext):
    await message.answer("Этот бот позволяет оценивать\\комментировать разных пользователей Telegram. "
                         "Запрашивая информацию о пользователе, вы видите отзывы только тех людей, о ком сами "
                         "оставили положительный отзыв; а также от тех, кому они оставили положительный отзыв, "
                         "и далее по цепочке до 3 человек\n\n"
                         "Положительный отзыв: _+ @пользователь комментарий_\n"
                         "Отрицательный отзыв: _- @пользователь комментарий_\n"
                         "Информация о пользователе: _@пользователь_", parse_mode="Markdown")


async def backup():
    while True:
        await sleep(BotSettings.backup_timeout())
        db.save_backup()


if __name__ == '__main__':
    dp.loop.create_task(backup())
    executor.start_polling(dp, skip_updates=True)
