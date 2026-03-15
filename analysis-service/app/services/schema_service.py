from app.database import get_inspector
from app.models.responses import ColumnInfo


def get_tables() -> list[str]:
    inspector = get_inspector()
    return inspector.get_table_names()


def get_columns(table_name: str) -> list[ColumnInfo]:
    inspector = get_inspector()
    tables = inspector.get_table_names()
    if table_name not in tables:
        raise ValueError(f"Table '{table_name}' not found")

    columns = inspector.get_columns(table_name)
    return [
        ColumnInfo(
            name=col["name"],
            type=str(col["type"]),
            nullable=col.get("nullable", True),
        )
        for col in columns
    ]
