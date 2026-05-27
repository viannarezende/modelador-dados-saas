from app.database.connection import SessionLocal
from app.database.models import User, Plano
from datetime import datetime, timedelta


def criar_usuario(email: str, senha: str, plano_id: int | None = None):
    db = SessionLocal()

    try:
        # Verifica se já existe
        existente = db.query(User).filter(User.email == email).first()
        if existente:
            raise Exception("Usuário já existe")

        # Buscar plano selecionado
        plano = db.query(Plano).filter(  Plano.id == plano_id).first()
        if not plano:
            raise Exception("Plano selecionado não encontrado")

        usuario = User(
            email=email,
            senha=senha,
            plano_id=plano.id,
            plano_ativo=False,
            pagamento_confirmado=False,
            plano_inicio=None,
            plano_fim=None,
        )

        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        return usuario

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()