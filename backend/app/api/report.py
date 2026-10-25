"""POST /report builds the PDF and stores it; GET /reports/{id}.pdf serves it to its owner."""
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session

from app.api.analyze import analyze_user
from app.api.deps import get_user
from app.config import get_settings
from app.db import get_session
from app.errors import AppError
from app.models.tables import Report, User
from app.schemas import Lang, Summary
from app.services.context import build_context
from app.services.pdf import build_report

router = APIRouter(prefix="/api", tags=["report"])


class ReportRequest(BaseModel):
    lang: Lang = "en"


class ReportResponse(BaseModel):
    report_id: int
    url: str
    summary: Summary


@router.post("/report", response_model=ReportResponse)
def create_report(
    body: ReportRequest, user: User = Depends(get_user), session: Session = Depends(get_session)
) -> ReportResponse:
    assert user.id is not None
    analysis = analyze_user(session, user)
    try:
        data = build_report(build_context(session, user), analysis, body.lang)
    except Exception as exc:  # PDF failures must not leak stack traces to the UI
        raise AppError("report_failed", "We could not build the report. Please try again.", 500) from exc
    row = Report(user_id=user.id, language=body.lang, summary_json=analysis.summary.model_dump())
    session.add(row)
    session.commit()
    session.refresh(row)
    assert row.id is not None
    folder = Path(get_settings().reports_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{row.id}.pdf"
    path.write_bytes(data)
    row.file_path = str(path)
    session.add(row)
    session.commit()
    return ReportResponse(report_id=row.id, url=f"/api/reports/{row.id}.pdf", summary=analysis.summary)


@router.get("/reports/{report_id}.pdf")
def get_report(
    report_id: int, user: User = Depends(get_user), session: Session = Depends(get_session)
) -> FileResponse:
    row = session.get(Report, report_id)
    if row is None or row.user_id != user.id or not Path(row.file_path).is_file():
        raise AppError("report_not_found", "Report not found.", 404)
    return FileResponse(row.file_path, media_type="application/pdf", filename=f"sakhi-report-{report_id}.pdf",
                        content_disposition_type="inline")
