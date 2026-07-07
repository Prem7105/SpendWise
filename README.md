# SpendWise — Personal Finance Tracker

A polished income & expense tracker built with **Django + Bootstrap 5**.

## Features
- 🔐 User registration, login & logout (Django auth)
- 📊 Dashboard with summary cards & interactive charts (Chart.js)
- 💵 Income & expense tracking with categories
- 🎨 Custom colour-coded categories
- 🔎 Filters by date range & category
- 📅 Monthly reports with category breakdown
- ⬇️ CSV export
- 👤 User profile with currency & monthly budget
- 📱 Responsive Bootstrap 5 UI

## Tech Stack
Python · Django · Bootstrap 5 · Chart.js · SQLite

## Run locally
```bash
git clone https://github.com/<your-username>/spendwise.git
cd spendwise
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo      # optional demo data (login: demo / demo12345)
python manage.py runserver
```
Open http://127.0.0.1:8000/

## What I Learned
- Django authentication & per-user data isolation
- ORM aggregation (`Sum`, `values().annotate()`, date filtering)
- ModelForms, templates, template inheritance, the messages framework
- Bootstrap 5 layout (sidebar, cards, responsive grid)
- Turning backend data into Chart.js charts
- CSV export, signals, context processors, and writing tests