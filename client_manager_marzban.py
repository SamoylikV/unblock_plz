import asyncio
import uuid
from datetime import datetime, timedelta

import qrcode
from marzban import MarzbanAPI, UserCreate, ProxySettings
from config import MARZBAN_URL, MARZBAN_TOKEN


class MarzbanClientManager:
    def __init__(self):
        self.api = MarzbanAPI(base_url=MARZBAN_URL)
        self.token = MARZBAN_TOKEN


    def generate_clients(self, email, days):
        client = UserCreate(username=f"{email}", proxies={"vless": ProxySettings(flow="xtls-rprx-vision")},
                          inbounds={'vless': ['VLESS TCP REALITY']}, expire=int((datetime.now() + timedelta(days=days)).timestamp()))
        return client

    async def get_vless(self, username: str):
        try:
            user_info = await self.api.get_user(username=username, token=self.token)
            vless_key = user_info.links[0]
            return vless_key
        except Exception as e:
            raise Exception(f"{username}\n{e}")

    async def add_clients(self, client):
        try:
            added_client = await self.api.add_user(user=client, token=self.token)
            return added_client
        except Exception as e:
            raise Exception(e)

    def generate_qr(self, key):
        unique_name = f"qr_{uuid.uuid4().hex}.png"
        img = qrcode.make(key)
        img.save(unique_name)
        return unique_name