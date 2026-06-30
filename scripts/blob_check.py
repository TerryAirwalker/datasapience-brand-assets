#!/usr/bin/env python3
"""DS blob render auto-check — ловит «обрублённые края» фоновых блобов.

Контекст (зафиксированный урок). Фирменные блобы-шестиугольники часто вставляют
картинкой (PNG с альфой) в прямоугольные рамки (blipFill stretch) по углам слайда
или баннера. Если у картинки мало прозрачного запаса по краю ИЛИ альфа-переход
слишком резкий (ступенька), то прямая граница рамки/слайда режет непрозрачную
часть блоба ПРЯМОЙ линией — «край обрублен». Фикс: прозрачное поле по периметру
+ мягкая растушёвка края (softEdge / Gaussian blur).

Хелпер автоматизирует проверку этого в Шаге 4 самопроверки
(manifest.slides.background_decor.auto_check):

  1. check_blob_image(png)  — у исходного блоба есть прозрачный запас по периметру
                              и мягкий (постепенный) альфа-переход, а не ступенька.
  2. check_pptx(pptx)       — все блоб-картинки, вставленные blipFill, проходят (1);
                              плюс нет отрицательных fillRect-инсетов (зум-кроп).
  3. scan_render(png)       — на ГОТОВОМ рендере нет длинных прямых ДИАГОНАЛЬНЫХ
                              жёстких краёв в гладких (фоновых) зонах = подпись среза.

CLI:
    python3 blob_check.py asset.png            # проверить картинку-блоб
    python3 blob_check.py deck.pptx            # проверить вставки блобов в .pptx
    python3 blob_check.py --render slide.png   # проверить рендер на жёсткие срезы
    python3 blob_check.py deck.pptx --render slide.png
Код выхода 0 = PASS, 1 = есть замечания. Замечания печатаются построчно.

    from blob_check import check_blob_image, check_pptx, scan_render
"""
import sys, os, re, io, zipfile
import numpy as np
from PIL import Image

LO, HI = 25, 230  # пороги альфы: «прозрачно» / «непрозрачно»


# ── 1. картинка-блоб ────────────────────────────────────────────────────────
def _ramp_inward(profile):
    """Ширина (px) перехода LO→HI при движении внутрь от края профиля."""
    hits = np.where(profile >= HI)[0]
    if not len(hits):
        return None                       # непрозрачного ядра нет — не блоб
    hi_i = hits[0]
    los = np.where(profile[:hi_i + 1] <= LO)[0]
    if not len(los):
        return 0                          # дошли до ядра, не встретив прозрачного — впритык
    return int(hi_i - los[-1])


