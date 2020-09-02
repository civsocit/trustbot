from aiogram import types
from typing import Callable, Coroutine
from aiogram.dispatcher import FSMContext


class BadCommandFormat(Exception):
    pass


def usage(usage_text):
    def decorator(func):
        async def wrapped(message: types.Message, state: FSMContext):
            try:
                await func(message, state)
            except BadCommandFormat:
                await message.answer(usage_text)

        return wrapped
    return decorator
