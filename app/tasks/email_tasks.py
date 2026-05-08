from app.core.celery_app import celery_app
from app.services.email_service import send_email


@celery_app.task(bind=True, max_retries=3, name="send_email_task")
def send_email_task(
    self,
    to_email: str,
    subject: str,
    body: str,
) -> None:

    retry_delays = [1, 5, 10]

    try:
        send_email(
            to_email=to_email,
            subject=subject,
            body=body,
        )

    except Exception as exc:

        retry_count = self.request.retries

        if retry_count < len(retry_delays):
            raise self.retry(
                exc=exc,
                countdown=retry_delays[retry_count],
            )

        raise exc