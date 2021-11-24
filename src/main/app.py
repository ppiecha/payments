import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.main.crud import create_transaction, create_user
from src.main.model import UserResponse, UserRequest, DepositRequest, Transaction, TransferRequest
from src.main.settings import settings, database, init_db
from src.main.utils.constants import CREATE_USER, DEPOSIT_MONEY, TRANSFER_MONEY
from src.main.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


app = FastAPI(title=settings.app_title)


@app.on_event("startup")
async def startup():
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc):
    return PlainTextResponse(str(exc), status_code=400)


@app.exception_handler(Exception)
def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=500)


@app.post(path=CREATE_USER, status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_client(request: UserRequest):
    """Creates client with an assigned wallet"""
    return await create_user(request=request)


@app.post(path=DEPOSIT_MONEY, response_model=Transaction)
async def deposit_money(request: DepositRequest):
    """Creates user deposit"""
    return await create_transaction(to_user_id=request.user_id, amount=request.amount)


@app.post(path=TRANSFER_MONEY, response_model=Transaction)
async def transfer_money(request: TransferRequest):
    """Creates money transfer"""
    return await create_transaction(to_user_id=request.to_user_id, amount=request.amount,
                                    from_user_id=request.from_user_id)


if __name__ == '__main__':
    uvicorn.run(app)
