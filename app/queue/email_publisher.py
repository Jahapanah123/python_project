from app.queue.email_tasks import send_todo_completed_email


class EmailPublisher:

    def send_todo_completed_email(
        self,
        to_email: str,
        title: str,
    ) -> None:

        send_todo_completed_email.delay(
            to_email=to_email,
            title=title,
        )