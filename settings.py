from dotenv import load_dotenv
from os import getenv

load_dotenv()


class BotSettings:
    @classmethod
    def token(cls) -> str:
        token = getenv("TOKEN")
        if not token:
            raise ValueError("TOKEN variable must be specified")
        return token
