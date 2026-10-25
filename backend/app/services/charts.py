"""Static matplotlib charts for the PDF report (PNG bytes). Failures are handled by the caller."""
import io
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from app.schemas import UserContext  # noqa: E402

INK, ROSE, TEAL = "#3b2f3a", "#c4456e", "#2f8f8a"
HEAT = LinearSegmentedColormap.from_list("heat", ["#f6f1f4", "#f3c6d5", "#c4456e"])
FLOW = {"none": 0, "spotting": 1, "light": 2, "medium": 3, "heavy": 4}


def _png(fig: Any) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def timeline_png(ctx: UserContext) -> bytes:
    """Daily pain bars with flow shading and period-start markers."""
    logs = sorted(ctx.logs, key=lambda x: x.date)
    fig, ax = plt.subplots(figsize=(7.2, 1.9))
    dates = [x.date for x in logs]
    ax.bar(dates, [x.pain_level or 0 for x in logs], color=ROSE, width=0.8, label="Pain (0-10)")
    ax.fill_between(dates, [FLOW[x.flow] * 2.5 for x in logs], color=TEAL, alpha=0.25, step="mid",
                    label="Flow")
    for c in ctx.cycles:
        if dates and dates[0] <= c.start_date <= dates[-1]:
            ax.axvline(c.start_date, color=INK, lw=0.8, ls="--")
    ax.set_ylim(0, 10)
    ax.legend(loc="upper right", fontsize=6, frameon=False, ncol=2)
    ax.tick_params(labelsize=6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _png(fig)


def heatmap_png(spec: dict[str, Any] | None) -> bytes | None:
    """Symptom x day heat strip from the Health Story `symptom_heatmap` chart data."""
    if not spec or not spec.get("data"):
        return None
    rows = spec["data"]
    grid = [[(v if v is not None else 0) for v in r["levels"]] for r in rows]
    fig, ax = plt.subplots(figsize=(7.2, 0.22 * len(rows) + 0.4))
    ax.imshow(grid, aspect="auto", cmap=HEAT, vmin=0, vmax=5)
    ax.set_yticks(range(len(rows)), [r["key"].replace("_", " ") for r in rows], fontsize=6)
    dates = (spec.get("meta") or {}).get("dates", [])
    if dates:
        ticks = list(range(0, len(dates), max(1, len(dates) // 6)))
        ax.set_xticks(ticks, [dates[i][5:] for i in ticks], fontsize=6)
    for s in ax.spines.values():
        s.set_visible(False)
    return _png(fig)
