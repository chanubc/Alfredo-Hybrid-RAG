import httpx

from app.config import settings


class TelegramClient:
    @property
    def _base(self) -> str:
        return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    async def send_message(self, chat_id: int, text: str) -> None:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._base}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            )

    async def set_webhook(self, url: str) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base}/setWebhook",
                json={"url": url},
            )
            resp.raise_for_status()
