from pathlib import Path
import shutil
import uuid
from fastapi import UploadFile


EXTENSOES_PERMITIDAS = {".txt", ".csv", ".xlsx", ".xls", ".pdf", ".docx"}

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def salvar_arquivo(upload_file: UploadFile | None) -> str | None:
    if not upload_file or not upload_file.filename:
        return None

    extensao = Path(upload_file.filename).suffix.lower()

    if extensao not in EXTENSOES_PERMITIDAS:
        raise ValueError(
            f"Arquivo inválido. Extensões permitidas: {', '.join(sorted(EXTENSOES_PERMITIDAS))}"
        )

    nome_unico = f"{uuid.uuid4().hex}{extensao}"
    caminho_arquivo = UPLOAD_DIR / nome_unico

    with caminho_arquivo.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return str(caminho_arquivo)