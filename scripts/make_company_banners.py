#!/usr/bin/env python3
"""DS company banners with stats — square 1080×1080 + horizontal 1920×1080.

Brand rules honored:
  - dark gradient bg (social_banner canon) + 3 BRAND-hexagon blobs (custGeom path),
    soft edge + glow; NO tiled pattern.
  - stats = equal columns via CSS grid repeat(N,1fr), equal gaps regardless of
    label length (layout.stats_blocks).
  - green #8DE969 only as accent (the "+" signs), numbers white. One DS mention = logo.
  - fonts embedded via @font-face base64.
"""
import base64, zipfile
from pathlib import Path

# reference-скрипт: пути — относительно чекаута datasapience-brand-assets
# (скрипт лежит в scripts/, ассеты — в fonts/logos/graphics соседних папках репо).
REPO_ROOT = Path(__file__).resolve().parent.parent
FONT_ZIP_UNBOUNDED = REPO_ROOT / "fonts" / "Unbounded.zip"
FONT_ZIP_PINGLCG   = REPO_ROOT / "fonts" / "PingLCG.zip"
LOGO_DIR = REPO_ROOT / "logos" / "png" / "variants"
GRPH_DIR = REPO_ROOT / "graphics"

def b64(p): return base64.b64encode(Path(p).read_bytes()).decode()

def b64_zip(zip_path, member):
    with zipfile.ZipFile(zip_path) as z:
        return base64.b64encode(z.read(member)).decode()

ub_extrabold = b64_zip(FONT_ZIP_UNBOUNDED, "static/Unbounded-ExtraBold.ttf")
ub_bold      = b64_zip(FONT_ZIP_UNBOUNDED, "static/Unbounded-Bold.ttf")
ub_medium    = b64_zip(FONT_ZIP_UNBOUNDED, "static/Unbounded-Medium.ttf")
ping_medium  = b64_zip(FONT_ZIP_PINGLCG, "PingLCG-Medium.ttf")
ping_bold    = b64_zip(FONT_ZIP_PINGLCG, "PingLCG-Bold.ttf")
logo_white   = b64(LOGO_DIR / "horizontal-white.png")
ring         = b64(GRPH_DIR / "ring.png")

HEX_PATH = ("M 58.499,0.000 L 21.308,9.475 L 17.920,10.791 L 14.941,12.771 "
    "L 12.461,15.326 L 10.568,18.367 L 0.569,54.553 L 0.000,59.061 L 0.050,60.184 "
    "L 0.988,64.548 L 3.059,68.528 L 29.238,95.052 L 32.858,97.799 L 37.010,99.452 "
    "L 41.456,99.948 L 42.586,99.884 L 78.647,90.474 L 82.036,89.157 L 85.014,87.177 "
    "L 87.494,84.622 L 89.387,81.581 L 99.386,45.395 L 99.956,40.888 L 99.906,39.765 "
    "L 98.968,35.401 L 96.897,31.421 L 70.716,4.895 L 67.098,2.149 L 62.946,0.495 "
    "L 58.499,0.000 Z")

FONT_CSS = f"""
@font-face {{ font-family:'Unbounded'; font-weight:800; src:url('data:font/ttf;base64,{ub_extrabold}') format('truetype'); }}
@font-face {{ font-family:'Unbounded'; font-weight:700; src:url('data:font/ttf;base64,{ub_bold}') format('truetype'); }}
@font-face {{ font-family:'Unbounded'; font-weight:500; src:url('data:font/ttf;base64,{ub_medium}') format('truetype'); }}
@font-face {{ font-family:'PingLCG'; font-weight:500; src:url('data:font/ttf;base64,{ping_medium}') format('truetype'); }}
@font-face {{ font-family:'PingLCG'; font-weight:700; src:url('data:font/ttf;base64,{ping_bold}') format('truetype'); }}
"""

