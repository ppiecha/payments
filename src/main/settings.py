from databases import Database
from pydantic import BaseSettings, PostgresDsn

from src.main.utils.constants import DATABASE_URL, APP_TITLE, YES, NO, USERS, TRANSACTIONS, WALLETS
from src.main.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


class Settings(BaseSettings):
    """Automatically read modifications to the configuration from environment variables"""
    app_title: str = APP_TITLE
    testing: str = NO
    DATABASE_URL: PostgresDsn = DATABASE_URL
    pool_min: int = 5
    pool_max: int = 25


class AsyncDatabase:
    """Database configuration based on settings"""
    def __init__(self, settings: Settings):
        logger.info(f'Connecting to {settings.DATABASE_URL}')
        if settings.testing == YES:
            self.database = Database(settings.DATABASE_URL, min_size=settings.pool_min, max_size=settings.pool_max,
                                     force_rollback=True)
            logger.info('Connected (testing mode)')
        else:
            self.database = Database(settings.DATABASE_URL, min_size=settings.pool_min, max_size=settings.pool_max)
            logger.info('Connected')


settings = Settings()
database = AsyncDatabase(settings=settings).database


async def init_db():
    """Initialises connection and creates tables if they don't exist"""
    await database.connect()
    await database.execute(USERS)
    await database.execute(WALLETS)
    await database.execute(TRANSACTIONS)
