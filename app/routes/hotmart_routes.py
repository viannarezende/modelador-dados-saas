import os
from datetime import datetime, timedelta,timezone

from fastapi import APIRouter, Request, Header, HTTPException, Body

from app.database.connection import SessionLocal
from app.database.models import User, LogRenovacaoCreditos

from app.services.limites_service import obter_ou_criar_uso_mensal


router = APIRouter()


@router.post("/webhook/hotmart")
async def webhook_hotmart(
    request: Request,
    payload: dict = Body(...),
    x_hotmart_hottok: str | None = Header(default=None),
):
    hottok_configurado = os.getenv("HOTMART_HOTTOK")

    if not hottok_configurado or x_hotmart_hottok != hottok_configurado:
        raise HTTPException(status_code=401, detail="Webhook não autorizado")
    
  



    evento = payload.get("event")
    dados = payload.get("data", {})

    comprador = dados.get("buyer", {})
    compra = dados.get("purchase", {})
    oferta = compra.get("offer", {})

    email = comprador.get("email")
    oferta_codigo = str(oferta.get("code"))

    if not email:
        return {"ok": True, "mensagem": "Evento sem e-mail do comprador"}

    if evento not in ["PURCHASE_APPROVED", "PURCHASE_COMPLETE"]:
        return {"ok": True, "mensagem": f"Evento ignorado: {evento}"}

    plano_id = None

    if oferta_codigo == os.getenv("HOTMART_OFERTA_BASICO_ID"):
        plano_id = 1

    elif oferta_codigo == os.getenv("HOTMART_OFERTA_PROFISSIONAL_ID"):
        plano_id = 2

    if not plano_id:
        return {
            "ok": True,
            "mensagem": f"Oferta não mapeada: {oferta_codigo}",
        }

    db = SessionLocal()

    try:
        usuario = db.query(User).filter(User.email == email).first()

        if not usuario:
            return {"ok": True, "mensagem": "Usuário ainda não cadastrado"}

        usuario.plano_id = plano_id
        usuario.plano_ativo = True
        usuario.pagamento_confirmado = True
        usuario.plano_inicio = datetime.now(timezone.utc)

        uso = obter_ou_criar_uso_mensal(db, usuario.id)

        log_renovacao = LogRenovacaoCreditos(
            usuario_id=usuario.id,
            plano_id=plano_id,
            geracoes_completas_usadas_antes=uso.geracoes_completas_usadas,
            ajustes_usados_antes=uso.ajustes_usados,
            tokens_entrada_antes=uso.tokens_entrada,
            tokens_saida_antes=uso.tokens_saida,
            tokens_total_antes=uso.tokens_total,
            origem="hotmart",
        )

        db.add(log_renovacao)

        uso.geracoes_completas_usadas = 0
        uso.ajustes_usados = 0
        uso.tokens_entrada = 0
        uso.tokens_saida = 0
        uso.tokens_total = 0

        if plano_id == 1:
            usuario.plano_fim = None

        elif plano_id == 2:
            usuario.plano_fim = datetime.now(timezone.utc) + timedelta(days=30)

        db.commit()

        return {
            "ok": True,
            "mensagem": "Plano ativado com sucesso",
            "email": email,
            "plano_id": plano_id,
            "oferta_codigo": oferta_codigo,
        }

    finally:
        db.close()