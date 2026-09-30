import html as html_mod
from datetime import datetime
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import QMessageBox


_print_refs = []


def print_records(parent, title, headers, rows, meta_lines=None):
    if not rows:
        QMessageBox.information(parent, "提示", "没有可打印的记录")
        return

    parts = ["<html><head><meta charset='utf-8'></head><body>"]
    parts.append(f"<h2 style='text-align:center; font-family:Microsoft YaHei,SimSun; font-size:22pt;'>{html_mod.escape(title)}</h2>")
    parts.append("<div style='margin-bottom:12px; font-size:14pt; color:#555;'>")
    if meta_lines:
        for line in meta_lines:
            parts.append(f"<div>{html_mod.escape(line)}</div>")
    parts.append(f"<div>打印时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>")
    parts.append(f"<div>记录总数: {len(rows)}</div>")
    parts.append("</div>")

    parts.append("<table border='1' cellpadding='8' cellspacing='0' "
                 "style='border-collapse:collapse; width:100%; font-size:14pt; font-family:Microsoft YaHei,SimSun;'>")
    parts.append("<tr style='background:#f0f0f0;'>")
    for h in headers:
        parts.append(f"<th>{html_mod.escape(h)}</th>")
    parts.append("</tr>")
    for row in rows:
        parts.append("<tr>")
        for cell in row:
            parts.append(f"<td>{html_mod.escape(str(cell))}</td>")
        parts.append("</tr>")
    parts.append("</table></body></html>")

    doc_html = "".join(parts)

    printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
    printer.setOrientation(QPrinter.Orientation.Landscape)
    dialog = QPrintDialog(printer, parent)
    if dialog.exec() != QPrintDialog.DialogCode.Accepted:
        return

    doc = QTextDocument()
    doc.setHtml(doc_html)

    page_rect = printer.pageRect(QPrinter.Unit.Point)
    doc.setPageSize(page_rect.size())

    _print_refs.append((printer, doc))

    try:
        doc.print(printer)
    except Exception as e:
        QMessageBox.warning(parent, "打印出错", str(e))
