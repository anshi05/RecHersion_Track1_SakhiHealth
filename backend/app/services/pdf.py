"""Doctor-ready PDF (guide §5 P8, brief §11.3). fpdf2 with HarfBuzz shaping for Devanagari.
Chart failures degrade to a text-only report."""
import io
import logging
from pathlib import Path
from typing import Any

from fpdf import FPDF

from app.schemas import AnalyzeResponse, UserContext
from app.services import charts

log = logging.getLogger(__name__)
FONTS = Path(__file__).resolve().parents[2] / "assets" / "fonts"
DISCLAIMER = ("Awareness only. This report is not a diagnosis. It shows patterns commonly associated "
              "with health conditions; please discuss it with a doctor.")
HI_DISCLAIMER = "यह रिपोर्ट केवल जागरूकता के लिए है, निदान नहीं। कृपया अपने डॉक्टर से चर्चा करें।"

# Section titles per language. Body text stays English until P11 (i18n).
T: dict[str, dict[str, str]] = {
    "en": {
        "title": "Sakhi Health report", "story": "Your health story", "stats": "Key statistics",
        "timeline": "Cycle timeline (last 90 days)", "heatmap": "Symptom heatmap",
        "findings": "Findings and evidence", "changed": "What changed recently",
        "questions": "Questions to ask your doctor", "tests": "Tests you could ask about",
        "appendix": "Appendix: data summary",
    },
    "hi": {
        "title": "सखी स्वास्थ्य रिपोर्ट", "story": "आपकी स्वास्थ्य कहानी", "stats": "मुख्य आंकड़े",
        "timeline": "चक्र समयरेखा (पिछले 90 दिन)", "heatmap": "लक्षण हीटमैप",
        "findings": "निष्कर्ष और प्रमाण", "changed": "हाल में क्या बदला",
        "questions": "डॉक्टर से पूछने के सवाल", "tests": "जिन जांचों के बारे में पूछ सकती हैं",
        "appendix": "परिशिष्ट: डेटा सारांश",
    },
}
AGENT_TITLE = {"health_story": "Health Story", "pcos_endo": "PCOS / Endometriosis patterns",
               "menopause": "Menopause transition", "maternal": "Pregnancy monitoring"}
PUNCT = {"–": "-", "—": "-", "≥": ">=", "≤": "<=", "’": "'", "‘": "'", "“": '"', "”": '"', "•": "-"}


