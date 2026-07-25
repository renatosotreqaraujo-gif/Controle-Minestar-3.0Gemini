"""
Importa Equipamentos e seus 4 Ativos padrão (MEMS, DISPLAY, DIM/RIM/PLE,
AVI LTE) a partir da planilha "IPs Automação Mina Convencional" (aba "IPs").

Colunas esperadas na aba (nomes reais encontrados na planilha da Sotreq):
  TAG                          -> tag do equipamento (ex: CA101)
  MODELO                       -> modelo (ex: 793F)
  AVI LTE\\nmine-default        -> IP do ativo AVI_LTE
  G407 /G610/Router            -> IP do ativo DISPLAY
  DIM/TIM/PLE                  -> IP do ativo DIM_RIM_PLE
  MEMS                         -> IP do ativo MEMS

Se os nomes de coluna mudarem um pouco entre revisões da planilha, a busca
abaixo tenta várias variações antes de desistir.
"""
import io
import re
import pandas as pd
from sqlalchemy.orm import Session

from .database import Equipment, Asset
from .equipment_types import classify_tag

COLUMN_CANDIDATES = {
    "AVI_LTE": ["avi lte\nmine-default", "avi lte", "avi lte mine-default"],
    "DISPLAY": ["g407 /g610/router", "g407/g610/router", "g407 / g610 / router", "g407/g610", "display"],
    "DIM_RIM_PLE": ["dim/tim/ple", "dim/rim/ple", "dim tim ple"],
    "MEMS": ["mems"],
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())


def _find_column(columns, candidates: list[str]):
    norm_map = {_norm(c): c for c in columns}
    for cand in candidates:
        if cand in norm_map:
            return norm_map[cand]
    return None


def _clean_ip(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text in ("", "-", "nan", "NaN", "não", "nao"):
        return None
    return text


def import_equipment_from_excel(db: Session, file_bytes: bytes, sheet_name: str = "IPs") -> dict:
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
    columns = list(df.columns)

    tag_col = _find_column(columns, ["tag"])
    model_col = _find_column(columns, ["modelo"])
    if not tag_col:
        raise ValueError("Não encontrei a coluna 'TAG' na planilha. Verifique se a aba correta é 'IPs'.")

    asset_cols = {
        asset_type: _find_column(columns, candidates)
        for asset_type, candidates in COLUMN_CANDIDATES.items()
    }

    equipments_created, equipments_updated = 0, 0
    assets_created, assets_updated = 0, 0

    for _, row in df.iterrows():
        tag = str(row[tag_col]).strip() if pd.notna(row[tag_col]) else ""
        if not tag or tag.lower() == "nan":
            continue

        model = str(row[model_col]).strip() if model_col and pd.notna(row[model_col]) else ""
        machine_type, icon = classify_tag(tag)

        equipment = db.query(Equipment).filter(Equipment.tag == tag).first()
        if equipment:
            equipment.model = model
            equipment.machine_type = machine_type
            equipment.icon = icon
            equipments_updated += 1
        else:
            equipment = Equipment(tag=tag, model=model, machine_type=machine_type, icon=icon)
            db.add(equipment)
            db.flush()  # garante equipment.id disponível
            equipments_created += 1

        for asset_type, col in asset_cols.items():
            ip = _clean_ip(row[col]) if col else None

            asset = (
                db.query(Asset)
                .filter(Asset.equipment_id == equipment.id, Asset.asset_type == asset_type)
                .first()
            )
            if asset:
                asset.ip = ip
                assets_updated += 1
            else:
                db.add(Asset(equipment_id=equipment.id, asset_type=asset_type, ip=ip))
                assets_created += 1

    db.commit()
    return {
        "equipamentos_criados": equipments_created,
        "equipamentos_atualizados": equipments_updated,
        "ativos_criados": assets_created,
        "ativos_atualizados": assets_updated,
    }
