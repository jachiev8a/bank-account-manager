"""Static HTML report: which monthly statements exist and which are missing."""
import html
import re
from collections import defaultdict
from pathlib import Path

MONTHS = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
          "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

CSS = """
:root {
  color-scheme: dark;
  --bg: #0f1115; --card: #171a21; --line: #262b36; --text: #e6e8ee; --muted: #8a92a6;
  --ok: #1f6f4a; --ok-text: #c9f7dc; --miss: #6b1f2a; --miss-text: #ffd3d9; --accent: #7aa2f7;
  scrollbar-color: #3a4152 var(--bg);
}
* { box-sizing: border-box; }
body { margin: 0; padding: 2.5rem clamp(1rem, 4vw, 3rem); background: var(--bg); color: var(--text);
       font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
h1 { margin: 0 0 .25rem; font-size: 1.75rem; }
h2 { margin: 0; font-size: 1.1rem; }
.sub { color: var(--muted); margin: 0 0 2rem; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
.stat, .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; }
.stat { padding: 1rem 1.25rem; }
.stat b { display: block; font-size: 2rem; line-height: 1.1; }
.stat span { color: var(--muted); font-size: .85rem; }
.stat.bad b { color: #ff7b8a; }
.card { padding: 1.25rem; margin-bottom: 1.25rem; overflow-x: auto; }
.card header { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; margin-bottom: .75rem; }
.tag { font-size: .8rem; color: var(--muted); }
.bar { height: 6px; background: var(--miss); border-radius: 3px; margin-bottom: 1rem; overflow: hidden; }
.bar i { display: block; height: 100%; background: #3ecf8e; }
table { border-collapse: separate; border-spacing: 4px; }
th { color: var(--muted); font-weight: 500; font-size: .8rem; padding: 0 .25rem; }
td { width: 3.25rem; height: 2.5rem; border-radius: 6px; text-align: center; font-size: .85rem; padding: 0; }
td.ok { background: var(--ok); }
td.ok a { display: flex; height: 100%; align-items: center; justify-content: center; gap: .2rem;
          color: var(--ok-text); text-decoration: none; border-radius: 6px; }
td.ok a:hover { background: #2a8f61; }
td.ok a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
td.miss { background: var(--miss); color: var(--miss-text); font-weight: 600; }
td.out { background: transparent; border: 1px dashed var(--line); }
.legend { display: flex; gap: 1.25rem; color: var(--muted); font-size: .85rem; margin-bottom: 1.5rem; }
.legend i { display: inline-block; width: .9rem; height: .9rem; border-radius: 3px; vertical-align: -2px; margin-right: .35rem; }
.missing li, .failed li { margin: .25rem 0; }
.missing b { color: #ff7b8a; }
code { color: var(--accent); }
details.card summary { cursor: pointer; font-weight: 600; }
.config { display: grid; grid-template-columns: max-content 1fr; gap: .4rem 1.5rem; margin: 1rem 0 0; }
.config dt { color: var(--muted); }
.config dd { margin: 0; }
"""


def last4(statement):
    """Last 4 digits of card number, else account number (only thing shown)."""
    if not getattr(statement, "SPLIT_REPORT_BY_NUMBER", True):
        return None
    for value in (statement.numero_de_tarjeta, statement.numero_de_cuenta):
        digits = re.sub(r"\D", "", value or "")
        if len(digits) >= 4:
            return digits[-4:]
    return None


def account_label(key):
    bank, account_type, suffix = key
    return f"{bank} {account_type}" + (f" ····{suffix}" if suffix else "")


def group_by_account(statements):
    """{(bank, type, last4): {(year, month): [statement, ...]}}"""
    accounts = defaultdict(lambda: defaultdict(list))
    for s in statements:
        key = (s.get_bank_name(), s.get_account_type_name(), last4(s))
        accounts[key][(s.periodo_inicio.year, s.periodo_inicio.month)].append(s)
    return accounts


