from pathlib import Path
import re
import shutil
import uuid
import os
from app.database.models import HistoricoExecucao
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.utils.auth import senha_valida, gerar_hash_senha, verificar_senha
from app.utils.files import salvar_arquivo
from app.agents.modelador_agent import executar_modelagem
from app.database.connection import SessionLocal, engine
from app.database.models import Base, User
from app.services.planos_seed import criar_planos_padrao
from app.services.limites_service import obter_plano_usuario, obter_ou_criar_uso_mensal, calcular_saldo
from openai import OpenAI, RateLimitError
from datetime import datetime, timedelta


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI(title="Modelador de Dados")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    criar_planos_padrao(db)
finally:
    db.close()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")






def usuario_logado(request: Request) -> bool:
    return "user_id" in request.session


def obter_email_sessao(request: Request) -> str:
    return request.session.get("email", "")


def redirecionar_se_nao_logado(request: Request):
    if not usuario_logado(request):
        return RedirectResponse(url="/login", status_code=303)
    return None

def plano_esta_ativo(usuario):
    if not usuario:
        return False

    if not usuario.plano_ativo:
        return False

    if not usuario.pagamento_confirmado:
        return False

    if not usuario.plano_fim:
        return False

    if usuario.plano_fim < datetime.utcnow():
        return False

    return True


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if usuario_logado(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "erro": None,
            "sucesso": None,
            "email": "",
        },
    )
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, sucesso: str | None = None):
    if usuario_logado(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "erro": None,
            "sucesso": sucesso,
            "email": "",
        },
    )


@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
):
    erro = None
    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

    if not re.match(email_regex, email):
        erro = "Informe um e-mail válido."

    if erro:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "erro": erro,
                "sucesso": None,
                "email": email,
            },
        )

    db = SessionLocal()

    try:
        usuario = db.query(User).filter(User.email == email).first()

        if not usuario:
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={
                    "request": request,
                    "erro": "Usuário não encontrado. Faça cadastro.",
                    "sucesso": None,
                    "email": email,
                },
            )

        if not verificar_senha(senha, usuario.senha):
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={
                    "request": request,
                    "erro": "Senha incorreta.",
                    "sucesso": None,
                    "email": email,
                },
            )

        request.session["user_id"] = usuario.id
        request.session["email"] = usuario.email

    finally:
        db.close()

    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, plano_id: int | None = None):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "request": request,
            "erro": None,
            "email": "",
            "plano_id": plano_id,
        },
    )


@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    confirmar_senha: str = Form(...),
    plano_id: int = Form(...),
):
    erro = None
    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

    if not re.match(email_regex, email):
        erro = "Informe um e-mail válido."
    elif not senha_valida(senha):
        erro = "A senha deve ter no mínimo 8 caracteres, com letras e números."
    elif senha != confirmar_senha:
        erro = "As senhas não coincidem."  

    db = SessionLocal()

    try:
        usuario_existente = db.query(User).filter(User.email == email).first()

        if usuario_existente:
            erro = "Já existe uma conta com este e-mail. Faça login ou use outro e-mail."

        if erro:
            return templates.TemplateResponse(
                request=request,
                name="register.html",
                context={
                    "request": request,
                    "erro": erro,
                    "email": email,
                },
            )

        novo_usuario = User(
            email=email,
            senha=gerar_hash_senha(senha),
            plano_id=plano_id,
            plano_ativo=False,
            pagamento_confirmado=False,
            plano_inicio=None,
            plano_fim=None,
        )

        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)

    finally:
        db.close()

    return RedirectResponse(
    url="/login?sucesso=Cadastro realizado. Agora finalize o pagamento pela Hotmart.",
    status_code=303
    )

@app.get("/dashboard", response_class=HTMLResponse)
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


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.post("/gerar-modelo", response_class=HTMLResponse)
async def gerar_modelo(
    request: Request,
    acao: str = Form(...),
    descricao: str = Form(...),
    banco: str = Form(...),
    padrao_nomenclatura: str = Form(...),
    padrao_abreviacao: str = Form(...),
    etapa: str = Form(...),
    arquivo_nomenclatura: UploadFile | None = File(None),
    arquivo_abreviacao: UploadFile | None = File(None),
):
    redirecionamento = redirecionar_se_nao_logado(request)
    if redirecionamento:
        return redirecionamento

    if "execucao" not in request.session:
        request.session["execucao"] = {
            "em_andamento": False,
            "interrompido": False,
        }

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
                "mostrar_modal": False,
                "historico": [],
                "page": 1,
                "page_size": 5,
                "tem_proxima": False,
                "mostrar_historico": 0,
                "filtro_historico": "todos",
            },
        )

    usuario_id = request.session.get("user_id")

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
    )

    saldo = resultado.get("saldo")


    # Tratamento amigável dos campos
    nomenclatura_info = caminho_arquivo_nomenclatura or "Não informado"
    abreviacao_info = caminho_arquivo_abreviacao or "Não informado"

    if resultado["sucesso"]:
       output_debug = f"""
       <h3>Informações da Solicitação</h3>

       <p><strong>Banco:</strong> {banco}</p>
       <p><strong>Etapa:</strong> {etapa}</p>
       <p><strong>Nomenclatura:</strong> {nomenclatura_info}</p>
       <p><strong>Abreviação:</strong> {abreviacao_info}</p>

       <hr>

       {resultado["output"]}
       """
    else:
        output_debug = resultado["output"]

    if request.session.get("execucao", {}).get("interrompido"):
        output_debug = "Execução interrompida pelo usuário."

    request.session["execucao"]["em_andamento"] = False

    page = 1
    page_size = 5
    offset = (page - 1) * page_size
    filtro_historico = "todos"

    db = SessionLocal()
    try:
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

    finally:
        db.close()

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
            "page": page,
            "page_size": page_size,
            "tem_proxima": tem_proxima,
            "mostrar_historico": 1,
            "filtro_historico": filtro_historico,
        },
    )


@app.post("/parar-execucao", response_class=HTMLResponse)
def parar_execucao(request: Request):
    redirecionamento = redirecionar_se_nao_logado(request)
    if redirecionamento:
        return redirecionamento

    request.session["execucao"] = {
    "em_andamento": False,
    "interrompido": True,
}

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "output": "Execução interrompida pelo usuário.",
            "email": obter_email_sessao(request),
        },
    )

@app.get("/planos", response_class=HTMLResponse)
def pagina_planos(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="planos.html",
        context={"request": request},
    )



@app.get("/teste")
def teste():
    return "FUNCIONANDO 123"

@app.get("/dev/ativar-usuario")
def dev_ativar_usuario(email: str):
    db = SessionLocal()

    try:
        usuario = db.query(User).filter(User.email == email).first()

        if not usuario:
            return {"erro": "Usuário não encontrado"}

        usuario.plano_id = usuario.plano_id or 1
        usuario.plano_ativo = True
        usuario.pagamento_confirmado = True
        usuario.plano_inicio = datetime.utcnow()
        usuario.plano_fim = datetime.utcnow() + timedelta(days=30)

        db.commit()

        return {
            "mensagem": "Usuário ativado por 30 dias",
            "email": usuario.email,
            "plano_id": usuario.plano_id,
            "plano_fim": usuario.plano_fim,
        }

    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)