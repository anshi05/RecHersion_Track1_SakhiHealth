import re

import pytest

from app.agents.orchestrator import orchestrate
from app.schemas import AnalyzeResponse, UserContext
from app.services.pdf import build_report
from tests.test_api import env as env  # noqa: F401, PLC0414


def _pdf(ctx: UserContext, lang: str = "en") -> bytes:
    routing, results, summary = orchestrate(ctx)
    a = AnalyzeResponse(
        run_id=0, ran_at="2026-01-01T00:00:00", routing=routing, results=results, summary=summary)
    return build_report(ctx, a, lang)


def _pages(data: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", data))


@pytest.mark.parametrize("key", ["priya", "meena", "sunita"])
def test_pdf_is_valid_and_short(personas: dict[str, UserContext], key: str) -> None:
    data = _pdf(personas[key])
    assert data.startswith(b"%PDF")
    assert 1 <= _pages(data) <= 2


def test_hindi_report_renders(personas: dict[str, UserContext]) -> None:
    data = _pdf(personas["priya"], "hi")
    assert data.startswith(b"%PDF") and _pages(data) <= 2




def test_report_endpoint_roundtrip(env, tmp_path, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    c, _ = env
    r = c.post("/api/report", json={"lang": "en"})
    assert r.status_code == 200
    got = c.get(r.json()["url"])
    assert got.status_code == 200 and got.content.startswith(b"%PDF")
    assert c.get("/api/reports/9999.pdf").json()["error"]["code"] == "report_not_found"