def blobs(layout):
    """3 brand-hexagon blobs (gradient fill + glow), positions tuned per layout."""
    if layout == "square":
        specs = [("hx-l","760px","760px","left:-330px;top:520px;","8"),
                 ("hx-tr","540px","540px","right:-180px;top:-180px;","-6"),
                 ("hx-br","560px","560px","right:-170px;bottom:-180px;","14")]
    else:  # horizontal
        specs = [("hx-l","720px","720px","left:-260px;top:-220px;","8"),
                 ("hx-tr","560px","560px","right:-170px;top:-200px;","-6"),
                 ("hx-br","600px","600px","right:-150px;bottom:-220px;","14")]
    css, body = "", ""
    for cls,w,h,pos,rot in specs:
        css += (f".{cls}{{position:absolute;width:{w};height:{h};{pos}"
                f"transform:rotate({rot}deg);filter:blur(13px) drop-shadow(0 0 60px rgba(79,154,171,0.42));}}\n")
        body += (f'<svg class="{cls}" viewBox="0 0 100 100"><path d="{HEX_PATH}" fill="url(#hg)"/></svg>\n')
    return css, body

GRAD_DEF = ('<svg width="0" height="0" style="position:absolute"><defs>'
    '<linearGradient id="hg" x1="1" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#001D37"/><stop offset="0.55" stop-color="#2B6478"/>'
    '<stop offset="1" stop-color="#C5E2EA"/></linearGradient></defs></svg>')

STATS = [("65", "+", "успешных проектов"),
         ("40", "+", "корпоративных клиентов"),
         ("5",  "",  "линеек продуктов"),
         ("20", "+", "лет опыта в команде")]

def stat_cells():
    out = ""
    for num, suf, label in STATS:
        out += (f'<div class="stat"><div class="snum">{num}<span class="sacc">{suf}</span></div>'
                f'<div class="slabel">{label}</div></div>\n')
    return out

