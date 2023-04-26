import typing as t
from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from src.app.auth import schema, service
from src.base.schema.response import ResponseMessage

router = APIRouter(prefix="/auth", tags=["Auth"], include_in_schema=True)


@router.post(
    "/login",
    response_model=t.Union[schema.IToken, ResponseMessage],
    status_code=status.HTTP_200_OK,
)
async def auth_login(
    background_task: BackgroundTasks,
    request: Request,
    data_in: OAuth2PasswordRequestForm = Depends(),
) -> t.Union[schema.IToken, ResponseMessage]:
    return await service.auth_login(
        background_task=background_task, data_in=data_in, request=request
    )


@router.post(
    "/token-refresh",
    response_model=schema.IToken,
    status_code=status.HTTP_200_OK,
)
async def auth_login_token_refresh(data_in: schema.IRefreshToken, request: Request):
    return await service.auth_login_token_refresh(data_in=data_in, request=request)


@router.post("/check/dev", status_code=status.HTTP_200_OK, response_model=ResponseMessage)
async def check_user_email(data_in: schema.ICheckUserEmail) -> ResponseMessage:
    return await service.check_user_email(data_in)
