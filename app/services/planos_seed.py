from sqlalchemy.orm import Session

from app.database.models import Plano


def criar_planos_padrao(db: Session) -> None:
    planos = [
        {
            "id": 1,
            "nome": "BASICO",
            "limite_geracoes_completas": 5,
            "limite_ajustes": 15,
            "valor_mensal": 29,
            "ativo": True,
        },
        {
            "id": 2,
            "nome": "PROFISSIONAL",
            "limite_geracoes_completas": 15,
            "limite_ajustes": 50,
            "valor_mensal": 59,
            "ativo": True,
        },
        {
            "id": 3,
            "nome": "PREMIUM",
            "limite_geracoes_completas": 50,
            "limite_ajustes": 100,
            "valor_mensal": 99,
            "ativo": True,
        },
    ]

    for plano_data in planos:
        existe = db.query(Plano).filter(Plano.id == plano_data["id"]).first()
        if not existe:
            db.add(Plano(**plano_data))

    db.commit()