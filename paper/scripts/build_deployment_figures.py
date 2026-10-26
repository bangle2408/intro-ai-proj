"""Compose vector annotations over captures from the real game.py application.

Run from the repository root with a Python interpreter providing reportlab:
    python -B paper/scripts/build_deployment_figures.py

All coordinates come from the capture metadata; chess pieces and application
text are never redrawn. Generated figures are written to paper/figures/.
"""

import json
import math
from pathlib import Path

from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

PAPER = Path(__file__).resolve().parents[1]
FIGURES = PAPER / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)
TRACE = json.loads((PAPER / "data/deployment-trace.json").read_text())
CAPTURES = TRACE["captures"]
for name, filename in (("Game", "DejaVuSans.ttf"), ("GameBold", "DejaVuSans-Bold.ttf")):
    pdfmetrics.registerFont(TTFont(name, "/usr/share/fonts/TTF/" + filename))

INK = HexColor("#26352D")
GREEN = HexColor("#365B49")
MUTED = HexColor("#626F66")
BORDER = HexColor("#D8DDD5")
PAPER_BG = HexColor("#F6F5F1")
SAGE = HexColor("#CCD5AE")
GOLD = HexColor("#DEC98B")


def new_pdf(name, width, height):
    c = canvas.Canvas(str(FIGURES / name), pagesize=(width, height), pageCompression=1)
    c.setTitle(name.removesuffix(".pdf").replace("-", " ").title())
    c.setAuthor("Chess AI project")
    return c


def text(c, x, y, value, size=8, bold=False, color=INK, align="left"):
    c.setFillColor(color)
    c.setFont("GameBold" if bold else "Game", size)
    {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}[align](x, y, value)


def rule(c, x1, y1, x2, y2, color=BORDER, width=.6):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)


def arrow(c, start, end, color=GREEN, width=1.7, inset=9):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    a = (start[0] + ux * inset, start[1] + uy * inset)
    b = (end[0] - ux * inset, end[1] - uy * inset)
    c.saveState()
    c.setStrokeColor(PAPER_BG)
    c.setLineWidth(width + 1.8)
    c.line(*a, *b)
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(*a, *b)
    head = 4.5
    p = c.beginPath()
    p.moveTo(*b)
    p.lineTo(b[0] - head * ux + head * .6 * uy, b[1] - head * uy - head * .6 * ux)
    p.lineTo(b[0] - head * ux - head * .6 * uy, b[1] - head * uy + head * .6 * ux)
    p.close()
    c.setFillColor(color)
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def capture(c, name, x, y, width):
    meta = CAPTURES[name]
    logical_width, logical_height = meta["logical_size"]
    scale = width / logical_width
    height = logical_height * scale
    c.drawImage(str(PAPER / meta["file"]), x, y, width, height, mask="auto")

    def square(square_name):
        sx, sy = meta["square_centers"][square_name]
        if logical_width != 376:  # full window: square coordinates are board-local
            sx += meta["board_rect"][0]
            sy += meta["board_rect"][1]
        return x + sx * scale, y + (logical_height - sy) * scale

    return square, scale


def outline(c, center, cell, color=GREEN):
    c.setStrokeColor(PAPER_BG)
    c.setLineWidth(2.4)
    c.rect(center[0] - cell / 2 + 1, center[1] - cell / 2 + 1, cell - 2, cell - 2)
    c.setStrokeColor(color)
    c.setLineWidth(1.2)
    c.rect(center[0] - cell / 2 + 1, center[1] - cell / 2 + 1, cell - 2, cell - 2)


def marker(c, n, x, y, target):
    rule(c, x, y, *target, color=GREEN, width=.8)
    c.setFillColor(GREEN)
    c.setStrokeColor(PAPER_BG)
    c.setLineWidth(1.2)
    c.circle(x, y, 6.5, fill=1, stroke=1)
    text(c, x, y - 2.6, str(n), 7.5, True, PAPER_BG, "center")


