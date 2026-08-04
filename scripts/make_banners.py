#!/usr/bin/env python3
"""Generate DS vertical mobile banners (dark + light), 1080×1920.

Backgrounds follow brandbook `slides.background_decor`:
  - NO tiled/repeat pattern texture.
  - EXACTLY 3 large soft-edged blobs in the BRAND HEXAGON shape (rounded hexagon
    from the template custGeom, `<a:custGeom>` inside templates/Data-Sapience-template.pptx —
    HEX_PATH below is the same shape as an SVG path), NOT a generic sharp polygon.
    Positions: big left off-canvas, top-right, bottom-right.
  - Fill: gradient 001D37→2B6478→C5E2EA (dark) / solid #CAE7EF (light); + glow
    (#4F9AAB) + soft edge (NOT a blur-spot).
  - Dark = gradient cover (001D37→256478→B3D6E0) + 3D ring accent (natural only
    on gradient+blob). Light = light_blob: near-white + #CAE7EF hex glows in corners.
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

def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

def b64_zip(zip_path, member):
    with zipfile.ZipFile(zip_path) as z:
        return base64.b64encode(z.read(member)).decode()

# ── fonts (упакованы zip'ами в репо — распаковываем в памяти) ──────────────
ub_extrabold = b64_zip(FONT_ZIP_UNBOUNDED, "static/Unbounded-ExtraBold.ttf")
ub_bold      = b64_zip(FONT_ZIP_UNBOUNDED, "static/Unbounded-Bold.ttf")
ub_medium    = b64_zip(FONT_ZIP_UNBOUNDED, "static/Unbounded-Medium.ttf")
ping_medium  = b64_zip(FONT_ZIP_PINGLCG, "PingLCG-Medium.ttf")
ping_bold    = b64_zip(FONT_ZIP_PINGLCG, "PingLCG-Bold.ttf")

# ── images ─────────────────────────────────────────────────────────────────
logo_white   = b64(LOGO_DIR / "horizontal-white.png")
logo_blue    = b64(LOGO_DIR / "horizontal-blue.png")
ring         = b64(GRPH_DIR / "ring.png")          # 3D ring — dark/gradient only
hex3d        = b64(GRPH_DIR / "hexagon-3d.png")    # 3D volumetric hexagon (as-is, не перекрашивать)

# ── BRAND hexagon path (rounded hexagon, from template custGeom · hexpath.txt) ─
HEX_PATH = ("M 58.499,0.000 L 21.308,9.475 L 17.920,10.791 L 14.941,12.771 "
            "L 12.461,15.326 L 10.568,18.367 L 0.569,54.553 L 0.000,59.061 "
            "L 0.050,60.184 L 0.988,64.548 L 3.059,68.528 L 29.238,95.052 "
            "L 32.858,97.799 L 37.010,99.452 L 41.456,99.948 L 42.586,99.884 "
            "L 78.647,90.474 L 82.036,89.157 L 85.014,87.177 L 87.494,84.622 "
            "L 89.387,81.581 L 99.386,45.395 L 99.956,40.888 L 99.906,39.765 "
            "L 98.968,35.401 L 96.897,31.421 L 70.716,4.895 L 67.098,2.149 "
            "L 62.946,0.495 L 58.499,0.000 Z")

def hex_svg(cls, grad_id, fill, rotate):
    """One brand-hexagon blob as an inline SVG (shape stays correct at any size)."""
    return (f'<svg class="hex {cls}" viewBox="0 0 100 100" '
            f'style="transform:rotate({rotate}deg)">'
            f'<path d="{HEX_PATH}" fill="{fill}"/></svg>')

# ── shared font-face block ─────────────────────────────────────────────────
FONT_CSS = f"""
@font-face {{ font-family:'Unbounded'; font-weight:800;
  src:url('data:font/ttf;base64,{ub_extrabold}') format('truetype'); }}
@font-face {{ font-family:'Unbounded'; font-weight:700;
  src:url('data:font/ttf;base64,{ub_bold}') format('truetype'); }}
@font-face {{ font-family:'Unbounded'; font-weight:500;
  src:url('data:font/ttf;base64,{ub_medium}') format('truetype'); }}
@font-face {{ font-family:'PingLCG'; font-weight:500;
  src:url('data:font/ttf;base64,{ping_medium}') format('truetype'); }}
@font-face {{ font-family:'PingLCG'; font-weight:700;
  src:url('data:font/ttf;base64,{ping_bold}') format('truetype'); }}
