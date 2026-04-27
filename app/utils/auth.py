import re

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def senha_valida(senha: str) -> bool:
    if len(senha) < 8:
        return False
    if not re.search(r"[A-Za-z]", senha):
        return False
    if not re.search(r"\d", senha):
        return False
    return True


def gerar_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha_texto: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_texto, senha_hash)