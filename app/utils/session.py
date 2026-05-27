from fastapi import Request
from fastapi.responses import RedirectResponse


def usuario_logado(request: Request) -> bool:
    return "user_id" in request.session


def obter_email_sessao(request: Request) -> str:
    return request.session.get("email", "")


def redirecionar_se_nao_logado(request: Request):
    if not usuario_logado(request):
        return RedirectResponse(url="/login", status_code=303)
    return None

from datetime import datetime

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