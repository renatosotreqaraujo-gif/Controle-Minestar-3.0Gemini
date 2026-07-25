"""
Mapeia o prefixo do TAG do equipamento (ex: "CA101" -> "CA") para um tipo de
equipamento legível e um ícone. Baseado nos prefixos reais encontrados no
Cadastro de Equipamentos da Sotreq/CAT.
"""

# Ordem importa: prefixos mais específicos/longos primeiro
EQUIPMENT_TYPES = [
    ("1LT", "Veículo Leve", "light_vehicle"),
    ("BM", "Veículo de Apoio (Perfuração/MSR)", "support"),
    ("CA", "Caminhão Fora de Estrada", "truck"),
    ("EC", "Escavadeira Hidráulica", "excavator"),
    ("ES", "Pá Carregadeira de Cabo (Shovel)", "shovel"),
    ("PC", "Carregadeira de Rodas", "loader"),
    ("PZ", "Perfuratriz", "drill"),
    ("MA", "Motoniveladora", "grader"),
    ("GD", "Motoniveladora", "grader"),
    ("TT", "Trator de Esteira", "dozer"),
    ("TU", "Trator de Pneu", "wheel_dozer"),
    ("RP", "Pá Carregadeira", "shovel"),
]

DEFAULT_TYPE = ("Outro / Não Classificado", "generic")


def classify_tag(tag: str) -> tuple[str, str]:
    """Retorna (label, icon_key) para um TAG de equipamento, ex: 'CA101'."""
    tag = (tag or "").strip().upper()
    for prefix, label, icon in EQUIPMENT_TYPES:
        if tag.startswith(prefix):
            return label, icon
    return DEFAULT_TYPE


# Tipos de ativo padrão que todo equipamento deve ter
ASSET_TYPES = ["MEMS", "DISPLAY", "DIM_RIM_PLE", "AVI_LTE"]

ASSET_TYPE_LABELS = {
    "MEMS": "MEMS",
    "DISPLAY": "Display (G407/G610)",
    "DIM_RIM_PLE": "DIM/RIM/PLE",
    "AVI_LTE": "AVI LTE (Rádio)",
}
