from app.database.connection import SessionLocal
from app.database.models import Plano

db = SessionLocal()

planos = [
    Plano(
        nome="Gratuito",
        limite_geracoes_completas=3,
        limite_ajustes=5,
        valor_mensal=0,
        ativo=True,
    ),
    Plano(
        nome="Profissional",
        limite_geracoes_completas=100,
        limite_ajustes=300,
        valor_mensal=4900,
        ativo=True,
    ),
]

for plano in planos:
    existente = db.query(Plano).filter(Plano.nome == plano.nome).first()

    if not existente:
        db.add(plano)

db.commit()
db.close()

print("Planos cadastrados com sucesso!")