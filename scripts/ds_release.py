#!/usr/bin/env python3
"""DS unified release tool — единая версионность + публикация.

Проставляет один номер сборки во ВСЕ источники и публикует их в оба репо,
плюс ставит git-тег. Запускать на каждое изменение брендбука/манифеста/скилла.

Использование:
    python3 ds_release.py 2.7                 # проштамповать + опубликовать + тег
    python3 ds_release.py 2.7 --no-publish     # только локально проставить версию
    python3 ds_release.py 2.7 --date 18.06.2026

Источник правды версии — manifest.meta.version. Брендбук показывает v<major> · сборку.

ВАЖНО (архитектура managed skills): ~/.claude/skills/datasapience-design/SKILL.md
физически read-only — Chat App материализует managed-скиллы в сессию только на чтение.
Поэтому SKILL здесь указывает на staging-копию в /workspace/datasapience-design/SKILL.md
(конвенция skill_save: скопировать ~/.claude/skills/<name> -> /workspace/<name>, править,
зазипить, вызвать mcp__chatapp_provided_mcp_tools__skill_save). Этот скрипт публикует
staging-копию в оба репо через API, но НЕ обновляет установленный в сессии managed-скилл —
это отдельный шаг, который должен сделать агент (zip + skill_save) после запуска релиза.
"""
import sys, os, json, re, base64, urllib.request, urllib.error, time, datetime

MANIFEST  = "/workspace/manifest.json"
BRANDBOOK = "/workspace/Брендбук Data Sapience v1.html"
SKILL     = "/workspace/datasapience-design/SKILL.md"
SETTINGS  = "/home/sandbox/.claude/settings.json"
GH_TOKEN_FILE = "/workspace/.gh_token"  # durable fallback (workspace-диск переживает рестарт рантайма)

# Хелперы самопроверки — публикуются в репо ассетов (scripts/), чтобы быть durable.
HELPERS = {
    "blob_check.py": "/workspace/blob_check.py",   # автопроверка отрисовки блобов
    "ru_typo.py":    "/workspace/ru_typo.py",      # висячие предлоги (неразрывные пробелы)
    "ds_release.py": "/workspace/ds_release.py",   # сам этот релиз-тул (самопубликация)
}

def parse_args():
    if len(sys.argv) < 2:
        sys.exit("usage: ds_release.py <version> [--no-publish] [--no-tag] [--date DD.MM.YYYY]")
    ver = sys.argv[1].lstrip("v")
    publish = "--no-publish" not in sys.argv
    tag = "--no-tag" not in sys.argv
    date_disp = None
    if "--date" in sys.argv:
        date_disp = sys.argv[sys.argv.index("--date") + 1]
    if not date_disp:
        t = datetime.date.today()
        date_disp = t.strftime("%d.%m.%Y")
    iso = "-".join(reversed(date_disp.split("."))) if "." in date_disp else date_disp
    return ver, publish, tag, date_disp, iso

