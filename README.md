# EcoFinds (Rebuilt)

A clean, modern Flask app using Tailwind (via CDN) for UI. Compatible with **Flask 3.x**.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run
python app.py
# or
flask --app app run
```

## Demo Credentials
A demo user and a few products are auto-seeded:

- Email: `demo@ecofinds.local`
- Password: `demo1234`

## Notes
- Database: SQLite (`ecofinds.db`) created automatically.
- Tailwind: via CDN in `base.html`.
- Features: Auth (login/signup), product CRUD (create, view), cart, checkout, orders, dashboard.
