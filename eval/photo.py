"""Render invoices and sales-book pages as phone-photo-like JPEGs, from ground-truth JSON.

Used by scripts/make_demo_images.py (seed/images/) and eval/make_eval_set.py (eval/images/).
Everything is seeded, so the same truth and seed give the same image. Fonts come from
Windows (C:/Windows/Fonts); elsewhere Pillow's default font is used.
"""

import io
import math
import random
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")]
PRINT_FONTS = ["arial.ttf", "calibri.ttf", "consola.ttf", "cour.ttf", "DejaVuSans.ttf"]
BOLD_FONTS = ["arialbd.ttf", "calibrib.ttf", "consolab.ttf", "DejaVuSans-Bold.ttf"]
HAND_FONTS = ["Inkfree.ttf", "segoepr.ttf", "DejaVuSans.ttf"]


def _font(names: list[str], size: int, pick: int = 0) -> ImageFont.FreeTypeFont:
    names = names[pick % len(names):] + names[:pick % len(names)]
    for name in names:
        for d in FONT_DIRS:
            if (d / name).exists():
                return ImageFont.truetype(str(d / name), size)
    return ImageFont.load_default(size)


def _d(iso: str, style: int) -> str:
    x = date.fromisoformat(iso)
    return [x.strftime("%d %b %Y"), x.strftime("%d/%m/%Y"), x.strftime("%d-%m-%Y")][style % 3]


def _exp(iso: str, style: int) -> str:
    x = date.fromisoformat(iso)
    return [x.strftime("%b %Y"), x.strftime("%m/%Y"), x.strftime("%m/%y")][style % 3]


def _n(x: float) -> str:
    return f"{x:,.0f}" if float(x).is_integer() else f"{x:,.2f}"


# --- Documents ------------------------------------------------------------------------

def render_invoice(inv: dict, style: int = 0, planted: str | None = None) -> Image.Image:
    """A printed supplier invoice. `planted` adds an instruction-like line (injection test)."""
    W, H = 1240, 1754
    im = Image.new("RGB", (W, H), "white")
    g = ImageDraw.Draw(im)
    big, bold, reg, small = (_font(BOLD_FONTS, 46, style), _font(BOLD_FONTS, 26, style),
                             _font(PRINT_FONTS, 25, style), _font(PRINT_FONTS, 21, style))
    g.text((80, 70), inv["supplier_name"], font=big, fill="black")
    g.text((80, 130), "Wholesale medicine distributor, Bogura, Bangladesh", font=small, fill="#333")
    g.text((W - 330, 75), "INVOICE", font=big, fill="#1d3557")
    y = 210
    g.line((80, y, W - 80, y), fill="black", width=3)
    y += 25
    for label, val in (("Invoice No:", inv["invoice_no"]), ("Invoice date:", _d(inv["invoice_date"], style)),
                       ("Due date:", _d(inv["due_date"], style))):
        g.text((80, y), label, font=bold, fill="black")
        g.text((300, y), val, font=reg, fill="black")
        y += 42
    g.text((W - 520, 235), "Bill to: Green Life Pharmacy", font=reg, fill="black")
    g.text((W - 520, 277), "Bogura", font=reg, fill="black")

    cols = [(80, "#"), (130, "Product"), (590, "Batch"), (730, "Expiry"), (870, "Qty"),
            (960, "Unit cost"), (1100, "Total")]
    y += 30
    g.rectangle((80, y, W - 80, y + 48), fill="#e9ecef")
    for x, h in cols:
        g.text((x + 6, y + 10), h, font=bold, fill="black")
    y += 58
    for i, ln in enumerate(inv["lines"]):
        cells = [str(i + 1), ln["product"], ln["batch_no"], _exp(ln["expiry_date"], style), str(ln["qty"]),
                 _n(ln["unit_cost"]), _n(ln["line_total"])]
        for (x, _), c in zip(cols, cells):
            f = small if x == 130 and g.textlength(c, font=reg) > 450 else reg
            g.text((x + 6, y), c, font=f, fill="black")
        y += 50
        g.line((80, y - 8, W - 80, y - 8), fill="#ccc", width=1)
    y += 20
    g.text((870, y), "TOTAL (BDT)", font=bold, fill="black")
    g.text((1100, y), _n(inv["total"]), font=bold, fill="black")
    y += 90
    if planted:
        g.text((80, y), planted, font=reg, fill="#222")
        y += 60
    g.text((80, y), "Goods once sold are returnable as per the return policy.", font=small, fill="#555")
    g.text((80, H - 140), "Authorised signature: ____________________", font=reg, fill="black")
    return im


