"""Render management Markdown reports as accessible, offline HTML pages."""

import html
import json
import re

import mistune

from .common import REPORTS, ROOT


class ReportRenderer(mistune.HTMLRenderer):
    """Add anchor navigation and scrollable tables without changing evidence."""

    def __init__(self):
        super().__init__(escape=True)
        self.contents = []

    def heading(self, text, level, **attrs):
        if level == 1:
            return ""  # The page header supplies the report title.
        anchor = f"section-{len(self.contents) + 1}"
        if level == 2:
            self.contents.append((anchor, text))
        return f'<h{level} id="{anchor}">{text}</h{level}>\n'

    def table(self, text):
        return f'<div class="table-wrap"><table>{text}</table></div>\n'


def render_pages():
    """Generate all three pages directly from the checked-in report sources."""
    payload = json.loads((REPORTS / "portfolio_data.json").read_text())
    quality = json.loads((REPORTS / "quality_summary.json").read_text())
    summary = payload["summary"]
    action_source = (REPORTS / "business_recommendations.md").read_text()
    action_priorities = re.findall(r"^\| (High|Medium|Low) \|", action_source, re.M)
    definitions = [
        {
            "title": "Executive summary",
            "code": "01",
            "source": "executive_summary.md",
            "description": "Eight operational findings: what changed, why it matters, and the next management decision.",
            "stats": [
                (
                    "Net revenue",
                    f"A${summary['revenue']:,.0f}",
                    "Full history · excluding GST",
                ),
                (
                    "Operating margin",
                    f"{summary['profit'] / summary['revenue']:.1%}",
                    "All observed operating costs",
                ),
                (
                    "Complete orders",
                    f"{quality['clean_orders']:,}",
                    "After quality validation",
                ),
                (
                    "Management findings",
                    str(len(payload["insights"])),
                    "Evidence, impact and action",
                ),
            ],
        },
        {
            "title": "Action plan",
            "code": "02",
            "source": "business_recommendations.md",
            "description": "Turn the findings into controlled pilots with clear owners, timeframes and success measures.",
            "stats": [
                (
                    "Workstreams",
                    str(len(action_priorities)),
                    "Operational and data controls",
                ),
                (
                    "High priority",
                    str(action_priorities.count("High")),
                    "Roster, waste, promotions and quality",
                ),
                ("Initial pilots", "4 weeks", "Roster and preparation trials"),
                ("Review cadence", "Weekly", "Compare, document and adjust"),
            ],
        },
        {
            "title": "Quality audit",
            "code": "03",
            "source": "data_quality_report.md",
            "description": "Trace the validation rules, repairs and exclusions behind the restaurant scorecards.",
            "extra_link": '<a href="exports/data_quality_audit.csv" download>Download audit CSV</a>',
            "stats": [
                (
                    "Validated lines",
                    f"{quality['clean_lines']:,}",
                    "Complete retained baskets",
                ),
                (
                    "Quarantined orders",
                    f"{quality['quarantined_orders']:,}",
                    "Whole orders excluded from KPIs",
                ),
                (
                    "Order retention",
                    f"{quality['clean_orders'] / (quality['clean_orders'] + quality['quarantined_orders']):.2%}",
                    "After deduplication · not a quality score",
                ),
                (
                    "Source datasets",
                    str(len(quality["clean_rows"])),
                    "Validated across connected systems",
                ),
            ],
        },
    ]
    template = (ROOT / "src/report_template.html").read_text()
    for report in definitions:
        renderer = ReportRenderer()
        markdown = mistune.create_markdown(renderer=renderer, plugins=["table"])
        source = (REPORTS / report["source"]).read_text()
        # Explicit anchors also cover the introductory tables in shorter reports.
        if report["code"] == "02":
            source = source.replace(
                "| Priority |", "## Prioritised workstreams\n\n| Priority |", 1
            )
        elif report["code"] == "03":
            source = source.replace(
                "| Table |", "## Validation rules and actions\n\n| Table |", 1
            )
            source = source.replace(
                "Counts can overlap",
                "## How to interpret the audit\n\nCounts can overlap",
                1,
            )
        content = markdown(source)
        content = content.replace(
            "<p><strong>Recommended action:</strong>",
            '<p class="action"><strong>Recommended action:</strong>',
        )
        navigation = []
        for other in definitions:
            current = ' aria-current="page"' if other is report else ""
            target = other["source"].replace(".md", ".html")
            navigation.append(f'<a href="{target}"{current}>{other["title"]}</a>')
        stats = "".join(
            f'<div class="stat"><div class="stat-label">{html.escape(label)}</div>'
            f'<div class="value">{html.escape(value)}</div>'
            f'<div class="stat-note">{html.escape(note)}</div></div>'
            for label, value, note in report["stats"]
        )
        contents = "".join(
            f'<li><a href="#{anchor}">{re.sub(r"^\d+\.\s*", "", title)}</a></li>'
            for anchor, title in renderer.contents
        )
        replacements = {
            "TITLE": html.escape(report["title"]),
            "CODE": report["code"],
            "DESCRIPTION": html.escape(report["description"]),
            "SOURCE": report["source"],
            "EXTRA_LINK": report.get("extra_link", ""),
            "NAVIGATION": "".join(navigation),
            "STATS": stats,
            "CONTENTS": contents,
            "CONTENT": content,
        }
        page = template
        for key, value in replacements.items():
            page = page.replace(f"__{key}__", value)
        (REPORTS / report["source"].replace(".md", ".html")).write_text(page)


if __name__ == "__main__":
    render_pages()
