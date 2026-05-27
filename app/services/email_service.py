import os
import aiosmtplib
from email.message import EmailMessage


async def enviar_email(destinatario: str, assunto: str, mensagem: str):
    email = EmailMessage()
    email["From"] = os.getenv("SMTP_FROM")
    email["To"] = destinatario
    email["Subject"] = assunto
    email.set_content(mensagem)

    await aiosmtplib.send(
        email,
        hostname=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", 587)),
        username=os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASSWORD"),
        start_tls=True,
    )