def render_sales_page(days: list[dict], style: int = 0) -> Image.Image:
    """A handwritten sales-book page on ruled paper."""
    W, H = 1240, 1754
    im = Image.new("RGB", (W, H), "#fbf8ee")
    g = ImageDraw.Draw(im)
    rnd = random.Random(style)
    for y in range(160, H - 60, 70):
        g.line((40, y, W - 40, y), fill="#9fc5e8", width=2)
    g.line((150, 0, 150, H), fill="#e06666", width=2)
    head, hand = _font(HAND_FONTS, 44, style), _font(HAND_FONTS, 40, style)
    g.text((180, 60), "Daily sales book", font=head, fill="#1a237e")
    cols = [(60, "Date"), (330, "Cash"), (560, "Credit"), (790, "Dues coll."), (1030, "Expenses")]
    for x, h in cols:
        g.text((x, 172), h, font=hand, fill="#1a237e")
    y = 242
    for d in days:
        cells = [date.fromisoformat(d["date"]).strftime("%d/%m/%y"), _n(d["cash_sales"]), _n(d["credit_sales"]),
                 _n(d["dues_collected"]), _n(d["expenses"]) if d["expenses"] else "-"]
        for (x, _), c in zip(cols, cells):
            g.text((x + rnd.randint(-6, 6), y + rnd.randint(-5, 5)), c, font=hand, fill="#0d1b4c")
        y += 70
    return im


# --- Photo effects --------------------------------------------------------------------

def photograph(doc: Image.Image, seed: int, hard: str | None = None) -> bytes:
    """Place the page on a table, tilt it, add uneven light, blur and noise.
    `hard`: "blur", "dark", "covered" or "fold" for the eval set's hard cases."""
    rnd = random.Random(seed)
    if hard == "covered":
        g = ImageDraw.Draw(doc)
        x, y = rnd.randint(600, 900), rnd.randint(500, 700)
        g.rectangle((x, y, x + 260, y + 120), fill="#c9b79c")  # a sticky note over part of the table
    if hard == "fold":
        g = ImageDraw.Draw(doc)
        y = doc.height // 2 + rnd.randint(-80, 80)
        g.line((0, y, doc.width, y + rnd.randint(-20, 20)), fill="#bdbdbd", width=6)

    angle = rnd.uniform(-4, 4)
    page = doc.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))
    bg = Image.new("RGB", (page.width + 160, page.height + 160), tuple(rnd.randint(70, 120) for _ in range(3)))
    bg.paste(page, (80 + rnd.randint(-30, 30), 80 + rnd.randint(-30, 30)), page)

    # uneven light: a soft gradient from one corner
    shade = Image.new("L", bg.size)
    sd = ImageDraw.Draw(shade)
    cx, cy = rnd.choice([(0, 0), (bg.width, 0), (0, bg.height), (bg.width, bg.height)])
    r = math.hypot(bg.width, bg.height)
    for k in range(20, 0, -1):
        sd.ellipse((cx - r * k / 20, cy - r * k / 20, cx + r * k / 20, cy + r * k / 20), fill=int(255 - k * 4))
    bg = Image.composite(bg, ImageEnhance.Brightness(bg).enhance(0.8), shade)

    bg = bg.filter(ImageFilter.GaussianBlur(2.6 if hard == "blur" else rnd.uniform(0.4, 0.9)))
    bg = ImageEnhance.Brightness(bg).enhance(0.55 if hard == "dark" else rnd.uniform(0.9, 1.05))
    noise = Image.effect_noise(bg.size, 10).convert("RGB")
    bg = Image.blend(bg, noise, 0.04)
    bg.thumbnail((1500, 1500))
    out = io.BytesIO()
    bg.save(out, format="JPEG", quality=88)
    return out.getvalue()
