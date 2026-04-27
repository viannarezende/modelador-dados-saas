# Mapeamento entre o identificador técnico da Hotmart e o plano interno
# Substitua os valores abaixo pelos códigos reais das suas ofertas/planos na Hotmart.

HOTMART_PLANO_MAP = {
    "HOTMART_BASICO": 1,
    "HOTMART_PROFISSIONAL": 2,
    "HOTMART_PREMIUM": 3,
}


def obter_plano_id_hotmart(identificador_hotmart: str) -> int | None:
    if not identificador_hotmart:
        return None

    return HOTMART_PLANO_MAP.get(identificador_hotmart.strip().upper())