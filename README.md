# dupekiller

First public upload: 2026-05-09

Локальный чистильщик дублей. Без API, без LLM, без отправки файлов наружу.

Что есть сейчас:

- точные дубли через `SHA-256`;
- похожие фото и скриншоты через `dHash`;
- похожие текстовые документы и PDF через `simhash`;
- локальные ML-эмбеддинги документов: `TfidfVectorizer` + `TruncatedSVD` из `scikit-learn`, затем cosine similarity;
- SQLite-кеш, чтобы повторный скан не пересчитывал всё заново;
- HTML + JSON отчет;
- безопасный карантин вместо удаления.

## Где тут ML

Группы `ml-doc-*` строятся локально: приложение читает текст/PDF, обучает векторизатор на найденном корпусе документов, сжимает признаки через SVD в embedding-пространство и сравнивает документы по cosine similarity. Никаких внешних API и скачивания модели не требуется.

## Установка

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Скан

```powershell
python -m dupekiller scan "D:\Photos"
```

Отчет появится здесь:

```text
dupekiller-report\index.html
dupekiller-report\report.json
```

Настройки:

```powershell
python -m dupekiller scan "D:\Photos" --image-threshold 6 --text-threshold 12 --ml-threshold 0.80 --min-size 1024 --workers 8
```

Чем выше threshold, тем строже матчинг похожих файлов. ML-эмбеддинги документов включены по умолчанию, отключить можно через `--no-ml`.

## Карантин

Сначала dry-run:

```powershell
python -m dupekiller quarantine dupekiller-report\report.json --dry-run
```

Потом перенос:

```powershell
python -m dupekiller quarantine dupekiller-report\report.json --apply --keep shortest
```

Варианты `--keep`: `shortest`, `newest`, `oldest`, `largest`.

Файлы не удаляются. Они переезжают в:

```text
<scanned-folder>\.quarantine\<timestamp>\
```

## Smoke test

```powershell
python scripts\smoke.py
```

