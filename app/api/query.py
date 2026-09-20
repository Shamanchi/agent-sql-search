"""Эндпоинты схемы, перевода и выполнения."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.services.executor import QueryResult, execute
from app.services.schema import describe_schema
from app.services.translator import Translation, translate

router = APIRouter()


class TranslateRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class ExecuteRequest(BaseModel):
    sql: str = Field(min_length=8, max_length=2000)


@router.get("/schema")
async def schema() -> dict:
    return {"tables": describe_schema()}


@router.post("/translate", response_model=Translation)
async def translate_query(
    request: TranslateRequest,
    settings: Settings = Depends(get_settings),
) -> Translation:
    try:
        return translate(request.question, settings.default_limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/execute", response_model=QueryResult)
async def execute_query(
    request: ExecuteRequest,
    settings: Settings = Depends(get_settings),
) -> QueryResult:
    try:
        return execute(request.sql, settings.max_rows)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
