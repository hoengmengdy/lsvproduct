# LSV

A complete Flask e-commerce application with customer accounts, catalog search
and filtering, cart, wishlist, checkout, orders, and a protected admin dashboard.

## Local setup (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into `SECRET_KEY` in `.env`, then initialize sample
data and create the first admin interactively:

```powershell
python seed.py
python app.py
```

Open <http://127.0.0.1:5000> for the store and
<http://127.0.0.1:5000/admin/login> for administration.

The SQLite database is created automatically at `database/shopping.db`. For
production, set `DATABASE_URL` to a PostgreSQL URL and configure secrets in the
hosting environment. Never commit `.env`.

## Tests

```powershell
python -m unittest discover -s tests -v
```