def find_gaps(months):
    """Months missing between the first and last (year, month) present."""
    index = [y * 12 + m - 1 for y, m in months]
    return [(i // 12, i % 12 + 1)
            for i in range(min(index), max(index) + 1)
            if (i // 12, i % 12 + 1) not in months]


def _link_path(statement):
    """The organized .tmp copy; the original only if the copy step didn't run."""
    return statement.output_file_path or statement.get_pdf_file_path()


def _cell(year, month, by_month, first, last):
    if (year, month) in by_month:
        files = by_month[(year, month)]
        links = "".join(
            f'<a href="{Path(_link_path(f)).as_uri()}" target="_blank" '
            f'title="{html.escape(Path(_link_path(f)).name)}">'
            f'{f.periodo_inicio.day:02d}</a>'
            for f in files
        )
        count = f'<span class="tag">×{len(files)}</span>' if len(files) > 1 else ""
        return f'<td class="ok">{links}{count}</td>'
    if first <= (year, month) <= last:
        return f'<td class="miss" title="Falta {MONTHS[month - 1]} {year}">✘</td>'
    return '<td class="out"></td>'


def _stat(value, label, bad=False):
    cls = "stat bad" if bad and value else "stat"
    return f'<div class="{cls}"><b>{value}</b><span>{label}</span></div>'


def build_report(statements, failed_files, output_path, config=None):
    accounts = group_by_account(statements)
    all_gaps = {key: find_gaps(by_month) for key, by_month in accounts.items()}
    total_missing = sum(len(g) for g in all_gaps.values())

    parts = [
        "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
        "<meta name='color-scheme' content='dark'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>Estados de cuenta</title><style>{CSS}</style></head><body>",
        "<h1>Estados de cuenta</h1>",
        "<p class='sub'>Meses con estado de cuenta por banco y tipo de cuenta. "
        "Clic en un mes para abrir el PDF.</p>",
        "<div class='stats'>",
        _stat(len(accounts), "Cuentas"),
        _stat(len(statements), "Estados de cuenta"),
        _stat(total_missing, "Meses faltantes", bad=True),
        _stat(len(failed_files), "PDFs no leídos", bad=True),
        "</div>",
        "<div class='legend'>"
        "<span><i style='background:var(--ok)'></i>Encontrado (día de inicio)</span>"
        "<span><i style='background:var(--miss)'></i>Faltante</span>"
        "<span><i style='border:1px dashed var(--line)'></i>Fuera de rango</span></div>",
    ]

    if config:
        parts.append("<details class='card' open><summary>Configuración usada</summary><dl class='config'>")
        for label, value in config.items():
            if isinstance(value, (list, tuple)):
                value = "<br>".join(f"<code>{html.escape(str(v))}</code>" for v in value) or "—"
            else:
                value = html.escape(str(value))
            parts.append(f"<dt>{html.escape(label)}</dt><dd>{value}</dd>")
        parts.append("</dl></details>")

    if total_missing:
        parts.append("<section class='card missing'><h2>Faltantes</h2><ul>")
        for key, gaps in sorted(all_gaps.items(), key=lambda kv: str(kv[0])):
            if gaps:
                months = ", ".join(f"{MONTHS[m - 1]} {y}" for y, m in gaps)
                parts.append(f"<li>{html.escape(account_label(key))}: <b>{months}</b></li>")
        parts.append("</ul></section>")

    for key in sorted(accounts, key=str):
        by_month = accounts[key]
        first, last = min(by_month), max(by_month)
        span = (last[0] * 12 + last[1]) - (first[0] * 12 + first[1]) + 1
        coverage = round(100 * len(by_month) / span)
        parts.append(
            f"<section class='card'><header><h2>{html.escape(account_label(key))}</h2>"
            f"<span class='tag'>{MONTHS[first[1] - 1]} {first[0]} – {MONTHS[last[1] - 1]} {last[0]}"
            f" · {coverage}% completo · {len(all_gaps[key])} faltantes</span></header>"
            f"<div class='bar'><i style='width:{coverage}%'></i></div>"
            "<table><tr><th></th>"
        )
        parts.extend(f"<th>{m}</th>" for m in MONTHS)
        parts.append("</tr>")
        for year in range(first[0], last[0] + 1):
            parts.append(f"<tr><th>{year}</th>")
            parts.extend(_cell(year, m, by_month, first, last) for m in range(1, 13))
            parts.append("</tr>")
        parts.append("</table></section>")

    if failed_files:
        parts.append("<section class='card failed'><h2>PDFs no leídos</h2><ul>")
        parts.extend(
            f"<li><code>{html.escape(Path(p).name)}</code>: {html.escape(reason)}</li>"
            for p, reason in failed_files
        )
        parts.append("</ul></section>")

    parts.append("</body></html>")
    Path(output_path).write_text("".join(parts), encoding="utf-8")
    return output_path
