# RESTOPS visual direction

User-selected style: **Formula 1-inspired — dark, bold, racing red**.

The interface uses a motorsport performance-screen aesthetic while keeping the
restaurant KPIs and management language easy to understand.

| Token | Value | Purpose |
|---|---|---|
| Canvas | `#101014` | Page background |
| Panel | `#19191F` | Charts and information cards |
| Raised surface | `#202027` | Inactive controls |
| Primary text | `#F4F4F6` | Titles and values |
| Secondary text | `#B0B0BB` | Explanations, axes and denominators |
| Racing red | `#FF3B30` | Brand accent, active tabs, main series |
| Cyan | `#58D6DF` | Comparison series, links, informational badges |
| Amber | `#FFC16A` | Review flags and opportunity caveats |

Bold italic titles, tabular numerals, compact field labels, numbered navigation,
subtle circuit artwork and chamfer-inspired panel corners establish the style.
The circuit illustration is decorative; the restaurant performance grid retains
its actual analytical ordering and labels.

Charts, the README cover, notebook figures and Tableau design specification use
the same palette. The HTML overview uses local system fonts and no remote assets.

The executive summary, action plan and quality audit have matching offline HTML
pages generated from their Markdown sources by `src/report_pages.py`. Reports
include highlight cards, section navigation, source downloads and a browser
Print / Save PDF option with a light print layout. The audit also links to its
rule-level CSV. Regenerate the pages with `python -m src.report_pages`, or as part
of the reporting pipeline. Markdown remains suitable for reading on GitHub.

Responsive layouts stack charts on smaller screens and allow wide tables to
scroll within their panel. Controls have visible keyboard focus. Tabs support
arrow keys, Home and End; a reduced-motion preference disables smooth scrolling.
Colour is supplemented by numbers, labels and text rather than used alone to
explain performance. Formula 1 is design inspiration, not company affiliation.
