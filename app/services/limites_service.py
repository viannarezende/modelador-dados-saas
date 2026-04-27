from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models import Plano, UsoMensalUsuario, User


ACOES_VALIDAS = {"geracao_completa", "ajuste"}


def obter_mes_atual() -> tuple[int, int]:
    agora = datetime.now()
    return agora.year, agora.month


def obter_plano_usuario(db: Session, usuario_id: int) -> Plano:
    usuario = db.query(User).filter(User.id == usuario_id).first()

    if not usuario:
        raise ValueError("Usuário não encontrado.")

    if not usuario.plano_id:
        raise ValueError("Usuário sem plano vinculado.")

    plano = db.query(Plano).filter(
        Plano.id == usuario.plano_id,
        Plano.ativo.is_(True),
    ).first()

    if not plano:
        raise ValueError("Plano do usuário não encontrado ou inativo.")

    return plano


def obter_ou_criar_uso_mensal(db: Session, usuario_id: int) -> UsoMensalUsuario:
    ano, mes = obter_mes_atual()

    uso = db.query(UsoMensalUsuario).filter(
        UsoMensalUsuario.usuario_id == usuario_id,
        UsoMensalUsuario.ano == ano,
        UsoMensalUsuario.mes == mes,
    ).first()

    if uso:
        return uso

    uso = UsoMensalUsuario(
        usuario_id=usuario_id,
        ano=ano,
        mes=mes,
        geracoes_completas_usadas=0,
        ajustes_usados=0,
        tokens_entrada=0,
        tokens_saida=0,
        tokens_total=0,
    )
    db.add(uso)
    db.commit()
    db.refresh(uso)
    return uso


def validar_limite(uso: UsoMensalUsuario, plano: Plano, acao: str) -> tuple[bool, str]:
    if acao not in ACOES_VALIDAS:
        return False, "Ação inválida."

    if acao == "geracao_completa":
        if uso.geracoes_completas_usadas >= plano.limite_geracoes_completas:
            return False, "Limite de gerações completas atingido no mês."

    elif acao == "ajuste":
        if uso.ajustes_usados >= plano.limite_ajustes:
            return False, "Limite de ajustes atingido no mês."

    return True, "Permitido"


def registrar_consumo(
    db: Session,
    uso: UsoMensalUsuario,
    acao: str,
    tokens_entrada: int,
    tokens_saida: int,
) -> UsoMensalUsuario:
    if acao == "geracao_completa":
        uso.geracoes_completas_usadas += 1
    elif acao == "ajuste":
        uso.ajustes_usados += 1
    else:
        raise ValueError("Ação inválida para registro de consumo.")

    uso.tokens_entrada += int(tokens_entrada or 0)
    uso.tokens_saida += int(tokens_saida or 0)
    uso.tokens_total += int(tokens_entrada or 0) + int(tokens_saida or 0)

    db.add(uso)
    db.commit()
    db.refresh(uso)
    return uso


def calcular_saldo(plano: Plano, uso: UsoMensalUsuario) -> dict:
    return {
        "plano": plano.nome,
        "limite_geracoes_completas": plano.limite_geracoes_completas,
        "limite_ajustes": plano.limite_ajustes,
        "geracoes_completas_usadas": uso.geracoes_completas_usadas,
        "ajustes_usados": uso.ajustes_usados,
        "geracoes_completas_restantes": max(
            plano.limite_geracoes_completas - uso.geracoes_completas_usadas, 0
        ),
        "ajustes_restantes": max(
            plano.limite_ajustes - uso.ajustes_usados, 0
        ),
        "tokens_entrada": uso.tokens_entrada,
        "tokens_saida": uso.tokens_saida,
        "tokens_total": uso.tokens_total,
    }