def stamp_manifest(ver, iso):
    m = json.load(open(MANIFEST, encoding="utf-8"))
    old = m["meta"].get("version")
    m["meta"]["version"] = ver
    m["meta"]["updated"] = iso
    json.dump(m, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.load(open(MANIFEST, encoding="utf-8"))  # validate
    print(f"  manifest.json: meta.version {old} -> {ver}, updated {iso}")

def _sub_class(html, cls, value):
    """Replace inner text of ALL <b class="cls">…</b> — версия отображается в нескольких местах."""
    pat = re.compile(r'(<b class="%s"[^>]*>)(.*?)(</b>)' % re.escape(cls), re.S)
    new, n = pat.subn(lambda mm: mm.group(1) + value + mm.group(3), html)
    if n < 1:
        raise SystemExit(f"ABORT: class .{cls} not found in brandbook")
    return new, n

def stamp_brandbook(ver, date_disp):
    html = open(BRANDBOOK, encoding="utf-8").read()
    major = "v" + ver.split(".")[0]
    html, a = _sub_class(html, "ds-major", major)
    html, b = _sub_class(html, "ds-build", ver)
    html, c = _sub_class(html, "ds-date", date_disp)
    open(BRANDBOOK, "w", encoding="utf-8").write(html)
    print(f"  brandbook: {major} · сборка {ver} · {date_disp}  (обновлено вхождений: major={a}, build={b}, date={c})")

def stamp_skill(ver):
    if not os.path.exists(SKILL):
        os.makedirs(os.path.dirname(SKILL), exist_ok=True)
        installed = "/home/sandbox/.claude/skills/datasapience-design/SKILL.md"
        if os.path.exists(installed):
            import shutil; shutil.copy(installed, SKILL)
        else:
            raise SystemExit(f"ABORT: {SKILL} not found and no installed skill to seed from")
    txt = open(SKILL, encoding="utf-8").read()
    new, n = re.subn(r'(\*\*Версия скилла:\s*)([0-9.]+)(\*\*)',
                     lambda mm: mm.group(1) + ver + mm.group(3), txt, count=1)
    if n != 1:
        raise SystemExit(f"ABORT: skill version line matched {n} times")
    open(SKILL, "w", encoding="utf-8").write(new)
    print(f"  SKILL.md (staging {SKILL}): Версия скилла -> {ver}")
    print(f"  NOTE: установленный managed-скилл НЕ обновлён автоматически — "
          f"зазипь {os.path.dirname(SKILL)} и вызови skill_save() отдельно.")

# ── GitHub publish/tag ──────────────────────────────────────────────────────
def resolve_token():
    """settings.json env → process env → durable file; самовосстанавливает settings.json из файла."""
    tok = ""
    try:
        tok = json.load(open(SETTINGS)).get("env", {}).get("GITHUB_TOKEN", "") or ""
    except Exception:
        pass
    if not tok:
        tok = os.environ.get("GITHUB_TOKEN", "") or ""
    if not tok and os.path.exists(GH_TOKEN_FILE):
        tok = open(GH_TOKEN_FILE).read().strip()
        try:  # self-heal: вернуть токен в settings.json
            s = json.load(open(SETTINGS)); s.setdefault("env", {})["GITHUB_TOKEN"] = tok
            json.dump(s, open(SETTINGS, "w"), ensure_ascii=False, indent=2); os.chmod(SETTINGS, 0o600)
        except Exception:
            pass
    return tok

def gh():
    try:
        user = json.load(open(SETTINGS)).get("env", {}).get("GITHUB_USER", "TerryAirwalker")
    except Exception:
        user = "TerryAirwalker"
    return resolve_token(), user

def api(method, url, token, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Authorization": f"token {token}", "Accept": "application/vnd.github+json", "User-Agent": "ds-release"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r: return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try: return e.code, json.load(e)
        except Exception: return e.code, {"raw": e.read().decode(errors="replace")}

def put_file(token, user, repo, path, local, msg):
    url = f"https://api.github.com/repos/{user}/{repo}/contents/{path}"
    st, cur = api("GET", url, token); sha = cur.get("sha") if st == 200 else None
    payload = {"message": msg, "content": base64.b64encode(open(local, "rb").read()).decode(), "branch": "main"}
    if sha: payload["sha"] = sha
    for _ in range(3):
        st, res = api("PUT", url, token, payload)
        if st in (200, 201): return st
        if st == 409 or "secondary rate" in json.dumps(res).lower(): time.sleep(45); continue
        return (st, res)
    return st

def tag_release(token, user, repo, ver):
    st, ref = api("GET", f"https://api.github.com/repos/{user}/{repo}/git/refs/heads/main", token)
    sha = ref.get("object", {}).get("sha")
    if not sha: return f"no main sha ({st})"
    name = f"refs/tags/v{ver}"
    st, res = api("POST", f"https://api.github.com/repos/{user}/{repo}/git/refs", token,
                  {"ref": name, "sha": sha})
    if st == 422:  # exists -> move it
        st, res = api("PATCH", f"https://api.github.com/repos/{user}/{repo}/git/refs/tags/v{ver}", token,
                      {"sha": sha, "force": True})
    return st

def main():
    ver, publish, tag, date_disp, iso = parse_args()
    assert TOKEN_OK_GUARD(), "token must not be in SKILL.md"
    print(f"== DS release v{ver} ({date_disp}) ==")
    stamp_manifest(ver, iso); stamp_brandbook(ver, date_disp); stamp_skill(ver)
    if not publish:
        print("Stamped locally (--no-publish)."); return
    token, user = gh()
    jobs = [
        ("datasapience-brandbook", "index.html", BRANDBOOK, f"Release v{ver}: brandbook"),
        ("datasapience-brandbook", "manifest.json", MANIFEST, f"Release v{ver}: manifest"),
        ("datasapience-brandbook", "skill/datasapience-design/SKILL.md", SKILL, f"Release v{ver}: skill"),
        ("datasapience-brand-assets", "skill/datasapience-design/SKILL.md", SKILL, f"Release v{ver}: skill"),
    ]
    # хелперы самопроверки → репо ассетов / scripts/ (durable)
    for fn, local in HELPERS.items():
        if os.path.exists(local):
            jobs.append(("datasapience-brand-assets", f"scripts/{fn}", local, f"Release v{ver}: helper {fn}"))
        else:
            print(f"  skip helper {fn}: {local} not found")
    for repo, path, local, msg in jobs:
        print(f"  publish {repo}/{path}: {put_file(token, user, repo, path, local, msg)}")
    if tag:
        for repo in ("datasapience-brandbook", "datasapience-brand-assets"):
            print(f"  tag v{ver} on {repo}: {tag_release(token, user, repo, ver)}")
    print("Done.")

def TOKEN_OK_GUARD():
    tok = resolve_token()
    return tok and tok not in open(SKILL, encoding="utf-8").read() if os.path.exists(SKILL) else tok

if __name__ == "__main__":
    main()
