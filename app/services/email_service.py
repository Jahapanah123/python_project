import httpx
from app.core.config import settings


class EmailService:
    async def send_email(self, to: str, subject: str, html: str):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                settings.EMAIL_PROVIDER_URL,
                headers={
                    "Authorization": f"Bearer {settings.EMAIL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.EMAIL_FROM,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
        
        if response.status_code >= 400:
            raise Exception("Email sending failed")