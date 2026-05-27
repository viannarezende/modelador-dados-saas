import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.routes import hotmart_routes
from app.database.connection import SessionLocal, engine
from app.database.models import Base, User
from app.routes import auth_routes, dashboard_routes, modelagem_routes
from app.services.planos_seed import criar_planos_padrao
from app.utils.session import (
    usuario_logado,
    obter_email_sessao,
    redirecionar_se_nao_logado,
)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
APP_ENV = os.getenv("APP_ENV", "production")

app = FastAPI(title="Modelador de Dados")
app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(modelagem_routes.router)
app.include_router(hotmart_routes.router)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    criar_planos_padrao(db)
finally:
    db.close()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

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
        context={
            "request": request,
            "checkout_basico": os.getenv("HOTMART_CHECKOUT_BASICO"),
            "checkout_profissional": os.getenv("HOTMART_CHECKOUT_PROFISSIONAL"),
        },
    )



@app.get("/teste")
def teste():
    return "FUNCIONANDO 123"

@app.get("/dev/ativar-usuario")
def dev_ativar_usuario(email: str):
    if APP_ENV != "development":
        return {"erro": "Endpoint disponível apenas em desenvolvimento"}

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