from sqlalchemy.orm import Session

from app.database.models import HistoricoExecucao


def registrar_historico_execucao(
    db: Session,
    usuario_id: int,
    acao: str,
    banco: str,
    etapa: str,
    descricao: str,
    padrao_nomenclatura: str,
    padrao_abreviacao: str,
    arquivo_nomenclatura: str | None,
    arquivo_abreviacao: str | None,
    status: str,
    resposta: str | None,
    tokens_entrada: int = 0,
    tokens_saida: int = 0,
    tokens_total: int = 0,
) -> HistoricoExecucao:
    historico = HistoricoExecucao(
        usuario_id=usuario_id,
        acao=acao,
        banco=banco,
        etapa=etapa,
        descricao=descricao,
        padrao_nomenclatura=padrao_nomenclatura,
        padrao_abreviacao=padrao_abreviacao,
        arquivo_nomenclatura=arquivo_nomenclatura,
        arquivo_abreviacao=arquivo_abreviacao,
        status=status,
        resposta=resposta,
        tokens_entrada=tokens_entrada,
        tokens_saida=tokens_saida,
        tokens_total=tokens_total,
    )

    db.add(historico)
    db.commit()
    db.refresh(historico)

    return historico