def interface():
    c = new_pdf("deployment-interface.pdf", 396, 348)
    square, scale = capture(c, "interface", 0, 35, 396)
    # Numbered pointers relate actual interface elements to the decision loop.
    marker(c, 1, 231, 146, square("f3"))
    marker(c, 2, 220, 296, (194, 289))
    marker(c, 3, 378, 135, (348, 137))
    marker(c, 4, 378, 91, (333, 91))
    rule(c, 0, 33, 396, 33)
    for x, y, label in (
        (3, 20, "1  Live position and legal actions"),
        (219, 20, "2  Deliberation budget"),
        (3, 6, "3  Committed move history"),
        (219, 6, "4  Static positional estimate"),
    ):
        text(c, x, y, label, 7.5)
    c.save()


def decision_loop():
    c = new_pdf("deployment-loop.pdf", 396, 132)

    def box(x, y, width, height, fill=PAPER_BG):
        c.setFillColor(fill)
        c.setStrokeColor(BORDER)
        c.setLineWidth(.7)
        c.roundRect(x, y, width, height, 3, fill=1, stroke=1)

    box(0, 80, 73, 33)
    text(c, 36.5, 100, "Live state", 7.7, True, align="center")
    text(c, 36.5, 88, "Board + history", 6.8, align="center")
    box(115, 103, 155, 25)
    text(c, 192.5, 113, "Eligible opening book", 7.6, True, align="center")
    box(115, 45, 155, 45)
    text(c, 192.5, 78, "Iterative search (B)", 7.6, True, align="center")
    text(c, 192.5, 66, "Negamax · bounds · depth", 7, align="center")
    text(c, 192.5, 54, "Tactical frontier · evaluation", 7, align="center")
    box(316, 80, 80, 33)
    text(c, 356, 100, "Candidate", 7.6, True, align="center")
    text(c, 356, 88, "action", 7.2, align="center")
    box(133, 3, 150, 27)
    text(c, 208, 13, "Validate generation + legality", 7, True, align="center")
    rule(c, 73, 96, 92, 96, color=GREEN, width=.9)
    rule(c, 92, 67, 92, 115.5, color=GREEN, width=.9)
    arrow(c, (92, 115.5), (115, 115.5), width=.9, inset=2)
    arrow(c, (92, 67), (115, 67), width=.9, inset=2)
    rule(c, 270, 115.5, 297, 115.5, color=GREEN, width=.9)
    rule(c, 270, 67, 297, 67, color=GREEN, width=.9)
    rule(c, 297, 67, 297, 115.5, color=GREEN, width=.9)
    arrow(c, (297, 96), (316, 96), width=.9, inset=2)
    rule(c, 356, 80, 356, 16.5, color=GREEN, width=.9)
    arrow(c, (356, 16.5), (283, 16.5), width=.9, inset=2)
    rule(c, 133, 16.5, 36.5, 16.5, color=GREEN, width=.9)
    arrow(c, (36.5, 16.5), (36.5, 80), width=.9, inset=2)
    text(c, 83, 25, "Apply", 7, color=MUTED, align="center")
    c.save()


def opening():
    c = new_pdf("deployment-opening.pdf", 190, 213)
    sq, scale = capture(c, "opening", 0, 20, 190)
    outline(c, sq("c5"), 43.5 * scale)
    arrow(c, sq("c7"), sq("c5"), inset=6)
    rule(c, 0, 18, 190, 18)
    text(c, 0, 4, "1. e4 c5", 8.2, True)
    text(c, 190, 4, "Opening-book action", 7, color=MUTED, align="right")
    c.save()


def tactics():
    c = new_pdf("deployment-tactics.pdf", 396, 168)
    panels = (
        ("tactic-before", "(a) Before the exchange", "Material: 0.00", ("b5", "c6")),
        ("tactic-capture", "(b) 4. Bxc6", "Material: +3.00", ("d7", "c6")),
        ("tactic-recapture", "(c) 4...dxc6", "Material: −0.20", None),
    )
    for index, (name, title, material, move) in enumerate(panels):
        x = index * 134
        text(c, x, 160, title, 7.2, True)
        sq, scale = capture(c, name, x, 25, 128)
        outline(c, sq("c6"), 43.5 * scale)
        if move:
            arrow(c, sq(move[0]), sq(move[1]), width=1.4, inset=4)
        rule(c, x, 22, x + 128, 22)
        text(c, x, 8, material, 7.5, color=MUTED)
    c.save()


