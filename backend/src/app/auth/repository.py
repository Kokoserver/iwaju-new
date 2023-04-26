from fastapi import Request
from src.app.user.model import User
from src.base.repository.base_repository import BaseRepository
from src.app.auth import model, schema
from src.lib.utils.security import JWTAUTH


class AuthTokeRepository(BaseRepository[model.AuthToken]):
    def __init__(self):
        super().__init__(model.AuthToken)

    async def create(
        self, user: User, request: Request, access_token: str, refresh_token: str
    ) -> model.AuthToken:
        user_ip: str = self.get_user_ip(request)

        check_token = await super().get_by_attr(
            attr=dict(ip_address=user_ip), first=True
        )
        if check_token:
            result = await super().update(
                check_token.id,
                dict(
                    access_token=access_token,
                    refresh_token=refresh_token,
                ),
            )
            return result
        new_auth_token = await super().create(
            dict(
                access_token=access_token,
                refresh_token=refresh_token,
                ip_address=user_ip,
                user_id=user.id,
            )
        )
        return new_auth_token

    def get_user_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0]
        elif real_ip:
            client_ip = real_ip
        else:
            client_ip = request.client.host
        return client_ip

    async def get_by_ip(self, ip_address: str) -> model.AuthToken:
        return await super().get_by_attr(attr=dict(ip_address=ip_address), first=True)


auth_token_repo = AuthTokeRepository()
