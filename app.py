"""Flask web application for the personal expense tracker."""

import logging
import os
from datetime import date
from decimal import Decimal, InvalidOperation

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg2 import Error

from db import DatabaseManager

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "local-development-key")

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

db_manager = DatabaseManager(database_url)


def _period_bounds(selected_month: str) -> tuple[str, str, str]:
    """Validate a YYYY-MM month and return start, exclusive end, and label."""
    try:
        year, month = (int(value) for value in selected_month.split("-"))
        start = date(year, month, 1)
    except (AttributeError, ValueError):
        raise ValueError("Choose a valid month.")
    end = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
    return start.isoformat(), end.isoformat(), start.strftime("%B %Y")


def _amount(value: str) -> Decimal:
    """Parse a positive currency amount."""
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError("Amount must be a valid number.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return amount


@app.template_filter("currency")
def currency(value: Decimal | None) -> str:
    return f"₹{(value or 0):,.2f}"


@app.route("/", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        try:
            db_manager.insert_expense(
                request.form["expense_date"],
                _amount(request.form["amount"]),
                request.form["category"].strip(),
                request.form["payment_method"].strip(),
                request.form.get("description", "").strip() or None,
                request.form.get("notes", "").strip() or None,
            )
            flash("Expense added successfully.", "success")
        except (KeyError, ValueError) as exc:
            flash(str(exc), "error")
        except Error:
            logger.exception("Could not add expense")
            flash("The expense could not be saved. Please try again.", "error")
        return redirect(url_for("dashboard", month=request.form.get("month")))

    month = request.args.get("month", date.today().strftime("%Y-%m"))
    try:
        start, end, month_label = _period_bounds(month)
        data = db_manager.get_dashboard_data(start, end)
    except (ValueError, Error):
        logger.exception("Could not load dashboard")
        flash("Choose a valid month and verify the database connection.", "error")
        month = date.today().strftime("%Y-%m")
        start, end, month_label = _period_bounds(month)
        data = db_manager.get_dashboard_data(start, end)
    category_labels = [row[0] for row in data["categories"]]
    category_values = [float(row[1]) for row in data["categories"]]
    monthly_map = {row[0]: row for row in data["monthly"]}
    return render_template(
        "dashboard.html",
        data=data,
        month=month,
        month_label=month_label,
        category_labels=category_labels,
        category_values=category_values,
        monthly_labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        monthly_expenses=[float(monthly_map.get(index, (index, 0, 0))[1] or 0)
                          for index in range(1, 13)],
        monthly_income=[float(monthly_map.get(index, (index, 0, 0))[2] or 0)
                        for index in range(1, 13)],
    )


@app.route("/income", methods=["POST"])
def add_income():
    try:
        source = request.form["source"].strip()
        if not source:
            raise ValueError("Source is required.")
        db_manager.insert_income(
            request.form["income_date"],
            _amount(request.form["amount"]),
            source,
            request.form.get("category", "Other income").strip() or "Other income",
            request.form.get("description", "").strip() or None,
            request.form.get("notes", "").strip() or None,
        )
        flash("Income added successfully.", "success")
    except (KeyError, ValueError) as exc:
        flash(str(exc), "error")
    except Error:
        logger.exception("Could not add income")
        flash("The income could not be saved. Please try again.", "error")
    return redirect(url_for("dashboard", month=request.form.get("month")))


@app.route("/queries", methods=["GET", "POST"])
def queries():
    query = request.form.get("query", "") if request.method == "POST" else ""
    results = []
    error = None
    if request.method == "POST":
        try:
            results = db_manager.execute_query(query)
        except (ValueError, Error) as exc:
            logger.warning("Read-only query rejected or failed: %s", exc)
            error = str(exc)
        except Exception:
            logger.exception("Unexpected query dashboard error")
            error = "The query could not be executed."
    columns = list(results[0].keys()) if results else []
    return render_template("queries.html", query=query, results=results,
                           columns=columns, error=error)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "").lower() == "true")
