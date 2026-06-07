from app.database.connection import SessionLocal
from app.database.models import User, Plano


def criar_usuario(email: str, senha: str, plano_id: int | None = None):
    db = SessionLocal()

    try:
        plano = db.query(Plano).filter(Plano.id == plano_id).first()

        if not plano:
            raise Exception("Plano selecionado não encontrado")

        existente = db.query(User).filter(User.email == email).first()

        if existente:
            existente.plano_id = plano.id
            existente.plano_ativo = False
            existente.pagamento_confirmado = False
            existente.plano_inicio = None
            existente.plano_fim = None

            db.commit()
            db.refresh(existente)

            return existente

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