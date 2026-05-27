from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Form
from app.database.connection import SessionLocal
from app.database.models import User
from app.utils.auth import verificar_senha
from app.utils.auth import gerar_hash_senha, verificar_senha
import re
from app.utils.auth import senha_valida, gerar_hash_senha
from app.services.user_service import criar_usuario
from typing import Optional
from app.services.password_service import resetar_senha_por_email
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, sucesso: str | None = None):
    if "user_id" in request.session:
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

@router.post("/login", response_class=HTMLResponse)
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

@router.post("/esqueci-senha", response_class=HTMLResponse)
async def esqueci_senha(
    request: Request,
    email: str = Form(...),
):
    await resetar_senha_por_email(email)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "mensagem_sucesso": (
                "Se o e-mail existir, uma nova senha foi enviada."
            ),
        },
    )

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, plano_id: Optional[int] = None):
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

@router.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    confirmar_senha: str = Form(...),
    plano_id: Optional[int] = Form(None),
):
    erro = None
    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

    if not re.match(email_regex, email):
        erro = "Informe um e-mail válido."
    elif not senha_valida(senha):
        erro = "A senha deve ter no mínimo 8 caracteres, com letras e números."
    elif senha != confirmar_senha:
        erro = "As senhas não coincidem."

    if erro:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "request": request,
                "erro": erro,
                "email": email,
                "plano_id": plano_id,
            },
        )

    try:
        criar_usuario(
            email=email,
            senha=gerar_hash_senha(senha),
            plano_id=plano_id,
        )

    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "request": request,
                "erro": str(e),
                "email": email,
                "plano_id": plano_id,
            },
        )

    return RedirectResponse(
        url="/pagamento-pendente",
        status_code=303
    )


@router.get("/pagamento-pendente", response_class=HTMLResponse)
def pagamento_pendente(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pagamento_pendente.html",
        context={
            "request": request,
            "checkout_basico": os.getenv("HOTMART_CHECKOUT_BASICO"),
            "checkout_profissional": os.getenv("HOTMART_CHECKOUT_PROFISSIONAL"),
        },
    )


@router.post("/alterar-senha", response_class=HTMLResponse)
async def alterar_senha(
    request: Request,
    senha_atual: str = Form(...),
    nova_senha: str = Form(...),
    confirmar_senha: str = Form(...),
):
    usuario_id = request.session.get("user_id")

    if not usuario_id:
        return RedirectResponse(url="/login", status_code=303)

    if nova_senha != confirmar_senha:
        return RedirectResponse(url="/dashboard?erro_senha=senhas_diferentes", status_code=303)

    db = SessionLocal()

    try:
        usuario = db.query(User).filter(User.id == usuario_id).first()

        if not usuario:
            return RedirectResponse(url="/login", status_code=303)

        if not verificar_senha(senha_atual, usuario.senha):
            return RedirectResponse(url="/dashboard?erro_senha=senha_atual_incorreta", status_code=303)

        usuario.senha = gerar_hash_senha(nova_senha)
        db.commit()

        return RedirectResponse(url="/dashboard?senha_alterada=1", status_code=303)

    finally:
        db.close()