# ── SQUARE 1080×1080 ────────────────────────────────────────────────────────
bc, bb = blobs("square")
square = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{FONT_CSS}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
body{{width:1080px;height:1080px;overflow:hidden;position:relative;font-family:'Unbounded',sans-serif;}}
.bg{{position:absolute;inset:0;background:linear-gradient(315deg,#001D37 0%,#256478 55%,#4F8A9E 100%);}}
{bc}
.content{{position:relative;z-index:10;height:100%;padding:76px 76px 70px;display:flex;flex-direction:column;}}
.logo img{{height:50px;}}
.eyebrow{{font-family:'PingLCG';font-weight:500;font-size:22px;letter-spacing:0.10em;text-transform:uppercase;color:#CAE7EF;opacity:0.85;margin:54px 0 22px;}}
.headline{{font-family:'Unbounded';font-weight:800;font-size:46px;line-height:1.18;color:#FFFFFF;letter-spacing:-0.01em;}}
.headline .g{{color:#8DE969;}}
.stats{{display:grid;grid-template-columns:repeat(2,1fr);gap:30px;margin-top:auto;}}
.stat{{background:rgba(255,255,255,0.05);border:1px solid rgba(202,231,239,0.18);border-radius:18px;padding:30px 32px;}}
.snum{{font-family:'Unbounded';font-weight:800;font-size:72px;line-height:1;color:#FFFFFF;}}
.snum .sacc{{color:#8DE969;}}
.slabel{{font-family:'PingLCG';font-weight:500;font-size:23px;color:#CAE7EF;margin-top:14px;}}
.foot{{display:flex;align-items:center;justify-content:space-between;margin-top:34px;}}
.note{{font-family:'PingLCG';font-weight:500;font-size:21px;color:#9FC4D0;}}
.note b{{color:#CAE7EF;font-weight:700;}}
</style></head><body>
<div class="bg"></div>
{GRAD_DEF}
{bb}
<div class="content">
  <div class="logo"><img src="data:image/png;base64,{logo_white}" alt="Data Sapience"></div>
  <div class="eyebrow">О компании</div>
  <div class="headline">Платформы данных<br>и аналитики для<br><span class="g">крупного бизнеса</span></div>
  <div class="stats">{stat_cells()}</div>
  <div class="foot">
    <span class="note"><b>Реестр отечественного ПО</b></span>
    <span class="note">datasapience.ru</span>
  </div>
</div>
</body></html>"""

# ── HORIZONTAL 1920×1080 ────────────────────────────────────────────────────
bc2, bb2 = blobs("horizontal")
LINES = ["Data Ocean", "CM Ocean", "TALYS Ocean", "Kolmogorov AI", "Data Ocean Governance"]
chips = "".join(f'<span class="chip">{l}</span>' for l in LINES)
horizontal = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{FONT_CSS}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
body{{width:1920px;height:1080px;overflow:hidden;position:relative;font-family:'Unbounded',sans-serif;}}
.bg{{position:absolute;inset:0;background:linear-gradient(315deg,#001D37 0%,#256478 58%,#4F8A9E 100%);}}
{bc2}
.content{{position:relative;z-index:10;height:100%;padding:96px 110px 90px;display:flex;flex-direction:column;}}
.top{{display:flex;align-items:flex-start;justify-content:space-between;}}
.logo img{{height:58px;}}
.eyebrow{{font-family:'PingLCG';font-weight:500;font-size:24px;letter-spacing:0.10em;text-transform:uppercase;color:#CAE7EF;opacity:0.85;margin:64px 0 24px;}}
.headline{{font-family:'Unbounded';font-weight:800;font-size:76px;line-height:1.12;color:#FFFFFF;letter-spacing:-0.01em;max-width:1180px;}}
.headline .g{{color:#8DE969;}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:36px;margin-top:auto;}}
.stat{{border-left:3px solid rgba(141,233,105,0.55);padding:8px 0 8px 28px;}}
.snum{{font-family:'Unbounded';font-weight:800;font-size:88px;line-height:1;color:#FFFFFF;}}
.snum .sacc{{color:#8DE969;}}
.slabel{{font-family:'PingLCG';font-weight:500;font-size:26px;color:#CAE7EF;margin-top:16px;}}
.foot{{display:flex;align-items:center;justify-content:space-between;margin-top:46px;}}
.chips{{display:flex;flex-wrap:wrap;gap:14px;}}
.chip{{font-family:'PingLCG';font-weight:500;font-size:22px;color:#CAE7EF;border:1px solid rgba(202,231,239,0.30);border-radius:999px;padding:11px 24px;}}
.note{{font-family:'PingLCG';font-weight:500;font-size:24px;color:#9FC4D0;}}
.note b{{color:#CAE7EF;font-weight:700;}}
</style></head><body>
<div class="bg"></div>
{GRAD_DEF}
{bb2}
<div class="content">
  <div class="top">
    <div class="logo"><img src="data:image/png;base64,{logo_white}" alt="Data Sapience"></div>
    <span class="note"><b>Реестр отечественного ПО</b></span>
  </div>
  <div class="eyebrow">О компании</div>
  <div class="headline">Аналитические инструменты и платформы данных <span class="g">для крупного бизнеса</span></div>
  <div class="stats">{stat_cells()}</div>
  <div class="foot">
    <div class="chips">{chips}</div>
    <span class="note">datasapience.ru</span>
  </div>
</div>
</body></html>"""

Path("/workspace/company_square.html").write_text(square, encoding="utf-8")
Path("/workspace/company_horizontal.html").write_text(horizontal, encoding="utf-8")
print("HTML written.")

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, fhtml, fpng, w, h in [
        ("square","/workspace/company_square.html","/workspace/banner_company_square_1080.png",1080,1080),
        ("horizontal","/workspace/company_horizontal.html","/workspace/banner_company_horizontal_1920.png",1920,1080),
    ]:
        pg = b.new_page(viewport={"width":w,"height":h})
        pg.goto(f"file://{fhtml}"); pg.wait_for_timeout(800)
        pg.screenshot(path=fpng, full_page=False)
        print(f"  {name} -> {fpng}")
    b.close()
print("Done.")
