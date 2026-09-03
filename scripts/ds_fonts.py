#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Шрифты Data Sapience для редактируемой сборки (Режим A).

Одна таблица FACES — источник правды и для (1) @font-face CSS, который вставляется
в HTML-макет (чтобы Chromium считал ПРАВИЛЬНЫЕ метрики → верный bbox текста), и для
(2) встраивания в .pptx (OOXML p:embeddedFontLst).

Приём для сохранения НАЧЕРТАНИЙ: каждый вес — отдельное имя гарнитуры (typeface).
PowerPoint сопоставляет run.font.name ↔ typeface в embeddedFontLst и берёт нужный
.fntdata независимо от внутреннего имени TTF. Поэтому Unbounded SemiBold/ExtraBold
и Ping LCG Medium/Light едут как самостоятельные семейства с одним regular-слотом.

Обе гарнитуры — OFL (Unbounded, Ping LCG), лицензия на встраивание не требуется.
"""
import os, base64, zipfile, re

HERE = os.path.dirname(os.path.abspath(__file__))


def _find(fname, roots):
    """Найти TTF по имени, обходя типовые места распаковки Unbounded.zip / PingLCG.zip."""
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            if fname in files:
                return os.path.join(dirpath, fname)
    return None


# Корни поиска: $DS_FONT_DIR, затем типовые расположения (рядом со скриптом, /workspace, cwd).
_ROOTS = [os.environ.get("DS_FONT_DIR"),
          os.path.normpath(os.path.join(HERE, "..", "fonts")),
          os.path.join(HERE, "fonts"),
          "/workspace/fonts", "/workspace", os.getcwd()]


def F(fname):
    p = _find(fname, _ROOTS)
    return p or fname  # если не нашли — вернём имя (упадёт явной ошибкой при чтении)

# typeface(pptx) -> {"reg": ttf_path, "bold": ttf_path|None, "css": [(weight,int, path)]}
# css: какие CSS font-weight должны резолвиться в это семейство при рендере HTML.
# ВАЖНО: PowerPoint/Keynote на macOS honor'ят встроенное семейство ТОЛЬКО если оно
# укомплектовано И regular, И bold-слотом. Однослотовые (только regular) семейства
# игнорируются → системный фолбэк. Поэтому у КАЖДОГО семейства заполнены оба слота
# (для одновесных — тем же файлом), а каждый вес живёт в отдельном семействе с точным
# именем начертания (typeface = run.font.name = css @font-face family).
FACES = [
    # --- Unbounded (заголовки/акценты) ---
    ("Unbounded", {
        "reg": F("Unbounded-Regular.ttf"), "bold": F("Unbounded-Bold.ttf"),
        "css": [(400, F("Unbounded-Regular.ttf")), (700, F("Unbounded-Bold.ttf"))],
    }),
    ("Unbounded Medium", {
        "reg": F("Unbounded-Medium.ttf"), "bold": F("Unbounded-Medium.ttf"),
        "css": [(500, F("Unbounded-Medium.ttf"))],
    }),
    ("Unbounded SemiBold", {
        "reg": F("Unbounded-SemiBold.ttf"), "bold": F("Unbounded-SemiBold.ttf"),
        "css": [(600, F("Unbounded-SemiBold.ttf"))],
    }),
    ("Unbounded ExtraBold", {
        "reg": F("Unbounded-ExtraBold.ttf"), "bold": F("Unbounded-ExtraBold.ttf"),
        "css": [(800, F("Unbounded-ExtraBold.ttf"))],
    }),
    # --- Ping LCG (основной текст) ---
    ("Ping LCG", {
        "reg": F("PingLCG-Regular.ttf"), "bold": F("PingLCG-Bold.ttf"),
        "css": [(400, F("PingLCG-Regular.ttf")), (700, F("PingLCG-Bold.ttf"))],
    }),
    ("Ping LCG Medium", {
        "reg": F("PingLCG-Medium.ttf"), "bold": F("PingLCG-Medium.ttf"),
        "css": [(500, F("PingLCG-Medium.ttf"))],
    }),
    ("Ping LCG Light", {
        "reg": F("PingLCG-Light.ttf"), "bold": F("PingLCG-Light.ttf"),
        "css": [(300, F("PingLCG-Light.ttf"))],
    }),
]

# CSS-семьи, под которыми автор пишет HTML (натуральные имена + вес).
CSS_FAMILIES = {"Unbounded", "Ping LCG"}


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def build_css():
    """@font-face для 'Unbounded' и 'Ping LCG' со всеми весами (base64). Вставляется в HTML."""
    out = ["<style id=\"ds-fonts\">"]
    # Unbounded: собираем все css-веса из FACES где typeface стартует с Unbounded
    for family, want in (("Unbounded", "Unbounded"), ("Ping LCG", "Ping LCG")):
        seen = set()
        for tf, spec in FACES:
            if not tf.startswith(want):
                continue
            for wght, path in spec["css"]:
                if wght in seen:
                    continue
                seen.add(wght)
                out.append(
                    f"@font-face{{font-family:'{family}';font-weight:{wght};font-style:normal;"
                    f"font-display:block;src:url(data:font/ttf;base64,{_b64(path)}) format('truetype')}}"
                )
    out.append("</style>")
    return "".join(out)


def resolve_facename(css_family, css_weight):
    """(computed fontFamily, fontWeight) HTML -> имя гарнитуры pptx (typeface) + bold-флаг.

    КЛЮЧЕВОЕ ОГРАНИЧЕНИЕ macOS: Core Text группирует все статические веса под ОДНИМ
    типографским семейством ('Unbounded', 'Ping LCG'), а отдельные имена весов
    ('Unbounded ExtraBold/SemiBold/Medium', 'Ping LCG Medium/Light') как самостоятельные
    семейства НЕ адресуются — PowerPoint/Keynote выбирают в семействе только Regular/Bold.
    Поэтому надёжно резолвятся лишь два семейства × {Regular, Bold}. Тяжёлые веса (≥600)
    → Bold, лёгкие/средние → Regular. Это даёт бренд-шрифт вместо системного фолбэка на
    любой машине с обычными Unbounded + Ping LCG (без переименованных пакетов).
    """
    w = int(round(float(css_weight)))
    fam = css_family.strip().strip("'\"").split(",")[0].strip().strip("'\"")
    if fam.startswith("Unbounded"):
        return ("Unbounded", w >= 600)      # 600/700/800 → Bold, 400/500 → Regular
    if fam.startswith("Ping"):
        return ("Ping LCG", w >= 700)        # 700 → Bold, 300/400/500 → Regular
    return (fam, w >= 600)


# ---- встраивание в pptx (адаптация alphyn/embed_fonts.py под DS FACES) ----
REL_FONT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"


def embed_fonts(src, dst=None):
    dst = dst or (src.rsplit(".", 1)[0] + "_embedded.pptx")
    with zipfile.ZipFile(src) as z:
        data = {n: z.read(n) for n in z.namelist()}
    ct = data["[Content_Types].xml"].decode()
    rels = data["ppt/_rels/presentation.xml.rels"].decode()
    pres = data["ppt/presentation.xml"].decode()

    if 'Extension="fntdata"' not in ct:
        ct = ct.replace('<Default Extension="rels"',
                        '<Default Extension="fntdata" ContentType="application/x-fontdata"/>'
                        '<Default Extension="rels"', 1)

    nid = max([int(m) for m in re.findall(r'Id="rId(\d+)"', rels)]) + 1
    entries, newfiles = [], {}
    for typeface, spec in FACES:
        inner = []
        for slot, path in (("regular", spec["reg"]), ("bold", spec.get("bold"))):
            if not path:
                continue
            rid = f"rId{nid}"; nid += 1
            fname = f"dsfont{nid}.fntdata"
            with open(path, "rb") as f:
                newfiles[f"ppt/fonts/{fname}"] = f.read()
            rels = rels.replace("</Relationships>",
                                f'<Relationship Id="{rid}" Type="{REL_FONT}" Target="fonts/{fname}"/></Relationships>')
            tag = "p:regular" if slot == "regular" else "p:bold"
            inner.append(f'<{tag} r:id="{rid}"/>')
        entries.append(f'<p:embeddedFont><p:font typeface="{typeface}"/>{"".join(inner)}</p:embeddedFont>')

    lst = f'<p:embeddedFontLst>{"".join(entries)}</p:embeddedFontLst>'
    if "embedTrueTypeFonts" not in pres:
        pres = pres.replace("<p:presentation ", '<p:presentation embedTrueTypeFonts="1" ', 1)
    # Порядок детей CT_Presentation по схеме OOXML: ... sldIdLst, sldSz, notesSz,
    # embeddedFontLst, ... — вставлять СТРОГО после notesSz/sldSz, иначе PowerPoint/
    # Keynote считают файл повреждённым (LibreOffice это терпит). См. ECMA-376.
    for pat in (r'<p:notesSz\b[^>]*/>', r'<p:notesSz\b.*?</p:notesSz>',
                r'<p:sldSz\b[^>]*/>', r'<p:sldSz\b.*?</p:sldSz>'):
        m = re.search(pat, pres, re.S)
        if m:
            pres = pres[:m.end()] + lst + pres[m.end():]
            break
    else:
        # запасной вариант: перед defaultTextStyle, иначе перед закрытием presentation
        m = re.search(r'<p:defaultTextStyle\b', pres) or re.search(r'</p:presentation>', pres)
        pres = pres[:m.start()] + lst + pres[m.start():]

    data["[Content_Types].xml"] = ct.encode()
    data["ppt/_rels/presentation.xml.rels"] = rels.encode()
    data["ppt/presentation.xml"] = pres.encode()
    data.update(newfiles)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in data.items():
            z.writestr(n, b)
    return dst


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "css":
        print(build_css()[:200], "...")
    elif len(sys.argv) >= 2:
        print("embedded ->", embed_fonts(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
    else:
        # sanity: все файлы на месте?
        miss = [p for _, s in FACES for p in [s["reg"], s.get("bold")] if p and not os.path.exists(p)]
        print("MISSING:" if miss else "all fonts present", *miss, sep="\n")
