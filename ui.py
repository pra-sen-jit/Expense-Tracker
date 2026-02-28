"""
UI module for Expense Tracker application.

Handles all GUI components and user interactions using PySide6 (Qt for Python).
"""

import logging
from decimal import Decimal
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QDateEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QGroupBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QPainter
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from db import DatabaseManager
from psycopg2 import Error

logger = logging.getLogger(__name__)


class ExpenseTrackerUI(QMainWindow):
    """Main application window for the expense tracker."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the UI.

        Args:
            db_manager: DatabaseManager instance for database operations
        """
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("Expense Tracker")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()

        # Create left panel (form)
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel, 1)

        # Create right panel (query and results)
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel, 1)

        central_widget.setLayout(main_layout)
        self._refresh_monthly_chart(self.year_selector.value())

    def _create_left_panel(self) -> QGroupBox:
        """Create the form panel for adding expenses."""
        group = QGroupBox("Add New Expense")
        layout = QVBoxLayout()

        # Title font
        title_font = QFont()
        title_font.setBold(True)

        # Date input
        layout.addWidget(QLabel("Expense Date:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self.date_input)

        # Amount input
        layout.addWidget(QLabel("Amount ($):"))
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMinimum(0.0)
        self.amount_input.setMaximum(999999.99)
        self.amount_input.setDecimals(2)
        layout.addWidget(self.amount_input)

        # Category input
        layout.addWidget(QLabel("Category:"))
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("e.g., Food, Transportation")
        layout.addWidget(self.category_input)

        # Payment method input
        layout.addWidget(QLabel("Payment Method:"))
        self.payment_method_input = QLineEdit()
        self.payment_method_input.setPlaceholderText("e.g., Cash, Credit Card")
        layout.addWidget(self.payment_method_input)

        # Description input
        layout.addWidget(QLabel("Description:"))
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Optional description")
        layout.addWidget(self.description_input)

        # Notes input
        layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Optional notes")
        self.notes_input.setMaximumHeight(100)
        layout.addWidget(self.notes_input)

        # Add Expense button
        self.add_button = QPushButton("Add Expense")
        self.add_button.clicked.connect(self._on_add_expense)
        layout.addWidget(self.add_button)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def _create_right_panel(self) -> QGroupBox:
        """Create the query execution and results panel."""
        group = QGroupBox("Query Executor")
        layout = QVBoxLayout()

        # Query input
        layout.addWidget(QLabel("Custom SQL (SELECT only):"))
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText(
            "Example: SELECT * FROM expenses WHERE amount > 50 ORDER BY expense_date DESC"
        )
        self.query_input.setMaximumHeight(100)
        layout.addWidget(self.query_input)

        # Run Query button
        self.run_query_button = QPushButton("Run Query")
        self.run_query_button.clicked.connect(self._on_run_query)
        layout.addWidget(self.run_query_button)

        # Results table
        layout.addWidget(QLabel("Results:"))
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(0)
        self.results_table.setRowCount(0)
        layout.addWidget(self.results_table)

        # Query status label
        self.query_status_label = QLabel("")
        self.query_status_label.setWordWrap(True)
        layout.addWidget(self.query_status_label)

        # Monthly chart controls
        layout.addWidget(QLabel("Monthly Expenses (Year-wise):"))
        chart_controls_layout = QHBoxLayout()
        chart_controls_layout.addWidget(QLabel("Year:"))

        self.year_selector = QSpinBox()
        self.year_selector.setRange(2000, 2100)
        self.year_selector.setValue(QDate.currentDate().year())
        chart_controls_layout.addWidget(self.year_selector)

        self.refresh_chart_button = QPushButton("Show Monthly Chart")
        self.refresh_chart_button.clicked.connect(self._on_refresh_chart)
        chart_controls_layout.addWidget(self.refresh_chart_button)
        chart_controls_layout.addStretch()
        layout.addLayout(chart_controls_layout)

        self.monthly_chart = QChart()
        self.monthly_chart_view = QChartView(self.monthly_chart)
        self.monthly_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.monthly_chart_view.setMinimumHeight(260)
        layout.addWidget(self.monthly_chart_view)

        group.setLayout(layout)
        return group

    def _on_add_expense(self) -> None:
        """Handle the Add Expense button click."""
        try:
            # Validate required fields
            expense_date = self.date_input.date().toString("yyyy-MM-dd")
            amount = self.amount_input.value()
            category = self.category_input.text().strip()
            payment_method = self.payment_method_input.text().strip()
            description = self.description_input.text().strip() or None
            notes = self.notes_input.toPlainText().strip() or None

            if not category:
                self._show_error("Please enter a category")
                return

            if not payment_method:
                self._show_error("Please enter a payment method")
                return

            if amount <= 0:
                self._show_error("Amount must be greater than 0")
                return

            # Insert expense
            expense_id = self.db_manager.insert_expense(
                expense_date=expense_date,
                amount=amount,
                category=category,
                payment_method=payment_method,
                description=description,
                notes=notes
            )

            # Show success message
            self._show_success(f"Expense added successfully (ID: {expense_id})")

            # Clear form
            self._clear_form()

            # Refresh chart if inserted expense belongs to selected year
            inserted_year = int(expense_date.split("-")[0])
            if inserted_year == self.year_selector.value():
                self._refresh_monthly_chart(inserted_year)

        except Error as e:
            self._show_error(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Error adding expense: {e}")
            self._show_error(f"Error: {str(e)}")

    def _on_run_query(self) -> None:
        """Handle the Run Query button click."""
        try:
            query = self.query_input.toPlainText().strip()

            if not query:
                self._show_query_error("Please enter a query")
                return

            # Execute query
            results = self.db_manager.execute_query(query)

            # Display results
            self._display_results(results)
            self._show_query_success(f"Query executed successfully ({len(results)} rows)")

        except ValueError as e:
            self._show_query_error(f"Invalid query: {str(e)}")
        except Error as e:
            self._show_query_error(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Error running query: {e}")
            self._show_query_error(f"Error: {str(e)}")

    def _display_results(self, results: list) -> None:
        """
        Display query results in the table widget.

        Args:
            results: List of dictionaries with query results
        """
        self.results_table.clear()

        if not results:
            self.results_table.setColumnCount(0)
            self.results_table.setRowCount(0)
            return

        # Get column names from first result
        columns = list(results[0].keys())
        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(columns)

        # Set number of rows
        self.results_table.setRowCount(len(results))

        # Populate table
        for row_idx, result in enumerate(results):
            for col_idx, column in enumerate(columns):
                value = result.get(column, "")
                # Convert to string for display
                if isinstance(value, Decimal):
                    value = f"${value:.2f}"
                elif isinstance(value, (datetime,)):
                    value = value.isoformat()

                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.results_table.setItem(row_idx, col_idx, item)

        # Resize columns to content
        self.results_table.resizeColumnsToContents()

    def _on_refresh_chart(self) -> None:
        """Handle the monthly chart refresh action for the selected year."""
        selected_year = self.year_selector.value()
        self._refresh_monthly_chart(selected_year)

    def _refresh_monthly_chart(self, year: int) -> None:
        """
        Load monthly totals for a year and render a bar chart.

        Args:
            year: Year to visualize
        """
        try:
            results = self.db_manager.get_monthly_totals_by_year(year)

            month_totals = {month: 0.0 for month in range(1, 13)}
            for row in results:
                month = int(row["month"])
                total_amount = float(row["total_amount"] or 0)
                month_totals[month] = total_amount

            chart = QChart()
            chart.setTitle(f"Monthly Total Expenses - {year}")

            bar_set = QBarSet(str(year))
            for month in range(1, 13):
                bar_set.append(month_totals[month])

            series = QBarSeries()
            series.append(bar_set)
            chart.addSeries(series)

            month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            axis_x = QBarCategoryAxis()
            axis_x.append(month_labels)
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axis_x)

            axis_y = QValueAxis()
            max_total = max(month_totals.values())
            axis_y.setRange(0, (max_total * 1.1) if max_total > 0 else 10)
            axis_y.setLabelFormat("%.2f")
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_y)

            chart.legend().setVisible(False)
            self.monthly_chart_view.setChart(chart)
            self._show_query_success(f"Monthly chart loaded for {year}")

        except Error as e:
            self._show_query_error(f"Database error while loading chart: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading monthly chart: {e}")
            self._show_query_error(f"Error while loading chart: {str(e)}")

    def _clear_form(self) -> None:
        """Clear all form inputs."""
        self.date_input.setDate(QDate.currentDate())
        self.amount_input.setValue(0.0)
        self.category_input.clear()
        self.payment_method_input.clear()
        self.description_input.clear()
        self.notes_input.clear()

    def _show_success(self, message: str) -> None:
        """
        Show success message in the status label.

        Args:
            message: Message to display
        """
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: green;")
        logger.info(message)

    def _show_error(self, message: str) -> None:
        """
        Show error message in the status label.

        Args:
            message: Message to display
        """
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: red;")
        logger.warning(message)

    def _show_query_success(self, message: str) -> None:
        """
        Show success message in the query status label.

        Args:
            message: Message to display
        """
        self.query_status_label.setText(message)
        self.query_status_label.setStyleSheet("color: green;")
        logger.info(message)

    def _show_query_error(self, message: str) -> None:
        """
        Show error message in the query status label.

        Args:
            message: Message to display
        """
        self.query_status_label.setText(message)
        self.query_status_label.setStyleSheet("color: red;")
        logger.warning(message)

    def closeEvent(self, event):
        """
        Handle window close event.

        Args:
            event: Close event
        """
        self.db_manager.close()
        event.accept()
