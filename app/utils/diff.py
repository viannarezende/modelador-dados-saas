import difflib
import re


def limpar_html(texto: str) -> str:
    if not texto:
        return ""

    texto = re.sub(r"<[^>]+>", "", texto)
    texto = texto.replace("&nbsp;", " ")

    return texto


def gerar_diff_html(texto_antigo: str, texto_novo: str) -> str:
    antigo = limpar_html(texto_antigo).splitlines()
    novo = limpar_html(texto_novo).splitlines()

    diff = difflib.HtmlDiff(wrapcolumn=80).make_table(
        antigo,
        novo,
        fromdesc="Modelo anterior",
        todesc="Modelo ajustado",
        context=True,
        numlines=2,
    )

    return diff