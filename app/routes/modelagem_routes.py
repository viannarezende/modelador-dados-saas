from fastapi import APIRouter, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


from app.utils.session import obter_email_sessao, redirecionar_se_nao_logado
from app.utils.files import salvar_arquivo
from app.agents.modelador_agent import executar_modelagem
from app.database.connection import SessionLocal
from app.database.models import HistoricoExecucao

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def carregar_historico_usuario(db, usuario_id: int, page: int = 1, page_size: int = 5):
    offset = (page - 1) * page_size

    query_historico = db.query(HistoricoExecucao).filter(
        HistoricoExecucao.usuario_id == usuario_id
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

    return historico, tem_proxima


@router.post("/gerar-modelo", response_class=HTMLResponse)
async def gerar_modelo(
    request: Request,
    acao: str = Form(...),
    descricao: str = Form(...),
    banco: str | None = Form(None),
    padrao_nomenclatura: str | None = Form(None),
    padrao_abreviacao: str | None = Form(None),
    etapa: str | None = Form(None),
    arquivo_nomenclatura: UploadFile | None = File(None),
    arquivo_abreviacao: UploadFile | None = File(None),
    historico_origem_id: int | None = Form(None),
):
    redirecionamento = redirecionar_se_nao_logado(request)
    if redirecionamento:
        return redirecionamento

    usuario_id = request.session.get("user_id")

    request.session["execucao"] = {
        "em_andamento": True,
        "interrompido": False,
    }

    try:
        caminho_arquivo_nomenclatura = salvar_arquivo(arquivo_nomenclatura)
        caminho_arquivo_abreviacao = salvar_arquivo(arquivo_abreviacao)
    except ValueError as erro:
        request.session["execucao"]["em_andamento"] = False

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "output": str(erro),
                "email": obter_email_sessao(request),
                "saldo": None,
                "historico": [],
                "page": 1,
                "page_size": 5,
                "tem_proxima": False,
                "mostrar_historico": 0,
                "filtro_historico": "todos",
                "modo_ajuste": False,
                "historico_id": None,
               
            },
        )

    db = SessionLocal()

    try:
        historico_origem = None

        if acao == "ajuste":
            if not historico_origem_id:
                raise ValueError("Para realizar um ajuste, selecione um modelo do histórico.")

            historico_origem = db.query(HistoricoExecucao).filter(
                HistoricoExecucao.id == historico_origem_id,
                HistoricoExecucao.usuario_id == usuario_id,
            ).first()

            if not historico_origem:
                raise ValueError("Modelo original não encontrado para ajuste.")

            banco = banco or historico_origem.banco
            etapa = etapa or historico_origem.etapa
            padrao_nomenclatura = padrao_nomenclatura or historico_origem.padrao_nomenclatura
            padrao_abreviacao = padrao_abreviacao or historico_origem.padrao_abreviacao

        if not banco or not etapa or not padrao_nomenclatura or not padrao_abreviacao:
            raise ValueError(
                "Preencha banco, etapa, padrão de nomenclatura e padrão de abreviação."
            )

        resultado = executar_modelagem(
            usuario_id=usuario_id,
            acao=acao,
            descricao=descricao,
            banco=banco,
            etapa=etapa,
            padrao_nomenclatura=padrao_nomenclatura,
            padrao_abreviacao=padrao_abreviacao,
            arquivo_nomenclatura=caminho_arquivo_nomenclatura,
            arquivo_abreviacao=caminho_arquivo_abreviacao,
            historico_origem_id=historico_origem_id,
        )

   

        saldo = resultado.get("saldo")

        nomenclatura_info = caminho_arquivo_nomenclatura or "Não informado"
        abreviacao_info = caminho_arquivo_abreviacao or "Não informado"

        if resultado.get("sucesso"):
            output_debug = f"""
            <h3>Informações da Solicitação</h3>
            <p><strong>Banco:</strong> {banco}</p>
            <p><strong>Etapa:</strong> {etapa}</p>
            <p><strong>Nomenclatura:</strong> {nomenclatura_info}</p>
            <p><strong>Abreviação:</strong> {abreviacao_info}</p>
            <hr>
            {resultado.get("output")}
            """
        else:
            output_debug = resultado.get("output")

        if request.session.get("execucao", {}).get("interrompido"):
            output_debug = "Execução interrompida pelo usuário."

        request.session["execucao"]["em_andamento"] = False

        historico, tem_proxima = carregar_historico_usuario(
            db=db,
            usuario_id=usuario_id,
            page=1,
            page_size=5,
        )

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "output": output_debug,
                "email": obter_email_sessao(request),
                "saldo": saldo,
                "mostrar_modal": True,
                "historico": historico,
                "page": 1,
                "page_size": 5,
                "tem_proxima": tem_proxima,
                "mostrar_historico": 1,
                "filtro_historico": "todos",
                "modo_ajuste": False,
                "historico_id": None,
              
            },
        )

    except ValueError as erro:
        request.session["execucao"]["em_andamento"] = False

        historico, tem_proxima = carregar_historico_usuario(
            db=db,
            usuario_id=usuario_id,
            page=1,
            page_size=5,
        )

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "output": str(erro),
                "email": obter_email_sessao(request),
                "saldo": None,
                "historico": historico,
                "page": 1,
                "page_size": 5,
                "tem_proxima": tem_proxima,
                "mostrar_historico": 1,
                "filtro_historico": "todos",
                "modo_ajuste": acao == "ajuste",
                "historico_id": historico_origem_id,
               
            },
        )

    finally:
        db.close()


@router.post("/ajustar-modelo", response_class=HTMLResponse)
async def ajustar_modelo(
    request: Request,
    historico_id: int = Form(...),
):
    redirecionamento = redirecionar_se_nao_logado(request)
    if redirecionamento:
        return redirecionamento

    usuario_id = request.session.get("user_id")
    db = SessionLocal()

    try:
        historico_origem = db.query(HistoricoExecucao).filter(
            HistoricoExecucao.id == historico_id,
            HistoricoExecucao.usuario_id == usuario_id,
        ).first()

        historico, tem_proxima = carregar_historico_usuario(
            db=db,
            usuario_id=usuario_id,
            page=1,
            page_size=5,
        )

        if not historico_origem:
            return templates.TemplateResponse(
                request=request,
                name="dashboard.html",
                context={
                    "request": request,
                    "output": "Modelo original não encontrado para ajuste.",
                    "email": obter_email_sessao(request),
                    "saldo": None,
                    "historico": historico,
                    "page": 1,
                    "page_size": 5,
                    "tem_proxima": tem_proxima,
                    "mostrar_historico": 1,
                    "filtro_historico": "todos",
                    "modo_ajuste": False,
                    "historico_id": None,
                   
                },
            )

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "historico_id": historico_id,
                "modo_ajuste": True,
                "modelo_base": historico_origem,
                "output": None,
                "email": obter_email_sessao(request),
                "saldo": None,
                "historico": historico,
                "page": 1,
                "page_size": 5,
                "tem_proxima": tem_proxima,
                "mostrar_historico": 1,
                "filtro_historico": "todos",
                
            },
        )

    finally:
        db.close()