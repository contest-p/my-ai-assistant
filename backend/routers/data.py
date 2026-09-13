from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response

from models.schemas import DataCreate, DataUpdate
from services import analysis_service, export_service, firestore_service

router = APIRouter(prefix="/api/data", tags=["data"])

PUBLIC_FIELDS = ("id", "date", "value", "memo", "category")


def _public(record: dict) -> dict:
    return {field: record.get(field) for field in PUBLIC_FIELDS}


@router.post("", status_code=201)
def create_data(payload: DataCreate):
    return firestore_service.add_data(payload.model_dump())


@router.get("")
def list_data(
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    start_date: str | None = None,
    end_date: str | None = None,
):
    records = firestore_service.query_data(start_date, end_date)
    records.sort(key=lambda r: (r["date"], r.get("created_at")), reverse=True)
    page = records[offset : offset + limit]
    return {"count": len(records), "items": [_public(r) for r in page]}


@router.get("/summary")
def get_summary():
    return analysis_service.get_summary()


@router.get("/export")
def export_data(format: Literal["csv", "json"] = "csv", months: Literal["all", "6", "3"] = "all"):
    content, media_type = export_service.export_data(format, months)
    return Response(content=content, media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="transactions-{months}.{format}"',
        "Cache-Control": "no-store",
    })


@router.put("/{data_id}")
def update_data(data_id: str, payload: DataUpdate):
    fields = payload.model_dump(exclude_unset=True)
    updated = firestore_service.update_data(data_id, fields)
    if updated is None:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다.")
    return updated


@router.delete("/{data_id}")
def delete_data(data_id: str):
    deleted = firestore_service.delete_data(data_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다.")
    return {"deleted": True, "id": data_id}
