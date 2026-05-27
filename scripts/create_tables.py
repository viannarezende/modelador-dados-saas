from app.database.connection import engine, Base
import app.database.models

print("Criando tabelas no PostgreSQL...")

Base.metadata.create_all(bind=engine)

print("Tabelas criadas com sucesso!")