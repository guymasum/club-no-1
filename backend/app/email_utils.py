"""Receipt email delivery.

Plain SMTP rather than a vendor SDK on purpose: at this app's scale (one
restaurant, on-demand sends triggered by staff — see POST
/bills/{id}/send-email) a vendor SDK is not justified. Currently configured
against Gmail's relay (smtp.gmail.com, see .env.example for the App
Password requirement), but this function doesn't know or care which
provider it's talking to — any SMTP relay (SMTP2GO, SendGrid, Mailgun,
...) works via the same SMTP_* env vars.
If volume ever grows enough to need templates, webhooks, or deliverability
analytics, swap this module for a provider SDK without touching the caller.

send_email() is a *blocking* call (smtplib does blocking socket I/O). It
must only ever be invoked via asyncio.to_thread(...) from async code —
never awaited directly — or it will stall the event loop for every other
request in flight. See bills.py's send_receipt_email_task for the one
place that's allowed to call it.
"""

import smtplib
from email.message import EmailMessage

from app.config import settings


class EmailSendError(RuntimeError):
    """Raised when the SMTP conversation fails for any reason."""


def send_email(*, to: str, subject: str, body: str, attachment: bytes, attachment_filename: str) -> None:
    if not settings.smtp_host:
        raise EmailSendError("SMTP n'est pas configuré (SMTP_HOST manquant)")

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    message.add_attachment(attachment, maintype="application", subtype="pdf", filename=attachment_filename)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailSendError(str(exc)) from exc
