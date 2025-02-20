import json
import uuid

import qrcode
import requests
from datetime import datetime, timedelta
from config import SERVER_IP
from urllib.parse import quote
from config import AUTH_URL, USERNAME, PASSWORD

class ClientManager:
    def __init__(self):
        self.auth_url = AUTH_URL
        self.username = USERNAME
        self.password = PASSWORD
        self.session = requests.Session()
        self.session_cookie = None

    def authenticate(self):
        auth_data = {"username": self.username, "password": self.password}
        auth_response = self.session.post(self.auth_url, data=auth_data)

        if auth_response.status_code != 200:
            raise Exception(f"{auth_response.status_code}\n{auth_response.text}")

        try:
            auth_json = auth_response.json()
            if not auth_json.get("success"):
                raise Exception(auth_json)
        except json.JSONDecodeError:
            raise Exception(auth_response.text)

        self.session_cookie = self.session.cookies.get("3x-ui")

    def generate_clients(self, email, days):
        clients = []
        expiry_time = int((datetime.now() + timedelta(days=days)).timestamp() * 1000)
        clients.append({
            "id": str(uuid.uuid4()),
            "flow": "",
            "email": f"@{email}",
            "limitIp": 0,
            "totalGB": 0,
            "expiryTime": expiry_time,
            "enable": True,
            "tgId": "",
            "subId": uuid.uuid4().hex[:12],
            "reset": 0
        })
        return clients

    def get_vless(self, email):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cookie": f"3x-ui={self.session_cookie}"
        }
        url = "http://" + self.auth_url.split("/")[2] + "/" + self.auth_url.split("/")[3] + "/" + "panel/inbound/list"

        data = {
            "id": 3
        }

        inbound_data = self.session.post(url, headers=headers, data=json.dumps(data)).json()["obj"][1]
        for elem in inbound_data["clientStats"]:
            if elem["email"] == f"@{email}":
                settings = json.loads(inbound_data["settings"])
                client = next(c for c in settings["clients"] if c["email"] == f"@{email}")
                client_uuid = client["id"]

                stream_settings = json.loads(inbound_data["streamSettings"])
                reality_settings = stream_settings["realitySettings"]

                port = inbound_data["port"]
                network = stream_settings["network"]
                security = stream_settings["security"]
                sni = reality_settings["dest"].split(":")[0]
                pbk = reality_settings["settings"]["publicKey"]
                fp = reality_settings["settings"]["fingerprint"]
                sid = reality_settings["shortIds"][0]
                spx = quote(reality_settings["settings"]["spiderX"])

                remark = inbound_data["remark"]
                client_name = f"{remark}-{elem['email']}"
                encoded_name = quote(client_name)

                vless_key = (
                    f"vless://{client_uuid}@{SERVER_IP}:{port}?"
                    f"type={network}&"
                    f"security={security}&"
                    f"pbk={pbk}&"
                    f"fp={fp}&"
                    f"sni={sni}&"
                    f"sid={sid}&"
                    f"spx={spx}"
                    f"#{encoded_name}"
                )

                return vless_key



    def add_clients(self, clients):
        url = "http://" + self.auth_url.split("/")[2] + "/" + self.auth_url.split("/")[3] + "/" + "panel/api/inbounds/addClient"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cookie": f"3x-ui={self.session_cookie}"
        }

        data = {
            "id": 3,
            "settings": json.dumps({"clients": clients})
        }

        response = self.session.post(url, headers=headers, data=json.dumps(data))

        if response.status_code != 200:
            raise Exception(f"О{response.status_code}\n{response.text}")

        return response.json()

    def generate_qr(self, key):
        unique_name = f"qr_{uuid.uuid4().hex}.png"
        img = qrcode.make(key)
        img.save(unique_name)
        return unique_name