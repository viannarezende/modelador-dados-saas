import secrets
import string

from app.database.connection import SessionLocal
from app.database.models import User
from app.utils.auth import gerar_hash_senha
from app.services.email_service import enviar_email


def gerar_senha_temporaria(tamanho: int = 10) -> str:
    caracteres = string.ascii_letters + string.digits
    return "".join(secrets.choice(caracteres) for _ in range(tamanho))


async def resetar_senha_por_email(email: str):
    db = SessionLocal()

    try:
        usuario = db.query(User).filter(User.email == email).first()

        if not usuario:
            return

        nova_senha = gerar_senha_temporaria()

        usuario.senha = gerar_hash_senha(nova_senha)

        db.commit()

        mensagem = f"""
Olá,

Recebemos uma solicitação de recuperação de senha.

Sua nova senha temporária é:

{nova_senha}

Recomendamos alterar a senha após o próximo login.

Atenciosamente,
Equipe Modelador de Dados
"""

        await enviar_email(
            destinatario=email,
            assunto="Recuperação de senha - Modelador de Dados",
            mensagem=mensagem,
        )

    finally:
        db.close()