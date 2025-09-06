# EcoFinds - Sustainable Second-Hand Marketplace (MVP)

A minimal Flask-based MVP implementing the hackathon Problem Statement 1.

## Features
- Email/Password authentication (signup, login, logout)
- User dashboard (edit display name)
- Product listing CRUD (title, description, category, price, image URL placeholder)
- Browse listings with search (title) + category filter
- Product detail view
- Cart (add/remove)
- Checkout -> Order + Order Items
- Previous Purchases (order history)
- Responsive UI using Bootstrap

## Quick Start

### 1) Create & activate a virtualenv (recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Run the app (development)
```bash
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run
```
On Windows PowerShell:
```powershell
$env:FLASK_APP="app.py"
$env:FLASK_DEBUG="1"
flask run
```

Open: http://127.0.0.1:5000

**Default categories** are defined in `app.py` (`CATEGORIES`).

## Notes
- Uses SQLite (`instance/ecofinds.db`) – auto-created on first run.
- For demo purposes, image handling is by **image URL** or shows a placeholder if empty.
- Prices are stored as INTEGER (rupees).

## Project Structure
```
ecofinds/
  app.py
  requirements.txt
  templates/
    base.html
    index.html
    login.html
    signup.html
    product_form.html
    product_detail.html
    my_listings.html
    dashboard.html
    cart.html
    orders.html
  static/
    style.css
```

Good luck at the hackathon! 🚀
