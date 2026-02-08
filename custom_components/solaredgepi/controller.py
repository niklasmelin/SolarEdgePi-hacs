# controller.py
import aiohttp

class SolarEdgeController:
    def __init__(self, host):
        self.host = host
        self.status = {}

    async def send_control(self, payload: dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"http://{self.host}/control", json=payload) as resp:
                data = await resp.json()
                self.status["control"] = data.get("control", self.status.get("control", {}))
