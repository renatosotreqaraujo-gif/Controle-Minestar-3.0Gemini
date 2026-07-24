"""
Importação de ativos via Excel.

Aceita colunas (nome flexível, sem case-sensitive):
  - nome / name / ativo / equipamento
  - ip / ip address / endereco ip
  - grupo / group / frota   (opcional)

Ativos com IP que já existe no banco são atualizados (nome/grupo);
IPs novos são inseridos. Isso permite reimportar a planilha
periodicamente sem duplicar nada.
"""
import io
import pandas as pd
from sqlalchemy.orm import Session
from .database import Asset

COLUMN_ALIASES = {
    "name": ["nome", "name", "ativo", "equipamento", "descricao", "descrição"],
    "ip": ["ip", "ip address", "endereco ip", "endereço ip", "ip_address"],
    "group": ["grupo", "group", "frota", "setor", "area", "área"],
}


def _find_column(columns, aliases):
    lower_map = {c.lower().strip(): c for c in columns}
    for alias in aliases:
        if alias in lower_map:
            return lower_map[alias]
    return None


def import_assets_from_excel(db: Session, file_bytes: bytes) -> dict:
    df = pd.read_excel(io.BytesIO(file_bytes))
    columns = list(df.columns)

    name_col = _find_column(columns, COLUMN_ALIASES["name"])
    ip_col = _find_column(columns, COLUMN_ALIASES["ip"])
    group_col = _find_column(columns, COLUMN_ALIASES["group"])

    if not ip_col:
        raise ValueError(
            "Não encontrei uma coluna de IP na planilha. "
            "Use um cabeçalho como 'IP', 'Endereço IP' ou 'IP Address'."
        )

    created, updated, skipped = 0, 0, 0

    for _, row in df.iterrows():
        ip = str(row[ip_col]).strip()
        if not ip or ip.lower() == "nan":
            skipped += 1
            continue

        name = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else ip
        group = str(row[group_col]).strip() if group_col and pd.notna(row[group_col]) else "Geral"

        existing = db.query(Asset).filter(Asset.ip == ip).first()
        if existing:
            existing.name = name
            existing.group = group
            updated += 1
        else:
            db.add(Asset(name=name, ip=ip, group=group, active=True))
            created += 1

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}