"""

# ══════════════════════════════════════════════════════════════════════════
# DARK VERSION  — gradient cover + 3 brand-hexagon blobs + 3D ring
# ══════════════════════════════════════════════════════════════════════════
dark_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
{FONT_CSS}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  width: 1080px; height: 1920px; overflow: hidden;
  font-family: 'Unbounded', sans-serif;
  position: relative;
}}

/* bg gradient — 001D37 → 256478 → B3D6E0, diagonal 315° (per background_decor) */
.bg-grad {{
  position: absolute; inset: 0;
  background: linear-gradient(315deg, #001D37 0%, #256478 55%, #4F8A9E 100%);
}}

/* 3 brand-hexagon blobs — soft edges (NOT a blur-spot) + glow #4F9AAB */
.hex {{
  position: absolute;
  filter: blur(11px) drop-shadow(0 0 60px rgba(79,154,171,0.42));
}}
.hex-left {{ width: 840px; height: 840px; left:-380px; top: 540px;  opacity: 0.92; }}
.hex-tr   {{ width: 600px; height: 600px; right:-210px; top: -200px; opacity: 0.85; }}
.hex-br   {{ width: 640px; height: 640px; right:-200px; bottom:-220px; opacity: 0.80; }}

/* 3D ring — natural only on gradient+blob bg (graphics_usage) */
.ring-img {{
  position: absolute; width: 720px; top: 300px; right: -160px;
  opacity: 0.85; transform: rotate(-15deg);
}}

.content {{
  position: relative; z-index: 10;
  display: flex; flex-direction: column;
  height: 100%; padding: 88px 80px 80px;
}}
.logo img {{ height: 56px; width: auto; }}
.spacer {{ flex: 1; }}

.label {{
  font-family: 'PingLCG', sans-serif; font-weight: 500; font-size: 28px;
  color: #CAE7EF; letter-spacing: 0.04em; text-transform: uppercase;
  margin-bottom: 32px; opacity: 0.88;
}}
.headline {{
  font-family: 'Unbounded', sans-serif; font-weight: 800; font-size: 76px;
  line-height: 1.1; color: #FFFFFF; letter-spacing: -0.01em; margin-bottom: 48px;
}}
.headline .accent {{ color: #8DE969; }}

.badge {{
  display: inline-flex; align-items: center; gap: 16px;
  background: rgba(141,233,105,0.12); border: 2px solid #8DE969;
  border-radius: 999px; padding: 20px 40px; margin-bottom: 80px;
}}
.badge-num {{ font-family:'Unbounded'; font-weight:800; font-size:52px; color:#8DE969; line-height:1; }}
.badge-text {{ font-family:'PingLCG'; font-weight:500; font-size:28px; color:#FFFFFF; line-height:1.3; }}

.bottom {{ display: flex; align-items: center; }}
.website {{ font-family:'PingLCG'; font-weight:500; font-size:24px; color:#CAE7EF; letter-spacing:0.02em; opacity:0.85; }}
</style>
</head><body>

<div class="bg-grad"></div>

<svg width="0" height="0" style="position:absolute">
  <defs>
    <linearGradient id="hexgrad" x1="1" y1="0" x2="0" y2="1">
      <stop offset="0"    stop-color="#001D37"/>
      <stop offset="0.55" stop-color="#2B6478"/>
      <stop offset="1"    stop-color="#C5E2EA"/>
    </linearGradient>
  </defs>
</svg>
{hex_svg("hex-left", "hexgrad", "url(#hexgrad)", 6)}
{hex_svg("hex-tr",   "hexgrad", "url(#hexgrad)", -8)}
{hex_svg("hex-br",   "hexgrad", "url(#hexgrad)", 14)}

<img class="ring-img" src="data:image/png;base64,{ring}" alt="">

<div class="content">
  <div class="logo"><img src="data:image/png;base64,{logo_white}" alt="Data Sapience"></div>
  <div class="spacer"></div>
  <div class="text-block">
    <div class="label">Компания</div>
    <div class="headline">ведущий<br>интегратор<br><span class="accent">BI&#8209;систем</span><br>в России</div>
    <div class="badge">
      <span class="badge-num">№1</span>
      <span class="badge-text">по версии<br>CNews</span>
    </div>
  </div>
  <div class="bottom"><span class="website">datasapience.ru</span></div>
</div>

</body></html>
"""

# ══════════════════════════════════════════════════════════════════════════
# LIGHT VERSION — light_blob: near-white + #CAE7EF brand-hexagon glows (corners)
# ══════════════════════════════════════════════════════════════════════════
light_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
{FONT_CSS}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  width: 1080px; height: 1920px; overflow: hidden;
  font-family: 'Unbounded', sans-serif;
  position: relative;
}}

