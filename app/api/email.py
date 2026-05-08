from fastapi import APIRouter
from app.services.email_service import EmailService

router = APIRouter(prefix="/email", tags=["Email"])

@router.post("/test")
async def send_test_email(to:str):
    service = EmailService()
    await service.send_email(
        to=to,
        subject="Test Email",
        html="<h1>This is a test email</h1><p>Sent from FastAPI</p>"
    )
    return {"message": "Test email sent successfully"}