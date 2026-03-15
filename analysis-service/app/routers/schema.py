from fastapi import APIRouter, HTTPException

from app.models.responses import TablesResponse, ColumnsResponse
from app.services import schema_service

router = APIRouter(prefix="/api/v1", tags=["schema"])


@router.get("/tables", response_model=TablesResponse)
def list_tables():
    try:
        tables = schema_service.get_tables()
        return TablesResponse(tables=tables)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table_name}/columns", response_model=ColumnsResponse)
def list_columns(table_name: str):
    try:
        columns = schema_service.get_columns(table_name)
        return ColumnsResponse(table=table_name, columns=columns)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