def check_blob_image(path, min_margin_frac=0.035, min_ramp_frac=0.012):
    """Проверить PNG-блоб. Возвращает список замечаний (пустой = OK)."""
    issues = []
    im = Image.open(path).convert("RGBA")
    W, H = im.size
    a = np.asarray(im.split()[3], dtype=np.int16)
    if a.max() == 0:
        return [f"{os.path.basename(path)}: полностью прозрачный — это не блоб"]
    if a.min() >= HI:
        return [f"{os.path.basename(path)}: НЕТ прозрачности — любой край рамки даст "
                f"жёсткий прямой срез; используйте PNG с альфой и мягким краем"]

    ys, xs = np.where(a > LO)
    top, bot = ys.min(), H - 1 - ys.max()
    left, right = xs.min(), W - 1 - xs.max()
    need_w, need_h = min_margin_frac * W, min_margin_frac * H
    for name, val, need in (("слева", left, need_w), ("справа", right, need_w),
                            ("сверху", top, need_h), ("снизу", bot, need_h)):
        if val < need:
            issues.append(f"{os.path.basename(path)}: блоб впритык к краю картинки {name} "
                          f"(запас {val}px < {need:.0f}px) → граница рамки режет блоб; "
                          f"добавьте прозрачное поле")

    cy = int(np.clip((ys.min() + ys.max()) // 2, 0, H - 1))
    cx = int(np.clip((xs.min() + xs.max()) // 2, 0, W - 1))
    ramps = [_ramp_inward(a[cy, :cx + 1]),            # слева
             _ramp_inward(a[cy, cx:][::-1]),          # справа
             _ramp_inward(a[:cy + 1, cx]),            # сверху
             _ramp_inward(a[cy:, cx][::-1])]          # снизу
    ramps = [r for r in ramps if r is not None]
    min_ramp = max(4, int(min_ramp_frac * min(W, H)))
    if ramps and min(ramps) < min_ramp:
        issues.append(f"{os.path.basename(path)}: слишком резкий альфа-переход "
                      f"(растушёвка {min(ramps)}px < {min_ramp}px) → при увеличении "
                      f"читается линией; смягчите край (Gaussian blur / softEdge)")
    return issues


# ── 2. вставки блобов в .pptx ────────────────────────────────────────────────
def _is_blob(im):
    """Эвристика: картинка похожа на блоб/свечение (сплошная мягкая форма с альфой),
    а не на иконку/логотип (тонкие штрихи, низкая заполненность) или скриншот (без альфы)."""
    if im.mode != "RGBA":
        return False
    a = np.asarray(im.split()[3], dtype=np.int16)
    if a.max() < HI or a.min() >= HI:
        return False                       # без прозрачности — не блоб
    ys, xs = np.where(a > LO)
    if not len(ys):
        return False
    bbox_area = (ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1)
    fill = (a > LO).sum() / max(1, bbox_area)
    return fill > 0.5                       # заполненность bbox > 50% → сплошная форма


def check_pptx(path):
    """Найти блоб-картинки во вставках blipFill и проверить каждую. Список замечаний."""
    issues = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        slides = sorted(n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n))
        for sl in slides:
            xml = z.read(sl).decode("utf-8", "replace")
            relp = f"ppt/slides/_rels/{os.path.basename(sl)}.rels"
            rels = z.read(relp).decode("utf-8", "replace") if relp in names else ""
            rid2img = {m.group(1): m.group(2) for m in
                       re.finditer(r'Id="([^"]+)"[^>]*Target="\.\./media/([^"]+)"', rels)}
            checked = {}
            for m in re.finditer(r"<p:pic\b.*?</p:pic>|<p:sp\b.*?</p:sp>", xml, re.S):
                blk = m.group(0)
                emb = re.search(r'r:embed="([^"]+)"', blk)
                if not emb or 'blipFill' not in blk:
                    continue
                img = rid2img.get(emb.group(1))
                if not img:
                    continue
                mp = f"ppt/media/{img}"
                if mp not in names:
                    continue
                try:
                    im = Image.open(io.BytesIO(z.read(mp)))
                    im.load()
                except Exception:
                    continue
                if not _is_blob(im.convert("RGBA")):
                    continue
                # отрицательный fillRect inset = зум-кроп, режет блоб
                fr = re.search(r"<a:fillRect([^/>]*)/?>", blk)
                if fr and re.search(r'(?:l|t|r|b)="-\d+"', fr.group(1)):
                    issues.append(f"{os.path.basename(sl)}: блоб {img} вставлен с "
                                  f"отрицательным fillRect-инсетом (зум-кроп) → край режется")
                if img not in checked:
                    tmp = f"/tmp/_blobchk_{img}"
                    im.convert("RGBA").save(tmp)
                    checked[img] = [f"{os.path.basename(sl)} · {it}"
                                    for it in check_blob_image(tmp)]
                    issues.extend(checked[img])
    return issues


# ── 3. рендер: длинные прямые ДИАГОНАЛЬНЫЕ жёсткие края в гладких зонах ───────
def scan_render(path, min_len_frac=0.16, smooth_std=14.0):
    """Скан готового PNG на подпись «среза»: длинная прямая диагональ с РЕЗКИМ
    перепадом яркости, по обе стороны которой — гладкий (низкотекстурный) фон.
    Карточки/рамки (0°/90°) и занятые зоны (иконки, графики) исключаются.

    ВАЖНО — это лишь высокоточный «второй взгляд», а не основной детектор.
    Он ловит только ЖЁСТКИЕ прямые срезы на ровном фоне. МЯГКИЙ (растушёванный)
    срез — а именно так выглядит обрезанный блоб с softEdge — не даёт чёткого
    Canny-края, и за карточками/контентом такой срез на рендере не виден.
    Корневую причину (мало прозрачного запаса / резкая альфа / отрицательный
    fillRect-инсет) надёжно и детерминированно ловит check_pptx/check_blob_image —
    ИМЕННО ОНИ являются воротами самопроверки. scan_render лишь подстраховывает."""
    try:
        import cv2
    except Exception:
        return ["(scan_render пропущен: нет cv2 — проверьте рендер глазами)"]
    bgr = cv2.imread(path)
    if bgr is None:
        return [f"{os.path.basename(path)}: не открыть как изображение"]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape
    diag = (H * H + W * W) ** 0.5
    edges = cv2.Canny(gray, 30, 90)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=90,
                            minLineLength=int(min_len_frac * diag),
                            maxLineGap=int(0.01 * diag))
    if lines is None:
        return []
    hits = []
    for x1, y1, x2, y2 in lines[:, 0]:
        ang = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        ang = min(ang, 180 - ang)
        if ang < 12 or ang > 78:
            continue                                   # оси (карточки/рамки) — пропуск
        nx, ny = (y2 - y1), -(x2 - x1)
        nrm = (nx * nx + ny * ny) ** 0.5 or 1
        nx, ny, off = nx / nrm, ny / nrm, max(8, int(0.012 * diag))
        sA, sB = [], []
        for t in np.linspace(0.15, 0.85, 9):
            px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            for sign, bucket in ((+1, sA), (-1, sB)):
                qx, qy = int(px + sign * nx * off), int(py + sign * ny * off)
                if 0 <= qx < W and 0 <= qy < H:
                    bucket.append(gray[qy, qx])
        if len(sA) < 6 or len(sB) < 6:
            continue
        # обе стороны гладкие (низкий разброс), но между ними заметный перепад
        if np.std(sA) < smooth_std and np.std(sB) < smooth_std and \
                abs(np.mean(sA) - np.mean(sB)) > 16:
            hits.append((int(x1), int(y1), int(x2), int(y2), round(float(ang), 1)))
    return [f"{os.path.basename(path)}: подозрение на жёсткий срез блоба — прямая "
            f"диагональ {h[4]}° ({h[0]},{h[1]})→({h[2]},{h[3]}) между гладкими зонами; "
            f"смягчите край блоба" for h in hits]


# ── dispatcher / CLI ─────────────────────────────────────────────────────────
def check(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pptx":
        return check_pptx(path)
    if ext in (".png", ".jpg", ".jpeg", ".webp"):
        return check_blob_image(path)
    return [f"{path}: неподдерживаемый тип (ожидается .pptx / .png)"]


def main(argv):
    render = None
    if "--render" in argv:
        i = argv.index("--render")
        render = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    issues = []
    for p in argv:
        issues += check(p)
    if render:
        issues += scan_render(render)
    if not (argv or render):
        print(__doc__)
        return 2
    if issues:
        print("BLOB-CHECK: ⚠️ замечания (%d):" % len(issues))
        for it in issues:
            print("  •", it)
        return 1
    print("BLOB-CHECK: ✅ блобы в порядке (прозрачный запас + мягкий край, без срезов)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
