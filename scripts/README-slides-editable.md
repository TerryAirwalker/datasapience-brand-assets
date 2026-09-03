# Data Sapience — редактируемая сборка презентаций (Режим A)

Детерминированный конвейер: **HTML-макет → редактируемый .pptx с живым текстом и встроенными
шрифтами**, бренд-верный по вёрстке. Заменяет ручную расстановку текстовых рамок.

## Файлы
- `ds_fonts.py` — @font-face CSS (base64) для Chromium + встраивание шрифтов в .pptx
  (`p:embeddedFontLst`). Каждый вес — отдельное имя гарнитуры (typeface), поэтому Unbounded
  SemiBold/ExtraBold/Medium и Ping LCG Medium/Light сохраняют начертание.
- `html_to_pptx.py` — движок: рендерит фон (текст скрыт), снимает bbox+стили каждого
  текстового блока из HTML (Playwright `getBoundingClientRect` + computed style), кладёт живой
  текст точно по координатам, встраивает шрифты.

## Подготовка
1. Скачай оба скрипта из `datasapience-brand-assets/scripts/`.
2. Распакуй `fonts/Unbounded.zip` и `fonts/PingLCG.zip` (внутри `.ttf`). Скрипт ищет шрифты
   автоматически ($DS_FONT_DIR → ./fonts → ../fonts → /workspace). При нестандартном месте —
   `export DS_FONT_DIR=/путь/к/распакованным/шрифтам`.
3. Зависимости уже есть в рантайме: `python-pptx`, `playwright` (chromium), Pillow.

## Контракт авторинга HTML (по одному файлу на слайд, 1920×1080)
- Холст ровно `1920×1080` px (16:9 = canvas 12192000×6858000 EMU). **Кегль в px = pt × 2**
  (обложка 36–48pt → 72–96px; заголовок слайда 24–32pt → 48–64px; текст 14–16pt → 28–32px).
- **Декор** (фон/градиент, блобы-шестиугольники #CAE7EF/#4F9AAB, логотип, знак ds, номер,
  карточки-контейнеры, бейджи) — обычными div/img; он запечётся в фон.
- **Каждый текстовый блок** — элемент с классом `t`, `position:absolute; left; top; width`.
  Шрифты — семейства `'Unbounded'` и `'Ping LCG'` со стандартными `font-weight`
  (Unbounded 400/500/600/700/800; Ping LCG 300/400/500/700) — @font-face внедряется движком.
  - Акцентные цвет/вес внутри блока — вложенным `<span style="color:…;font-weight:…">`.
  - Перенос строки в блоке — `<br>` (станет новым абзацем).
  - Однострочные метки/цифры — атрибут `data-nowrap` (без переноса, +запас ширины).
  - Вертикальное выравнивание в рамке — `data-valign="middle"` / `"bottom"`.
- Цвета/размеры/фоны — строго из манифеста (`colors`, `typography.on_slides`,
  `slides.backgrounds`); фон по тону чередовать (≤2 слайдов одного тона подряд).

## Сборка
```bash
python3 html_to_pptx.py cover.html content.html section.html -o deck.pptx
```
Результат — `deck.pptx`: текст живой (редактируемый), шрифты встроены. Проверь рендером
LibreOffice→PDF→PNG (текст в контейнерах, без переноса по слогам, вёрстка = HTML).

Референс-макеты см. `cover.html` / `content.html` (обложка dark_blob и контент light_blob).
