import os
from pathlib import Path
from app.services.historico_service import registrar_historico_execucao

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

from app.database.connection import SessionLocal
from app.services.limites_service import (
    calcular_saldo,
    obter_ou_criar_uso_mensal,
    obter_plano_usuario,
    registrar_consumo,
    validar_limite,
)

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.4")


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente.")

    return OpenAI(api_key=api_key)


def montar_prompt_modelagem(
    banco: str,
    etapa: str,
    padrao_nomenclatura: str,
    padrao_abreviacao: str,
    descricao: str,
    arquivo_nomenclatura: str | None = None,
    arquivo_abreviacao: str | None = None,
) -> str:
    return f"""
Você é um especialista em modelagem de dados.

Objetivo:
Gerar uma resposta técnica de modelagem de dados com base nas informações abaixo.

Banco de dados: {banco}
Etapa: {etapa}
Padrão de nomenclatura: {padrao_nomenclatura}
Padrão de abreviação: {padrao_abreviacao}

Descrição da solicitação:
{descricao}

Arquivos auxiliares:
- Arquivo de nomenclatura: {arquivo_nomenclatura or "não enviado"}
- Arquivo de abreviação: {arquivo_abreviacao or "não enviado"}

Instruções:
- Responda em português do Brasil.
- Seja objetivo, técnico e organizado.
- Estruture a resposta para exibição em tela.
- Quando fizer sentido, apresente entidades, campos, relacionamentos e observações.
- Retorne a resposta em HTML puro (NÃO usar markdown).
- NÃO use símbolos como ###, **, etc.

- Utilize as seguintes tags HTML:
  <h2>, <h3>, <p>, <ul>, <li>, <strong>, <pre>, <code>

- Estruture a resposta da seguinte forma:

<h2>Título do modelo</h2>

<h3>Entidades</h3>
<ul>
  <li>...</li>
</ul>

<h3>Descrição</h3>
<p>...</p>

<h3>DDL</h3>
<pre>...</pre>

<h3>Observações</h3>
<p>...</p>
- Quando listar campos de tabelas, utilize tabelas HTML (<table>).
- Sempre que possível, apresente os campos no formato:

<table>
  <thead>
    <tr>
      <th>Campo</th>
      <th>Tipo</th>
      <th>Obrigatório</th>
      <th>Descrição</th>
    </tr>
  </thead>
  <tbody>
    ...
  </tbody>
</table>
""".strip()


def executar_modelagem(
    usuario_id: int,
    acao: str,
    descricao: str,
    banco: str,
    etapa: str,
    padrao_nomenclatura: str,
    padrao_abreviacao: str,
    arquivo_nomenclatura: str | None = None,
    arquivo_abreviacao: str | None = None,
) -> dict:
    db = SessionLocal()

    try:
        plano = obter_plano_usuario(db, usuario_id)
        uso = obter_ou_criar_uso_mensal(db, usuario_id)

        permitido, mensagem = validar_limite(uso, plano, acao)
        if not permitido:
            saldo = calcular_saldo(plano, uso)
            return {
                "sucesso": False,
                "output": mensagem,
                "saldo": saldo,
                "tokens_entrada": 0,
                "tokens_saida": 0,
                "tokens_total": 0,
            }

        prompt = montar_prompt_modelagem(
            banco=banco,
            etapa=etapa,
            padrao_nomenclatura=padrao_nomenclatura,
            padrao_abreviacao=padrao_abreviacao,
            descricao=descricao,
            arquivo_nomenclatura=arquivo_nomenclatura,
            arquivo_abreviacao=arquivo_abreviacao,
        )

        client = get_openai_client()

        response = client.responses.create(
            model=MODEL_NAME,
            input=prompt,
        )

        output_text = getattr(response, "output_text", None) or "Nenhuma resposta retornada."

        usage = getattr(response, "usage", None)
        tokens_entrada = getattr(usage, "input_tokens", 0) if usage else 0
        tokens_saida = getattr(usage, "output_tokens", 0) if usage else 0
        tokens_total = getattr(usage, "total_tokens", tokens_entrada + tokens_saida) if usage else 0

        uso = registrar_consumo(
            db=db,
            uso=uso,
            acao=acao,
            tokens_entrada=tokens_entrada,
            tokens_saida=tokens_saida,
        )

        saldo = calcular_saldo(plano, uso)
        registrar_historico_execucao(
            db=db,
            usuario_id=usuario_id,
            acao=acao,
            banco=banco,
            etapa=etapa,
            descricao=descricao,
            padrao_nomenclatura=padrao_nomenclatura,
            padrao_abreviacao=padrao_abreviacao,
            arquivo_nomenclatura=arquivo_nomenclatura,
            arquivo_abreviacao=arquivo_abreviacao,
            status="sucesso",
            resposta=output_text,
            tokens_entrada=tokens_entrada,
            tokens_saida=tokens_saida,
            tokens_total=tokens_total,
        )

        return {
            "sucesso": True,
            "output": output_text,
            "saldo": saldo,
            "tokens_entrada": tokens_entrada,
            "tokens_saida": tokens_saida,
            "tokens_total": tokens_total,
        }

    except RateLimitError as exc:
        mensagem = str(exc)

        if "insufficient_quota" in mensagem or "exceeded your current quota" in mensagem:
            mensagem = (
                "A integração com a OpenAI está configurada, mas a conta está sem saldo/cota no momento. "
                "Assim que a cota for liberada, a geração voltará a funcionar normalmente."
            )
        else:
            mensagem = f"Limite temporário da API atingido: {str(exc)}"

        saldo = calcular_saldo(plano, uso)
        registrar_historico_execucao(
            db=db,
            usuario_id=usuario_id,
            acao=acao,
            banco=banco,
            etapa=etapa,
            descricao=descricao,
            padrao_nomenclatura=padrao_nomenclatura,
            padrao_abreviacao=padrao_abreviacao,
            arquivo_nomenclatura=arquivo_nomenclatura,
            arquivo_abreviacao=arquivo_abreviacao,
            status="erro",
            resposta=mensagem,
        )

        return {
            "sucesso": False,
            "output": mensagem,
            "saldo": saldo,
            "tokens_entrada": 0,
            "tokens_saida": 0,
            "tokens_total": 0,
        }   

    except Exception as exc:
        saldo = calcular_saldo(plano, uso)
        registrar_historico_execucao(
            db=db,
            usuario_id=usuario_id,
            acao=acao,
            banco=banco,
            etapa=etapa,
            descricao=descricao,
            padrao_nomenclatura=padrao_nomenclatura,
            padrao_abreviacao=padrao_abreviacao,
            arquivo_nomenclatura=arquivo_nomenclatura,
            arquivo_abreviacao=arquivo_abreviacao,
            status="erro",
            resposta=str(exc),
        )

        return {
            "sucesso": False,
            "output": f"Erro ao executar modelagem: {str(exc)}",
            "saldo": saldo,
            "tokens_entrada": 0,
            "tokens_saida": 0,
            "tokens_total": 0,
        }

    finally:
        db.close()