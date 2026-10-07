# Ledgerly Expense Tracker

Ledgerly is a browser-based personal finance tracker built with Flask and
PostgreSQL (including Neon). It preserves the existing `expenses` table and
adds a separate `income` table for salary and other credits.

## What it does

- Dashboard with monthly income, expenditure, net balance, and entry counts.
- Salary received KPI for the selected month (salary is an income category).
- Cash-flow chart comparing income and expenses across the selected year.
- Expense-by-category chart generated from the database.
- Separate forms for recording expenses and income.
- Query lab that displays read-only SQL results in a table.
- Existing expense records remain untouched.

## Requirements

- Python 3.11 or newer
- A PostgreSQL database or Neon project
- A database URL with SSL enabled, for example:
  `postgresql://user:password@host.neon.tech/neondb?sslmode=require`

## Setup on Windows

From PowerShell in this folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set:

```dotenv
DATABASE_URL=postgresql://user:password@host.neon.tech/neondb?sslmode=require
SECRET_KEY=replace-with-a-long-random-value
FLASK_DEBUG=false
```

Never commit `.env`. It is ignored by Git.

## Start the web application

```powershell
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:5000** in a browser. Keep the PowerShell process
running while using the app. To stop it, press `Ctrl+C`.

Use the project virtual-environment interpreter explicitly. If `python.exe`
resolves to a different system installation, it may not have Flask,
`python-dotenv`, or the PostgreSQL driver installed:

```powershell
.\.venv\Scripts\python.exe app.py
```

If port 5000 is already occupied by an older server, stop that server first
with `Ctrl+C`, or start this app on another port:

```powershell
$env:FLASK_PORT=5001
.\.venv\Scripts\python.exe app.py
```

Then open **http://127.0.0.1:5001**.

The application creates the additive `income` table automatically on first
start. It does not migrate, rewrite, or delete any row in `expenses`.

## Database schema

The existing table remains:

```sql
expenses (
  id, expense_date, amount, category, payment_method,
  description, notes, created_at, updated_at
)
```

The web app creates this separate table:

```sql
CREATE TABLE income (
  id BIGSERIAL PRIMARY KEY,
  income_date DATE NOT NULL,
  amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  source VARCHAR(100) NOT NULL,
  category VARCHAR(100) NOT NULL DEFAULT 'Other income',
  description VARCHAR(255),
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Choose **Salary** as the income category when recording monthly salary. The
dashboard's month selector can be set to September 2026 or any later month.

## Query lab

Use the **Query lab** navigation item to run read-only `SELECT` statements.
Examples:

```sql
SELECT * FROM expenses
ORDER BY expense_date DESC
LIMIT 25;

SELECT category, SUM(amount) AS total
FROM expenses
GROUP BY category
ORDER BY total DESC;

SELECT * FROM income
ORDER BY income_date DESC;
```

The server rejects statements that do not begin with `SELECT`. Use the entry
forms for inserts so validation and parameterized queries are preserved.

## Project structure

```text
app.py                 Flask routes and request validation
db.py                  PostgreSQL pool, schema, writes, and reports
templates/base.html    Shared layout and navigation
templates/dashboard.html
templates/queries.html
static/app.css         Responsive dashboard styling
requirements.txt       Python dependencies
.env.example           Environment variable template
```

## Troubleshooting

- **`DATABASE_URL` is not set:** copy `.env.example` to `.env` and fill in the
  Neon connection string.
- **Connection or SSL errors:** copy the connection string from Neon and keep
  `sslmode=require`.
- **Port 5000 is busy:** run `app.run(port=5001)` temporarily in `app.py` and
  browse to `http://127.0.0.1:5001`.
- **Charts do not render:** the chart library is loaded from Plotly's CDN, so
  the browser needs internet access; the tables and forms still work without
  chart rendering.