class Report(FPDF):
    def __init__(self, lang: str) -> None:
        super().__init__(format="A4")
        self.set_auto_page_break(True, margin=12)
        self.set_margins(14, 12, 14)
        self.set_text_shaping(True)
        self.add_font("dev", "", str(FONTS / "mangal.ttf"))
        self.add_font("dev", "B", str(FONTS / "mangalb.ttf"))
        self.fam = "dev" if lang == "hi" else "Helvetica"

    def txt(self, s: str) -> str:
        """Core Helvetica is latin-1 only: map common punctuation, replace the rest."""
        if self.fam == "dev":
            return s
        s = "".join(PUNCT.get(c, c) for c in s)
        return s.encode("latin-1", "replace").decode("latin-1")

    def head(self, s: str) -> None:
        self.set_font(self.fam, "B", 11)
        self.set_text_color(196, 69, 110)
        self.ln(1.5)
        self.cell(0, 6, self.txt(s), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(59, 47, 58)

    def p(self, s: str, size: int = 9, bold: bool = False) -> None:
        self.set_font(self.fam, "B" if bold else "", size)
        self.multi_cell(0, 4.2, self.txt(s), new_x="LMARGIN", new_y="NEXT")

    def bullets(self, items: list[str], size: int = 8) -> None:
        for it in items:
            self.p("- " + it, size)

    def dev_line(self, s: str, size: int = 8) -> None:
        """Always-Devanagari line (shaped): the Hindi risk check inside the English report."""
        self.set_font("dev", "", size)
        self.multi_cell(0, 4.2, s, new_x="LMARGIN", new_y="NEXT")

    def chart(self, png: bytes) -> None:
        self.image(io.BytesIO(png), w=self.epw)


def _stats_rows(hs_stats: dict[str, Any], ctx: UserContext) -> list[tuple[str, str]]:
    cyc = hs_stats.get("cycle") or {}
    rows = [("Days logged", str(len(ctx.logs)))]
    if cyc.get("count"):
        rows += [("Cycles tracked", str(cyc["count"])),
                 ("Average cycle length", f"{cyc['mean']:.0f} days"),
                 ("Shortest / longest", f"{cyc['min']} / {cyc['max']} days")]
    for m in ("bp", "hemoglobin"):
        ms = [x for x in ctx.measurements if x.type == m]
        if ms:
            x = max(ms, key=lambda y: y.date)
            two = m == "bp" and x.value_2
            val = f"{x.value_1:.0f}/{x.value_2:.0f} mmHg" if two else f"{x.value_1:g} {x.unit}"
            rows.append((f"Latest {m}", f"{val} ({x.date})"))
    return rows


def build_report(ctx: UserContext, analysis: AnalyzeResponse, lang: str = "en") -> bytes:
    t = T.get(lang, T["en"])
    pdf = Report(lang if lang in T else "en")
    pdf.add_page()
    logs = sorted(ctx.logs, key=lambda x: x.date)
    span = f"{logs[0].date} to {logs[-1].date}" if logs else "no logs yet"
    hs = next((r for r in analysis.results if r.agent == "health_story"), None)
    hs_stats = hs.stats if hs else {}

    pdf.set_font(pdf.fam, "B", 16)
    pdf.cell(0, 8, pdf.txt(t["title"]), new_x="LMARGIN", new_y="NEXT")
    pdf.p(f"{ctx.profile.name}, age {ctx.age}  |  {span}", 9)
    pdf.set_text_color(110, 100, 108)
    pdf.p(DISCLAIMER, 8)
    pdf.set_text_color(59, 47, 58)

    pdf.head(t["story"])
    pdf.p(analysis.summary.text)

    pdf.head(t["stats"])
    for k, v in _stats_rows(hs_stats, ctx):
        pdf.p(f"{k}: {v}", 8)

    try:
        if logs:
            png = charts.timeline_png(ctx)
            pdf.head(t["timeline"])
            pdf.chart(png)
        spec = next((c.model_dump() for c in hs.charts if c.id == "symptom_heatmap"), None) if hs else None
        png = charts.heatmap_png(spec)
        if png:
            pdf.head(t["heatmap"])
            pdf.chart(png)
    except Exception:  # charts are optional: keep the text report
        log.exception("report charts failed")

    pdf.head(t["findings"])
    for r in analysis.results:
        pdf.p(f"{AGENT_TITLE[r.agent]}: {r.headline}", 9, bold=True)
        pdf.bullets([e.detail for e in r.evidence[:3]])

    notable = [d for d in hs_stats.get("deltas", []) if d.get("notable")]
    if notable:
        pdf.head(t["changed"])
        pdf.bullets([f"{d['metric'].replace('_', ' ')}: {d['previous']} -> {d['recent']} "
                     "(last 14 days vs the 14 before)" for d in notable])

    qs = list(dict.fromkeys(q for r in analysis.results for q in r.questions_for_doctor))[:5]
    if qs:
        pdf.head(t["questions"])
        pdf.bullets(qs)
    tests = list(dict.fromkeys(x for r in analysis.results for x in r.suggested_tests))[:5]
    if tests:
        pdf.head(t["tests"])
        pdf.bullets(tests)

    pdf.head(t["appendix"])
    pdf.p(f"{len(ctx.logs)} daily logs, {len(ctx.cycles)} cycle events, {len(ctx.measurements)} "
          "measurements in the period. Raw data is available in the app.", 8)
    pdf.dev_line(HI_DISCLAIMER)
    return bytes(pdf.output())
