# Data Sapience — фирменные ассеты

Брендбук: https://TerryAirwalker.github.io/datasapience-brandbook/
Манифест для ИИ-агента: https://TerryAirwalker.github.io/datasapience-brandbook/manifest.json

## Структура
- `logos/svg/` — логотип DS (full/symbol/text, ч/б); `logos/png/variants/` — 12 PNG: horizontal/stacked/side/symbol × black/blue/white (полный набор версий)
- `logos/products/` — исходники логотипов продуктов (svg/ai/zip); `logos/products/png/` — готовые превью (cm-ocean, kolmogorov, talys, data-ocean-governance, `data-ocean/` — Nova/Flex Loader/SDI, `industrial-ocean/` — Industrial Ocean); `logos/products/svg/industrial-ocean/` — SVG Industrial Ocean (horizontal/vertical/icon/text × color/white/black, исходные цвета продукта — не перекрашивать)
- `fonts/` — Unbounded, Ping LCG
- `templates/` — `Data-Sapience-template.pptx` (фоны, типы слайдов, иконки, шрифты)
- `icons/` — превью (светлая/тёмная) + icons-png-800.zip (340 PNG)
- `patterns/{png,eps,ai}` — 12 паттернов (Blob/Glow 01–03, Filled 04–06, Outline 07–09, Ribbon 10–12)
- `gradients/{png,eps,ai}` — 3 градиента
- `graphics/` — 3D-элементы (кольцо, объёмный знак, шестиугольник) и `hexagon.svg` — фирменная форма блоба
- `backgrounds/` — эталонные фоны слайдов
- `examples/` — эталон качества `CVM-эталон.pptx`
- `scripts/` — хелперы агента: `blob_check.py` (проверка блобов), `ru_typo.py` (неразрывные пробелы), `html_to_pptx.py` + `ds_fonts.py` (редактируемая .pptx), `ds_release.py` (релиз брендбука)
- `skill/datasapience-design/SKILL.md` — публичный скилл агента по дизайну

## Чего нет
- Логотип линейки **Data Ocean** (другой брендинг → dataplatform.ru)

## Тексты
Описания компании и продуктов — в `manifest.products` и во вкладке брендбука «Описания компании и продуктов». Состав продуктов синхронизируется с сайтами https://datasapience.ru/ («Платформы и продукты») и https://dataplatform.ru/ («Продукты»); Google-таблица больше не используется.

## Контакт
Маркетинг: ms@datasapience.ru (Марика Саар — руководитель маркетинга).
