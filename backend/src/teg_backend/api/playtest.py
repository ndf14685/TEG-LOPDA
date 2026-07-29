from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from ..api.admin import admin_auth

router = APIRouter(prefix="/api/playtest", tags=["playtest"])
admin_router = APIRouter(prefix="/api/admin/playtest", tags=["admin-playtest"], dependencies=[Depends(admin_auth)])


class SessionBody(BaseModel):
    session_id: str | None = Field(default=None, max_length=80)
    game_id: str | None = Field(default=None, max_length=80)
    player_id: str | None = Field(default=None, max_length=80)
    player_alias: str | None = Field(default=None, max_length=80)
    build_version: str | None = Field(default=None, max_length=120)
    user_agent: str | None = Field(default=None, max_length=500)
    viewport: dict = Field(default_factory=dict)


class ActionBody(BaseModel):
    session_id: str = Field(max_length=80)
    game_id: str | None = Field(default=None, max_length=80)
    player_id: str | None = Field(default=None, max_length=80)
    action_type: str = Field(max_length=120)
    event_id: str | None = Field(default=None, max_length=120)
    sequence_number: int | None = None
    data: dict = Field(default_factory=dict)


class IncidentBody(BaseModel):
    category: str = Field(default="other", max_length=80)
    title: str | None = Field(default=None, max_length=160)
    message: str = Field(default="", max_length=4000)
    severity: str | None = Field(default=None, max_length=20)
    error_type: str | None = Field(default=None, max_length=120)
    component: str | None = Field(default=None, max_length=160)
    endpoint: str | None = Field(default=None, max_length=300)
    action: str | None = Field(default=None, max_length=120)
    code: str | None = Field(default=None, max_length=80)
    phase: str | None = Field(default=None, max_length=80)
    session_id: str | None = Field(default=None, max_length=80)
    game_id: str | None = Field(default=None, max_length=80)
    player_id: str | None = Field(default=None, max_length=80)
    player_alias: str | None = Field(default=None, max_length=80)
    request_id: str | None = Field(default=None, max_length=120)
    event_id: str | None = Field(default=None, max_length=120)
    sequence_number: int | None = None
    build_version: str | None = Field(default=None, max_length=120)
    timestamp_local: str | None = Field(default=None, max_length=80)
    url: str | None = Field(default=None, max_length=1000)
    viewport: dict = Field(default_factory=dict)
    browser: str | None = Field(default=None, max_length=500)
    context: dict = Field(default_factory=dict)
    action_trail: list[dict] = Field(default_factory=list, max_length=60)
    recent_errors: list[dict] = Field(default_factory=list, max_length=30)
    screenshot_data_url: str | None = Field(default=None, max_length=3_000_000)


class TriageBody(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    severity: str | None = Field(default=None, max_length=20)
    note: str | None = Field(default=None, max_length=1000)


class PurgeBody(BaseModel):
    days: int | None = Field(default=None, ge=1, le=365)
    delete_attachments: bool = False
    keep_confirmed: bool = True


def svc(request: Request):
    service = getattr(request.app.state, "playtest", None)
    if service is None:
        raise HTTPException(status_code=503, detail={"code": "PLAYTEST_UNAVAILABLE", "message": "playtest no inicializado"})
    return service


@router.get("/status")
async def status(request: Request) -> dict:
    return svc(request).status()


@router.post("/sessions")
async def session(body: SessionBody, request: Request) -> dict:
    return await svc(request).register_session(body.model_dump())


@router.post("/actions")
async def action(body: ActionBody, request: Request) -> dict:
    return await svc(request).add_action(body.model_dump())


@router.post("/incidents")
async def incident(body: IncidentBody, request: Request, x_request_id: str | None = Header(default=None)) -> dict:
    data = body.model_dump()
    data["request_id"] = data.get("request_id") or x_request_id
    try:
        result = await svc(request).create_occurrence(data)
        if body.screenshot_data_url and result.get("incident_id"):
            await svc(request).add_attachment(result["incident_id"], result.get("occurrence_id"), body.screenshot_data_url)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_ATTACHMENT", "message": str(exc)})


@admin_router.get("")
async def admin_list(
    request: Request,
    severity: str = "",
    category: str = "",
    status: str = "",
    build: str = "",
) -> dict:
    return await svc(request).list_admin({"severity": severity, "category": category, "status": status, "build": build})


@admin_router.get("/incidents/{code}")
async def admin_detail(code: str, request: Request) -> dict:
    try:
        return await svc(request).incident_detail(code)
    except ValueError:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "incidente inexistente"})


@admin_router.patch("/incidents/{code}")
async def admin_triage(code: str, body: TriageBody, request: Request) -> dict:
    try:
        return await svc(request).triage(code, body.status, body.severity, body.note)
    except ValueError:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "incidente inexistente"})


@admin_router.post("/export")
async def admin_export(request: Request) -> dict:
    return await svc(request).export()


@admin_router.post("/purge")
async def admin_purge(body: PurgeBody, request: Request) -> dict:
    return await svc(request).purge_old(body.days, body.delete_attachments, body.keep_confirmed)
