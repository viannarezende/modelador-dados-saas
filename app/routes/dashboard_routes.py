from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database.connection import SessionLocal
from app.database.models import User, HistoricoExecucao
from app.utils.session import plano_esta_ativo
from app.services.limites_service import (
    obter_plano_usuario,
    obter_ou_criar_uso_mensal,
    calcular_saldo
)

from app.utils.session import (
    obter_email_sessao,
    redirecionar_se_nao_logado,
    usuario_logado,
)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")



@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    page: int = 1,
    mostrar_historico: int = 0,
    filtro_historico: str = "todos",
):
    redirecionamento = redirecionar_se_nao_logado(request)
    if redirecionamento:
        return redirecionamento

    usuario_id = request.session.get("user_id")
    db = SessionLocal()
    try:
        usuario = db.query(User).filter(User.id == usuario_id).first()

        if not plano_esta_ativo(usuario):
            return RedirectResponse(
                url="/planos",
                status_code=303
            )
    finally:
        db.close()
    page_size = 5
    offset = (page - 1) * page_size

    saldo = None
    historico = []
    tem_proxima = False

    db = SessionLocal()
    try:
        plano = obter_plano_usuario(db, usuario_id)
        uso = obter_ou_criar_uso_mensal(db, usuario_id)
        saldo = calcular_saldo(plano, uso)

        query_historico = db.query(HistoricoExecucao).filter(
            HistoricoExecucao.usuario_id == usuario_id
        )

        if filtro_historico != "todos":
            query_historico = query_historico.filter(
                HistoricoExecucao.acao == filtro_historico
            )

        total_historico = query_historico.count()

        historico = (
            query_historico
            .order_by(HistoricoExecucao.id.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        tem_proxima = total_historico > (page * page_size)

    except Exception:
        saldo = None
        historico = []
        tem_proxima = False

    finally:
        db.close()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "output": None,
            "email": obter_email_sessao(request),
            "saldo": saldo,
            "historico": historico,
            "page": page,
            "page_size": page_size,
            "tem_proxima": tem_proxima,
            "mostrar_historico": mostrar_historico,
            "filtro_historico": filtro_historico,
        },
    )