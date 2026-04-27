from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    UniqueConstraint,
    DateTime,
)
from app.database.connection import Base
from datetime import datetime
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    senha = Column(String, nullable=False)

    plano_id = Column(Integer, ForeignKey("planos.id"), nullable=True)

    plano_ativo = Column(Boolean, nullable=False, default=False)
    pagamento_confirmado = Column(Boolean, nullable=False, default=False)
    plano_inicio = Column(DateTime, nullable=True)
    plano_fim = Column(DateTime, nullable=True)

    plano = relationship("Plano", back_populates="usuarios")
    usos_mensais = relationship("UsoMensalUsuario", back_populates="usuario")


class Plano(Base):
    __tablename__ = "planos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False, unique=True)
    limite_geracoes_completas = Column(Integer, nullable=False)
    limite_ajustes = Column(Integer, nullable=False)
    valor_mensal = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True)

    usuarios = relationship("User", back_populates="plano")


class UsoMensalUsuario(Base):
    __tablename__ = "uso_mensal_usuario"
    __table_args__ = (
        UniqueConstraint("usuario_id", "ano", "mes", name="uq_uso_usuario_ano_mes"),
    )

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)

    geracoes_completas_usadas = Column(Integer, nullable=False, default=0)
    ajustes_usados = Column(Integer, nullable=False, default=0)

    tokens_entrada = Column(BigInteger, nullable=False, default=0)
    tokens_saida = Column(BigInteger, nullable=False, default=0)
    tokens_total = Column(BigInteger, nullable=False, default=0)

    usuario = relationship("User", back_populates="usos_mensais")

class HistoricoExecucao(Base):
        __tablename__ = "historico_execucao"

        id = Column(Integer, primary_key=True, index=True)
        usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)

        acao = Column(String(30), nullable=False)
        banco = Column(String(30), nullable=False)
        etapa = Column(String(50), nullable=False)

        descricao = Column(String, nullable=False)

        padrao_nomenclatura = Column(String(10), nullable=False)
        padrao_abreviacao = Column(String(10), nullable=False)

        arquivo_nomenclatura = Column(String, nullable=True)
        arquivo_abreviacao = Column(String, nullable=True)

        status = Column(String(20), nullable=False)  # sucesso / erro
        resposta = Column(String, nullable=True)

        tokens_entrada = Column(BigInteger, nullable=False, default=0)
        tokens_saida = Column(BigInteger, nullable=False, default=0)
        tokens_total = Column(BigInteger, nullable=False, default=0) 
        criado_em = Column(String, nullable=False, default=lambda: datetime.now().strftime("%d/%m/%Y %H:%M"))   