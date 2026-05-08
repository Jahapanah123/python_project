import resend

from app.core.config import settings


class EmailService:
    def send_todo_completed_email(self, to_email: str, title: str) -> None:
        resend.api_key = settings.EMAIL_API_KEY

        params = {
            "from": settings.EMAIL_FROM,
            "to": [to_email],
            "subject": "Todo completed",
            "html": f"""
                <h2>Todo Completed ✅</h2>
                <p>Your todo <strong>{title}</strong> has been marked as completed.</p>
            """,
        }

        resend.Emails.send(params)