/* светлый градиент по канону (белый → голубой), держим текстовую зону светлой */
.bg-tint {{
  position: absolute; inset: 0;
  background: linear-gradient(150deg, #FFFFFF 0%, #EAF5F8 55%, #D8EEF4 100%);
}}

/* 3 фирменных ОБЪЁМНЫХ шестиугольника (hexagon-3d.png) — как есть, только поворот.
   Раскладка как в тёмной версии (большой слева + верх-право + низ-право, разные размеры).
   Ассет: тёмный край сверху, светлый снизу → поворачиваю светлой стороной ВНУТРЬ (к тексту),
   тёмной — НАРУЖУ (в угол/за кадр). */
.hex3d-img  {{ position: absolute; }}
.hex3d-left {{ width: 840px; top: 540px;   left:  -380px; transform: rotate(-90deg); opacity: 0.90; }}
.hex3d-tr   {{ width: 600px; top: -180px;  right: -210px; transform: rotate(45deg);   opacity: 0.95; }}
.hex3d-br   {{ width: 640px; bottom:-200px; right: -200px; transform: rotate(135deg);  opacity: 0.95; }}

.content {{
  position: relative; z-index: 10;
  display: flex; flex-direction: column;
  height: 100%; padding: 88px 80px 80px;
}}
.logo img {{ height: 56px; width: auto; }}
.spacer {{ flex: 1; }}

.label {{
  font-family: 'PingLCG', sans-serif; font-weight: 700; font-size: 24px;
  color: #4F9AAB; letter-spacing: 0.08em; text-transform: uppercase;
  margin-bottom: 36px; display: flex; align-items: center; gap: 16px;
}}
.label::before {{ content:''; display:block; width:40px; height:4px; background:#4F9AAB; border-radius:2px; }}

.headline {{
  font-family: 'Unbounded', sans-serif; font-weight: 800; font-size: 72px;
  line-height: 1.1; color: #004158; letter-spacing: -0.01em; margin-bottom: 52px;
}}
.headline .accent {{ color: #4F9AAB; }}

.badge {{
  display: inline-flex; align-items: center; gap: 20px;
  background: #004158; border-radius: 999px; padding: 20px 44px; margin-bottom: 80px;
}}
.badge-num {{ font-family:'Unbounded'; font-weight:800; font-size:52px; color:#8DE969; line-height:1; }}
.badge-text {{ font-family:'PingLCG'; font-weight:500; font-size:26px; color:#FFFFFF; line-height:1.35; }}

.bottom {{ display: flex; align-items: center; }}
.website {{ font-family:'PingLCG'; font-weight:500; font-size:24px; color:#6B8A96; letter-spacing:0.02em; }}
</style>
</head><body>

<div class="bg-tint"></div>

<img class="hex3d-img hex3d-left" src="data:image/png;base64,{hex3d}" alt="">
<img class="hex3d-img hex3d-tr"   src="data:image/png;base64,{hex3d}" alt="">
<img class="hex3d-img hex3d-br"   src="data:image/png;base64,{hex3d}" alt="">

<div class="content">
  <div class="logo"><img src="data:image/png;base64,{logo_blue}" alt="Data Sapience"></div>
  <div class="spacer"></div>
  <div class="text-block">
    <div class="label">Компания</div>
    <div class="headline">ведущий<br>интегратор<br><span class="accent">BI&#8209;систем</span><br>в России</div>
    <div class="badge">
      <span class="badge-num">№1</span>
      <span class="badge-text">по версии<br>CNews</span>
    </div>
  </div>
  <div class="bottom"><span class="website">datasapience.ru</span></div>
</div>

</body></html>
"""

# ── write HTML files ──────────────────────────────────────────────────────
Path("/workspace/banner_dark.html").write_text(dark_html, encoding="utf-8")
Path("/workspace/banner_light.html").write_text(light_html, encoding="utf-8")
print("HTML files written.")

# ── screenshot with Playwright ────────────────────────────────────────────
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, file_html, file_png in [
        ("dark",  "/workspace/banner_dark.html",  "/workspace/banner_vertical_dark.png"),
        ("light", "/workspace/banner_light.html", "/workspace/banner_vertical_light.png"),
    ]:
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.goto(f"file://{file_html}")
        page.wait_for_timeout(800)
        page.screenshot(path=file_png, full_page=False)
        print(f"  {name} → {file_png}")
    browser.close()

print("Done.")
