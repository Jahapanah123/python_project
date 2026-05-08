from app.queue.celery_app import celery_app
from app.services.email_service import EmailService


@celery_app.task(
    bind=True,
    max_retries=3,
    name="send_todo_completed_email",
)
def send_todo_completed_email(
    self,
    to_email: str,
    title: str,
) -> None:

    retry_delays = [1, 5, 10]

    email_service = EmailService()

    try:
        email_service.send_todo_completed_email(
            to_email=to_email,
            title=title,
        )

    except Exception as exc:

        retry_count = self.request.retries

        if retry_count < len(retry_delays):
            raise self.retry(
                exc=exc,
                countdown=retry_delays[retry_count],
            )

        raise exc