def endgame():
    c = new_pdf("deployment-endgame.pdf", 190, 213)
    sq, scale = capture(c, "endgame-after", 0, 20, 190)
    outline(c, sq("d4"), 43.5 * scale)
    arrow(c, sq("c3"), sq("d4"), inset=6)
    rule(c, 0, 18, 190, 18)
    text(c, 0, 4, "1. Kd4", 8.2, True)
    text(c, 190, 4, "Endgame king activity", 7, color=MUTED, align="right")
    c.save()


def ui_detail(c, name, x, y, width, box):
    """Clip an existing capture in the PDF, retaining its original raster."""
    meta = CAPTURES[name]
    bx, by, bw, bh = box
    scale = width / bw
    height = bh * scale
    c.saveState()
    path = c.beginPath()
    path.rect(x, y, width, height)
    c.clipPath(path, stroke=0)
    c.drawImage(
        str(PAPER / meta["file"]),
        x - bx * scale,
        y - (meta["logical_size"][1] - by - bh) * scale,
        meta["logical_size"][0] * scale,
        meta["logical_size"][1] * scale,
        mask="auto",
    )
    c.restoreState()
    return height


def iterations():
    c = new_pdf("deployment-iterations.pdf", 396, 236)
    run = TRACE["searches"]["tactics"]
    rows = run["iterations"]
    # The UI excerpts show real states; the trace diagram below is explanatory.
    ui_detail(c, "thinking", 0, 190, 190, (456, 181, 250, 55))
    ui_detail(c, "committed", 206, 190, 190, (456, 181, 250, 55))
    arrow(c, (177, 210), (220, 210), width=1.2, inset=13)
    text(c, 0, 176, "Snapshot → search worker", 7.6, True)
    text(c, 206, 176, "Validated action → live board", 7.6, True)
    rule(c, 0, 167, 396, 167)
    text(c, 0, 153, "Completed nominal depth", 7.3, color=MUTED)
    left, right, bottom, top = 35, 372, 54, 139
    deadline = run["result"]["elapsed_ms"]
    xpos = lambda ms: left + (right - left) * ms / deadline
    ypos = lambda depth: bottom + (top - bottom) * depth / 6
    last = rows[-1]
    c.setFillColor(Color(.80, .84, .68, alpha=.28))
    c.rect(xpos(last["elapsed_ms"]), bottom, right - xpos(last["elapsed_ms"]), top - bottom, fill=1, stroke=0)
    for depth in range(1, 7):
        yy = ypos(depth)
        rule(c, left, yy, right, yy, width=.35)
        text(c, left - 8, yy - 2.5, str(depth), 7, color=MUTED, align="right")
    rule(c, left, bottom, right, bottom, color=MUTED)
    for ms in (0, 500, 1000, 1500, 1800):
        xx = xpos(ms)
        rule(c, xx, bottom - 2.5, xx, bottom, color=MUTED)
        text(c, xx, bottom - 13, f"{ms / 1000:g}", 7, color=MUTED, align="center")
    text(c, right, 28, "Elapsed search time (s)", 7.3, color=MUTED, align="right")
    previous = (left, bottom)
    for row in rows:
        point = (xpos(row["elapsed_ms"]), ypos(row["depth"]))
        rule(c, *previous, point[0], previous[1], color=GREEN, width=1.4)
        rule(c, point[0], previous[1], *point, color=GREEN, width=1.4)
        c.setFillColor(GREEN)
        c.circle(*point, 2.5, fill=1, stroke=0)
        previous = point
    rule(c, *previous, right, previous[1], color=GREEN, width=1.4)
    c.saveState()
    c.setDash(2, 2)
    rule(c, right, bottom, right, top, color=GREEN, width=.8)
    c.restoreState()
    text(c, xpos(1330), top - 10, "Deeper search", 7)
    text(c, xpos(1330), top - 21, "interrupted", 7)
    text(c, xpos(1282) - 4, ypos(5) - 11, "d* = 5 at 1.282 s", 7, align="right")
    text(c, 0, 7, "Retained action: 4...dxc6", 8, True)
    text(c, 396, 7, "Deadline: 1.800 s", 7.5, color=MUTED, align="right")
    c.save()


if __name__ == "__main__":
    interface()
    decision_loop()
    opening()
    tactics()
    endgame()
    iterations()
    print("Wrote six deployment figures from captures, worker messages, and the decision loop.")
