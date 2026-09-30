import html as html_mod
import os
import tempfile
from datetime import datetime
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QMessageBox


def print_records(parent, title, headers, rows, meta_lines=None):
    if not rows:
        QMessageBox.information(parent, "提示", "没有可打印的记录")
        return

    parts = ["<!DOCTYPE html><html><head><meta charset='utf-8'>"]
    parts.append("<style>")
    parts.append("@media print { .no-print { display: none; } }")
    parts.append("body { font-family: 'Microsoft YaHei', SimSun, sans-serif; margin: 20px; }")
    parts.append("h2 { text-align: center; font-size: 22pt; margin-bottom: 8px; }")
    parts.append(".meta { margin-bottom: 12px; font-size: 11pt; color: #555; }")
    parts.append("table { border-collapse: collapse; width: 100%; font-size: 11pt; }")
    parts.append("th, td { border: 1px solid #333; padding: 6px 10px; text-align: left; }")
    parts.append("th { background: #f0f0f0; font-weight: bold; }")
    parts.append("tr:nth-child(even) { background: #fafafa; }")
    parts.append(".btn { margin: 16px 0; padding: 8px 24px; font-size: 14pt; cursor: pointer; }")
    parts.append("@page { size: landscape; margin: 15mm; }")
    parts.append("</style></head><body>")

    parts.append(f"<h2>{html_mod.escape(title)}</h2>")
    parts.append("<div class='meta'>")
    if meta_lines:
        for line in meta_lines:
            parts.append(f"<div>{html_mod.escape(line)}</div>")
    parts.append(f"<div>打印时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>")
    parts.append(f"<div>记录总数: {len(rows)}</div>")
    parts.append("</div>")

    parts.append("<table><tr>")
    for h in headers:
        parts.append(f"<th>{html_mod.escape(h)}</th>")
    parts.append("</tr>")
    for row in rows:
        parts.append("<tr>")
        for cell in row:
            parts.append(f"<td>{html_mod.escape(str(cell))}</td>")
        parts.append("</tr>")
    parts.append("</table>")

    parts.append("<div class='no-print'><button class='btn' onclick='window.print()'>打印</button></div>")
    parts.append("</body></html>")

    html_content = "".join(parts)

    tmp = os.path.join(tempfile.gettempdir(), f"print_{title}.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html_content)

    QDesktopServices.openUrl(QUrl.fromLocalFile(tmp))
