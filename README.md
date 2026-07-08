# SpendWise

A personal finance tracker where you can log income and expenses, sort them into your own categories, and see where your money goes each month. Built with Django and Bootstrap.

Live app: https://spendwise-kz43.onrender.com

(It's hosted on Render's free tier, so the first load after a while can take around 30 seconds to wake up.)

## What it does

- Sign up, log in, and log out. Each user only sees their own data.
- A dashboard with totals for income, expenses, and balance, plus charts (Chart.js).
- Add, edit, and delete income and expense entries.
- Create your own categories with custom colours.
- Filter transactions by date range and category.
- Monthly reports broken down by category.
- Export your transactions to CSV.
- Set your currency and a monthly budget in your profile.
- Works on phones and desktops.

## Built with

- Python 3.13 and Django 6
- Bootstrap 5 and Chart.js for the frontend
- SQLite for local development (Postgres-ready through dj-database-url)
- Gunicorn as the server, deployed on Render

## Running it locally

You'll need Python 3.13 or newer and Git.

```bash
git clone https://github.com/Prem7105/SpendWise.git
cd SpendWise

python -m venv .venv
.venv\Scripts\activate        # on Windows
# source .venv/bin/activate   # on macOS or Linux

pip install -r requirements.txt
python manage.py migrate

python manage.py seed_demo     # optional, adds demo data (login: demo / demo12345)
python manage.py runserver
```

Then open http://127.0.0.1:8000/ in your browser.

## Project layout

```
spendwise/
  config/       project settings, urls, wsgi/asgi
  tracker/      the main app
    models.py   Profile, Category, Transaction
    views.py    dashboard, CRUD, reports, CSV export
    forms.py    forms
    urls.py     routes
    signals.py  creates a profile when a user signs up
    templates/  the HTML
  static/       css
  build.sh      Render build script
  requirements.txt
  manage.py
```

## Data model

- Profile holds a user's currency and monthly budget (one per user).
- Category belongs to a user, has a type (income or expense), and a colour.
- Transaction belongs to a user and a category, and stores the amount, date, type, and an optional note.

## Author

Prem Yadav
https://github.com/Prem7105
