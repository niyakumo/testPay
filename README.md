## Local dev

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
mkdocs serve
```

## Deploy

```bash
git push origin main  # workflow публикует в gh-pages
```
